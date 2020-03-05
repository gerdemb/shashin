from datetime import datetime
from pathlib import Path
from unittest import TestCase

import jinja2

from library import Library


class TestLibrary(TestCase):

    def setUp(self):
        self.metadata = {'FileModifyDate': datetime(2020, 3, 2, 0, 0, 38),
                         'DateTimeOriginal': datetime(2018, 10, 21, 16, 58, 28),
                         'SourceFile': '/0.jpg'}

    def test_get_path_heirarchy_default(self):
        hierarchy = r'''
{% if DateTimeOriginal %}
    {{ DateTimeOriginal.strftime('%Y/%m/%d') }}
{% else %}
    {{ FileModifyDate.strftime('%Y/%m/%d') }}
{% endif %}
'''

        path = Library(None, hierarchy)._get_path_heirarchy(self.metadata)
        self.assertEqual(path, Path('2018/10/21'))

    def test_get_path_heirarchy_modify_date(self):
        hierarchy = r'''
    {{ FileModifyDate.strftime('%Y/%m/%d') }}
'''

        path = Library(None, hierarchy)._get_path_heirarchy(self.metadata)
        self.assertEqual(path, Path('2020/03/02'))

    def test_get_path_heirarchy_missing_data(self):
        del self.metadata['DateTimeOriginal']
        hierarchy = r'''
    {{ DateTimeOriginal.strftime('%Y/%m/%d') }}
'''

        with self.assertRaises(jinja2.exceptions.UndefinedError):
            Library(None, hierarchy)._get_path_heirarchy(self.metadata)

    def test_get_path_heirarchy_only_modify_date(self):
        del self.metadata['DateTimeOriginal']
        hierarchy = r'''
        {% if DateTimeOriginal %}
            {{ DateTimeOriginal.strftime('%Y/%m/%d') }}
        {% else %}
            {{ FileModifyDate.strftime('%Y/%m/%d') }}
        {% endif %}
        '''

        path = Library(None, hierarchy)._get_path_heirarchy(self.metadata)
        self.assertEqual(path, Path('2020/03/02'))
