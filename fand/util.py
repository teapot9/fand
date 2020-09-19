"""Utility library for fand"""

import logging
import os
import signal
import socket
import sys
import time
from typing import (Any, Callable, List, NoReturn, Optional, Tuple, Dict,
                    TYPE_CHECKING)

from fand import __version__

if TYPE_CHECKING:
    import argparse

# Constants
# Logger to use
logger = logging.getLogger(__name__)

# Global variables
# Set by terminate(), get by terminating()
__TERMINATE__ = False
# Store the terminate error
__TERMINATE_ERROR__: Optional[str] = None
# List of functions to call when the program is terminating
__WHEN_TERMINATE__: List[Tuple[Callable, Tuple, Dict]] = []


def terminate(error: Optional[str] = None) -> None:
    """Function terminating the program

    Sets the terminate flag (see :func:`terminating`), and does some cleanup
    (see :func:`when_terminate`)

    :param error: Error message to print
    """
    global __TERMINATE__, __TERMINATE_ERROR__
    if error is not None:
        logger.critical(error)
    if terminating():
        return
    logger.info("Terminating...")
    __TERMINATE__ = True
    __TERMINATE_ERROR__ = error
    for function, args, kwargs in __WHEN_TERMINATE__:
        function(*args, **kwargs)


def sys_exit() -> NoReturn:
    """Exit the program with the error from :func:`terminate` if any"""
    if not terminating():
        terminate()
    if __TERMINATE_ERROR__ is None:
        sys.exit(0)
    else:
        sys.exit(__TERMINATE_ERROR__)


def terminating() -> bool:
    """Returns True if the program is terminating, else False"""
    return __TERMINATE__


def when_terminate(function: Callable, *args: Any, **kwargs: Any) -> None:
    """Add function to call when terminating

    :param function: Function to call
    :param args: Arguments to call the function with
    :param kwargs: Keyworded arguments to call the function with
    """
    __WHEN_TERMINATE__.append((function, args, kwargs))


def sleep(secs: float) -> None:
    """Sleep some time, stops if terminating

    :param secs: Number of seconds to sleep
    """
    logger.debug("Waiting for %s seconds", secs)
    while secs > 0 and not terminating():
        time.sleep(1 if secs > 1 else secs)
        secs -= 1


def default_signal_handler(sig: signal.Signals, _: Any) -> None:
    """Default signal handler"""
    if sig == signal.SIGINT:
        logger.warning("Received SIGINT, terminating")
        terminate()
    elif sig == signal.SIGTERM:
        logger.warning("Received SIGTERM, terminating")
        terminate()
    else:
        logger.error("Unknown signal %s received, ignoring", sig)


def parse_args(parser: 'argparse.ArgumentParser') -> 'argparse.Namespace':
    """Add common arguments, parse arguments, set root logger verbosity

    :param parser: Argument parser to use
    """
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
