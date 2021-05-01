import hashlib
import os
import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

from db import DB
from dhash import dhash_row_col, format_bytes
from exceptions import UserError
from exif import Exif
from file_utils import path_file_walk, print_action
from wand.exceptions import DelegateError, MissingDelegateError, WandRuntimeError
from wand.image import Image

from synology import get_thumbnail

class ScanCommand(object):

    def __init__(self, config):
        self.verbose = config.verbose
        self.quiet = config.quiet
        self.cache_dir = config.cache_dir
        self.scan_dirs = [Path(scan_dir).expanduser() for scan_dir in config.scan_dirs]
        for scan_dir in self.scan_dirs: 
            if not scan_dir.exists():
                raise UserError(f"{scan_dir} does not exist")

    def execute(self):
        with DB(self.cache_dir) as db:
            with Exif() as et:
                for scan_dir in self.scan_dirs:
                    self.scan_files(db, et, scan_dir)
            self.scan_db(db)

    def scan_files(self, db, et, scan_dir):
        for file in path_file_walk(Path(scan_dir).expanduser()):
            # Get file Stats
            stat = file.stat()
            mtime = stat.st_mtime
            size = stat.st_size

            # Check if file is already in DB
            row = db.image_select_by_file_name(file)
            if row and row['mtime'] == mtime and row['size'] == size:
                # File in db and unchanged
                if self.verbose:
                    print_action("SKIPPED", file)
                continue
            # File is missing from DB or has been modified

            try:
                metadata = et.get_metadata(file)
            except Exception as e:
                print_action("ERROR", file, e)
                continue

            try:
                dhash = self.calculate_dhash(et, file)
            except Exception as e:
                dhash = None
                print_action("WARNING", file, e)

            data = {
                'mtime': mtime,
                'size': size,
                'dhash': dhash,
                'metadata': metadata,
            }
            db.image_insert_or_replace(
                file_name=file,
                **data
            )
            if self.quiet:
                if row:
                    print_action("UPDATED", file)
                else:
                    print_action("ADDED", file)

    @staticmethod
    def calculate_dhash(et, file):
        thumbnail = get_thumbnail(file)
        if thumbnail.exists(): 
            file = thumbnail
        with Image(filename=str(file)) as image:
            return sqlite3.Binary(format_bytes(*dhash_row_col(image)))

    @staticmethod
    def scan_db(db):
        db.image_purge(
            lambda row: not Path(row['file_name']).exists()
        )
