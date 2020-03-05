from datetime import datetime

from exiftool import ExifTool


class Exif(ExifTool):
    DATE_TIME_TAGS = ('DateTimeOriginal', 'FileModifyDate')
    DATE_TIME_FMT = '%Y:%m:%d %H:%M:%S'

    @classmethod
    def _annotate_date_time_tags(cls, json):
        for d in json:
            for tag in cls.DATE_TIME_TAGS:
                if tag in d:
                    # TODO ignoring the +00:00 timezone information. Is that OK?
                    d[tag] = datetime.strptime(d[tag][:19], cls.DATE_TIME_FMT)

    @staticmethod
    def _remove_groups(json):
        for d in json:
            for k in list(d.keys()):
                d[k.split(':')[-1]] = d.pop(k)

    def execute_json(self, *params):
        json = super().execute_json(*params)
        self._remove_groups(json)
        self._annotate_date_time_tags(json)
        return json
