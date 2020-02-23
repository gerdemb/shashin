import os
from pathlib import Path
from db import DB
from exiftool import ExifTool

from utils import is_child, get_file_stats, import_image_library, path_walk, UnkownFileType, ExifToolError


def scan_files(db, library_root, import_path):
    with ExifTool() as et:
        for file in path_walk(import_path):
            # TODO no need to calculate dhash at this point if md5 matches
            stats = get_file_stats(file)
            duplicates = db.image_select_by_md5_and_size(stats['md5'], stats['size']).fetchall()
            if duplicates:
                # TODO do full binary comparison not just md5/size check
                for duplicate in duplicates:
                    print("Duplicates {} = {}".format(file, duplicate['file_name']))
                continue
            # 2. If necessary, move file to new location
            try:
                relative_path = import_image_library(et, file, library_root)
            except (UnkownFileType, ExifToolError) as e:
                print("Error {} {}".format(file, e))
                continue
            db.image_insert(file_name=str(relative_path), **stats)
            print("Imported {} -> {}".format(file, relative_path.parent))


def execute(config):
    library_root = Path(config.library)
    import_path = Path(config.import_path)
    assert(not is_child(library_root, import_path))
    with DB(config.database) as db:
        scan_files(db, library_root, import_path)
