from ._file import FileCommand
from file_utils import mv, nop

class OrganizeCommand(FileCommand):
    def __init__(self, config):
        self.dry_run = config.dry_run
        if self.dry_run:
            action = nop
        else:
            action = mv
        config.dest = config.src
        super().__init__(config, action)

