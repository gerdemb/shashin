from pathlib import Path
from db import DB
from wand.image import Image
from wand.exceptions import DelegateError
import tempfile

def calculate_proportional_size(original, resize):
    ratio = min(resize[0] / original[0], resize[1] / original[1])
    return (int(original[0] * ratio), int(original[1] * ratio))

def execute(config):
    library_path = Path(config.library)
    export_path = Path(config.export_path)
    with DB(config.database) as db:
        for row in db.image_select_random(100):
            file = library_path / row['file_name']
            try:
                with Image(filename=str(file)) as original:
                    with original.convert('jpeg') as converted:
                        converted.thumbnail(
                            *calculate_proportional_size((original.size), 
                            (1024, 1024)))
                        converted.save(filename=tempfile.mktemp(
                            dir=str(export_path),
                            prefix="thumb_",
                            suffix=".jpg"))
            except DelegateError:
                # Error reading file
                continue