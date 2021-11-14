import shutil
import tempfile
from pathlib import Path

from wand.exceptions import DelegateError, MissingDelegateError
from wand.image import Image
from plugins import Plugin
from db import DB

from synology import get_thumbnail


class RandomSnapshotsCommand(Plugin):

    def __init__(self, config):
        super().__init__(
            config,
            r'''SELECT * FROM images ORDER BY RANDOM() LIMIT ?''',
            (config.number,)
        )
        self.export_dir = str(config.export_dir)
        self.verbose = config.verbose

    def process_row(self, et, row):
        file_path = Path(row['file_name'])
        thumbnail = get_thumbnail(file_path, size='XL')
        if thumbnail.exists(): 
            dest = tempfile.mktemp(
                dir=str(self.export_dir),
                prefix="thumb_",
                suffix=".jpg"
            )
            shutil.copy(thumbnail, dest)
            if self.verbose:
                print(dest)
