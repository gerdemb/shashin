from pathlib import Path


class ImageResource(object):

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)
        self.src_path = Path(__file__).parent / self.name

    def get_file_name(self, library_path):
        return library_path / self.relative_library_path / self.name

    def get_db_row(self, library_path):
        return {
            'file_name': str(self.get_file_name(library_path)),
            'md5': self.md5,
            'dhash': self.dhash,
            'size': self.size,
        }


IMG_0 = ImageResource(
    name='img_0.jpg',
    relative_library_path='2018/10/21',
    md5=b'\xfddK\x11\xe3\\\xdd=9V#!/\x1aF\x81',
    dhash=b'\xff\xff\xff\xff\xffyy\x17\xff\x00\x00\x00\x0c\x00\x00\x04',
    size=36587,
)

IMG_0_COPY = ImageResource(
    name='img_0_copy.jpg',
    relative_library_path='2018/10/21',
    md5=b'\xfddK\x11\xe3\\\xdd=9V#!/\x1aF\x81',
    dhash=b'\xff\xff\xff\xff\xffyy\x17\xff\x00\x00\x00\x0c\x00\x00\x04',
    size=36587,
)
