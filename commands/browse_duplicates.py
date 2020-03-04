from collections import defaultdict
from itertools import groupby
from math import floor, log10
from pathlib import Path

from exiftool import ExifTool
from flask import request, Flask, render_template, send_file
from werkzeug.exceptions import abort
from werkzeug.routing import PathConverter

from db import DB
from utils import delete_image, is_child


class BrowseDuplicatesCommand(object):

    def __init__(self, config):
        self.library_path = Path(config.library)
        self.database_path = config.database
        # TODO make these configurable
        self.FIRST_KEYS = [
            'SourceFile',
            'File:FileName',
            'Composite:ImageSize',
            'File:FileSize',
            'File:FileModifyDate',
            'EXIF:DateTimeOriginal',
        ]
        self.IGNORE_KEYS = [
            'File:Directory',
            'Shashin:RelativePath',
        ]

    @staticmethod
    def estimate_percentage(hash):
        # Maximum hash value as an long
        return (100 * int.from_bytes(bytes.fromhex(hash), "big")) / 340282366920938463463374607431768211455

    @staticmethod
    def round_to_1(x):
        return round(x, -int(floor(log10(abs(x)))))

    @staticmethod
    def get_diff_keys(dicts):
        # Collect all key values
        key_vals = defaultdict(list)
        for d in dicts:
            for key, val in d.items():
                key_vals[key].append(val)

        # Find all keys with equal values
        diff_keys = []
        for key, vals in key_vals.items():
            if len(vals) != len(dicts) or not all(v == vals[0] for v in vals):
                diff_keys.append(key)
        return diff_keys

    @staticmethod
    def order_keys(diff_keys, first_keys, ignore_keys):
        order_keys = list(first_keys)
        order_keys.extend(sorted(filter(
            lambda k: k not in first_keys and k not in ignore_keys,
            diff_keys)))
        return order_keys

    def execute(self):
        app = Flask(__name__, )
        app.url_map.converters['everything'] = EverythingConverter

        @app.route('/')
        def index():
            def sort_key(r):
                Megapixels = r['Composite:Megapixels']
                FileSize = r['File:FileSize']
                FileName = r['File:FileName']
                DateTimeOriginal = r.get('DateTimeOriginal', None)
                FileModifyDate = r['File:FileModifyDate']

                return (
                    -Megapixels,
                    -self.round_to_1(FileSize),
                    DateTimeOriginal,
                    FileModifyDate,
                    len(FileName),
                    -FileSize
                )

            def get_metadata(r):
                metadata = et.get_metadata(r['file_name'])
                metadata['Shashin:RelativePath'] = str(Path(r['file_name']).relative_to(self.library_path))
                return metadata

            with DB(self.database_path) as db:
                with ExifTool() as et:
                    start = bytes.fromhex(request.args.get('start', ''))
                    # with DB(config.database) as db:
                    duplicates = {}
                    keys = {}
                    rows = db.image_select_duplicate_dhash(start)
                    for dhash, rows in groupby(rows, lambda x: x['dhash']):
                        duplicate_group = sorted(
                            map(get_metadata, rows),
                            key=sort_key
                        )
                        duplicates[dhash.hex()] = duplicate_group
                        diff_keys = self.get_diff_keys(duplicate_group)
                        keys[dhash.hex()] = self.order_keys(
                            diff_keys, self.FIRST_KEYS, self.IGNORE_KEYS)
                    percentage = None
                    if duplicates:
                        percentage = self.estimate_percentage(tuple(duplicates.keys())[-1])
                    return render_template('index.html',
                                           duplicates=duplicates,
                                           keys=keys,
                                           percentage=percentage)

        @app.route('/image/<everything:file_name>', methods=['GET', 'DELETE'])
        def serve_pictures(file_name):
            with DB(self.database_path) as db:
                file = self.library_path / file_name

                if not db.image_select_by_file_name(str(file)):
                    abort(404)
                if request.method == 'GET':
                    return send_file(str(file))
                elif request.method == 'DELETE':
                    delete_image(db, file)
                    return 'True'


        app.run(host='0.0.0.0', port=8000)


class EverythingConverter(PathConverter):
    regex = '.*?'
