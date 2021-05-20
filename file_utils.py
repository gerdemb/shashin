import shlex
from pathlib import Path

def path_file_walk(path):
    if path.is_file():
        yield path
    else:
        for child in sorted(path.iterdir()):
            if child.is_file():
                yield child
            elif child.is_dir():
                # TODO make configurable
                if child.name != '@eaDir':
                    yield from path_file_walk(child)


def is_child(parent, child):
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def print_action(action, *args):
    action_ljust = action.ljust(8)
    print(f"[{action_ljust}] " + " ".join([str(a) for a in args]))


def quote_path(path: Path) -> str:
    return shlex.quote(str(path))