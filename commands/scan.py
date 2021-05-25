import sqlite3
from pathlib import Path

from db import DB
from dhash import dhash_row_col, format_bytes
from exceptions import UserError
from exif import Exif
from file_utils import normalized_path, path_file_walk, quote_path as qp
from wand.image import Image

from synology import get_thumbnail


class ScanCommand(object):

    def __init__(self, config):
        self.verbose = config.verbose
        self.quiet = config.quiet
        self.cache_dir = config.cache_dir
        self.scan_dirs = [normalized_path(scan_dir) for scan_dir in config.scan_dirs]
        for scan_dir in self.scan_dirs: 
            if not scan_dir.exists():
                raise UserError(f"{scan_dir} does not exist")

    def execute(self):
        with DB(self.cache_dir) as db:
            with Exif() as et:
                for scan_dir in self.scan_dirs:
                    for file in path_file_walk(scan_dir):
                        try:
                            action = self.scan_file(db, et, file)
                        except Exception as e:
                            print(f"# ERROR rm {qp(file)} # {e}")
                            continue
                        if self.verbose and action is None:
                            print(f"# SKIPPED {file}")
                        elif not self.quiet and action:
                            print(f"{action.upper()} {qp(file)}")
            self.scan_db(db)

    @classmethod
    def scan_file(cls, db, et, file):
        # Check if file is already in DB
        stat = file.stat()
        row = db.image_select_by_file_name_stats(
            str(file), stat.st_mtime, stat.st_size)
        if row:
            # File in db and unchanged
            return
        
        # File is missing from DB or has been modified
        metadata = et.get_metadata(file)
        
        dhash = None
        if metadata['MIMEType'].startswith('image/'):
            dhash = cls.calculate_dhash(file)

        data = {
            'mtime': stat.st_mtime,
            'size': stat.st_size,
            'dhash': dhash,
            'metadata': metadata,
        }
        db.image_insert_or_replace(
            file_name=file,
            **data
        )
        if row:
            return 'update'
        else:
            return 'insert'

    @staticmethod
    def calculate_dhash(file):
        thumbnail = get_thumbnail(file)
        if thumbnail.exists(): 
            file = thumbnail
        with Image(filename=str(file)) as image:
            return sqlite3.Binary(format_bytes(*dhash_row_col(image)))

    def scan_db(self, db):
        def file_missing(row):
            is_missing = not Path(row['file_name']).exists()
            if is_missing and not self.quiet:
                print(f"# DELETE {row['file_name']}")
            return is_missing
        db.image_purge(file_missing)
