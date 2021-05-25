# Sizes SM, M, XL
from pathlib import Path


def get_thumbnail(file: Path, size='SM') -> Path:
    return file.parent / "@eaDir" / file.name / f"SYNOPHOTO_THUMB_{size}.jpg"
