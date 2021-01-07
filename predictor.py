import json

import pandas as pd
from sklearn.ensemble import RandomForestClassifier


# Make a difference vector between two metadatas
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
        # Compare strings by length instead of alphabetical order
        if isinstance(a, str): a=len(a)
        if isinstance(b, str): b=len(b)
        feature[key] = cmp(a,b)
    return feature


def build_predictor(db, cache_dir):
    # Load json files from cache dir
    print("Loading json features")
    features = []
    for file in cache_dir.glob('*.json'):
        with file.open() as f:
            dhash, metadata_b = json.load(f)
            for row in db.image_select_by_dhash(bytes.fromhex(dhash)):
                metadata_a = json.loads(row['metadata'])
                feature = cmp_metadata(metadata_a, metadata_b)
                feature['Keep'] = -1 # Keep A (left-side)
                features.append(feature)

            df = pd.DataFrame.from_records(features)

    # If no features loaded, predict will just return 0 (equal)
    if not features:
        def predict(a,b):
            return 0
        return predict

    # Create a mirror set of features (ie. cmp(a,b) and cmp(b,a))
    df = pd.DataFrame.from_records(features)
    df = df.append(df * -1)
    df = df.fillna(0)
    
    X = df.drop('Keep', axis=1)
    y = df['Keep']

    print("Fitting model")
    model = RandomForestClassifier()
    model.fit(X, y)

    columns = list(X.columns)
    print("...done")

    def predict(metadata_a, metadata_b):
        comparison = cmp_metadata(metadata_a, metadata_b)
        feature = {
            col: comparison.get(col, 0)
            for col in columns
        }

        df = pd.DataFrame.from_records([feature])
        prediction = model.predict(df)
        print(metadata_a['SourceFile'], metadata_b['SourceFile'], prediction)
        return prediction
    return predict
