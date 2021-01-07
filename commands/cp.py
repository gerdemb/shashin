from ._file import FileCommand
from exceptions import UserError
from file_utils import cp, is_child

class CopyCommand(FileCommand):
    def __init__(self, config):
        super().__init__(config, cp)
        if is_child(self.src, self.dest):
            raise UserError(f"Destination {self.dest} is inside source {self.src}")