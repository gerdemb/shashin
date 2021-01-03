from exiftool import ExifTool, fsencode


class ExifError(Exception):
    pass

class Exif(ExifTool):
    @staticmethod
    def _remove_groups(json):
        for d in json:
            for k in list(d.keys()):
                d[k.split(':')[-1]] = d.pop(k)

    def execute_raw(self, *params):
        params = map(fsencode, params)
        return super().execute(*params).decode("utf-8")

    def execute_json(self, *params):
        json = super().execute_json(*params)
        self._remove_groups(json)
        return json

    def get_metadata(self, filename):
        metadata = super().get_metadata(filename)
        if 'Error' in metadata:
            raise ExifError(metadata['Error'])
        return metadata
