from sklearn.base import TransformerMixin, BaseEstimator
import pandas as pd
import numpy as np


def split(df):
    num_cols = df.shape[1]
    split = num_cols // 2
    l = df.iloc[:, 0:split]
    r = df.iloc[:, split:num_cols]
    return l, r


class Debug(BaseEstimator, TransformerMixin):
    def transform(self, X):
        df = pd.DataFrame(X)
        print(df.head())
        print(df.shape)
        df.to_csv('dump.csv')
        # print("rows inf", df.index[np.isinf(df).any(1)])
        # print("cols inf", df.columns.to_series()[np.isinf(df).any()])
        # print("rows nan", df.index[np.isnan(df).any(1)])
        # print("cols nan", df.columns.to_series()[np.isnan(df).any()])
        # breakpoint()
        return X

    def fit(self, X, y=None, **fit_params):
        return self