import shutil
import sqlite3
import tempfile
import unittest
import warnings
from argparse import Namespace
from pathlib import Path


class ShashinTestCase(unittest.TestCase):
    def setUp(self):
        # Disable warning when these temporary files are automatically cleaned
        warnings.simplefilter("ignore", ResourceWarning)
        self.temp_library = tempfile.TemporaryDirectory()
        self.temp_import = tempfile.TemporaryDirectory()
        self.library_path = Path(self.temp_library.name)
        self.import_path = Path(self.temp_import.name)

        self.temp_database = tempfile.NamedTemporaryFile()
        self.db_connection = sqlite3.connect(self.temp_database.name)
        self.db_cursor = self.db_connection.cursor()
        self.db_cursor.row_factory = sqlite3.Row

        self.config = Namespace(
            database=self.temp_database.name,
            library=self.temp_library.name,
            import_path=self.temp_import.name,
            import_action='cp',
            import_duplicates=False,
            delete_duplicates=False,
        )

    def _cp_resource(self, resource):
        src = str(Path(__file__).parent / "resources" / resource.name)
        shutil.copy2(src, self.temp_import.name)

    def _select_db_row(self, file_name):
        return self.db_cursor.execute(r'''
            SELECT * FROM images WHERE file_name = ?
        ''', (file_name,)).fetchone()

    def _get_resource_row(self, resource):
        return self._select_db_row(str(resource.get_file_name(self.library_path)))

    def assertPathExists(self, path):
        self.assertTrue(Path(path).exists())

    def assertPathNotExists(self, path):
        self.assertFalse(Path(path).exists())

    def assertResourceMatchesDatabase(self, resource):
        db_row = dict(self._get_resource_row(resource))
        resource_row = resource.get_db_row(self.library_path)

        # Sometimes mtime float values don't exactly match. Round to int.
        db_row['mtime'] = int(db_row['mtime'])
        resource_row['mtime'] = int(resource_row['mtime'])
        self.assertEqual(db_row, resource_row)

    def assertResourceNotInDatabase(self, resource):
        self.assertIsNone(self._get_resource_row(resource))

    def assertResourceInLibrary(self, resource):
        self.assertPathExists(resource.get_file_name(self.library_path))

    def assertResourceNotInLibrary(self, resource):
        self.assertPathNotExists(resource.get_file_name(self.library_path))

    def assertResourceInImportPath(self, resource):
        self.assertPathExists(Path(self.temp_import.name) / resource.name)

    def assertResourceNotInImportPath(self, resource):
        self.assertPathNotExists(Path(self.temp_import.name) / resource.name)