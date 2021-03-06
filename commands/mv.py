from ._file import FileCommand
from file_utils import mv, nop

class MoveCommand(FileCommand):
    def __init__(self, config):
        self.dry_run = config.dry_run
        if self.dry_run:
            action = nop
        else:
            action = mv
        super().__init__(config, action)
