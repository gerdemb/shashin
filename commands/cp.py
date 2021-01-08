from ._file import FileCommand
from exceptions import UserError
from file_utils import cp, is_child, nop

class CopyCommand(FileCommand):
    def __init__(self, config):
        self.dry_run = config.dry_run
        if self.dry_run:
            action = nop
        else:
            action = cp
        super().__init__(config, action)
        
        if is_child(self.src, self.dest):
            raise UserError(f"Destination {self.dest} is inside source {self.src}")