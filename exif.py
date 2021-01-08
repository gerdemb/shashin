from exiftool import ExifTool, fsencode


class ExifError(Exception):
    pass

class Exif(ExifTool):
    def execute_raw(self, *params):
        params = map(fsencode, params)
        return super().execute(*params).decode("utf-8")

    def execute_json(self, *params):
        json = super().execute_json(*params)

        # Remove group names from keys
        for d in json:
            for k in list(d.keys()):
                d[k.split(':')[-1]] = d.pop(k)
        return json

    def get_metadata(self, filename):
        metadata = super().get_metadata(str(filename))
        if 'Error' in metadata:
            raise ExifError(metadata['Error'])
        return metadata
