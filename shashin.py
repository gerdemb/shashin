#!/usr/bin/env python3

import sys

import configargparse

import exceptions
from commands import _import, organize_library, random_snapshots, browse_duplicates

DEFAULT_CONFIG_FILE = '~/.config/shashin/shashin.conf'
DEFAULT_DATABASE_FILE = '~/.config/shashin/shashin.db'
DEFAULT_HIERARCHY = r'''
{% if DateTimeOriginal %}
    {{ DateTimeOriginal.strftime('%Y/%m/%d') }}
{% else %}
    {{ FileModifyDate.strftime('%Y/%m/%d') }}
{% endif %}
'''


def get_parser():
    parser = configargparse.ArgumentParser(add_help=False, default_config_files=[DEFAULT_CONFIG_FILE],
                                           config_file_parser_class=configargparse.YAMLConfigFileParser)

    # https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument(
        '-h',
        '--help',
        action='help',
        default=configargparse.SUPPRESS,
        help='show this help message and exit'
    )
    required.add_argument('-l', '--library', required=True, help='library path')
    required.add_argument('-p', '--hierarchy', required=True, help='directory hierarchy for library',
                          default=DEFAULT_HIERARCHY)
    optional.add_argument('-c', '--config', is_config_file=True, default=DEFAULT_CONFIG_FILE,
                          help='Config file path (default: %(default)s)')
    optional.add_argument('-d', '--database', default=DEFAULT_DATABASE_FILE,
                          help='database filename (default: %(default)s)')
    # https://stackoverflow.com/questions/23349349/argparse-with-required-subparser
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    import_parser = subparsers.add_parser("import", help="Import files into the library")
    import_parser.add_argument("import_path", help="path of images to import")
    import_parser.add_argument("-m", "--move", dest='import_action', action='store_const', const='mv', default='cp',
                               help="move file on import (default is to copy)")
    group = import_parser.add_mutually_exclusive_group()
    group.add_argument("--import-duplicates", action="store_true", help="import duplicate files")
    group.add_argument("--delete-duplicates", action="store_true", help="delete duplicates from import directory")
    import_parser.set_defaults(cls=_import.ImportCommand)

    organize_library_parser = subparsers.add_parser("organize-library",
                                                  help="Rescan the library for changes and update the database")
    organize_library_parser.set_defaults(cls=organize_library.OrganizeLibraryCommand)

    random_snapshots_parser = subparsers.add_parser("random-snapshots",
                                                    help="Export a random selection of images as snapshots")
    random_snapshots_parser.add_argument("export_path", help="path to export images")
    random_snapshots_parser.set_defaults(cls=random_snapshots.RandomSnapshotsCommand)

    browse_duplicates_parser = subparsers.add_parser("browse-duplicates",
                                                     help="Start a server to allow browsing of duplicate images")
    browse_duplicates_parser.set_defaults(cls=browse_duplicates.BrowseDuplicatesCommand)

    return parser


def main(args):
    parser = get_parser()
    config = parser.parse_args(args)
    config.cls(config).execute()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except exceptions.UserError as e:
        print(e)
