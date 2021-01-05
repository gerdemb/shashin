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
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from functools import cmp_to_key

class Predictor(object):
    def __init__(self, database_path, features_path):
        self.database_path = database_path
        self.features_path = features_path
        self.model = None
        self.columns = None

    def predict(self, metadata_a, metadata_b):
        if not self.model:
            return 0
        comparison = self.cmp_metadata(metadata_a, metadata_b)
        feature = {
            col: comparison.get(col, 0)
            for col in self.columns
        }

        df = pd.DataFrame.from_records([feature])
        prediction = self.model.predict(df)
        print(metadata_a['SourceFile'], metadata_b['SourceFile'], prediction)
        return prediction

    def build_model(self):
        features = self.load_json_features()
        if not features:
            return

        df = pd.DataFrame.from_records(features)
        df = df.append(df * -1)
        df = df.fillna(0)
        
        X = df.drop('Keep', axis=1)
        y = df['Keep']

        self.model = RandomForestClassifier()
        self.model.fit(X, y)

        self.columns = list(X.columns)

    def load_json_features(self):
        features = []
        with DB(self.database_path) as db:
            for file in self.features_path.glob('*.json'):
                with file.open() as f:
                    dhash, metadata_b = json.load(f)
                    for row in db.image_select_by_dhash(bytes.fromhex(dhash)):
                        metadata_a = json.loads(row['metadata'])
                        feature = self.cmp_metadata(metadata_a, metadata_b)
                        feature['Keep'] = -1 # Keep A (left-side)
                        features.append(feature)
        return features

    @staticmethod
    def cmp_metadata(metadata_a, metadata_b):
        def cmp(a, b):
            if a is not None and b is not None:
                return (a > b) - (a < b)
            elif a is None and b is None:
                return 0
            elif a is None:
                return -1
            elif b is None:
                return 1

        keys = set(list(metadata_a.keys()) + list(metadata_b.keys()))

        feature = {}
        for key in keys:
            a = metadata_a.get(key)
            b = metadata_b.get(key)
            if isinstance(a, str): a=len(a)
            if isinstance(b, str): b=len(b)
            feature[key] = cmp(a,b)
        return feature



class BrowseDuplicatesCommand(object):

    def __init__(self, config):
        self.library_path = Path(config.library)
        self.database_path = config.database
        self.features_path = Path(config.features_path).expanduser()
        self.features_path.mkdir(parents=True, exist_ok=True)

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

        self.predictor = Predictor(self.database_path, self.features_path)
        self.predictor.build_model()

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
        data = (
            row['dhash'].hex(),
            json.loads(row['metadata'])
        )
        data_json = json.dumps(data)
        with tempfile.NamedTemporaryFile(
            dir = self.features_path,
            mode='w',
            delete=False,
            prefix='img',
            suffix='.json'
        ) as log:
            log.write(data_json)

    def execute(self):
        app = Flask(__name__, )
        app.url_map.converters['everything'] = EverythingConverter

        @app.route('/')
        def index():
            def sort_key(a, b):
                _, metadata_a = a
                _, metadata_b = b
                return self.predictor.predict(metadata_a,metadata_b)

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
                            key=cmp_to_key(sort_key)
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

        @app.route('/image/<everything:file_name>', methods=['GET', 'DELETE', 'POST'])
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
                    self.log_metadata(row)
                    delete_image(db, file)
                    return 'True'
                elif request.method == 'POST':
                    db.ignore_insert_dhash(row['dhash'])
                    return 'True'

        app.run(host='0.0.0.0', port=8000)


class EverythingConverter(PathConverter):
    regex = '.*?'
