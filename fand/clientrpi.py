"""fand client for Raspberry Pi"""

import argparse
import logging
import signal
import socket
import time
from typing import (NoReturn, Optional, Set, Union)

import gpiozero

import fand.util as util
import fand.communication as com
from fand.exceptions import (
    GpioError, TerminatingError, ShelfPwmBadValue, CommunicationError
)

# Constants
# Module docstring
__DOCSTRING__ = __doc__
# Logger to use
logger = logging.getLogger(__name__)
#: How much time to wait between updates
SLEEP_TIME: float = 60

# Global variables
# Set of active GPIO devices, closed when program exits
__GPIO_DEVICES__: Set[Union['GpioRpm', 'GpioPwm']] = set()


@util.when_terminate
def _terminate() -> None:
    for device in __GPIO_DEVICES__.copy():
        try:
            device.close()
        except GpioError:
            logger.exception("Failed to close GPIO %s", device)
        __GPIO_DEVICES__.remove(device)


def add_gpio_device(device: Union['GpioRpm', 'GpioPwm']) -> None:
    """Add a GPIO device to the set of managed GPIO devices

    :param device:
        GPIO device to add

    :raises TerminatingError: Trying to add a socket but
        :func:`fand.util.terminating` is True
    """
    if util.terminating():
        raise TerminatingError("Cannot add new GPIO device while terminating")
    __GPIO_DEVICES__.add(device)


class GpioRpm:
    """Class to handle RPM tachometer input from a fan

    :param pin: GPIO pin number to use
    :param managed: set to true to have the GPIO device automatically closed
        when :func:`fand.util.terminate` is called

    :raises GpioError: Received a :exc:`gpiozero.GPIOZeroError`
    """
    def __init__(self, pin: int, managed: bool = True) -> None:
        self.__pin = pin
        try:
            self.__gpio = gpiozero.Button(pin, pull_up=True)
            self.__gpio.when_pressed = self.__pressed
        except gpiozero.GPIOZeroError as error:
            raise GpioError from error
        except gpiozero.GPIOZeroWarning as warning:
            logger.warning("Ignoring GPIO warning %s", warning)
        self.__count, self.__start_time = 0, time.time()
        #: RPM value
        self.rpm: float = 0
        if managed:
            add_gpio_device(self)
        logger.info("Created GPIO RPM device on pin %s", pin)

    def __str__(self) -> str:
        return f"RPM on GPIO{self.__pin}"

    def __pressed(self) -> None:
        """Increment the press count"""
        self.__count += 1

    def update(self) -> None:
        """Update the RPM value"""
        self.rpm = (self.__count / 2) / (time.time() - self.__start_time) * 60
        self.__count, self.__start_time = 0, time.time()
        logger.debug("Updating RPM value to %s", self.rpm)

    def close(self) -> None:
        """Close the GPIO device

        :raises GpioError: Received a :exc:`gpiozero.GPIOZeroError`
        """
        try:
            self.__gpio.close()
        except gpiozero.GPIOZeroError as error:
            raise GpioError from error
        except gpiozero.GPIOZeroWarning as warning:
            logger.warning("Ignoring GPIO warning %s", warning)


class GpioPwm:
    """Class to handle PWM output for a fan

    :param pin: GPIO pin number to use
    :param managed: set to true to have the GPIO device automatically closed
        when :func:`fand.util.terminate` is called

    :raises GpioError: Received a :exc:`gpiozero.GPIOZeroError`
    """
    def __init__(self, pin: int, managed: bool = True) -> None:
        self.__pin = pin
        try:
            self.__gpio = gpiozero.PWMLED(pin, frequency=25000,
                                          active_high=True, initial_value=1)
        except gpiozero.GPIOZeroError as error:
            raise GpioError from error
        except gpiozero.GPIOZeroWarning as warning:
            logger.warning("Ignoring GPIO warning %s", warning)
        if managed:
            add_gpio_device(self)
        logger.info("Created GPIO PWM device on pin %s", pin)

    def __str__(self) -> str:
        return f"PWM on GPIO{self.__pin}"

    @property
    def pwm(self) -> float:
        """PWM output value, backend is :attr:`gpiozero.PWMLED.value`

        :raises GpioError: Received a :exc:`gpiozero.GPIOZeroError`
        """
        return self.__gpio.value * 100

    @pwm.setter
    def pwm(self, value: float) -> None:
        if value > 100 or value < 0:
            raise ShelfPwmBadValue("PWM value must be between 0 and 100")
        try:
            self.__gpio.value = value / 100
        except gpiozero.GPIOZeroError as error:
            raise GpioError from error
        except gpiozero.GPIOZeroWarning as warning:
            logger.warning("Ignoring GPIO warning %s", warning)

    def close(self) -> None:
        """Close the GPIO device

        :raises GpioError: Received a :exc:`gpiozero.GPIOZeroError`
        """
        try:
            self.__gpio.close()
        except gpiozero.GPIOZeroError as error:
            raise GpioError from error
        except gpiozero.GPIOZeroWarning as warning:
            logger.warning("Ignoring GPIO warning %s", warning)


def main() -> NoReturn:
    """Module entry point"""
    parser = argparse.ArgumentParser(
        description=__DOCSTRING__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('name', nargs='?', default=socket.gethostname(),
                        help='Shelf name, defaults to hostname')
    parser.add_argument('--pwmpin', '-W', default=18, type=int,
                        help="Set GPIO pin for PWM output, defaults to 2")
    parser.add_argument('--rpmpin', '-r', default=17, type=int,
                        help="Set GPIO pin for RPM input, defaults to 3")
    args = util.parse_args(parser)
    logger.info("Started from main entry point with parameters %s", args)

    # GPIO PWM
    try:
        gpio_pwm = GpioPwm(args.pwmpin)
    except GpioError:
        logger.exception("Failed to create GPIO PWM object")
        util.terminate("Cannot continue without GPIO PWM object")
        util.sys_exit()
    logger.debug("Created PWM GPIO device %s", gpio_pwm)
    # GPIO RPM
    try:
        gpio_rpm = GpioRpm(args.rpmpin)
    except GpioError:
        logger.exception("Failed to create GPIO RPM object")
        util.terminate("Cannot continue without GPIO RPM object")
        util.sys_exit()
    logger.debug("Created RPM GPIO device %s", gpio_rpm)

    try:
        daemon(gpio_pwm, gpio_rpm, shelf_name=args.name,
               address=args.address, port=args.port)
    finally:
        util.sys_exit()


def daemon(
        gpio_pwm: GpioPwm,
        gpio_rpm: GpioRpm,
        shelf_name: str = socket.gethostname(),
        address: str = socket.gethostname(),
        port: int = 9999,
        ) -> None:
    """Main function of this module

    :param gpio_pwm: GPIO device to use for PWM output
    :param gpio_rpm: GPIO device to use for RPM input
    :param shelf_name: Name of this shelf, used to communicate with the server
    :param address: Server address or hostname
    :param port: Port number to connect to
    """
    def reconnect(server: Optional[socket.socket] = None,
                  error: Optional[str] = None,
                  notice: bool = True) -> socket.socket:
        try:
            if server is not None:
                com.reset_connection(server, error, notice=notice)
            return com.connect(address, port)
        except CommunicationError:
            logger.exception("Failed to connect to %s:%s", address, port)
            util.terminate("Cannot connect to server")
            raise
    logger.debug("Starting client daemon")
    signal.signal(signal.SIGINT, util.default_signal_handler)
    signal.signal(signal.SIGTERM, util.default_signal_handler)
    server = reconnect()

    while not util.terminating():
        logger.info("Updating informations")

        logger.debug("Updating PWM")
        try:
            com.send(server, com.Request.GET_PWM, shelf_name)
            req, args = com.recv(server)
            server_shelf_name, pwm_value = args
        except ConnectionResetError:
            logger.info("Connection reset by %s", server)
            server = reconnect(server, notice=False)
        except CommunicationError:
            logger.exception("Failed to get PWM value from %s", server)
            server = reconnect(server)
        except ValueError:
            logger.error("Unexpected data received from %s: %s", server, args)
            server = reconnect(server, "Unexpected arguments")
        if req != com.Request.SET_PWM:
            logger.error("Unexpected request from %s: expected %s, got %s",
                         server, com.Request.SET_PWM, req)
            server = reconnect(server, "Unexpected request")
        elif server_shelf_name != shelf_name:
            logger.error("Unexpected shelf name %s received from %s",
                         server_shelf_name, server)
            server = reconnect(server, "Unexpected shelf")
        else:
            try:
                gpio_pwm.pwm = pwm_value
            except GpioError:
                logger.exception("Failed to set PWM value for %s", gpio_pwm)
                util.terminate("Cannot continue after GPIO failure")
                raise
            except ValueError:
                logger.exception("Unexpected PWM value from %s: %s",
                                 server, pwm_value)

        logger.debug("Updating RPM")
        gpio_rpm.update()
        util.sleep(1)
        gpio_rpm.update()
        try:
            com.send(server, com.Request.SET_RPM, shelf_name, gpio_rpm.rpm)
            req, args = com.recv(server)
        except ConnectionResetError:
            logger.info("Connection reset by %s", server)
            server = reconnect(server, notice=False)
        except CommunicationError:
            logger.exception("Failed to get RPM value from %s", server)
            server = reconnect(server)
        if req != com.Request.ACK:
            logger.error("Unexpected request from %s: expected %s, got %s",
                         server, com.Request.ACK, req)
            server = reconnect(server, "Unexpected request")

        logger.info("Updated: PWM = %s, RPM = %s", pwm_value, gpio_rpm.rpm)
        util.sleep(SLEEP_TIME)
