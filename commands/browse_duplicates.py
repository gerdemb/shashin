from pathlib import Path
from db import DB
from flask import request, Flask, render_template, send_file, abort, g
from werkzeug.routing import PathConverter
from exiftool import ExifTool
from itertools import groupby
from datetime import datetime
from utils import delete_image
from math import floor, log10
from collections import defaultdict

FIRST_KEYS = [  
                'SourceFile',
                'File:FileName', 
                'Composite:ImageSize',
                'File:FileSize',
                'File:FileModifyDate', 
                'EXIF:DateTimeOriginal',
            ]
IGNORE_KEYS = [    ]

class EverythingConverter(PathConverter):
    regex = '.*?'

def round_to_1(x):
    return round(x, -int(floor(log10(abs(x)))))

def get_diff_keys(dicts):
    # Collect all key values
    key_vals = defaultdict(list)
    for d in dicts:
        for key, val in d.items():
            key_vals[key].append(val)

    # Find all keys with equal values
    diff_keys = []
    for key, vals in key_vals.items():
        if len(vals) != len(dicts) or not all(v==vals[0] for v in vals):
            diff_keys.append(key)
    return diff_keys

def order_keys(diff_keys, first_keys, ignore_keys):
    order_keys = list(first_keys)
    order_keys.extend(sorted(filter(
        lambda k: k not in first_keys and k not in ignore_keys, 
        diff_keys)))
    return order_keys

def serve(database_path, library_path):
    app = Flask(__name__, )
    app.url_map.converters['everything'] = EverythingConverter

    def estimate_percentage(hash):
        # Maximum hash value as an long
        return (100 * int.from_bytes(bytes.fromhex(hash), "big")) / 340282366920938463463374607431768211455

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
                        -round_to_1(FileSize),
                        DateTimeOriginal,
                        FileModifyDate,
                        len(FileName),
                        -FileSize
                    )

        def get_metadata(r):
            return et.get_metadata(str(library_path / r['file_name']))

        with DB(database_path) as db:
            with ExifTool('/var/services/homes/admin/bin/exiftool') as et:
                start = bytes.fromhex(request.args.get('start', ''))
                # with DB(config.database) as db:
                duplicates = {}
                keys = {}
                rows = db.image_select_duplicate_dhash(start)
                for dhash, rows in groupby(rows, lambda x: x['dhash']):
                    duplicate_group = sorted(
                        map(get_metadata,rows),
                        key = sort_key
                    )
                    duplicates[dhash.hex()] = duplicate_group
                    diff_keys = get_diff_keys(duplicate_group)
                    keys[dhash.hex()] = order_keys(diff_keys, FIRST_KEYS, IGNORE_KEYS)
                percentage = estimate_percentage(tuple(duplicates.keys())[-1])
                return render_template('index.html', 
                    duplicates=duplicates, 
                    keys=keys,
                    percentage=percentage)

    @app.route('/image/<everything:file_name>', methods=['GET', 'DELETE'])
    def serve_pictures(file_name):
        file = library_path / file_name
        # TODO add security check that we are only serving files inside the library directory
        if request.method == 'GET':
            return send_file(str(file))
        elif request.method == 'DELETE':
            with DB(database_path) as db:
                delete_image(db, library_path, Path(file_name))
                return 'True'

    app.run(host='0.0.0.0', port=8000)

def execute(config):
    library_path = Path(config.library)
    database_path = config.database
    serve(database_path, library_path)
