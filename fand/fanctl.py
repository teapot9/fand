"""fand CLI"""

import argparse
import datetime
import logging
import re
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
  raw                   Send raw request to the server
                        Syntax: raw REQUEST REQUEST_ARGS
  ping                  Ping the server
                        Syntax: ping
  shelfpwm              Get the PWM value of a shelf
                        Syntax: shelfpwm SHELFNAME
  shelfpwm-override     Override the PWM value of a shelf
                        Syntax: shelfpwm-override SHELFNAME VALUE
                        VALUE: percentage (speed)
  shelfpwm-expire-in    Set expiration date of PWM override
                        Syntax: shelfpwm-expire-in SHELFNAME DURATION
                        DURATION: how much time before expiration
                        Supported DURATION examples: '21d4h1m5s', '4h10s',
                        '7:22:59:00' (7d, 22h, 59min, 00s),
                        '4:22.5' (4min, 22.5s), '10' (10 seconds)
                        See DATETIME_DURATION_FORMATS for more informations.
  shelfpwm-expire-on    Set expiration date of PWM override
                        Syntax: shelfpwm-expire-on SHELFNAME DATE
                        DATE: date on which the override expire
                        Supported DATE examples: '2020-29-12T01:01:59',
                        '2020-29-12T01:01:59+01:00', '08/16/1988 21:30:00',
                        'Tue Aug 16 21:30:00 1988' (last two examples are
                        locale defined).
                        See DATETIME_DATE_FORMATS for more informations.
  shelfrpm              Get the RPM value of a shelf
                        Syntax: shelfrpm SHELFNAME
"""
# Datetime accepted string formats for datetime.datetime
DATETIME_DATE_FORMATS = [
    "%c",
    "%x %X",
    "%xT%X",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%Z",
    "%Y-%m-%dT%H:%M:%S.%f%Z",
]
# Datetime accepted string formats for datetime.timedelta
DATETIME_DURATION_FORMATS = [
    r'^((?P<day>\d+?)d)?((?P<h>\d+?)h)?((?P<min>\d+?)m)?((?P<sec>\d+?)s)?$',
    r'^(?P<sec>\d+?)$',
    r'^(?P<min>\d+?):(?P<sec>\d+?)$',
    r'^(?P<h>\d+?):(?P<min>\d+?):(?P<sec>\d+?)$',
    r'^(?P<day>\d+?):(?P<h>\d+?):(?P<min>\d+?):(?P<sec>\d+?)$',
    r'^(?P<day>\d+?):(?P<h>\d+?):(?P<min>\d+?):(?P<sec>\d+?).(?P<ms>\d+?)$',
]


def _action_send_raw(server, *args):
    """Send raw request, print the returned request"""
    logger.debug("Sending raw request to %s", server)
    com.send(server, *args)
    req, args = com.recv(server)
    print(f"{req}{args}")


def _action_ping(server):
    """Send ping"""
    logger.debug("Sending ping to %s", server)
    com.send(server, com.Request.PING)
    req, _ = com.recv(server)
    if req != com.Request.ACK:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.Request.ACK, req)
    else:
        print("ok")


def _action_get_shelf_pwm(server, shelf_id):
    """Get shelf PWM speed"""
    logger.debug("Sending get pwm to %s for %s", server, shelf_id)
    com.send(server, com.Request.GET_PWM, shelf_id)
    req, args = com.recv(server)
    if req != com.Request.SET_PWM:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.Request.SET_PWM, req)
    elif args[0] != shelf_id:
        logger.error("Wrong shelf returned by server: expected %s, got %s",
                     shelf_id, args[0])
    else:
        print(args[1])


def _action_get_shelf_rpm(server, shelf_id):
    """Get shelf RPM speed"""
    logger.debug("Sending get rpm to %s for %s", server, shelf_id)
    com.send(server, com.Request.GET_RPM, shelf_id)
    req, args = com.recv(server)
    if req != com.Request.SET_RPM:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.Request.SET_RPM, req)
    elif args[0] != shelf_id:
        logger.error("Wrong shelf returned by server: expected %s, got %s",
                     shelf_id, args[0])
    else:
        print(args[1])


def _action_set_pwm_override(server, shelf_id, value_str):
    """Override shelf PWM value to value_str"""
    logger.debug("Overriding PWM of %s to %s", shelf_id, value_str)
    if str(value_str).lower() == 'none':
        value = None
    else:
        value = int(value_str)
    logger.debug("Sending set PWM override to %s for %s to %s",
                 value, shelf_id, server)
    com.send(server, com.Request.SET_PWM_OVERRIDE, shelf_id, value)
    req, _ = com.recv(server)
    if req != com.Request.ACK:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.Request.ACK, req)
    else:
        print("ok")


def _action_set_pwm_expire_on(server, shelf_id, date_str):
    """Set shelf PWM override expiration to date_str"""
    logger.debug("Setting PWM override on %s for %s", date_str, shelf_id)
    for test_str in DATETIME_DATE_FORMATS:
        try:
            date = datetime.datetime.strptime(date_str.strip(), test_str)
            break
        except ValueError:
            pass
        except AttributeError as error:
            raise AttributeError(f"Expected string, got {type(date_str)}") \
                from error
    else:
        raise ValueError(f"Could not convert {date_str} to a datetime object")
    logger.debug("Sending set PWM expire on %s for %s to %s",
                 date, shelf_id, server)
    com.send(server, com.Request.SET_PWM_EXPIRE, shelf_id, date)
    req, _ = com.recv(server)
    if req != com.Request.ACK:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.Request.ACK, req)
    else:
        print("ok")


def _action_set_pwm_expire_in(server, shelf_id, duration_str):
    """Set shelf PWM override expiration in duration_str"""
    logger.debug("Setting PWM override in %s for %s", duration_str, shelf_id)
    for test_str in DATETIME_DURATION_FORMATS:
        match = re.match(test_str, duration_str.strip())
        if match:
            break
    else:
        raise ValueError(f"Cannot convert {duration_str} to timedelta object")
    match_dict = {k: v for k, v in match.groupdict().items() if v is not None}
    duration = datetime.timedelta(
        days=int(match_dict.get('day', 0)),
        hours=int(match_dict.get('h', 0)),
        minutes=int(match_dict.get('min', 0)),
        seconds=int(match_dict.get('sec', 0)),
        milliseconds=int(match_dict.get('ms', 0)),
    )
    logger.debug("Converted %s to %s = %s", duration_str, match_dict, duration)
    date = datetime.datetime.now(datetime.timezone.utc) + duration
    logger.debug("Sending set PWM expire in %s (%s) for %s to %s",
                 duration, date, shelf_id, server)
    com.send(server, com.Request.SET_PWM_EXPIRE, shelf_id, date)
    req, _ = com.recv(server)
    if req != com.Request.ACK:
        logger.error("Unexpected request from server: expected %s, got %s",
                     com.Request.ACK, req)
    else:
        print("ok")


ACTION_DICT = {
    'raw': _action_send_raw,
    'ping': _action_ping,
    'shelfpwm': _action_get_shelf_pwm,
    'shelfrpm': _action_get_shelf_rpm,
    'shelfpwm-override': _action_set_pwm_override,
    'shelfpwm-expire-on': _action_set_pwm_expire_on,
    'shelfpwm-expire-in': _action_set_pwm_expire_in,
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
            util.terminate("Invalid action")
        except ValueError:
            logger.exception("Received value error in action %s", action)
            util.terminate("Invalid arguments")
        except ConnectionResetError:
            logger.error("Connection reset by server during %s", action)
            util.terminate("Connection reset by server")
    util.terminate()
