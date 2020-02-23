#!/usr/bin/env python3

import configargparse
from pathlib import Path
import sys
import os
import commands 

DEFAULT_CONFIG_FILE = '~/.config/shashin/shashin.conf'

def get_parser():
    parser = configargparse.ArgParser(default_config_files=[DEFAULT_CONFIG_FILE])
    parser.add_argument('-l', '--library', required=True, help='library path')
    parser.add_argument('-d', '--database', default ='~/.config/shashin/shashin.db', help='database file')
    parser.add_argument('--magick_home', help='path to ImageMagick libraries')
    subparsers = parser.add_subparsers()

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("import_path", help="path of images to import")
    import_parser.set_defaults(func=commands._import)

    rescan_library_parser = subparsers.add_parser("rescan-library")
    rescan_library_parser.set_defaults(func=commands.rescan_library)

    random_snapshots_parser = subparsers.add_parser("random-snapshots")
    random_snapshots_parser.add_argument("export_path", help="path to export images")
    random_snapshots_parser.set_defaults(func=commands.random_snapshots)

    browse_duplicates_parser = subparsers.add_parser("browse-duplicates")
    browse_duplicates_parser.set_defaults(func=commands.browse_duplicates)

    return parser

def validate(config):
    # TODO make these into valid error messages
    library_root = Path(config.library)
    assert(library_root.exists())
    assert('func' in config)

def main(args):
    parser = get_parser()
    config = parser.parse_args(args)
    validate(config)
    config.func.execute(config)

if __name__ == "__main__":
    main(sys.argv[1:])