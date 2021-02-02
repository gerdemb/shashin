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
