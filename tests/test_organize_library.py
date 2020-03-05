import unittest

from pathlib import Path

from commands.organize_library import OrganizeLibraryCommand
from tests.resources.resources import IMG_0
from tests.testcase import ShashinTestCase


class TestOrganizeLibrary(ShashinTestCase):

    def test_organize_in_place(self):
        # Arrange
        self._cp_to_import(IMG_0)
        self.config.library = self.config.import_path
        self.config.hierarchy = '.'
        self.config.import_action = 'mv'

        # Act
        OrganizeLibraryCommand(self.config).execute()

        # Assert
        self.assertPathExists(Path(self.config.library) / IMG_0.name)

