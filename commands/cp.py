import shutil

from exceptions import UserError
from file_utils import is_child

from ._file import FileCommand


class CopyCommand(FileCommand):
    action_name = 'cp'

    def __init__(self, config):
        super().__init__(config)
        
        if is_child(self.src, self.dest):
            raise UserError(f"Destination {self.dest} is inside source {self.src}")

    @staticmethod
    def action(src, dest):
        assert not dest.exists() # Sanity check
        shutil.copy2(src, dest)
