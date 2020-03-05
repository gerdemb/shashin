import shutil

from commands._import import ImportCommand
from library import Library
from tests.resources.resources import IMG_0, IMG_0_COPY
from tests.testcase import ShashinTestCase


class TestImportCommand(ShashinTestCase):

    def test_init(self):
        # Test import_action
        command = ImportCommand(self.config)
        self.assertEqual(command.import_action, Library.cp)

        self.config.import_action = 'mv'
        command = ImportCommand(self.config)
        self.assertEqual(command.import_action, Library.mv)

        # Test duplicate action
        command = ImportCommand(self.config)
        self.assertEqual(command.duplicate_action, ImportCommand.DuplicateActions.SKIP)

        self.config.import_duplicates = True
        command = ImportCommand(self.config)
        self.assertEqual(command.duplicate_action, ImportCommand.DuplicateActions.IMPORT)

        self.config.import_duplicates = False
        self.config.delete_duplicates = True
        command = ImportCommand(self.config)
        self.assertEqual(command.duplicate_action, ImportCommand.DuplicateActions.RM)

    def test_execute_cp(self):
        # Arrange
        self._cp_to_import(IMG_0)

        # Act
        ImportCommand(self.config).execute()

        # Assert
        self.assertResourceInImportPath(IMG_0)
        self.assertResourceInLibrary(IMG_0)
        self.assertResourceMatchesDatabase(IMG_0)

    def test_execute_mv(self):
        # Arrange
        self._cp_to_import(IMG_0)
        self.config.import_action = 'mv'

        # Act
        ImportCommand(self.config).execute()

        # Assert
        self.assertResourceNotInImportPath(IMG_0)
        self.assertResourceInLibrary(IMG_0)
        self.assertResourceMatchesDatabase(IMG_0)

    def test_execute_duplicate_skip(self):
        # Arrange
        self._cp_to_import(IMG_0)
        self.config.import_action = 'mv'
        ImportCommand(self.config).execute()
        self._cp_to_import(IMG_0_COPY)

        # Act
        ImportCommand(self.config).execute()

        # Assert
        self.assertResourceInLibrary(IMG_0)
        self.assertResourceNotInLibrary(IMG_0_COPY)
        self.assertResourceNotInImportPath(IMG_0)
        self.assertResourceInImportPath(IMG_0_COPY)
        self.assertResourceMatchesDatabase(IMG_0)
        self.assertResourceNotInDatabase(IMG_0_COPY)

    def test_execute_duplicate_import(self):
        # Arrange
        self._cp_to_import(IMG_0)
        self.config.import_action = 'mv'
        self.config.import_duplicates = True
        ImportCommand(self.config).execute()
        self._cp_to_import(IMG_0_COPY)

        # Act
        ImportCommand(self.config).execute()

        # Assert
        self.assertResourceInLibrary(IMG_0)
        self.assertResourceInLibrary(IMG_0_COPY)
        self.assertResourceNotInImportPath(IMG_0)
        self.assertResourceNotInImportPath(IMG_0_COPY)
        self.assertResourceMatchesDatabase(IMG_0)
        self.assertResourceMatchesDatabase(IMG_0_COPY)

    def test_execute_duplicate_rm(self):
        # Arrange
        self._cp_to_import(IMG_0)
        self.config.import_action = 'mv'
        self.config.delete_duplicates = True
        ImportCommand(self.config).execute()
        self._cp_to_import(IMG_0_COPY)

        # Act
        ImportCommand(self.config).execute()

        # Assert
        self.assertResourceInLibrary(IMG_0)
        self.assertResourceNotInLibrary(IMG_0_COPY)
        self.assertResourceNotInImportPath(IMG_0)
        self.assertResourceNotInImportPath(IMG_0_COPY)
        self.assertResourceMatchesDatabase(IMG_0)
        self.assertResourceNotInDatabase(IMG_0_COPY)
