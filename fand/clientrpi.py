"""fand client for Raspberry Pi"""

import argparse
import logging
import signal
import socket
import time

import gpiozero

import fand.util as util
import fand.communication as com

# Constants
# Module docstring
__DOCSTRING__ = __doc__
# Logger to use
logger = logging.getLogger(__name__)
# How much time to wait between updates
SLEEP_TIME = 60

# Global variables
# List of active GPIO devices, closed when program exits
GPIO_DEVICES = []


@util.when_terminate
def _terminate():
    for device in GPIO_DEVICES.copy():
        try:
            device.close()
        except gpiozero.GPIOZeroError:
            logger.exception("Failed to close GPIO %s", device)
        except gpiozero.GPIOZeroWarning as warning:
            logger.warning("Ignoring GPIO warning %s", warning)
        GPIO_DEVICES.remove(device)


class GpioRpm:
    """Class to handle RPM tachometer from a fan
    Attributes:
    rpm: RPM value
    __gpio: gpiozero.Button object for the RPM input
    __count: count tachometer activation
    __start_time: time at which __count started
    """
    def __init__(self, pin):
        """Constructor (does not handle gpiozero exceptions)
        pin: GPIO pin number to use
        """
        self.__pin = pin
        self.__gpio = gpiozero.Button(pin, pull_up=True)
        self.__gpio.when_pressed = self.pressed
        self.__count, self.__start_time = 0, time.time()
        self.rpm = 0
        GPIO_DEVICES.append(self)
        logger.info("Created GPIO RPM device on pin %s", pin)

    def __str__(self):
        return f"RPM on GPIO{self.__pin}"

    def pressed(self):
        """Increment the press count"""
        self.__count += 1

    def update(self):
        """Update the RPM value"""
        self.rpm = (self.__count / 2) / (time.time() - self.__start_time) * 60
        self.__count, self.__start_time = 0, time.time()
        logger.debug("Updating RPM value to %s", self.rpm)

    def close(self):
        """Close the GPIO device"""
        self.__gpio.close()


def set_pwm(gpio_device, value):
    """Set PWM value for gpiozero.PWMLED object"""
    logger.info("Setting PWM value for %s to %s", gpio_device, value)
    try:
        gpio_device.value = value / 100
    except gpiozero.GPIOZeroError:
        logger.exception("Failed to set PWM value for %s", gpio_device)
        util.terminate("Cannot continue after GPIO failure")
    except gpiozero.GPIOZeroWarning as warning:
        logger.warning("Ignoring GPIO warning %s for %s", warning, gpio_device)


def main():
    """Module entry point"""
    parser = argparse.ArgumentParser(
        description=__DOCSTRING__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('name', nargs='?', default=socket.gethostname(),
                        help='Shelf name, defaults to hostname')
    parser.add_argument('--pwmpin', '-P', default=18, type=int,
                        help="Set GPIO pin for PWM output, defaults to 2")
    parser.add_argument('--rpmpin', '-r', default=17, type=int,
                        help="Set GPIO pin for RPM input, defaults to 3")
    args = util.parse_args(parser)
    logger.info("Started from main entry point with parameters %s", args)

    # GPIO PWM
    try:
        gpio_pwm = gpiozero.PWMLED(args.pwmpin, frequency=25000,
                                   active_high=True, initial_value=1)
    except gpiozero.GPIOZeroError:
        logger.exception("Failed to create GPIO PWM object")
        util.terminate("Cannot continue without GPIO PWM object")
    except gpiozero.GPIOZeroWarning as warning:
        logger.warning("Ignoring GPIO warning %s for %s", warning, gpio_pwm)
    logger.debug("Created PWM GPIO device %s", gpio_pwm)
    # GPIO RPM
    try:
        gpio_rpm = GpioRpm(args.rpmpin)
    except gpiozero.GPIOZeroError:
        logger.exception("Failed to create GPIO RPM object")
        util.terminate("Cannot continue without GPIO RPM object")
    except gpiozero.GPIOZeroWarning as warning:
        logger.warning("Ignoring GPIO warning %s for %s", warning, gpio_rpm)
    logger.debug("Created RPM GPIO device %s", gpio_rpm)

    start(gpio_pwm, gpio_rpm, shelf_name=args.name,
          address=args.address, port=args.port)


def start(gpio_pwm, gpio_rpm, shelf_name=socket.gethostname(),
          address=socket.gethostname(), port=9999):
    """Main function of this module"""
    def reconnect(server):
        try:
            com.reset_connection(server)
        except (TimeoutError, ConnectionError):
            logger.exception("Failed to connect to %s:%s", address, port)
            util.terminate("Cannot connect to server")
        return com.connect(address, port)
    logger.debug("Starting client daemon")
    signal.signal(signal.SIGINT, util.default_signal_handler)
    signal.signal(signal.SIGTERM, util.default_signal_handler)
    server = reconnect(None)

    while not util.terminating():
        logger.info("Updating informations")

        logger.debug("Updating PWM")
        try:
            com.send(server, com.REQ_GET_PWM, shelf_name)
            req, args = com.recv(server)
            server_shelf_name, pwm_value = args
        except (TimeoutError, ConnectionError):
            logger.exception("Failed to get PWM value from %s", server)
            server = reconnect(server)
        except ValueError:
            logger.error("Unexpected data received from %s: %s", server, args)
            server = reconnect(server)
        if req != com.REQ_SET_PWM:
            logger.error("Unexpected request from %s: expected %s, got %s",
                         server, com.REQ_SET_PWM, req)
            server = reconnect(server)
        elif server_shelf_name != shelf_name:
            logger.error("Unexpected shelf name %s received from %s",
                         server_shelf_name, server)
            server = reconnect(server)
        else:
            set_pwm(gpio_pwm, pwm_value)

        logger.debug("Updating RPM")
        gpio_rpm.update()
        util.sleep(1)
        gpio_rpm.update()
        try:
            com.send(server, com.REQ_SET_RPM, shelf_name, gpio_rpm.rpm)
            req, args = com.recv(server)
        except (TimeoutError, ConnectionError):
            logger.exception("Failed to get RPM value from %s", server)
            server = reconnect(server)
        if req != com.REQ_ACK:
            logger.error("Unexpected request from %s: expected %s, got %s",
                         server, com.REQ_ACK, req)
            server = reconnect(server)

        logger.info("Updated: PWM = %s, RPM = %s", pwm_value, gpio_rpm.rpm)
        util.sleep(SLEEP_TIME)

    util.terminate()
