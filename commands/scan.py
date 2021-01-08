import hashlib
import os
import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

from db import DB
from dhash import dhash_row_col, format_bytes
from exceptions import UserError
from exif import Exif
from file_utils import path_file_walk
from wand.exceptions import DelegateError, MissingDelegateError
from wand.image import Image


class ScanCommand(object):

    def __init__(self, config):
        self.cache_dir = config.cache_dir
        self.scan_dir = Path(config.scan_dir).expanduser()
        if not self.scan_dir.exists():
            raise UserError(f"{self.scan_dir} does not exist")

    def execute(self):
        with DB(self.cache_dir) as db:
            with Exif() as et:
                self.scan_files(db, et)
            self.scan_db(db)

    def scan_files(self, db, et):
        for file in path_file_walk(self.scan_dir):
            # Get file Stats
            stat = file.stat()
            mtime = stat.st_mtime
            size = stat.st_size

            # Check if file is already in DB
            row = db.image_select_by_file_name(file)
            if row and row['mtime'] == mtime and row['size'] == size:
                # File in db and unchanged
                continue
            # File is missing from DB or has been modified
            try:
                metadata = et.get_metadata(file)
            except Exception as e:
                print("Error {} {}".format(file, e))
                continue
            md5 = self.calculate_md5(file)
            dhash = self.calculate_dhash(et, file)
            if not dhash:
                dhash = md5

            data = {
                'mtime': mtime,
                'size': size,
                'md5': md5,
                'dhash': dhash,
                'metadata': metadata,
            }
            db.image_insert_or_replace(
                file_name=file,
                **data
            )
            print(f"Added {file}")

    @staticmethod
    def calculate_dhash(et, file):
        try:
            with Image(filename=str(file)) as image:
                return sqlite3.Binary(format_bytes(*dhash_row_col(image)))
        except (MissingDelegateError, DelegateError):
            # Unable to load Image. Probably a video.
            # Perceptual hashes are not supported for videos, use an md5 hash instead.
            # First, try to strip all metadata and calculate md5 hash. 
            # exiftool doesn't support modifying tags for most videos, so this usually (always?) fails.
            with NamedTemporaryFile() as t:
                tmp = Path(t.name)
                et.execute_raw(str(file), "-all=", "-o", str(tmp))
                if tmp.stat().st_size > 0:
                    return ScanCommand.calculate_md5(tmp)


    @staticmethod
    def calculate_md5(file):
        hash_md5 = hashlib.md5()
        with file.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return sqlite3.Binary(hash_md5.digest())

    @staticmethod
    def scan_db(db):
        db.image_purge(
            lambda row: not Path(row['file_name']).exists()
        )
