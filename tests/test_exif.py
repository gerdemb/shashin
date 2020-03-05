import unittest
from datetime import datetime

from exif import Exif


class TestExif(unittest.TestCase):

    def test_remove_groups(self):
        input = [{'File:FileModifyDate': '2020:03:02 00:00:38+00:00',
                  'SourceFile': '/0.jpg'},
                 {'File:FileModifyDate': '2020:03:02 00:00:38+00:00',
                  'SourceFile': '/1.jpg'}]
        output = input.copy()

        Exif._remove_groups(output)
        self.assertEqual(
            output,
            [{'FileModifyDate': '2020:03:02 00:00:38+00:00',
              'SourceFile': '/0.jpg'},
             {'FileModifyDate': '2020:03:02 00:00:38+00:00',
              'SourceFile': '/1.jpg'}]
        )

    def test_annotate_date_time_tags(self):
        input = [{'FileModifyDate': '2020:03:02 00:00:38+00:00',
                  'DateTimeOriginal': '2018:10:21 16:58:28',
                  'SourceFile': '/0.jpg'},
                 {'FileModifyDate': '2020:03:02 00:00:38+00:00',
                  'DateTimeOriginal': '2018:10:21 16:58:28',
                  'SourceFile': '/1.jpg'}]
        output = input.copy()

        Exif._annotate_date_time_tags(output)
        self.assertEqual(
            output,
            [{'FileModifyDate': datetime(2020, 3, 2, 0, 0, 38),
              'DateTimeOriginal': datetime(2018, 10, 21, 16, 58, 28),
              'SourceFile': '/0.jpg'},
             {'FileModifyDate': datetime(2020, 3, 2, 0, 0, 38),
              'DateTimeOriginal': datetime(2018, 10, 21, 16, 58, 28),
              'SourceFile': '/1.jpg'}]
        )
