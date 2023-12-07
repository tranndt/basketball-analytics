

import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
from model_tools import *
from load_tools import *

import pandas as pd
import time
from tqdm import tqdm
import argparse
import warnings
from pandas.errors import PerformanceWarning
from sklearn.exceptions import DataConversionWarning, ConvergenceWarning
from sklearn.feature_selection import f_classif, mutual_info_classif
warnings.filterwarnings('ignore', category=PerformanceWarning)
warnings.filterwarnings('ignore', category=DataConversionWarning)
warnings.filterwarnings('ignore', category=ConvergenceWarning)

parser = argparse.ArgumentParser(description='Normalize basketball-reference.com data')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-c', '--config', type=str, default='config.yaml', help='Source config file')
parser.add_argument('-m', '--mode', type=str, default='all', help='')

args = parser.parse_args()
debug = args.debug

MODE = args.mode

def run_feature_model_stacks(config_yaml):
    """
    Usage:
        python3 10_feature_selection_script.py -c feature_selection_config.yaml
    """
    config = load_yaml(config_yaml)
    SRC_DATA_CONFIG = config['src_data']
    SRC_DIR = SRC_DATA_CONFIG['src_dir']
    LABEL_NAME = SRC_DATA_CONFIG['label_name']

    TGT_DATA_CONFIG = config['tgt_data']
    TGT_DIR = TGT_DATA_CONFIG['tgt_dir']

    EXPMNT_CONFIG = config['experiment']
    TGT_EXPMNT_NAME = EXPMNT_CONFIG['experiment_name']
    FS_CONFIG = EXPMNT_CONFIG['feature_selection']
    FS_SCORING_FUNCS = FS_CONFIG['scoring_funcs']
    FS_MODE = FS_CONFIG['mode'] # percentile or k_best
    FS_PARAMS = FS_CONFIG['params'] # [10,20,30,40,...]
    MS_CONFIG = EXPMNT_CONFIG['model_selection']
    MS_CONFIG_CV = MS_CONFIG['cv']
    MS_CONFIG_MODELS = MS_CONFIG['models']
    MS_CONFIG_MODEL_PARAMS = MS_CONFIG['model_params']
    MS_CONFIG_SCORING_FUNCS = MS_CONFIG['scoring_funcs']

    FEATURES,LABELS = load_dataset(SRC_DIR)
    FEATURES = FEATURES.dropna()
    LABELS = LABELS.loc[FEATURES.index][LABEL_NAME]
    X,y = FEATURES, LABELS
    if debug:
        X, y = make_classification(n_samples=1000, n_features=30)  # Example dataset
        # X,y = make_regression(n_samples=1000, n_features=30)  # Example dataset
        X = pd.DataFrame(X)
        y = pd.Series(y)
    feature_stack = FeatureStack(FS_SCORING_FUNCS, mode=FS_MODE, params=FS_PARAMS)
    feature_stack.fit(X, y)

    if TGT_EXPMNT_NAME is None:
        TGT_EXPMNT_NAME = datetime.now().strftime('%Y%m%d-%H%M%S')
    make_directory('/'.join([TGT_DIR,TGT_EXPMNT_NAME]))

    scores_all = {}
    predictions_all = {}
    TQDM_FS_TRANSFORM = tqdm(feature_stack.transform(X),position=0, leave=True, ncols = 150,
                             total=len(feature_stack.scoring_funcs)*len(feature_stack.params))
    for transformed_X,meta in TQDM_FS_TRANSFORM:
        TQDM_FS_TRANSFORM.set_description(f'{meta}')
        if MS_CONFIG_CV is None:
            model_stack = ModelStack(models=MS_CONFIG_MODELS, model_params=MS_CONFIG_MODEL_PARAMS)
            predictions = model_stack.fit_predict(transformed_X, y)
            scores = model_stack.score(predictions, score_names=MS_CONFIG_SCORING_FUNCS)
        else:
            model_stack = ModelStackCV(models=MS_CONFIG_MODELS, model_params=MS_CONFIG_MODEL_PARAMS)
            predictions = model_stack.fit_predict(transformed_X, y, cv=MS_CONFIG_CV)
            scores = model_stack.score(predictions, score_names=MS_CONFIG_SCORING_FUNCS,avg_cv=True)
        predictions_all[meta]   = predictions
        scores_all[meta]        = scores
        predictions_all_df      = pd.concat(predictions_all.values(), keys=predictions_all.keys(), axis=1)
        scores_all_df           = pd.concat(scores_all.values(), keys=scores_all.keys(), axis=0)
        predictions_all_df.to_csv('/'.join([TGT_DIR,TGT_EXPMNT_NAME,'predictions.csv']))
        scores_all_df.to_csv('/'.join([TGT_DIR,TGT_EXPMNT_NAME,'scores.csv']))


    # if TGT_EXPMNT_NAME is None:
    #     TGT_EXPMNT_NAME = datetime.now().strftime('%Y%m%d-%H%M%S')
    # make_directory('/'.join([TGT_DIR,TGT_EXPMNT_NAME]))
    predictions_all_df      = pd.concat(predictions_all.values(), keys=predictions_all.keys(), axis=1)
    scores_all_df = pd.concat(scores_all.values(), keys=scores_all.keys(), axis=0)
    predictions_all_df.to_csv('/'.join([TGT_DIR,TGT_EXPMNT_NAME,'predictions.csv']))
    scores_all_df.to_csv('/'.join([TGT_DIR,TGT_EXPMNT_NAME,'scores.csv']))

    specs = {}
    specs['models'] = model_stack.get_params()
    specs['features'] = {
        str(k):list(v) for k,v in feature_stack.transformed_columns.items()
    }
    config['date_executed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_yaml( '/'.join([TGT_DIR,TGT_EXPMNT_NAME,'config.yaml']),config)
    save_json( '/'.join([TGT_DIR,TGT_EXPMNT_NAME,'specs.json']),specs)


if __name__ == "__main__":
    run_feature_model_stacks(args.config)