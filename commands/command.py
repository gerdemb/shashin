from pathlib import Path

from exceptions import UserError


class Command(object):
    def __init__(self, config):
        library_root = Path(config.library)
        if not library_root.exists():
            raise UserError("Library path {} does not exist".format(library_root))