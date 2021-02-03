from learn.utils import split
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

from learn.transformers import (
    DateReindexTransformer,
    NumericReindexTransformer,
    StringReindexTransformer,
    TokenizerTransformer
)


def to_numeric(df):
    return df.apply(pd.to_numeric, errors='coerce')


def split_cmp(df):
    """Split into left and right sides a calculate sign of the difference. Values need to be numeric"""
    l, r = split(df)
    # NOTE: 0-NaN should probably equal 1, but using fill_value=0 means it is evaluated as 0-0=0
    d = l.sub(r.values, fill_value=0).fillna(0)
    cmp = np.sign(d)
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


tokenizer_pipeline = Pipeline([
    ('reindex', StringReindexTransformer()),
    ('tokenizer', TokenizerTransformer(CountVectorizer())),
    # Put passthrough here to prevent exception in pipeline validation. TokenizerTransformer doesn't have to implement fit() as model step in parent pipeline is final
    # step. Seems like sklearn pipeline validation is broken here.
    ('passthrough', 'passthrough'),
])

feature_union = FeatureUnion([
    ('numeric_pipeline', numeric_pipeline),
    ('date_pipeline', date_pipeline),
    ('string_len_pipelien', string_len_pipeline),
    ('tokenizer_pipeline', tokenizer_pipeline),
])

pipeline = Pipeline([
    ('feature_union', feature_union),
    ('model', RandomForestClassifier())
])
