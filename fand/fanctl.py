"""fand CLI"""

import argparse
import logging
import signal
import socket

import fand.util as util
import fand.communication as com

# Constants
# Module docstring
__DOCSTRING__ = __doc__
# Logger to use
logger = logging.getLogger(__name__)
# Docstring for actions
__ACTION_DOC__ = """
Known actions are:
  raw         Send raw request to the server
              Syntax: raw REQUEST REQUEST_ARGS
  ping        Ping the server
              Syntax: ping
  shelfpwm    Get the PWM value of a shelf
              Syntax: shelfpwm SHELFNAME
  shelfrpm    Get the RPM value of a shelf
              Syntax: shelfrpm SHELFNAME
"""


def _action_send_raw(server, *args):
    """Send raw request, print the returned request"""
    logger.debug("Sending raw request to %s", server)
    com.send(server, *args)
    req, args = com.recv(server)
    print(f"{req}{args}")


def _action_ping(server):
    """Send ping"""
    logger.debug("Sending ping to %s", server)
    com.send(server, com.REQ_PING)
    req, _ = com.recv(server)
    if req != com.REQ_ACK:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.REQ_ACK, req)
    else:
        print("ok")


def _action_get_shelf_pwm(server, shelf_id):
    """Get shelf PWM speed"""
    logger.debug("Sending get pwm to %s for %s", server, shelf_id)
    com.send(server, com.REQ_GET_PWM, shelf_id)
    req, args = com.recv(server)
    if req != com.REQ_SET_PWM:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.REQ_SET_PWM, req)
    elif args[0] != shelf_id:
        logger.error("Wrong shelf returned by server: expected %s, got %s",
                     shelf_id, args[0])
    else:
        print(args[1])


def _action_get_shelf_rpm(server, shelf_id):
    """Get shelf RPM speed"""
    logger.debug("Sending get rpm to %s for %s", server, shelf_id)
    com.send(server, com.REQ_GET_RPM, shelf_id)
    req, args = com.recv(server)
    if req != com.REQ_SET_RPM:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.REQ_SET_RPM, req)
    elif args[0] != shelf_id:
        logger.error("Wrong shelf returned by server: expected %s, got %s",
                     shelf_id, args[0])
    else:
        print(args[1])


ACTION_DICT = {
    'raw': _action_send_raw,
    'ping': _action_ping,
    'shelfpwm': _action_get_shelf_pwm,
    'shelfrpm': _action_get_shelf_rpm,
}


def main():
    """Entry point of the module"""
    parser = argparse.ArgumentParser(
        description=__DOCSTRING__,
        epilog=__ACTION_DOC__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('action', help="Select an action")
    parser.add_argument('args', nargs='*', help="Action arguments")
    args = util.parse_args(parser)
    logger.info("Started from main entry point with parameters %s", args)
    send(args.action, *args.args, address=args.address, port=args.port)


def send(action, *args, address=socket.gethostname(), port=9999):
    """Main function of this module"""
    logger.debug("Running action %s", action)
    signal.signal(signal.SIGINT, util.default_signal_handler)
    signal.signal(signal.SIGTERM, util.default_signal_handler)
    try:
        server = com.connect(address, port)
    except (TimeoutError, ConnectionError):
        logger.exception("Failed to connect to %s:%s", address, port)
        util.terminate("Cannot connect to server")
    handler = ACTION_DICT.get(action)
    if not handler:
        logger.error("Invalid action %s", action)
    else:
        try:
            handler(server, *args)
        except TypeError:
            logger.exception("Invalid call to acion %s", action)
    util.terminate()
