import datetime
import CONSTANT
from util import log, timeit
import numpy as np
from sklearn.decomposition import PCA
from sklearn.utils import resample
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from lightgbm import LGBMClassifier
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold
import category_encoders as ce

@timeit
def clean_tables(tables):
    for tname in tables:
        log(f"cleaning table {tname}")
        clean_df(tables[tname])


@timeit
def clean_df(df):
    fillna(df)


@timeit
def fillna(df):
    for c in [c for c in df if c.startswith(CONSTANT.NUMERICAL_PREFIX)]:
        df[c].fillna(-1, inplace=True)

    for c in [c for c in df if c.startswith(CONSTANT.CATEGORY_PREFIX)]:
        df[c].fillna("0", inplace=True)

    for c in [c for c in df if c.startswith(CONSTANT.TIME_PREFIX)]:
        df[c].fillna(datetime.datetime(1970, 1, 1), inplace=True)

    for c in [c for c in df if c.startswith(CONSTANT.MULTI_CAT_PREFIX)]:
        df[c].fillna("0", inplace=True)


@timeit
def feature_engineer(df, config):
    transform_categorical_hash(df)
    transform_datetime(df, config)

@timeit
def transform_datetime(df, config):
    for c in [c for c in df if c.startswith(CONSTANT.TIME_PREFIX)]:
        df.drop(c, axis=1, inplace=True)


@timeit
def transform_categorical_hash(df):

    # categorical encoding mechanism 1:
    # for c in [c for c in df if c.startswith(CONSTANT.CATEGORY_PREFIX)]:
    #     # df[c] = df[c].apply(lambda x: int(x))
    #     df[c], _ = pd.factorize(df[c])
    #     # Set feature type as categorical
    #     df[c] = df[c].astype('category')
    #

    # categorical encoding mechanism 2:
    # categorical_feats = [
    #     col for col in df.columns if col.startswith(CONSTANT.CATEGORY_PREFIX)
    # ]
    #
    # # Specify the columns to encode then fit and transform
    # encoder = ce.backward_difference.BackwardDifferenceEncoder(cols=categorical_feats)
    # encoder.fit(df, verbose=1)
    # df = encoder.transform(df)

    # categorical encoding mechanism 3:
    for c in [c for c in df if c.startswith(CONSTANT.CATEGORY_PREFIX)]:
        # df[c] = df[c].apply(lambda x: int(x))
        # df[c], _ = pd.factorize(df[c])
        # calculate the frequency of item
        val_freq = df[c].value_counts(normalize=True).to_dict()
        df[c] = df[c].map(val_freq)
        df[c] = df[c].astype('float')


    for c in [c for c in df if c.startswith(CONSTANT.MULTI_CAT_PREFIX)]:
        df[c] = df[c].apply(lambda x: int(x.split(',')[0]))
        # TODO: multi value categorical feature -> ?
@timeit
def data_reduction_train(df):
    matrix = df.as_matrix()
    min_max_scaler = MinMaxScaler()
    matrix = min_max_scaler.fit_transform(matrix)
    pca = PCA()
    pca.fit(matrix)
    sum_ratio, flag_idx = 0, None
    # determine the reduced dimension
    for i in range(pca.explained_variance_ratio_.size):
        sum_ratio += pca.explained_variance_ratio_[i]
        if sum_ratio >= CONSTANT.VARIANCE_RATIO:
            flag_idx = i
            break
    if flag_idx:
        pca = PCA(n_components=flag_idx)
        matrix_trans = pca.fit_transform(matrix)
        # reconstruct dataframe
        d = {}
        for i in range(matrix_trans.shape[1]):
            d[f"f_{i}"] = matrix_trans[:,i]
        ret_df = pd.DataFrame(d)
        return ret_df, min_max_scaler, pca

@timeit
def data_reduction_test(df, scaler, pca):
    matrix = df.as_matrix()
    matrix = scaler.transform(matrix)
    matrix_trans = pca.transform(matrix)
    # reconstruct dataframe
    d = {}
    for i in range(matrix_trans.shape[1]):
        d[f"f_{i}"] = matrix_trans[:, i]
    ret_df = pd.DataFrame(d)
    return ret_df

@timeit
def data_balance(X, y, config, seed=None):
    # balance the raw dataset if there exist imbalance class in it.

    origin_size = len(X)
    X["class"] = y
    df_class_0 = X[X["class"]==0]#.drop(columns=["class"])
    df_class_1 = X[X["class"]==1]#.drop(columns=["class"])

    if len(df_class_0) < len(df_class_1):
        df_minority = df_class_0
        df_majority = df_class_1
    else:
        df_minority = df_class_1
        df_majority = df_class_0

    if CONSTANT.SAMPLE_UP_OR_DOWN == "up":
        # Upsample minority class
        df_minority_upsampled = resample(df_minority,
                                         replace=True,  # sample with replacement
                                         n_samples=len(df_majority))  # to match majority class
        # Combine majority class with upsampled minority class
        df_upsampled = pd.concat([df_majority, df_minority_upsampled])

        df_sampled = resample(df_upsampled,
                              replace=False,
                              n_samples=int(origin_size * 0.5),
                              random_state=seed)
    else:
        # Downsample majority class
        df_majority_downsampled = resample(df_majority,
                                           replace=False,  # sample without replacement
                                           n_samples=len(df_minority),
                                           random_state=seed)  # to match minority class

        # Combine minority class with downsampled majority class
        df_sampled = pd.concat([df_majority_downsampled, df_minority])

    # Display new class counts
    print(df_sampled["class"].value_counts())

    return df_sampled.drop(columns=["class"]), df_sampled["class"]

@timeit
def feature_selection(X, y, config, seed=None):
    # categorical_feats = [
    #     col for col in X.columns if col.startswith(CONSTANT.CATEGORY_PREFIX)
    # ]
    train_features = X.columns
    # Fit LightGBM in RF mode, yes it's quicker than sklearn RandomForest
    dtrain = lgb.Dataset(X, y, free_raw_data=False, silent=True)
    lgb_params = CONSTANT.pre_lgb_params
    lgb_params["seed"] = seed
    # Fit the model
    clf = lgb.train(params=lgb_params, train_set=dtrain, num_boost_round=200)

    # Get feature importances
    imp_df = pd.DataFrame()
    imp_df["feature"] = list(train_features)
    imp_df["importance_gain"] = clf.feature_importance(importance_type='gain')
    imp_df["importance_split"] = clf.feature_importance(importance_type='split')
    imp_df['trn_score'] = roc_auc_score(y, clf.predict(X))

    # imp_df.sort_values(by=["importance_gain", "importance_split"], ascending=False, inplace=True)

    selected_features = []
    selected_features = imp_df.query("importance_gain > 0")["feature"]

    return X[selected_features], selected_features

def get_feature_importance(df):
    pass