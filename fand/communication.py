"""Communicate request with a remote socket"""

import enum
import logging
import pickle
import socket

import fand.util as util

# Header = magic number + data size
HEADER_MAGIC = b'99F9'
HEADER_MAGIC_SIZE = 4
HEADER_DATA_SIZE = 4
HEADER_SIZE = HEADER_MAGIC_SIZE + HEADER_DATA_SIZE

# Setup logging
logger = logging.getLogger(__name__)

# List of open sockets, closed when program exits
SOCKETS = []


@util.when_terminate
def _terminate():
    for sock in SOCKETS.copy():
        reset_connection(sock)


class Request(enum.Enum):
    """Standard request"""
    ACK = 'ack'
    PING = 'ping'
    DISCONNECT = 'disconnect'
    GET_PWM = 'get_pwm'
    SET_PWM = 'set_pwm'
    GET_RPM = 'get_rpm'
    SET_RPM = 'set_rpm'
    SET_PWM_OVERRIDE = 'set_pwm_override'
    SET_PWM_EXPIRE = 'set_pwm_expire'


def send(sock, request, *args):
    """Send a request to a remote socket"""
    logger.debug("Sending %s to %s with arguments %s", request, sock, args)

    try:
        data = (request, args)
        data_bytes = pickle.dumps(data)
    except (pickle.PickleError, TypeError, ValueError) as error:
        raise ValueError() from error

    data_size = format(len(data_bytes), 'x').zfill(HEADER_DATA_SIZE)
    header_bytes = HEADER_MAGIC + bytes(data_size, 'utf-8')

    try:
        bytes_sent = sock.send(header_bytes + data_bytes)
    except socket.timeout as error:
        raise TimeoutError(f"Timeout from {sock}") from error
    except OSError as error:
        raise ConnectionError(f"OSError from {sock}") from error
    if bytes_sent != HEADER_SIZE + len(data_bytes):
        raise ConnectionError(f"Not all data sent to {sock}")

    logger.debug("%s sent to %s", request, sock)


def recv(sock):
    """Receive a request from a remote socket"""
    logger.debug("Waiting for data from %s", sock)

    try:
        header = sock.recv(HEADER_SIZE)
    except socket.timeout as error:
        raise TimeoutError(f"Timeout from {sock}") from error
    except OSError as error:
        raise ConnectionError(f"OSError from {sock}") from error
    if not header:
        raise ConnectionResetError(f"Nothing received from {sock}")
    if len(header) != HEADER_SIZE:
        raise ConnectionError(f"Invalid header size from {sock}")

    magic = header[0:HEADER_MAGIC_SIZE]
    data_size = int(header[HEADER_MAGIC_SIZE:HEADER_SIZE], base=16)
    if magic != HEADER_MAGIC:
        raise ConnectionError(f"Invalid magic number from {sock}")

    try:
        data_bytes = sock.recv(data_size)
        request, args = pickle.loads(data_bytes)
    except socket.timeout as error:
        raise TimeoutError(f"Timeout from {sock}") from error
    except OSError as error:
        raise ConnectionError(f"OSError from {sock}") from error
    except (pickle.PickleError, TypeError, ValueError) as error:
        raise ValueError() from error

    logger.debug("Received %s from %s with arguments %s", request, sock, args)
    if request == Request.DISCONNECT:
        if len(args) >= 1 and args[0] is not None:
            logger.error("Error: %s from socket %s", args[0], sock)
        raise ConnectionResetError(f"Connection reset by {sock}")
    return (request, args)


def connect(address, port):
    """Connect to server and return socket"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.settimeout(10)
    try:
        server.connect((address, port))
    except socket.timeout as error:
        raise TimeoutError() from error
    except OSError as error:
        raise ConnectionError() from error
    SOCKETS.append(server)
    logger.info("Connected to %s:%s, created %s", address, port, server)
    return server


def reset_connection(client_socket, error_msg=None, notice=True):
    """Closes a connection to a client
    error: error to send (string, exception)
    notice: send a notice about the reset to the remote socket
    """
    logger.info("Closing connection to %s", client_socket)
    if client_socket not in SOCKETS:
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
    SOCKETS.remove(client_socket)
