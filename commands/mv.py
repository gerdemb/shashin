from ._file import FileCommand
from file_utils import mv

class MoveCommand(FileCommand):
    def __init__(self, config):
        super().__init__(config, mv)
