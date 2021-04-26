# Sizes SM, M, XL
def get_thumbnail(file, size='SM'):
    return file.parent / "@eaDir" / file.name / f"SYNOPHOTO_THUMB_{size}.jpg"
