import tempfile
from pathlib import Path

from wand.exceptions import DelegateError
from wand.image import Image

from db import DB


class RandomSnapshotsCommand(object):

    def __init__(self, config):
        self.library = config.library
        self.export_path = config.export_path
        self.database = config.database

    def execute(self):
        library_path = Path(self.library)
        export_path = Path(self.export_path)
        with DB(self.database) as db:
            for row in db.image_select_random(100):
                file = library_path / row['file_name']
                try:
                    with Image(filename=str(file)) as original:
                        with original.convert('jpeg') as converted:
                            converted.thumbnail(
                                *self.calculate_proportional_size(original.size,
                                                                  (1024, 1024)))
                            converted.save(filename=tempfile.mktemp(
                                dir=str(export_path),
                                prefix="thumb_",
                                suffix=".jpg"))
                except DelegateError:
                    # Error reading file
                    continue

    @classmethod
    def calculate_proportional_size(cls, original, resize):
        ratio = min(resize[0] / original[0], resize[1] / original[1])
        return int(original[0] * ratio), int(original[1] * ratio)
