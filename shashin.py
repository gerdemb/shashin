#!/usr/bin/env python3

import argparse
from file_utils import normalized_path
from pathlib import Path
from plugins import export_random_snapshots
import sys

from exceptions import UserError
from commands import browse, organize, scan, cp, mv

CACHE_DIR = '~/.cache/shashin/'

# TODO make configurable
DEFAULT_HIERARCHY = r'''
{% if DateTimeOriginal and DateTimeOriginal|datetime %}
    {{ DateTimeOriginal|datetime('%Y/%m/%d') }}
{% else %}
    {{ FileModifyDate|datetime('%Y/%m/%d') }}
{% endif %}
'''



def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cache-dir', default=CACHE_DIR,
                        help='cache directory (default: %(default)s)')
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument('-v', '--verbose', action='store_true')    
    verbosity.add_argument('-q', '--quiet', action='store_true')    

    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("scan_dirs", nargs='+', help="directories of images to scan")
    scan_parser.set_defaults(cls=scan.ScanCommand)

    browse_parser = subparsers.add_parser("browse")
    browse_parser.set_defaults(cls=browse.BrowseCommand)

    cp_parser = subparsers.add_parser("cp")
    cp_parser.add_argument("src")
    cp_parser.add_argument("dest")
    cp_parser.add_argument('--hierarchy', default=DEFAULT_HIERARCHY)    
    cp_parser.add_argument('--dry-run', action='store_true')    
    cp_parser.set_defaults(cls=cp.CopyCommand)

    mv_parser = subparsers.add_parser("mv")
    mv_parser.add_argument("src")
    mv_parser.add_argument("dest")
    mv_parser.add_argument('--hierarchy', default=DEFAULT_HIERARCHY)
    mv_parser.add_argument('--dry-run', action='store_true')    
    mv_parser.set_defaults(cls=mv.MoveCommand)

    organize_parser = subparsers.add_parser("organize")
    organize_parser.add_argument("src")
    organize_parser.add_argument('--hierarchy', default=DEFAULT_HIERARCHY)
    organize_parser.add_argument('--dry-run', action='store_true')    
    organize_parser.set_defaults(cls=organize.OrganizeCommand)

    export_random_snapshots_parser = subparsers.add_parser("export-random-snapshots")
    export_random_snapshots_parser.add_argument("export_dir")
    export_random_snapshots_parser.add_argument("--number", default=10)
    export_random_snapshots_parser.set_defaults(cls=export_random_snapshots.RandomSnapshotsCommand)
    return parser


def main(args):
    parser = get_parser()
    config = parser.parse_args(args)

    # Check that cache_dir exists or create it
    config.cache_dir = normalized_path(config.cache_dir)
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
