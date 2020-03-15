from datetime import datetime

from exiftool import ExifTool

class ExifError(Exception):
    pass

class Exif(ExifTool):
    DATE_TIME_TAGS = ('DateTimeOriginal', 'FileModifyDate')
    DATE_TIME_FMT = '%Y:%m:%d %H:%M:%S'

    @classmethod
    def _annotate_date_time_tags(cls, json):
        for d in json:
            for tag in cls.DATE_TIME_TAGS:
                if tag in d:
                    try:
                        d[tag] = datetime.strptime(d[tag][:19], cls.DATE_TIME_FMT)
                    except ValueError:
                        # Leave unchanged strings that cannot be converted to datetime
                        pass

    @staticmethod
    def _remove_groups(json):
        for d in json:
            for k in list(d.keys()):
                d[k.split(':')[-1]] = d.pop(k)

    def execute_json(self, *params):
        json = super().execute_json(*params)
        self._remove_groups(json)
        if 'Error' in json:
            raise ExifError(json['Error'])
        self._annotate_date_time_tags(json)
        return json
