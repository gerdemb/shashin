import json
import tempfile
from collections import OrderedDict, defaultdict
from functools import cmp_to_key
from itertools import groupby
from math import floor, log10
from pathlib import Path

from db import DB
from exif import Exif
from flask import Flask, render_template, request, send_file
from predictor import build_predictor
from wand.image import Image
from werkzeug.exceptions import abort
from werkzeug.routing import PathConverter
from send2trash import send2trash

# TODO make these configurable
FIRST_KEYS = [
    'SourceFile',
    'FileName',
    'ImageSize',
    'FileSize',
    'FileModifyDate',
    'DateTimeOriginal',
]
IGNORE_KEYS = [
    'Directory',
]


def ordered_tags(metadata):
    # Get set of all keys from all rows
    keys = set([
        key
        for m in metadata
        for key in m.keys()
    ])
    # Find keys that are either missing in some rows or have different values between rows
    diff_keys = [
        k
        for k in keys
        if any([
            not k in m
            for m in metadata
        ]) or not all(
            metadata[0][k] == m[k]
            for m in metadata
        )
    ]
    ordered_keys = list(FIRST_KEYS) + [
        k
        for k in diff_keys
        if k not in FIRST_KEYS
        if k not in IGNORE_KEYS
    ]
    return ordered_keys


class BrowseCommand(object):

    def __init__(self, config):
        self.cache_dir = config.cache_dir

    @staticmethod
    def estimate_percentage(hash):
        # Maximum hash value as a long
        return (100 * int.from_bytes(bytes.fromhex(hash), "big")) / 340282366920938463463374607431768211455

    @staticmethod
    def round_to_1(x):
        return round(x, -int(floor(log10(abs(x)))))

    def log_metadata(self, row):
        data = (
            row['dhash'].hex(),
            json.loads(row['metadata'])
        )
        data_json = json.dumps(data)
        with tempfile.NamedTemporaryFile(
            dir=self.cache_dir,
            mode='w',
            delete=False,
            prefix='img',
            suffix='.json'
        ) as log:
            log.write(data_json)

    def execute(self):
        app = Flask(__name__, )
        app.url_map.converters['everything'] = EverythingConverter

        with DB(self.cache_dir) as db:
            predictor = build_predictor(db, self.cache_dir)

        @app.route('/')
        def index():
            with DB(self.cache_dir) as db:
                with Exif() as et:
                    start = bytes.fromhex(request.args.get('start', ''))
                    rows = db.image_select_duplicate_dhash(start).fetchall()

                    duplicates = []
                    for dhash, group in groupby(rows, lambda x: x['dhash']):
                        metadata = [
                            json.loads(row['metadata'])
                            for row in group
                        ]
                        duplicates.append(
                            {
                                'images': sorted(metadata, key=cmp_to_key(predictor)),
                                'tags': ordered_tags(metadata)
                            }
                        )

                    percentage = None
                    last_dhash = None
                    if rows:
                        # Maximum hash value as a long
                        last_dhash = rows[-1]['dhash']
                        percentage = (100 * int.from_bytes(last_dhash, "big")) / 340282366920938463463374607431768211455

                    return render_template(
                        'index.html',
                        duplicates=duplicates,
                        percentage=percentage,
                        last_dhash = last_dhash.hex()
                    )

        @app.route('/image/<everything:file_name>', methods=['GET', 'DELETE', 'POST'])
        def serve_pictures(file_name):
            with DB(self.cache_dir) as db:
                file = Path('/') / Path(file_name)
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
                    self.log_metadata(row)
                    db.image_delete(str(file_name))
                    send2trash(str(file_name))
                    return 'True'
                elif request.method == 'POST':
                    db.ignore_insert_dhash(row['dhash'])
                    return 'True'

        app.run(host='0.0.0.0', port=8000)


class EverythingConverter(PathConverter):
    regex = '.*?'
