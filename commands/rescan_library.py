from pathlib import Path
from utils import get_file_stats, import_image_library, get_mtime_and_size, path_walk, UnkownFileType, ExifToolError
from exiftool import ExifTool
import tempfile
import shutil
import re
from db import DB



def scan_files(db, library_path):
    with ExifTool('/var/services/homes/admin/bin/exiftool') as et:
        for file in path_walk(library_path):
            mtime, size = get_mtime_and_size(file)
            relative_file_name = file.relative_to(library_path)
            row = db.image_select_by_file_name(str(relative_file_name))
            if row and row['mtime'] == mtime and row['size'] == size:
                # File in db and unchanged
                continue
            # File md5 or size doesn't match database or file is missing
            # 1. Delete row from DB if it exists
            if row:
                db.image_delete(str(relative_file_name))
            # 2. If necessary, move file to new location
            try:
                relative_path = import_image_library(et, file, library_path)
            except (UnkownFileType, ExifToolError) as e:
                print("Error", file, e)
                continue
            stats = get_file_stats(library_path / relative_path)
            db.image_insert(file_name=str(relative_path), **stats)
            if row:
                print("Updated", file)
            else:
                print("Added", file)



def scan_database(db, library_path):
    db.image_purge(lambda row:
        not (library_path / row['file_name']).exists()
    )


def execute(config):
    library_path = Path(config.library)
    with DB(config.database) as db:
        scan_database(db, library_path)
        scan_files(db, library_path)
        # TODO delete empty directories
    