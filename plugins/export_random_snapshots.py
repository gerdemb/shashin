import tempfile
from pathlib import Path

from wand.exceptions import DelegateError, MissingDelegateError
from wand.image import Image
from plugins import Plugin
from db import DB

SQL_SELECT = r'''
            SELECT * FROM images ORDER BY RANDOM() LIMIT ?
'''

class RandomSnapshotsCommand(Plugin):

    def __init__(self, config):
        super().__init__(
            config,
            r'''SELECT * FROM images ORDER BY RANDOM() LIMIT ?''',
            (config.number,)
        )
        self.export_dir = str(config.export_dir)

    def process_row(self, et, row):
        file = Path(row['file_name'])
        if file.exists():
            try:
                with Image(filename=str(file)) as original:
                    with original.convert('jpeg') as converted:
                        converted.thumbnail(
                            *self.calculate_proportional_size(original.size,
                                                                (1024, 1024)))
                        filename = tempfile.mktemp(
                            dir=str(self.export_dir),
                            prefix="thumb_",
                            suffix=".jpg"
                        )
                        converted.save(filename=filename)
                        print(filename)
            except (DelegateError, MissingDelegateError):
                # Error reading file
                pass

    @staticmethod
    def calculate_proportional_size(original, resize):
        ratio = min(resize[0] / original[0], resize[1] / original[1])
        return int(original[0] * ratio), int(original[1] * ratio)