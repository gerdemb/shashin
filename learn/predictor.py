import json
import time
from collections import defaultdict

import pandas as pd
from sklearn.model_selection import train_test_split
from .numeric_pipeline import get_pipeline


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
    X, y = join(deleted, saved)
    pipeline = get_pipeline(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y)
    pipeline.fit(X_train, y_train)
    print('...R2 score: {0:.2f}'.format(pipeline.score(X_test, y_test)))

    def predict(a, b):
        X, _ = join({0: a}, {0: b})

        start = time.perf_counter()
        prediction = pipeline.predict(X.iloc[:1])
        end = time.perf_counter()
        print(f"{a['SourceFile']} {b['SourceFile']} y={prediction} {end-start:.2f}s")
        return prediction
    return predict


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
    def _from_records(records):
        data = [metadata for dhash in records for metadata in records[dhash]]
        index = [dhash for dhash in records for _ in records[dhash]]
        return pd.DataFrame.from_records(data, index=index,)
    deleted_df = _from_records(deleted)
    deleted_df['Deleted'] = True
    saved_df = _from_records(saved)
    saved_df['Saved'] = True

    merged = deleted_df.append(saved_df)

    deleted_saved = merged[merged['Deleted'] == True].join(
        merged[merged['Saved'] == True], 
        lsuffix='_l', 
        rsuffix='_r'
    )
    deleted_saved['Keep'] = 1
    saved_deleted = merged[merged['Saved'] == True].join(
        merged[merged['Deleted'] == True], 
        lsuffix='_l', 
        rsuffix='_r'
    )
    saved_deleted['Keep'] = -1

    joined = deleted_saved.append(saved_deleted)
    return joined.drop(['Keep'], axis=1), joined['Keep']
