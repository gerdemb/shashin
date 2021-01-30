import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, HashingVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer


def analyze_columns(df):
    numerical_cols = []
    string_cols = []
    date_cols = []

    for cname in df.columns:
        dtype = df[cname].dtype
        if 'Date' in cname:
            date_cols.append(cname)
        elif dtype in ['int64', 'float64']:
            numerical_cols.append(cname)
        elif dtype == "object":
            string_cols.append(cname)
        else:
            assert False
    return numerical_cols, string_cols, date_cols


def get_pipeline(X):
    numerical_cols, string_cols, date_cols = analyze_columns(X)
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
