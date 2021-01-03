import sys

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
                    # Sanity Check that actual metadata matches data in DB
                    if "DateTimeOriginal" not in metadata:
                        file_modify_date = metadata['FileModifyDate']
                        params = [
                            f'-DateTimeOriginal={file_modify_date[:19]}'
                        ]
                        result = et.execute_raw(
                            file_name,
                            *params
                        )
                        print(file_name, params, result)
