
from commands import mv


class OrganizeCommand(mv.MoveCommand):
    def __init__(self, config):
        config.dest = config.src
        super().__init__(config)

