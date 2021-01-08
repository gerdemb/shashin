from pathlib import Path
import json

def get_cached_metadata(et, row):
    file = Path(row['file_name'])
    stat = file.stat()
    mtime = stat.st_mtime
    size = stat.st_size

    if row['mtime'] == mtime and row['size'] == size:
        return json.loads(row['metadata'])
    else:
        return et.get_metadata(file)
