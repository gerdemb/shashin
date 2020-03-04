from exiftool import ExifTool

class Exif(ExifTool):

    def get_metadata(self, filename):
        metadata = super().get_metadata(filename)
        metadata.update({

        })
        return metadata