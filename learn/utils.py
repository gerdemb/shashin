def split(df):
    num_cols = df.shape[1]
    split = num_cols // 2
    l = df.iloc[:, 0:split]
    r = df.iloc[:, split:num_cols]
    return l, r
