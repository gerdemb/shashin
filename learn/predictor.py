import json
import time
from collections import defaultdict

import pandas as pd
from sklearn.model_selection import train_test_split
from .default_pipeline import get_pipeline


def build_predictor(db, cache_dir):
    print("Loading json features")
    deleted = load_json(cache_dir)
    print(f"...{len(deleted)} features")

    print("Loading from database")
    saved = load_db(db, deleted.keys())
    print(f"...{len(saved)} features")

    if len(deleted) == 0 or len(saved) == 0:
        return lambda a, b: 0

    print("Fitting data")
    deleted_df = data_frame_from_records(deleted)
    saved_df = data_frame_from_records(saved)
    pipeline = get_pipeline(deleted_df, saved_df)
    X, y = join(deleted_df, saved_df)
    X_train, X_test, y_train, y_test = train_test_split(X, y)
    pipeline.fit(X_train, y_train)
    print('...R2 score: {0:.2f}'.format(pipeline.score(X_test, y_test)))

    def predict(a, b):
        a_df = data_frame_from_records({0:[a]})
        b_df = data_frame_from_records({0:[b]})
        X, _ = join(a_df, b_df)

        start = time.perf_counter()
        prediction = pipeline.predict(X.iloc[:1])
        end = time.perf_counter()
        print(f"{a['SourceFile']} {b['SourceFile']} y={prediction} {end-start:.2f}s")
        return prediction
    return predict


def data_frame_from_records(records):
    def flatten_lists(d):
        def f(x):
            if isinstance(x, list):
                return ' '.join(str(x))
            else:
                return x
        return {k:f(v) for k, v in d.items()}

    return pd.DataFrame.from_records(
        [flatten_lists(metadata) for dhash in records for metadata in records[dhash]],
        index=[dhash for dhash in records for _ in records[dhash]],
    )


def load_json(cache_dir):
    features = defaultdict(list)
    for file in cache_dir.glob('*.json'):
        with file.open() as f:
            dhash, metadata = json.load(f)
            features[dhash].append(metadata)
    return features


def load_db(db, hashes):
    features = defaultdict(list)
    for dhash in hashes:
        for row in db.image_select_by_dhash(bytes.fromhex(dhash)):
            metadata = json.loads(row['metadata'])
            features[dhash].append(metadata)
    return features


def join(deleted, saved):
    left_to_right = deleted.join(saved, lsuffix='_l', rsuffix='_r')
    left_to_right['Keep'] = 1
    right_to_left = saved.join(deleted, lsuffix='_l', rsuffix='_r')
    right_to_left['Keep'] = -1
    joined = left_to_right.append(right_to_left)
    return joined.drop(['Keep'], axis=1), joined['Keep']


