"""fand server"""

import abc
import argparse
import concurrent.futures
import configparser
import datetime
import enum
import logging
import os
import signal
import socket

import psutil
import pySMART as pysmart

import fand.util as util
import fand.communication as com

# Constants
# Module docstring
__DOCSTRING__ = __doc__
# Logger to use
logger = logging.getLogger(__name__)

# Global variables
# Dictionnary of shelves, key = shelf ID
__SHELVES__ = {}


class Device:
    """Class handling devices to get temperature from
    Attributes:
    serial: serial number, string
    position: drive positionning information, string
    device: DeviceWrapper
    """
    def __init__(self, serial, position):
        """Constructor"""
        self.serial = serial
        self.position = position
        self.__device = self.find()
        logger.info("New device %s created", self)

    def __str__(self):
        return f"{str(self.serial)} at {str(self.position)}"

    def find(self):
        """Search device on the system"""
        if self.serial == 'cpu':
            if psutil.sensors_temperatures().get('coretemp') is not None:
                logger.debug("Identified host CPU")
                return Device._CpuWrapper()
            logger.debug("Cannot access CPU informations")
            return Device._NoneDevice()
        for device in pysmart.DeviceList().devices:
            if device.serial == self.serial:
                if not device.is_ssd:
                    logger.debug("Identified HDD %s", self.serial)
                    return Device._HddWrapper(device)
                logger.debug("Identified SSD %s", self.serial)
                return Device._SsdWrapper(device)
        logger.error("Device not found: %s", self.serial)
        return Device._NoneDevice()

    def update(self):
        """Update device informations"""
        logger.debug("Updating device %s", self)
        self.__device.update()
        if self.__device.serial != self.serial:
            self.__device = self.find()

    @property
    def temperature(self):
        """Get current drive temperature"""
        return self.__device.temperature

    @property
    def type(self):
        """DeviceType"""
        return self.__device.type

    class DeviceType(enum.Enum):
        """Enumeration of device types, to identify Device objects"""
        NONE = 0
        HDD = 1
        SSD = 2
        CPU = 3

    class _DeviceWrapper(abc.ABC):
        """Abstract class for device wrappers"""
        @abc.abstractmethod
        def update(self):
            """Update the device informations"""

        @property
        @abc.abstractmethod
        def temperature(self):
            """Current device temperature"""

        @property
        @abc.abstractmethod
        def serial(self):
            """Current device serial"""

        @property
        @abc.abstractmethod
        def type(self):
            """Device type"""

    class _HddWrapper(_DeviceWrapper):
        """Wrapper class for HDDs"""
        def __init__(self, device):
            self.pysmart = device

        def update(self):
            self.pysmart.update()

        @property
        def temperature(self):
            return self.pysmart.temperature

        @property
        def serial(self):
            return self.pysmart.serial

        @property
        def type(self):
            return Device.DeviceType.HDD

    class _SsdWrapper(_DeviceWrapper):
        """wrapper class for SSDs"""
        def __init__(self, device):
            self.pysmart = device

        def update(self):
            self.pysmart.update()

        @property
        def temperature(self):
            return self.pysmart.temperature

        @property
        def serial(self):
            return self.pysmart.serial

        @property
        def type(self):
            return Device.DeviceType.SSD

    class _CpuWrapper(_DeviceWrapper):
        """Wrapper class for host CPU"""
        def update(self):
            pass

        @property
        def temperature(self):
            return max(temp.current
                       for temp in psutil.sensors_temperatures()['coretemp'])

        @property
        def serial(self):
            return 'cpu'

        @property
        def type(self):
            return Device.DeviceType.CPU

    class _NoneDevice(_DeviceWrapper):
        """Wrapper for missing devices"""
        def update(self):
            pass

        @property
        def temperature(self):
            return 0

        @property
        def serial(self):
            return None

        @property
        def type(self):
            return Device.DeviceType.NONE


class Shelf:
    """Class handling shelf data
    Attributes:
    identifier: shelf identifier, string
    pwm: pwm speed of the shelf, float, percentage
    rpm: rpm of the shelf, float
    sleep_time: how many seconds to wait between each shelf update
    __devices: dictionnary, key = device serial (string),
        value = Device instance
    __temperatures: dictionnary of dictionnaries
        {DeviceType: {temperature in deg C: pwm speed in percent}}
    """
    def __init__(self, identifier, devices, sleep_time=60, hdd_temps=None,
                 ssd_temps=None, cpu_temps=None):
        """Constructor
        idenifier: shelf id
        devices: list of Device instances
        hdd_temps: dictionnary in the format `temp in deg C: speed in percent`,
            must have a 0 temperature key
        ssd_temps: dictionnary in the same format as hdd_temps
        cpu_temps: dictionnary in the same format as hdd_temps
        """
        logger.debug("Creating new shelf %s", identifier)
        self.identifier = identifier
        self.__devices = {device.serial: device for device in devices}
        self.__temperatures = {
            Device.DeviceType.NONE: {0: 0},
            Device.DeviceType.HDD: {0: 0} if hdd_temps is None else hdd_temps,
            Device.DeviceType.SSD: {0: 0} if ssd_temps is None else ssd_temps,
            Device.DeviceType.CPU: {0: 0} if cpu_temps is None else cpu_temps,
        }
        for dev_type, dev_temps in self.__temperatures.items():
            if dev_temps.get(0) is None:
                logger.critical("%s has no 0 temperature configured: %s",
                                dev_type, dev_temps)
                raise ValueError(f"{dev_type} has no 0 temperature")
        self.__pwm = 100
        self.rpm = 0
        self.__pwm_override = None
        self.pwm_expire = None
        self.sleep_time = sleep_time

    def __str__(self):
        return self.identifier

    def __iter__(self):
        return iter(self.__devices.values())

    @property
    def rpm(self):
        """Shelf fan speed RPM"""
        return self.__rpm

    @rpm.setter
    def rpm(self, speed):
        if speed < 0:
            raise ValueError("RPM cannot be below zero")
        self.__rpm = speed

    @property
    def pwm(self):
        """Get shelf PWM value
        Reading get the effective PWM value
        Changing override the PWM value
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        if ((self.__pwm_override is not None and self.__pwm_expire is None) or
                (self.__pwm_override is not None and self.__pwm_expire > now)):
            return self.__pwm_override
        return self.__pwm

    @pwm.setter
    def pwm(self, speed=None):
        if speed is not None and (speed < 0 or speed > 100):
            raise ValueError("PWM must be between 0 and 100")
        self.__pwm_override = speed

    @property
    def pwm_expire(self):
        """Set the PWM override expiration date
        Contains a datetime.datetime object, defaults to local timezone
        """
        return self.__pwm_expire

    @pwm_expire.setter
    def pwm_expire(self, date=None):
        if date is None:
            self.__pwm_expire = date
            return
        if date.tzinfo is None:
            localtz = datetime.datetime.now().astimezone().tzinfo
            date = date.replace(tzinfo=localtz)
        now = datetime.datetime.now(date.tzinfo)
        if date < now:
            raise ValueError(f"Expiration {date} is before now {now}")
        self.__pwm_expire = date

    def update(self):
        """Update shelf data"""
        logger.info("Updating shelf %s", self)
        # Update all drives
        for device in self.__devices.values():
            device.update()

        # temp_lists dict: `DeviceType: list of temperatures`
        temp_lists = {dev_type: [] for dev_type in Device.DeviceType}
        for device in self:
            if device.type != Device.DeviceType.NONE:
                temp_lists[device.type].append(device.temperature)
        logger.debug("Temperatures are: %s", temp_lists)

        # effective_temps dict: `DeviceType: effective temperature`
        effective_temps = {dev_type: 0 for dev_type in Device.DeviceType}
        for dev_type, temp_list in temp_lists.items():
            if temp_list:
                effective_temps[dev_type] = max(temp_list)
        logger.info("Effective temperatures are: %s", effective_temps)

        # pwm_list: list of effective PWM values
        pwm_list = []
        for dev_type, effective_temp in effective_temps.items():
            pwm_list.append(max(
                speed for temp, speed in self.__temperatures[dev_type].items()
                if effective_temp >= temp
            ))
        logger.debug("Effective PWM values are: %s", pwm_list)

        # Get final PWM speed
        self.__pwm = max(pwm_list)
        logger.info("PWM speed for shelf %s is %s", self, self.__pwm)


class ShelfNotFoundError(ValueError):
    """No shelf with the given name exists"""


def add_shelf(shelf):
    """Add a Shelf to the dictionnary of known shelves"""
    __SHELVES__[shelf.identifier] = shelf


def _handle_ping(client_socket):
    """Handle the ping request from a client"""
    logger.info("Received REQ_PING from %s", client_socket)
    com.send(client_socket, com.Request.ACK)


def _handle_get_pwm(client_socket, shelf_id):
    """Handle the request to get PWM speed of a shelf"""
    logger.info("Received REQ_GET_PWM from %s for %s", client_socket, shelf_id)
    try:
        pwm = __SHELVES__[shelf_id].pwm
    except KeyError as error:
        raise ShelfNotFoundError(f"Shelf {shelf_id} not found") from error
    com.send(client_socket, com.Request.SET_PWM, shelf_id, pwm)


def _handle_get_rpm(client_socket, shelf_id):
    """Handle the request to get RPM speed of a shelf"""
    logger.info("Received REQ_GET_RPN from %s for %s", client_socket, shelf_id)
    try:
        rpm = __SHELVES__[shelf_id].rpm
    except KeyError as error:
        raise ShelfNotFoundError(f"Shelf {shelf_id} not found") from error
    com.send(client_socket, com.Request.SET_RPM, shelf_id, rpm)


def _handle_set_rpm(client_socket, shelf_id, speed):
    """Handle the request to set RPM speef of a shelf"""
    logger.info("Received REQ_SET_RPM to %s from %s for %s",
                speed, client_socket, shelf_id)
    try:
        __SHELVES__[shelf_id].rpm = speed
    except KeyError as error:
        raise ShelfNotFoundError(f"Shelf {shelf_id} not found") from error
    except ValueError:
        logger.error("Wrong speed value %s received", speed)
        raise
    com.send(client_socket, com.Request.ACK)


def _handle_set_pwm_override(client_socket, shelf_id, speed):
    """Handle the request to override PWM value of a shelf"""
    logger.info("Received request to override PWM to %s%% from %s for %s",
                speed, client_socket, shelf_id)
    try:
        __SHELVES__[shelf_id].pwm = speed
    except KeyError as error:
        raise ShelfNotFoundError(f"Shelf {shelf_id} not found") from error
    except ValueError:
        logger.error("Wrong value %s received", speed)
        raise
    com.send(client_socket, com.Request.ACK)


def _handle_set_pwm_expire(client_socket, shelf_id, date):
    """Handle the request to set the expiration date of the PWM override of
    a shelf
    """
    logger.info("Received set PWM override expiration of %s to %s from %s",
                shelf_id, date, client_socket)
    try:
        __SHELVES__[shelf_id].pwm_expire = date
    except KeyError as error:
        raise ShelfNotFoundError(f"Shelf {shelf_id} not found") from error
    except ValueError:
        logger.error("Wrong value %s received", date)
        raise
    com.send(client_socket, com.Request.ACK)


REQUEST_HANDLERS = {
    com.Request.PING: _handle_ping,
    com.Request.GET_PWM: _handle_get_pwm,
    com.Request.GET_RPM: _handle_get_rpm,
    com.Request.SET_RPM: _handle_set_rpm,
    com.Request.SET_PWM_OVERRIDE: _handle_set_pwm_override,
    com.Request.SET_PWM_EXPIRE: _handle_set_pwm_expire,
}


def listen_client(client_socket):
    """Listen for client requests until the connection is closed"""
    logger.info("Listening to %s", client_socket)
    while com.is_socket_open(client_socket):
        try:
            req, args = com.recv(client_socket)
        except TimeoutError:
            logger.warning("%s timed out", client_socket)
            continue
        except ConnectionResetError:
            logger.info("Connection reset by %s", client_socket)
            com.reset_connection(client_socket, notice=False)
            continue
        except ConnectionError:
            logger.exception("Connection error from %s", client_socket)
            com.reset_connection(client_socket)
            continue
        handler = REQUEST_HANDLERS.get(req)
        if handler is None:
            logger.error("Invalid request %s from %s", req, client_socket)
            com.reset_connection(client_socket, "Invalid request")
            continue
        try:
            handler(client_socket, *args)
        except TypeError:
            logger.exception("Invalid call to request %s from %s",
                             req, client_socket)
            com.reset_connection(client_socket, "Invalid call")
            continue
        except ConnectionResetError:
            logger.info("Connection reset by %s", client_socket)
            com.reset_connection(client_socket, notice=False)
            continue
        except TimeoutError:
            logger.exception("%s timed out", client_socket)
            com.reset_connection(client_socket)
            continue
        except ConnectionError:
            logger.exception("Connection error from %s", client_socket)
            com.reset_connection(client_socket)
            continue
        except ShelfNotFoundError as error:
            logger.exception("Shelf not found for %s", client_socket)
            com.reset_connection(client_socket, error)
            continue
        except ValueError as error:
            logger.exception("Unexpected value from %s", client_socket)
            com.reset_connection(client_socket, error)
            continue
    logger.debug("Stopping client thread for %s: socket closed", client_socket)


def _find_config_file():
    """Find the configuration file to use
    Use in order:
      FAND_CONFIG environment variable
      ./fand.ini
      /etc/fand.ini
    """
    if os.environ.get('FAND_CONFIG') is not None:
        return os.environ['FAND_CONFIG']
    if os.path.isfile('./fand.ini'):
        return './fand.ini'
    if os.path.isfile('/etc/fand.ini'):
        return '/etc/fand.ini'
    return None


def _read_config_temps(config_string):
    """Parse a configuration string for a temperature dictionnary"""
    return {
        float(temp.split(':')[0].strip()): float(temp.split(':')[1].strip())
        for temp in config_string.split(',')
    }


def read_config(config_file=_find_config_file()):
    """Read configuration from a file, returns a set of shelves"""
    logger.debug("Reading configuration %s", config_file)
    if config_file is None:
        raise ValueError("No configuration file found")
    config = configparser.ConfigParser()
    config.read(config_file)
    shelves = set()
    for shelf_id in config['DEFAULT']['shelves'].strip().split(','):
        shelf_id = shelf_id.strip()
        logger.debug("Parsing shelf %s", shelf_id)
        devices = []
        for device_string in config[shelf_id]['devices'].strip().split('\n'):
            serial, position, *_ = device_string.split(';')
            devices.append(Device(serial.strip(), position.strip()))
        hdd_temps = _read_config_temps(config[shelf_id]['hdd_temps'])
        ssd_temps = _read_config_temps(config[shelf_id]['ssd_temps'])
        cpu_temps = _read_config_temps(config[shelf_id]['cpu_temps'])
        shelves.add(Shelf(shelf_id, devices, hdd_temps=hdd_temps,
                          ssd_temps=ssd_temps, cpu_temps=cpu_temps))
    return shelves


def shelf_thread(shelf):
    """Main thread for shelf"""
    logger.info("Monitoring %s", shelf)
    while not util.terminating():
        shelf.update()
        util.sleep(shelf.sleep_time)


def main():
    """Entry point of the module"""
    parser = argparse.ArgumentParser(
        description=__DOCSTRING__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--config', '-c', default=_find_config_file(),
                        help="Config file to parse")
    args = util.parse_args(parser)
    logger.info("Started from main entry point with parameters %s", args)
    try:
        start(config_file=args.config, address=args.address, port=args.port)
    finally:
        util.sys_exit()


def start(config_file=_find_config_file(), address=socket.gethostname(),
          port=9999):
    """Main function"""
    logger.debug("Starting server daemon")
    signal.signal(signal.SIGINT, util.default_signal_handler)
    signal.signal(signal.SIGTERM, util.default_signal_handler)
    try:
        for shelf in read_config(config_file):
            add_shelf(shelf)
    except ValueError as error:
        logger.exception("Error while reading config file %s", config_file)
        util.terminate("Cannot continue without configuration")
        raise ValueError("Cannot continue without configuration") from error

    with concurrent.futures.ThreadPoolExecutor() as executor:
        def shelf_thread_callback(future):
            """Callback when shelf_thread future is done"""
            error = future.exception()
            if error is not None:
                util.terminate(f"Exception {error} in shelf thread")

        logger.info("Starting shelves threads")
        shelves = []
        for shelf in __SHELVES__.values():
            thread = executor.submit(shelf_thread, shelf)
            thread.add_done_callback(shelf_thread_callback)
            shelves.append(thread)

        logger.info("Listening for clients on %s:%s", address, port)
        clients = []
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listen_socket.bind((address, port))
            listen_socket.listen()
        except OSError as error:
            logger.exception("Failed to bind to %s:%s", address, port)
            util.terminate("Cannot bind to requested interface and port")
            raise Exception("Cannot bind to requested interface and port") \
                from error
        com.add_socket(listen_socket)
        while com.is_socket_open(listen_socket):
            try:
                client_socket, client_address = listen_socket.accept()
                logger.info("New connection from %s", client_address)
                com.add_socket(client_socket)
                clients.append(executor.submit(listen_client, client_socket))
            except OSError as error:
                if not util.terminating():
                    util.terminate("Error while listening for clients")
                    raise Exception("Error while listening for clients") \
                        from error
