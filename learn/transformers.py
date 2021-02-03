from learn.utils import split
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer

class BaseReindexTransformer(BaseEstimator, TransformerMixin):
    def transform(self, X, y=None):
        return X.reindex(columns=self.columns)


class NumericReindexTransformer(BaseReindexTransformer):
    def fit(self, X, y=None):
        self.columns = X.select_dtypes(include=np.number).columns.tolist()
        return self


class DateReindexTransformer(BaseReindexTransformer):
    def fit(self, X, y=None):
        self.columns = X.filter(regex=".*Date.*").columns.tolist()
        return self


class StringReindexTransformer(BaseReindexTransformer):
    def fit(self, X, y=None):
        self.columns = X.select_dtypes(include=object).columns.tolist()
        return self




class TokenizerTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, vectorizer):
        self.vectorizer = vectorizer

    @staticmethod
    def str_join_cols(df):
        return df.astype(str).fillna('').apply(' '.join, axis=1)

    def fit(self, X, y=None):
        l, _ = split(X)
        corpus = self.str_join_cols(l)
        self.vectorizer.fit(corpus)
        return self
    
    def transform(self, X, y=None):
        l, r = split(X)
        l_corpus = self.str_join_cols(l)
        r_corpus = self.str_join_cols(r)
        l_transform = self.vectorizer.transform(l_corpus)        
        r_transform = self.vectorizer.transform(r_corpus)
        c = (l_transform - r_transform).sign()
        return c
