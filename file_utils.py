import shutil
from pathlib import Path
import tempfile


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


def prepare_destination(file, dest_path):
    # File is already at dest_path
    if file.parent == dest_path:
        return

    # This assertion should never happen, but is included to prevent unintended data loss by accidentally
    # overwriting files
    # Check that destination path is a directory or doesn't exist
    assert dest_path.is_dir() or not dest_path.exists()

    # Check that file with identical name doesn't already exist in dest_path
    if (dest_path / file.name).exists():
        # If destination exists and file is not already a parent of the destination
        if not is_child(dest_path, file.parent):
            # Create a new directory under the destination
            return Path(tempfile.mkdtemp(prefix=file.name + '.', dir=dest_path))
    else:
        dest_path.mkdir(parents=True, exist_ok=True)
        return dest_path


def mv(file, dest_path):
    dest_path = prepare_destination(file, dest_path)
    if dest_path:
        return shutil.move(str(file), str(dest_path))


def cp(file, dest_path):
    dest_path = prepare_destination(file, dest_path)
    if dest_path:
        return  shutil.copy2(file, dest_path)

def is_child(parent, child):
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False