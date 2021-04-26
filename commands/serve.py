from db_utils import get_cached_metadata
import json
import tempfile
from functools import cmp_to_key
from itertools import groupby
from pathlib import Path

from db import DB
from exif import Exif
from flask import Flask, render_template, request, send_file
from learn.predictor import build_predictor
from wand.image import Image
from werkzeug.exceptions import abort
from werkzeug.routing import PathConverter
from send2trash import send2trash

from synology import get_thumbnail
from collections import defaultdict
from urllib.parse import quote
import re

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

def get_duplicates(et, rows, predictor):
    duplicates = []
    for dhash, group in groupby(rows, lambda x: x['dhash']):
        metadata = [
            get_cached_metadata(et, row)
            for row in group
            if Path(row['file_name']).exists()
        ]
        if len(metadata) > 1:
            duplicates.append(
                {
                    'images': sorted(metadata, key=cmp_to_key(predictor)),
                    'tags': ordered_tags(metadata)
                }
            )
    return duplicates


def get_alerts(duplicates):
    # alert[source_file] = ['<p>alert1</p>', '<p>alert2</p>']
    alerts = defaultdict(list)

    for group in duplicates:
        source_files = [Path(image['SourceFile']) for image in group['images']]
    
        # Live Photos
        for source_file in source_files:
            # Search for files with the same stem that are not in the duplicates group
            for live_photo in [str(f) for f in source_file.parent.glob(f'{source_file.stem}.*') if f not in source_files]:
                live_photo_url = quote(live_photo)
                alerts[str(source_file)].append(f'Possible live photo <a href="/image/{live_photo_url}" class="alert-link">{live_photo}</a>')

        # Mismatched numbers
        # Finds first group of numbers in the filename
        digits = [re.findall("\d+", source_file.name)[0] for source_file in source_files]
        if not all(d==digits[0] for d in digits):
            for source_file in source_files: 
                alerts[str(source_file)].append(f'Possible false duplicates')

    return alerts


class ServeCommand(object):

    def __init__(self, config):
        self.cache_dir = config.cache_dir

    def execute(self):
        app = Flask(__name__, )
        app.url_map.converters['everything'] = EverythingConverter
        app.config['TESTING'] = True

        with DB(self.cache_dir) as db:
            predictor = build_predictor(db, self.cache_dir)

        @app.route('/')
        def index():
            with DB(self.cache_dir) as db:
                with Exif() as et:
                    start = bytes.fromhex(request.args.get('start', ''))
                    rows = db.image_select_duplicate_dhash(start).fetchall()

                    duplicates = get_duplicates(et, rows, predictor)

                    if duplicates:
                        alerts = get_alerts(duplicates)

                        last_dhash = rows[-1]['dhash']
                        # Maximum hash value as a long
                        percentage = (100 * int.from_bytes(last_dhash, "big")) / 340282366920938463463374607431768211455
                        return render_template(
                            'index.html',
                            duplicates=duplicates,
                            alerts=alerts,
                            percentage=percentage,
                            last_dhash = last_dhash.hex()
                        )
                    else:
                        return render_template('empty.html')

        @app.route('/image/<everything:file_name>', methods=['GET', 'DELETE', 'POST'])
        def serve_pictures(file_name):
            with DB(self.cache_dir) as db:
                file = Path(file_name)
                row = db.image_select_by_file_name(file)
                if not row:
                    abort(404)
                if request.method == 'GET':
                    return self.send_image(file)
                elif request.method == 'DELETE':
                    return self.delete_image(db, row, self.cache_dir)
                elif request.method == 'POST':
                    return self.ignore_image(db, row)
                    
        app.run(host='0.0.0.0', port=8000)

    @staticmethod
    def send_image(file):
        thumbnail = get_thumbnail(file, size="XL")
        if thumbnail.exists():
            return send_file(str(thumbnail))
        elif file.suffix == '.HEIC':
            with Image(filename=str(file)) as img:
                with tempfile.NamedTemporaryFile(prefix=file.name, suffix='.JPG', delete=True) as fp:
                    img.format = 'jpeg'
                    img.save(filename=fp.name)
                    return send_file(fp.name)
        else:
            return send_file(str(file))

    @staticmethod
    def delete_image(db, row, cache_dir):
        file_name = row['file_name']

        # Log metadata
        data = (
            row['dhash'].hex(),
            json.loads(row['metadata'])
        )
        data_json = json.dumps(data)
        with tempfile.NamedTemporaryFile(
            dir=cache_dir,
            mode='w',
            delete=False,
            prefix='img',
            suffix='.json'
        ) as log:
            log.write(data_json)

        db.image_delete(file_name)
        send2trash(str(file_name))
        return 'True'

    @staticmethod
    def ignore_image(db, row):
        db.ignore_insert_dhash(row['dhash'])
        return 'True'

    



class EverythingConverter(PathConverter):
    regex = '.*?'
