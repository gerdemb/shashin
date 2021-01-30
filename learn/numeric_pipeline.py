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

    def to_numeric(df):
        return df.apply(pd.to_numeric, errors='coerce').fillna(0)

    numerical_col_transformer = ColumnTransformer([
        ('numerical', FunctionTransformer(to_numeric), numerical_cols),
    ])

    feature_union = FeatureUnion([
        ('numerical_col_transformer', numerical_col_transformer),
    ])

    def subtractor(a):
        num_cols = a.shape[1]
        split = num_cols // 2
        l = a[:, 0:split]
        r = a[:, split:num_cols]
        return l - r

    return Pipeline([
        ('reindex', ReindexTransformer(numerical_cols)),
        ('feature_union', feature_union),
        ('subtractor', FunctionTransformer(subtractor)),
        ('model', RandomForestClassifier())
    ])


class ReindexTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return X.reindex(columns=self.columns)
