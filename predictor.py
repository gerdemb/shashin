import json
from collections import defaultdict

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer


def build_predictor(db, cache_dir):
    print("Loading json features")
    deleted = load_json(cache_dir)

    print("Loading from database")
    saved = load_db(db, deleted.index.unique())

    print("Fitting data")
    pipeline = get_pipeline(*analyze_columns(deleted, saved))
    X, y = join(deleted, saved)
    pipeline.fit(X, y)

    def predict(a, b):
        a_df = pd.DataFrame.from_records(a, index=[0])
        b_df = pd.DataFrame.from_records(b, index=[0])
        X, _ = join(a_df, b_df)
        prediction = pipeline.predict(X.iloc[:1])
        print(a['SourceFile'], b['SourceFile'], prediction)
        return prediction
    return predict


def data_frame_from_records(records):
    return pd.DataFrame.from_records(
        [metadata for dhash in records for metadata in records[dhash]],
        index=[dhash for dhash in records for _ in records[dhash]],
    )


def load_json(cache_dir):
    features = defaultdict(list)
    for file in cache_dir.glob('*.json'):
        with file.open() as f:
            dhash, metadata = json.load(f)
            features[dhash].append(metadata)
    df = data_frame_from_records(features)
    return df


def load_db(db, hashes):
    features = defaultdict(list)
    for dhash in hashes:
        for row in db.image_select_by_dhash(bytes.fromhex(dhash)):
            metadata = json.loads(row['metadata'])
            features[dhash].append(metadata)
    df = data_frame_from_records(features)
    return df


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
            lambda x: pd.to_datetime(x.str.slice(
                0, 19), format='%Y:%m:%d %H:%M:%S').apply(lambda d: d.value)
        )

    def tokenize(df):
        tokenizer = CountVectorizer().build_tokenizer()

        def f(x):
            return set(tokenizer(x))
        return df.fillna('').applymap(f)

    numerical_col_transformer = ColumnTransformer([
        ('date', FunctionTransformer(to_datetime_value), date_cols),
        ('numerical', 'passthrough', numerical_cols),
    ])

    def subtractor(a):
        # https://stackoverflow.com/questions/10198747/how-can-i-simultaneously-select-all-odd-rows-and-all-even-columns-of-an-array
        l = a[:, 1::2]
        r = a[:, ::2]
        return l - r

    numerical_pipeline = Pipeline([
        ('reindexer', ReindexTransformer(numerical_cols + date_cols)),
        ('numerical_col_transformer', numerical_col_transformer),
        # TODO can we do better here?
        ('imputer', SimpleImputer(strategy='constant')),
        ('subtractor', FunctionTransformer(subtractor)),
    ])

    string_col_transformer = ColumnTransformer([
        ('string', FunctionTransformer(tokenize), string_cols),
    ])

    def build_corpus(a):
        return [' '.join(set().union(*r)) for r in a]

    string_pipeline = Pipeline([
        ('reindexer', ReindexTransformer(string_cols)),
        ('string_col_transformer', string_col_transformer),
        ('build_corpus', FunctionTransformer(build_corpus)),
        ('count_vectorizer', CountVectorizer())
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
