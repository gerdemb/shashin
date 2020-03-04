import hashlib
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path

import dhash
from send2trash import send2trash
from wand.exceptions import MissingDelegateError, DelegateError
from wand.image import Image

from exceptions import UnknownFileType, ExifToolError


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


def _get_date_path(date_string):
    m = re.match(r'''(?P<Y>\d\d\d\d):(?P<m>\d\d):(?P<d>\d\d)''', date_string)
    if m and m.group('Y') != '0000' and m.group('m') != '00' and m.group('d') != '00':
        return Path(*m.groups())
    else:
        return None


def get_date_path(metadata):
    if 'ExifTool:Error' in metadata:
        raise ExifToolError(metadata['ExifTool:Error'])
    file_type = metadata['File:FileType']

    if file_type in ['JPEG', 'HEIC', 'MOV', 'TIFF']:
        tag = 'EXIF:DateTimeOriginal'
    elif file_type in ['AVI']:
        tag = 'RIFF:DateTimeOriginal'
    elif file_type in ['MP4', '3GP', 'M4V']:
        tag = 'QuickTime:MediaCreateDate'
    elif file_type in ['PNG', 'MPEG', 'GIF', 'BMP', 'DV']:
        tag = 'File:FileModifyDate'
    else:
        raise UnknownFileType(file_type)

    date_path = None
    if tag in metadata:
        date_path = _get_date_path(metadata[tag])
    if date_path is None:
        date_path = _get_date_path(metadata['File:FileModifyDate'])
    return date_path


def import_image(et, file, library_path, action):
    # 1. Calculate destination path
    metadata = et.get_metadata(str(file))
    dest_path = library_path / get_date_path(metadata)

    if is_child(dest_path, file):
        # File is already in correct location. Should only happen when importing
        # from inside the library
        return file
    if (dest_path / file.name).exists():
        # Different file, but with same name already exists
        dest_path = Path(tempfile.mkdtemp(prefix=file.name + '.', dir=str(dest_path)))
    # 2. Move file
    action(file, dest_path)
    return (dest_path / file.name)


def prepare_destination(file, dest_path):
    # These assertions should never happen, but are included to prevent unintended data loss by accidentally overwriting
    # files
    # Check that destination path doesn't exist or is a directory
    assert not dest_path.exists() or dest_path.is_dir()
    # Check that file with identical name doesn't already exist in dest_path
    assert not (dest_path / file.name).exists()
    dest_path.mkdir(parents=True, exist_ok=True)


def mv(file, dest_path):
    prepare_destination(file, dest_path)
    shutil.move(str(file), str(dest_path))


def cp(file, dest_path):
    prepare_destination(file, dest_path)
    shutil.copy2(str(file), str(dest_path))


def is_empty_dir(path):
    return path.is_dir() and not any(path.iterdir())


def delete_image(db, file_name):
    db.image_delete(str(file_name))
    send2trash(str(file_name))
    if is_empty_dir(file_name.parent):
        file_name.parent.rmdir()
