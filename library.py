import shutil
import tempfile
from pathlib import Path

from jinja2 import Template

from utils import is_child


class Library(object):

    def __init__(self, library_path, hierarchy):
        self.library_path = library_path
        self.template = Template(hierarchy)

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
