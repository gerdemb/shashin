import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
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
        return df.apply(pd.to_numeric, errors='coerce')

    def to_datetime_value(df):
        """Convert Datetime objects to seconds for numerical/quantitative parsing"""
        return df.apply(pd.to_datetime, format='%Y:%m:%d %H:%M:%S', exact=False, errors='coerce').applymap(lambda x: x.value)

    def str_len(df):
        return df.fillna('').astype(str).applymap(len)
        
    numerical_col_transformer = ColumnTransformer([
        ('numerical', FunctionTransformer(to_numeric), numerical_cols),
        ('date', FunctionTransformer(to_datetime_value), date_cols),
        ('string', FunctionTransformer(str_len), string_cols),
    ])

    feature_union = FeatureUnion([
        ('numerical_col_transformer', numerical_col_transformer),
    ])

    def dropna(a):
        return a[~np.isnan(a).any(axis=1)]

    def cmp(a):
        num_cols = a.shape[1]
        split = num_cols // 2
        l = np.nan_to_num(a[:, 0:split])
        r = np.nan_to_num(a[:, split:num_cols])
        d = np.sign(l - r)
        return d

    return Pipeline([
        ('reindex', ReindexTransformer(X.columns)),
        ('feature_union', feature_union),
        ('cmp', FunctionTransformer(cmp)),
        ('model', RandomForestClassifier())
    ])


class ReindexTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return X.reindex(columns=self.columns)
