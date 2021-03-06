from db_utils import get_cached_metadata
from datetime import datetime
from pathlib import Path

from db import DB
from exceptions import UserError
from exif import Exif
from file_utils import action_required, path_file_walk
from jinja2 import Environment


class FileCommand(object):

    def __init__(self, config, action):
        self.cache_dir = config.cache_dir
        self.src = Path(config.src).expanduser()
        self.dest = Path(config.dest).expanduser()
        self.hierarchy = config.hierarchy
        self.action = action

        if not self.src.exists():
            raise UserError(f"{self.src} does not exist")
        if not self.dest.exists():
            raise UserError(f"{self.dest} does not exist")
        if not self.dest.is_dir():
            raise UserError(f"{self.dest} is not a directory")

        self.template = self._get_template()

    def _get_template(self):
        environment = Environment()

        def to_datetime(value, format='%Y/%m/%d'):
            # Format of EXIF dates
            DATE_TIME_FMT = '%Y:%m:%d %H:%M:%S'
            try:
                return datetime.strptime(value[:19], DATE_TIME_FMT).strftime(format)
            except ValueError:
                # Unable to convert to datetime
                return None
        environment.filters['datetime'] = to_datetime
        return environment.from_string(self.hierarchy)

    def execute(self):
        with DB(self.cache_dir) as db:
            with Exif() as et:
                for file in path_file_walk(self.src):
                    # Check if file is already in DB
                    row = db.image_select_by_file_name(file)
                    try:
                        if row:
                            metadata = get_cached_metadata(et, row)
                        else:
                            metadata = et.get_metadata(file)
                    except Exception as e:
                        print("Error {} {}".format(file, e))
                        continue

                    hierarchy = self.template.render(metadata).strip()
                    dest_path = self.dest / hierarchy

                    if action_required(file, dest_path):
                        if self.action(file, dest_path):
                            print(f"{file} -> {dest_path}")
                        else:
                            print(f"Skipping existing file {file} -> {dest_path}")