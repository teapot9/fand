"""Communicate request with a remote socket"""

import enum
import logging
import pickle
import socket
from typing import (Any, Optional, Set, Tuple)

import fand.util as util
from fand.exceptions import (
    TerminatingError, UnpicklableError, FandTimeoutError, SendReceiveError,
    FandConnectionResetError, CorruptedDataError, ConnectionFailedError
)

# Header = magic number + data size
HEADER_MAGIC = b'99F9'
HEADER_MAGIC_SIZE = 4
HEADER_DATA_SIZE = 4
HEADER_SIZE = HEADER_MAGIC_SIZE + HEADER_DATA_SIZE

# Setup logging
logger = logging.getLogger(__name__)

# List of open sockets, closed when program exits
__SOCKETS__: Set[socket.socket] = set()


@util.when_terminate
def _terminate() -> None:
    for sock in __SOCKETS__.copy():
        reset_connection(sock)


class Request(enum.Enum):
    """Enumeration of known requests"""
    #: Acknowledge a previously received :class:`Request`
    ACK = 'ack'
    #: Request for a :data:`Request.ACK`
    PING = 'ping'
    #: Notification of disconnection
    DISCONNECT = 'disconnect'
    #: Request for a :data:`Request.SET_PWM` to get current PWM
    GET_PWM = 'get_pwm'
    #: Give the current PWM
    SET_PWM = 'set_pwm'
    #: Request for a :data:`Request.SET_RPM` to get current RPM
    GET_RPM = 'get_rpm'
    #: Give the current RPM
    SET_RPM = 'set_rpm'
    #: Override the PWM value
    SET_PWM_OVERRIDE = 'set_pwm_override'
    #: Set the expiration date of the PWM override
    SET_PWM_EXPIRE = 'set_pwm_expire'


def add_socket(sock: socket.socket) -> None:
    """Add sock to the set of managed sockets

    It can be removed with :func:`reset_connection`
    and will automatically be when :func:`fand.util.terminate` is called.

    :param sock: Socket to add

    :raises TerminatingError: Trying to add a socket but
        :func:`fand.util.terminating` is True
    """
    logger.debug("Adding socket %s", sock)
    if util.terminating():
        raise TerminatingError("Cannot create sockets while terminating")
    __SOCKETS__.add(sock)


def is_socket_open(sock: socket.socket) -> bool:
    """Returns True if sock is currently managed by this module

    This will be False after a socket has been closed with
    :func:`reset_connection`.

    :param sock: Socket to test
    """
    return sock in __SOCKETS__


def send(sock: socket.socket, request: Request, *args: Any) -> None:
    """Send a request to a remote socket

    :param sock: Socket to send the request to
    :param request: Request to send
    :param args: Request arguments

    :raises UnpicklableError: Given data cannot be pickled by :mod:`pickle`
    :raises FandTimeoutError: Connection timed out
    :raises SendReceiveError: Error while sending the data
    """
    logger.debug("Sending %s to %s with arguments %s", request, sock, args)

    try:
        data = (request, args)
        data_bytes = pickle.dumps(data)
    except (pickle.PickleError, TypeError, ValueError) as error:
        raise UnpicklableError() from error

    data_size = format(len(data_bytes), 'x').zfill(HEADER_DATA_SIZE)
    header_bytes = HEADER_MAGIC + bytes(data_size, 'utf-8')

    try:
        bytes_sent = sock.send(header_bytes + data_bytes)
    except socket.timeout as error:
        raise FandTimeoutError(f"Timeout from {sock}") from error
    except OSError as error:
        raise SendReceiveError(f"OSError {error} from {sock}") from error
    if bytes_sent != HEADER_SIZE + len(data_bytes):
        raise SendReceiveError(f"Not all data sent to {sock}")

    logger.debug("%s sent to %s", request, sock)


def recv(sock: socket.socket) -> Tuple[Request, Tuple]:
    """Receive a request from a remote socket, returns (request, args)

    :param sock: Socket to receive the request and its arguments from

    :raises FandTimeoutError: Connection timed out
    :raises SendReceiveError: Error while receiving the data
    :raises FandConnectionResetError: No data received or
        :data:`Request.DISCONNECT` received
    :raises CorruptedDataError: Invalid data received
    """
    logger.debug("Waiting for data from %s", sock)

    try:
        header = sock.recv(HEADER_SIZE)
    except socket.timeout as error:
        raise FandTimeoutError(f"Timeout from {sock}") from error
    except OSError as error:
        raise SendReceiveError(f"OSError {error} from {sock}") from error
    if not header:
        raise FandConnectionResetError(f"Nothing received from {sock}")
    if len(header) != HEADER_SIZE:
        raise CorruptedDataError(f"Invalid header size from {sock}")

    magic = header[0:HEADER_MAGIC_SIZE]
    data_size = int(header[HEADER_MAGIC_SIZE:HEADER_SIZE], base=16)
    if magic != HEADER_MAGIC:
        raise CorruptedDataError(f"Invalid magic number from {sock}")

    try:
        data_bytes = sock.recv(data_size)
        request, args = pickle.loads(data_bytes)
    except socket.timeout as error:
        raise FandTimeoutError(f"Timeout from {sock}") from error
    except OSError as error:
        raise SendReceiveError(f"OSError {error} from {sock}") from error
    except (pickle.PickleError, TypeError, ValueError) as error:
        raise CorruptedDataError("Cannot unpickle data") from error

    logger.debug("Received %s from %s with arguments %s", request, sock, args)
    if request == Request.DISCONNECT:
        if len(args) >= 1 and args[0] is not None:
            logger.error("Error: %s from socket %s", args[0], sock)
        raise FandConnectionResetError(f"Connection reset by {sock}")
    return (request, args)


def connect(address: str, port: int) -> socket.socket:
    """Connect to server and returns socket

    :param address: Server address
    :param port: Server port

    :raises FandTimeoutError: Connection timed out
    :raises ConnectionFailedError: Failed to connect to remote socket
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.settimeout(10)
    try:
        server.connect((address, port))
    except socket.timeout as error:
        raise FandTimeoutError() from error
    except OSError as error:
        raise ConnectionFailedError(
            f"Could not connect to {address}:{port}"
        ) from error
    add_socket(server)
    logger.info("Connected to %s:%s, created %s", address, port, server)
    return server


def reset_connection(
        client_socket: socket.socket,
        error_msg: Optional[str] = None,
        notice: bool = True,
        ) -> None:
    """Closes a connection to a client

    :param client_socket: Socket to close
    :param error: Error to send
    :param notice: Send a notice about the reset to the remote socket
    """
    logger.info("Closing connection to %s", client_socket)
    if not is_socket_open(client_socket):
        return
    try:
        if notice:
            send(client_socket, Request.DISCONNECT, error_msg)
    except OSError as error:
        logger.warning("Could not notify %s of disconnection because %s",
                       client_socket, error)
    try:
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()
    except OSError as error:
        logger.warning("Could not close %s because %s", client_socket, error)
    __SOCKETS__.remove(client_socket)
