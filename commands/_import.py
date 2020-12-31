from enum import Enum
from pathlib import Path

from exif import Exif

from commands.command import Command
from db import DB
from exceptions import UserError
from library import Library
from utils import get_file_stats, path_file_walk, is_child


class ImportCommand(Command):
    DuplicateActions = Enum('DuplicateActions', 'SKIP RM IMPORT')

    def __init__(self, config):
        super().__init__(config)
        if is_child(Path(config.library), Path(config.import_path)):
            raise UserError(
                "Import path {} is inside library {}".format(config.import_path, config.library))

        self.library_path = Path(config.library)
        self.hierarchy = config.hierarchy
        self.import_path = Path(config.import_path)
        self.database_file = config.database

        self.import_action = Library.cp
        if config.import_action == 'mv':
            self.import_action = Library.mv
        self.duplicate_action = self.DuplicateActions.SKIP
        if config.import_duplicates:
            self.duplicate_action = self.DuplicateActions.IMPORT
        elif config.delete_duplicates:
            self.duplicate_action = self.DuplicateActions.RM

    def execute(self):
        with DB(self.database_file) as db:
            with Exif() as et:
                library = Library(self.library_path, self.hierarchy)
                for file in path_file_walk(self.import_path):
                    # TODO no need to calculate dhash at this point if md5 matches
                    stats = get_file_stats(file)
                    duplicates = db.image_select_by_md5_and_size(stats['md5'], stats['size']).fetchall()
                    if duplicates:
                        if self.duplicate_action == self.DuplicateActions.SKIP:
                            print("Skipping duplicate {}".format(file))
                            continue
                        elif self.duplicate_action == self.DuplicateActions.RM:
                            print("Deleting duplicate {}".format(file))
                            file.unlink()
                            continue
                        elif self.duplicate_action == self.DuplicateActions.IMPORT:
                            pass
                    # 2. If necessary, move file to new location
                    try:
                        metadata = et.get_metadata(str(file))
                        imported_file = library.import_image(metadata, self.import_action)
                    except Exception as e:
                        print("Error {} {}".format(file, e))
                        continue
                    db.image_insert(file_name=str(imported_file), metadata=metadata, **stats)
                    print("Imported {} -> {}".format(file, imported_file.parent))
