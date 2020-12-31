import shutil
import tempfile
from pathlib import Path

from jinja2 import Environment
import datetime
from utils import is_child
from datetime import datetime

class Library(object):
    DATE_TIME_FMT = '%Y:%m:%d %H:%M:%S'

    def __init__(self, library_path, hierarchy):
        self.library_path = library_path
        self.template = self._get_template(hierarchy)

    def _get_template(self, hierarchy):
        environment = Environment()
        def to_datetime(value, format='%Y/%m/%d'):
            try:
                return datetime.strptime(value[:19], self.DATE_TIME_FMT).strftime(format)
            except ValueError:
                # Unable to convert to datetime
                return None
        environment.filters['datetime'] = to_datetime
        return environment.from_string(hierarchy)

    def _get_path_heirarchy(self, metadata):
        return Path(self.template.render(metadata).strip())

    def import_image(self, metadata, action):
        # 1. Calculate destination path
        file = Path(metadata['SourceFile'])
        dest_path = self.library_path / self._get_path_heirarchy(metadata)

        if is_child(dest_path, file):
            # File is already in correct location. Should only happen when importing
            # from inside the library or allowing duplicates to import
            return file
        if (dest_path / file.name).exists():
            # Different file, but with same name already exists
            dest_path = Path(tempfile.mkdtemp(prefix=file.name + '.', dir=str(dest_path)))
        # 2. Move file
        action(file, dest_path)
        return dest_path / file.name

    @staticmethod
    def _prepare_destination(file, dest_path):
        # These assertions should never happen, but are included to prevent unintended data loss by accidentally
        # overwriting files
        # Check that destination path doesn't exist or is a directory
        assert not dest_path.exists() or dest_path.is_dir()
        # Check that file with identical name doesn't already exist in dest_path
        assert not (dest_path / file.name).exists()
        dest_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def mv(cls, file, dest_path):
        cls._prepare_destination(file, dest_path)
        shutil.move(str(file), str(dest_path))

    @classmethod
    def cp(cls, file, dest_path):
        cls._prepare_destination(file, dest_path)
        shutil.copy2(str(file), str(dest_path))
