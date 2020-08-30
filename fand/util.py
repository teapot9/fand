"""Utility library for fand"""

import logging
import os
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
# Store the terminate error
__TERMINATE_ERROR__ = None
# List of functions to call when the program is terminating
__WHEN_TERMINATE__ = []


def terminate(error=None):
    """Function terminating the program
    Sets the terminate flag (see terminating()), and does some cleanup
    (see when_terminate())
    error: error message to print (defaults to nothing)
    """
    global __TERMINATE__, __TERMINATE_ERROR__
    if error is not None:
        logger.critical(error)
    if __TERMINATE__:
        return
    logger.info("Terminating...")
    __TERMINATE__ = True
    __TERMINATE_ERROR__ = error
    for function, args in __WHEN_TERMINATE__:
        function(*args)


def sys_exit():
    """Exit the program with the error from terminate()"""
    if not __TERMINATE__:
        terminate()
    if __TERMINATE_ERROR__ is None:
        sys.exit(0)
    else:
        sys.exit(__TERMINATE_ERROR__)


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
    parser.add_argument('--logfile', '-l', default=None,
                        help="Send output logs to logfile")
    parser.add_argument('--pidfile', '-P', default=None,
                        help="Set PID file for daemon")
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
    if args.logfile is not None:
        handler = logging.FileHandler(args.logfile, 'a', encoding='utf-8')
        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    if args.pidfile is not None:
        with open(args.pidfile, 'w') as pidfile:
            pidfile.write(str(os.getpid()))
    return args
