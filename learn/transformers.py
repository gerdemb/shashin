from learn.utils import split
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


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
    def _corpus(X):
        l, r = split(X)
        l_corpus = l.astype(str).fillna('').apply(' '.join, axis=1)
        r_corpus = r.astype(str).fillna('').apply(' '.join, axis=1)
        return l_corpus, r_corpus

    def _transform(self, l_corpus, r_corpus):
        l_transform = self.vectorizer.transform(l_corpus)
        r_transform = self.vectorizer.transform(r_corpus)
        return (l_transform - r_transform).sign()

    def fit_transform(self, X, y=None, **fit_params):
        l_corpus, r_corpus = self._corpus(X)
        self.vectorizer.fit(l_corpus)
        return self._transform(l_corpus, r_corpus)

    def transform(self, X, y=None):
        l_corpus, r_corpus = self._corpus(X)
        return self._transform(l_corpus, r_corpus)