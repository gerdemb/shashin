import shutil

from ._file import FileCommand


class MoveCommand(FileCommand):
    action_name = 'mv'

    @staticmethod
    def action(src, dest):
        assert not dest.exists() # Sanity check
        shutil.move(src, dest)
