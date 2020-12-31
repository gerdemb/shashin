from datetime import datetime

from exiftool import ExifTool

class ExifError(Exception):
    pass

class Exif(ExifTool):
    @staticmethod
    def _remove_groups(json):
        for d in json:
            for k in list(d.keys()):
                d[k.split(':')[-1]] = d.pop(k)

    def execute_json(self, *params):
        json = super().execute_json(*params)
        self._remove_groups(json)
        return json

    def get_metadata(self, filename):
        metadata = super().get_metadata(filename)
        if 'Error' in metadata:
            raise ExifError(metadata['Error'])
        return metadata
