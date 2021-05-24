import json
from datetime import datetime
from pathlib import Path

from db import DB
from exceptions import UserError
from exif import Exif
from file_utils import path_file_walk, quote_path as qp
from jinja2 import Environment


class FileCommand(object):
    action_name = None

    def __init__(self, config):
        self.verbose = config.verbose
        self.quiet = config.quiet
        self.src = Path(config.src).expanduser()
        self.dest = Path(config.dest).expanduser()
        self.hierarchy = config.hierarchy
        self.dry_run = config.dry_run

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
        with Exif() as et:
            for file in path_file_walk(self.src):
                try:
                    metadata = et.get_metadata(file)
                except Exception as e:
                    print(f"# ERROR {e}")
                    print(f"# rm {qp(file)}")
                    continue

                hierarchy = self.template.render(metadata).strip()
                dest_path = self.dest / hierarchy / file.name

                # Is the file already in the right place?
                if dest_path != file:
                    if dest_path.exists():
                        if self.verbose:
                            print(f"# WARNING Destination file already exists")
                            print(f"# {self.action_name} {qp(file)} {qp(dest_path)}")
                    else:
                        if not dest_path.parent.exists():
                            print(f"mkdir -p {qp(dest_path.parent)}")
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                        if not self.quiet:
                            print(f"{self.action_name} {qp(file)} {qp(dest_path)}")
                        if not self.dry_run:
                            self.action(file, dest_path)
