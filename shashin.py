#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys

from exceptions import UserError
from commands import browse, scan

CACHE_DIR = '~/.cache/shashin/'


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cache-dir', default=CACHE_DIR,
                        help='cache directory (default: %(default)s)')

    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("scan_dir", help="dir of images to scan")
    scan_parser.set_defaults(cls=scan.ScanCommand)

    browse_parser = subparsers.add_parser("browse")
    browse_parser.set_defaults(cls=browse.BrowseCommand)

    return parser


def main(args):
    parser = get_parser()
    config = parser.parse_args(args)

    # Check that cache_dir exists or create it
    config.cache_dir = Path(config.cache_dir).expanduser()
    if not config.cache_dir.exists():
        config.cache_dir.mkdir(parents=True)
    elif not config.cache_dir.is_dir():
        raise UserError(f"{config.cache_dir} is not a directory")

    config.cls(config).execute()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except UserError as e:
        print(e)
