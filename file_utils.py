import shlex
from pathlib import Path

def path_file_walk(path):
    from shashin import SKIP_DIRS
    if path.is_file():
        yield path
    else:
        for child in sorted(path.iterdir()):
            if child.is_file():
                yield child
            elif child.is_dir():
                if child.name not in SKIP_DIRS:
                    yield from path_file_walk(child)


def is_child(parent, child):
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def quote_path(path: Path) -> str:
    return shlex.quote(str(path))


def normalized_path(path: str) -> Path:
    return Path(path).expanduser().resolve()