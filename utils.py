import hashlib
import sqlite3

import dhash
from send2trash import send2trash
from wand.exceptions import MissingDelegateError, DelegateError
from wand.image import Image


def path_file_walk(path):
    if path.is_file():
        yield path
    else:
        for child in sorted(path.iterdir()):
            if child.is_file():
                yield child
            elif child.is_dir():
                if child.name != '@eaDir':
                    yield from path_file_walk(child)


def path_dir_walk(path):
    for child in sorted(path.iterdir()):
        if child.is_dir():
            yield from path_dir_walk(child)
            yield child


def calculate_dhash(file):
    try:
        with Image(filename=str(file)) as image:
            return sqlite3.Binary(dhash.format_bytes(*dhash.dhash_row_col(image)))
    except (MissingDelegateError, DelegateError):
        return None


def get_mtime_and_size(file):
    stat = file.stat()
    return stat.st_mtime, stat.st_size


def get_file_stats(file):
    mtime, size = get_mtime_and_size(file)
    md5 = sqlite3.Binary(hashlib.md5(file.read_bytes()).digest())
    dhash = calculate_dhash(file)
    return {'mtime': mtime,
            'size': size,
            'md5': md5,
            'dhash': dhash}


def is_child(parent, child):
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def is_empty_dir(path):
    return path.is_dir() and not any(path.iterdir())


def delete_image(db, file_name):
    db.image_delete(str(file_name))
    send2trash(str(file_name))
    if is_empty_dir(file_name.parent):
        file_name.parent.rmdir()
