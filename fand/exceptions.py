"""Module for fand exceptions"""


class FandError(Exception):
    """Base class for all exceptions in fand"""


class TerminatingError(FandError):
    """Daemon is terminating"""


# Communication related errors

class CommunicationError(FandError):
    """Base class for communication related errors"""


class SendReceiveError(CommunicationError, ConnectionError):
    """Error while sending or receiving data"""


class ListeningError(CommunicationError, ConnectionError):
    """Error when listening to clients"""


class ConnectionFailedError(CommunicationError, ConnectionError):
    """Cannot connect to given address and port"""


class CorruptedDataError(CommunicationError, ConnectionError):
    """Invalid data received"""


class FandConnectionResetError(CommunicationError, ConnectionResetError):
    """Connection reset"""


class FandTimeoutError(CommunicationError, TimeoutError):
    """Connection timed out"""


class UnpicklableError(CommunicationError, ValueError):
    """Given value cannot be pickled"""


# Shelf related errors

class ShelfTemperatureBadValue(FandError, ValueError):
    """Temperatures given for shelf are invalid"""


class ShelfRpmBadValue(FandError, ValueError):
    """RPM value is invalid"""


class ShelfPwmBadValue(FandError, ValueError):
    """PWM value is invalid"""


class ShelfPwmExpireBadValue(FandError, ValueError):
    """PWM override expiration date is invalid"""


class ShelfNotFoundError(FandError, ValueError):
    """Given shelf name is unknown"""


# Server and client related errors

class ServerNoConfigError(FandError, FileNotFoundError):
    """No configuration file found"""


class GpioError(FandError):
    """Any GPIO related errors"""


class FanctlActionBadValue(FandError, ValueError):
    """No action found with this name and parameters"""
