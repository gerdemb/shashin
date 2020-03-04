from pathlib import Path

from exif import ExifTool

from commands.command import Command
from db import DB
from exceptions import UnknownFileType, ExifToolError
from utils import get_file_stats, import_image, get_mtime_and_size, path_file_walk, mv, is_empty_dir, path_dir_walk


class RescanLibraryCommand(Command):

    def __init__(self, config):
        super().__init__(config)
        self.library_path = Path(config.library)
        self.database = config.database

    def execute(self):
        self.scan_database()
        self.scan_files()
        self.scan_directories()

    def scan_database(self):
        with DB(self.database) as db:
            db.image_purge(lambda row:
                           not Path(row['file_name']).exists()
                           )

    def scan_files(self):
        with DB(self.database) as db:
            with ExifTool() as et:
                for file in path_file_walk(self.library_path):
                    mtime, size = get_mtime_and_size(file)
                    row = db.image_select_by_file_name(str(file))
                    if row and row['mtime'] == mtime and row['size'] == size:
                        # File in db and unchanged
                        continue
                    # File md5 or size doesn't match database or file is missing
                    # 1. Delete row from DB if it exists
                    if row:
                        db.image_delete(str(file))
                    # 2. If necessary, move file to new location
                    try:
                        imported_file = import_image(et, file, self.library_path, action=mv)
                    except (UnknownFileType, ExifToolError) as e:
                        print("Error", file, e)
                        continue
                    stats = get_file_stats(imported_file)
                    db.image_insert(file_name=str(imported_file), **stats)
                    if row:
                        if file == imported_file:
                            print("Updated", file)
                        else:
                            print("Moved {} -> {}".format(file, imported_file))
                    else:
                        print("Added", file)

    def scan_directories(self):
        for dir in path_dir_walk(self.library_path):
            if is_empty_dir(dir):
                print("Empty directory {}".format(dir))
                dir.rmdir()
