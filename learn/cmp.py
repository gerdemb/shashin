import numpy as np
import pandas as pd
from scipy.sparse.csr import csr_matrix
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder

from learn.transformers import (DateReindexTransformer,
                                NumericReindexTransformer,
                                StringReindexTransformer)


def to_numeric(df):
    return df.apply(pd.to_numeric, errors='coerce')

def split_cmp(a):
    """Split into left and right sides a calculate sign of the difference. Values need to be numeric"""
    if isinstance(a, pd.DataFrame):
        a = a.to_numpy()
    num_cols = a.shape[1]
    split = num_cols // 2
    # TODO 0 - NaN should equal 1, but using fill_value=0 means it is evaluated as 0 - 0
    l = np.nan_to_num(a[:, 0:split])
    r = np.nan_to_num(a[:, split:num_cols])
    d = l - r
    if isinstance(d, np.ndarray):
        cmp = np.sign(d)
    elif isinstance(d, csr_matrix):
        cmp = d.sign()
    else:
        assert False
    return cmp

numeric_pipeline = Pipeline([
    ('reindex', NumericReindexTransformer()),
    ('to_numeric', FunctionTransformer(to_numeric)),
    ('cmp', FunctionTransformer(split_cmp)),
])

def to_datetime_value(df):
    return df.apply(
        pd.to_datetime,
        format='%Y:%m:%d %H:%M:%S',
        errors='coerce',
        exact=False
    ).applymap(lambda x: x.value)

date_pipeline = Pipeline([
    ('reindex', DateReindexTransformer()),
    ('to_datetime_value', FunctionTransformer(to_datetime_value)),
    ('cmp', FunctionTransformer(split_cmp)),
])

def str_len(df):
    return df.astype(str).fillna('').applymap(len)

string_len_pipeline = Pipeline([
    ('reindex', StringReindexTransformer()),
    ('str_len', FunctionTransformer(str_len)),
    ('cmp', FunctionTransformer(split_cmp)),
])

category_transfomer = ColumnTransformer([
    # ('categories', OneHotEncoder(handle_unknown='ignore'), category_cols),
])

def to_string(df):
    return df.astype(str)

category_pipeline = Pipeline([
    # ('reindex', ReindexTransformer(category_cols)),
    ('to_string', FunctionTransformer(to_string)),
    ('one_hot_encoder', category_transfomer),
    ('cmp', FunctionTransformer(split_cmp)),
])

def tokenizer(df):
    num_cols = df.shape[1]
    split = num_cols // 2
    l = df.iloc[:, 0:split]
    r = df.iloc[:, split:num_cols]
    text_l = l.astype(str).fillna('').apply(' '.join, axis=1)
    text_r = r.astype(str).fillna('').apply(' '.join, axis=1)
    t = pd.concat([text_l, text_r], axis=1)
    t.columns = ['text_l', 'text_r']
    return t

count_vectorizer = ColumnTransformer([
    ('tokens_l', CountVectorizer(), 'text_l'),
    ('tokens_r', CountVectorizer(), 'text_r'),
])

tokenizer_pipeline = Pipeline([
    # ('reindex', ReindexTransformer(string_cols)),
    ('tokenizer', FunctionTransformer(tokenizer)),
    ('count_vectorizer', count_vectorizer),
    ('cmp', FunctionTransformer(split_cmp)),
])

feature_union = FeatureUnion([
    ('numeric_pipeline', numeric_pipeline),
    ('date_pipeline', date_pipeline),
    ('string_len_pipelien', string_len_pipeline),
    # ('category_pipeline', category_pipeline),
    # ('tokenizer_pipeline', tokenizer_pipeline),
])

pipeline = Pipeline([
    ('feature_union', feature_union),
    ('model', RandomForestClassifier())
])

