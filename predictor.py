import json
import time
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, HashingVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer


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
    pipeline = get_pipeline(*analyze_columns(deleted_df, saved_df))
    X, y = join(deleted_df, saved_df)
    X_train, X_test, y_train, y_test = train_test_split(X, y)
    pipeline.fit(X_train, y_train)
    print("...done")
    print('R2 score: {0:.2f}'.format(pipeline.score(X_test, y_test)))

    def predict(a, b):
        a_df = data_frame_from_records({0:[a]})
        b_df = data_frame_from_records({0:[b]})
        X, _ = join(a_df, b_df)

        start = time.perf_counter()
        prediction = pipeline.predict(X.iloc[:1])
        end = time.perf_counter()
        print(f"{a['SourceFile']} {b['SourceFile']} {prediction} Time: {end-start}")
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


def analyze_columns(deleted, saved):
    numerical_cols = []
    string_cols = []
    date_cols = []

    df = deleted.append(saved)

    for cname in df.columns:
        dtype = df[cname].dtype
        pair = (cname + '_l', cname+'_r')
        if 'Date' in cname:
            date_cols.extend(pair)
        elif dtype in ['int64', 'float64']:
            numerical_cols.extend(pair)
        elif dtype == "object":
            string_cols.extend(pair)
        else:
            assert False
    return numerical_cols, string_cols, date_cols


def get_pipeline(numerical_cols, string_cols, date_cols):
    def to_datetime_value(df):
        """Convert Datetime objects to seconds for numerical/quantitative parsing"""
        return df.astype(str).apply(
            lambda x: pd.to_datetime(
                x.str.slice(0, 19), 
                format='%Y:%m:%d %H:%M:%S',
                errors='coerce'
            ).apply(lambda d: d.value)
        )

    def to_numeric(df):
        return df.apply(pd.to_numeric, errors='coerce')

    def str_len(df):
        return df.fillna('').astype(str).applymap(len)

    numerical_col_transformer = ColumnTransformer([
        ('date', FunctionTransformer(to_datetime_value), date_cols),
        ('numerical', FunctionTransformer(to_numeric), numerical_cols),
        ('string', FunctionTransformer(str_len), string_cols),
    ])

    def subtractor(a):
        # https://stackoverflow.com/questions/10198747/how-can-i-simultaneously-select-all-odd-rows-and-all-even-columns-of-an-array
        l = a[:, 1::2]
        r = a[:, ::2]
        return l - r

    def nan_to_num(x):
        return np.nan_to_num(x)

    numerical_pipeline = Pipeline([
        ('reindexer', ReindexTransformer(numerical_cols + date_cols + string_cols)),
        ('numerical_col_transformer', numerical_col_transformer),
        ('nan_to_num', FunctionTransformer(nan_to_num)),
        ('subtractor', FunctionTransformer(subtractor)),
    ])

    def tokenize(df):
        tokenizer = CountVectorizer().build_tokenizer()

        def f(x):
            return set(tokenizer(x))
        return df.astype(str).fillna('').applymap(f)

    string_col_transformer = ColumnTransformer([
        ('string', FunctionTransformer(tokenize), string_cols),
    ])

    def build_corpus(a):
        return [' '.join(set().union(*r)) for r in a]

    string_pipeline = Pipeline([
        ('reindexer', ReindexTransformer(string_cols)),
        ('string_col_transformer', string_col_transformer),
        ('build_corpus', FunctionTransformer(build_corpus)),
        ('count_vectorizer', HashingVectorizer())
    ])

    feature_union = FeatureUnion([
        ('numerical_pipeline', numerical_pipeline),
        ('string_pipeline', string_pipeline)
    ])

    return Pipeline([
        ('feature_union', feature_union),
        ('model', RandomForestClassifier())
    ])


class ReindexTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return X.reindex(columns=self.columns)
