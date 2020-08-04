"""Communicate request with a remote socket"""

import logging
import pickle
import socket

import fand.util as util

# Known requests
REQ_ACK = 'ack'
REQ_PING = 'ping'
REQ_GET_PWM = 'get_pwm'
REQ_SET_PWM = 'set_pwm'
REQ_GET_RPM = 'get_rpm'
REQ_SET_RPM = 'set_rpm'

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
        raise TimeoutError() from error
    except OSError as error:
        raise ConnectionError() from error
    if bytes_sent != HEADER_SIZE + len(data_bytes):
        raise ConnectionError(f"Not all data sent to {sock}")

    logger.debug("%s sent to %s", request, sock)


def recv(sock):
    """Receive a request from a remote socket"""
    logger.debug("Waining for data from %s", sock)

    try:
        header = sock.recv(HEADER_SIZE)
    except socket.timeout as error:
        raise TimeoutError() from error
    except OSError as error:
        raise ConnectionError() from error
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
        raise TimeoutError() from error
    except OSError as error:
        raise ConnectionError() from error
    except (pickle.PickleError, TypeError, ValueError) as error:
        raise ValueError() from error

    logger.debug("Received %s from %s with arguments %s", request, sock, args)
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


def reset_connection(client_socket):
    """Closes a connection to a client"""
    logger.info("Closing connection to %s", client_socket)
    if client_socket not in SOCKETS:
        return
    try:
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()
    except OSError as error:
        logger.warning("Could not close %s because %s", client_socket, error)
    SOCKETS.remove(client_socket)
