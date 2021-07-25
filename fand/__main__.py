"""fand entry points"""

import argparse
import sys

from fand import __version__


def entry_fand() -> None:
    """Main fand entry point"""
    sys.argv.insert(2, '--')
    parser = argparse.ArgumentParser(description=entry_fand.__doc__)
    parser.add_argument('--version', '-V', action='version',
                        version=f'%(prog)s {__version__}')
    parser.add_argument(
        'service', type=str, choices=('server', 'fanctl', 'clientrpi'),
        help="Select which service to use",
    )
    parser.add_argument('service_args', type=str, nargs='*',
                        help="Arguments to pass to the service")
    args = parser.parse_args()

    if args.service == 'server':
        sys.argv = [sys.argv[0]] + args.service_args
        from fand.server import main as server_main
        server_main()
    elif args.service == 'fanctl':
        sys.argv = [sys.argv[0]] + args.service_args
        from fand.fanctl import main as fanctl_main
        fanctl_main()
    elif args.service == 'clientrpi':
        sys.argv = [sys.argv[0]] + args.service_args
        from fand.clientrpi import main as clientrpi_main
        clientrpi_main()


if __name__ == '__main__':
    entry_fand()
