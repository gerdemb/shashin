from exiftool import ExifTool, fsencode


class ExifError(Exception):
    pass

class UnsupportedMIMETypeException(Exception):
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

    def get_image_medata(self, file):
        metadata = self.get_metadata(file)

        mime_type = metadata['MIMEType']
        if not (mime_type.startswith('image/') or mime_type.startswith('video/')):
            raise UnsupportedMIMETypeException(mime_type)
        return metadata
