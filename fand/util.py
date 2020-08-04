"""Utility library for fand"""

import logging
import signal
import socket
import sys
import time

from fand import __version__

# Constants
# Logger to use
logger = logging.getLogger(__name__)

# Global variables
# Set by terminate(), get by terminating()
__TERMINATE__ = False
# List of functions to call when the program is terminating
__WHEN_TERMINATE__ = []


def terminate(error=0):
    """Function terminating the program, does not return
    error: error message to print (defaults to nothing)
    """
    global __TERMINATE__
    if error != 0:
        logger.critical(error)
    if __TERMINATE__:
        sys.exit(error)
    logger.info("Terminating...")
    __TERMINATE__ = True
    for function, args in __WHEN_TERMINATE__:
        function(*args)
    sys.exit(error)


def terminating():
    """Returns True if the program is terminating, else False"""
    return __TERMINATE__


def when_terminate(function, *args):
    """Add function to call when terminating"""
    __WHEN_TERMINATE__.append((function, args))


def sleep(secs):
    """Sleep secs seconds, stops if terminating"""
    logger.debug("Waiting for %s seconds", secs)
    while secs > 0 and not terminating():
        time.sleep(1 if secs > 1 else secs)
        secs -= 1


def default_signal_handler(sig, _):
    """Default signal handler"""
    if sig == signal.SIGINT:
        logger.warning("Received SIGINT, terminating")
        terminate()
    elif sig == signal.SIGTERM:
        logger.warning("Received SIGTERM, terminating")
        terminate()
    else:
        logger.error("Unknown signal %s received, ignoring", sig)


def parse_args(parser):
    """Add common arguments, parse arguments, set root logger verbosity"""
    parser.add_argument('--version', '-V', action='version',
                        version='%(prog)s '+__version__)
    parser.add_argument('--address', '-a', default=socket.gethostname(),
                        help="Server address, defaults to hostname")
    parser.add_argument('--port', '-p', default=9999, type=int,
                        help="Server port, defaults to 9999")
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help="Set verbosity level")
    parser.add_argument('--quiet', '-q', action='store_true',
                        help="Set minimal output")
    args = parser.parse_args()
    if args.quiet:
        level = logging.CRITICAL
    elif args.verbose == 0:
        level = logging.ERROR
    elif args.verbose == 1:
        level = logging.WARNING
    elif args.verbose == 2:
        level = logging.INFO
    else:
        level = logging.DEBUG
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    return args
