import json
import tempfile
from collections import OrderedDict, defaultdict
from itertools import groupby
from math import floor, log10
from pathlib import Path

from db import DB
from exif import Exif
from flask import Flask, render_template, request, send_file
from utils import delete_image
from wand.image import Image
from werkzeug.exceptions import abort
from werkzeug.routing import PathConverter


class BrowseDuplicatesCommand(object):

    def __init__(self, config):
        self.library_path = Path(config.library)
        self.database_path = config.database
        self.features_path = config.features_path

        # TODO make these configurable
        self.FIRST_KEYS = [
            'SourceFile',
            'FileName',
            'ImageSize',
            'FileSize',
            'FileModifyDate',
            'DateTimeOriginal',
        ]
        self.IGNORE_KEYS = [
            'Directory',
        ]

    @staticmethod
    def estimate_percentage(hash):
        # Maximum hash value as a long
        return (100 * int.from_bytes(bytes.fromhex(hash), "big")) / 340282366920938463463374607431768211455

    @staticmethod
    def round_to_1(x):
        return round(x, -int(floor(log10(abs(x)))))

    @staticmethod
    def get_diff_tags(dicts):
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
    def order_tags(diff_keys, first_keys, ignore_keys):
        order_keys = list(first_keys)
        order_keys.extend(sorted(filter(
            lambda k: k not in first_keys and k not in ignore_keys,
            diff_keys)))
        return order_keys

    def log_metadata(self, row):
        log = tempfile.NamedTemporaryFile(
            dir = self.features_path,
            delete=False, 
            suffix='.json'
        )
        dhash = row['dhash'].hex()
        metadata = json.loads(row['metadata'])
        data = {
            dhash: metadata 
        }
        log.write(json.dumps(data))
        log.close()
        
    def execute(self):
        app = Flask(__name__, )
        app.url_map.converters['everything'] = EverythingConverter

        @app.route('/')
        def index():
            def sort_key(t):
                _, r = t
                Megapixels = r['Megapixels']
                FileSize = r['FileSize']
                FileStem = Path(r['FileName']).stem
                FileSuffix = Path(r['FileName']).suffix
                DateTimeOriginal = r.get('DateTimeOriginal', None)
                FileModifyDate = r['FileModifyDate']

                return (
                    -Megapixels,
                    len(FileStem),
                    FileSuffix,
                    DateTimeOriginal,
                    FileModifyDate,
                    -FileSize
                )

            def get_metadata(r):
                metadata = et.get_metadata(r['file_name'])
                return str(Path(r['file_name']).relative_to(self.library_path)), metadata

            with DB(self.database_path) as db:
                with Exif() as et:
                    start = bytes.fromhex(request.args.get('start', ''))
                    duplicates = {}
                    tags = {}
                    rows = db.image_select_duplicate_dhash(start)
                    for dhash, rows in groupby(rows, lambda x: x['dhash']):
                        duplicate_group = OrderedDict(sorted(
                            map(get_metadata, rows),
                            key=sort_key
                        ))
                        duplicates[dhash.hex()] = duplicate_group
                        diff_tags = self.get_diff_tags(duplicate_group.values())
                        tags[dhash.hex()] = self.order_tags(
                            diff_tags, self.FIRST_KEYS, self.IGNORE_KEYS)
                    percentage = None
                    if duplicates:
                        percentage = self.estimate_percentage(tuple(duplicates.keys())[-1])
                    return render_template('index.html',
                                           duplicates=duplicates,
                                           tags=tags,
                                           percentage=percentage)

        @app.route('/image/<everything:file_name>', methods=['GET', 'DELETE'])
        def serve_pictures(file_name):
            with DB(self.database_path) as db:
                file = self.library_path / file_name
                row = db.image_select_by_file_name(str(file))
                if not row:
                    abort(404)
                if request.method == 'GET':
                    if file.suffix == '.HEIC':
                        with Image(filename=str(file)) as img:
                            with tempfile.NamedTemporaryFile(prefix=file.name, suffix='.JPG', delete=True) as fp:
                                img.format = 'jpeg'
                                img.save(filename=fp.name)
                                return send_file(fp.name)
                    else:
                        return send_file(str(file))
                elif request.method == 'DELETE':
                    self.log_metadata(db, row)
                    delete_image(db, file)
                    return 'True'

        app.run(host='0.0.0.0', port=8000)


class EverythingConverter(PathConverter):
    regex = '.*?'
