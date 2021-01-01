import tempfile
from pathlib import Path

from wand.exceptions import DelegateError
from wand.image import Image

from db import DB
from exif import Exif


class FixDatesCommand(object):

    def __init__(self, config):
        self.database = config.database

    def execute(self):
        with DB(self.database) as db:
            with Exif() as et:
                for row in db.image_select_date_time_original_is_null():
                    file_name = row['file_name']
                    metadata = et.get_metadata(file_name)
                    date_time_original = metadata['FileModifyDate'][:19]
                    params = [
                        file_name,
                        '-DateTimeOriginal="{}"'.format(date_time_original)
                    ]
                    print(file_name, date_time_original)
                    et.execute_json(*params)