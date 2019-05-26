NUMERICAL_TYPE = "num"
NUMERICAL_PREFIX = "n_"
CATEGORY_TYPE = "cat"
CATEGORY_PREFIX = "c_"

TIME_TYPE = "time"
TIME_PREFIX = "t_"

MULTI_CAT_TYPE = "multi-cat"
MULTI_CAT_PREFIX = "m_"
MULTI_CAT_DELIMITER = ","


MAIN_TABLE_NAME = "main"
MAIN_TABLE_TEST_NAME = "main_test"
TABLE_PREFIX = "table_"

LABEL = "label"

# parameter of table merge
'''
There must exist a relationship between HASH_MAX and WINDOW_SIZE:
1. The larger the HASH_MAX, the less information from other records with identical hash value can be used.
2. The larger the WINDOW_SIZE, the more temporal information can be used.
'''
HASH_MAX = 200
WINDOW_SIZE = 5

# Switch and parameter of data reduction
REDUCTION_SWITCH = False
VARIANCE_RATIO = 0.95 # the VARIANCE RAITO is used in PCA

# Switch and parameter of feature selection
FEATURE_SELECTION_SWITCH = True
pre_lgb_params = {
        'objective': 'binary',
        'boosting_type': 'rf',
        'metric': 'auc',
        'subsample': 0.5,
        'colsample_bytree': 0.5,
        'num_leaves': 127,
        'max_depth': 8,
        'bagging_freq': 1,
        'n_jobs': 4,
        'verbose':-1
}

# Switch and parameter of data balance
DATA_BALANCE_SWITCH = False
SAMPLE_UP_OR_DOWN = "down"

# Switch and parameter of data downsampling
DATA_DOWNSAMPLING_SWITCH = False
DOWNSAMPLING_RATIO = 0.8

# Parameter of model ensemble
ENSEMBLE = True
ENSEMBLE_OBJ = 2  # currently 2 is better than 3

# Parameter of categorical hash
cat_hash_params = {
    "cat": {
        "method": "fact"#, "bd", "freq"
    },
    "multi_cat": {
    }
}

# Parameter of automl
train_lgb_params = {
        "objective": "binary",
        # 'boosting_type': 'rf',
        "metric": "auc",
        "verbosity": -1,
        "seed": None,
        "num_threads": 4,
        # "is_unbalance": True
}