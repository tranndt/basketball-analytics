import pandas as pd
from sklearn.feature_selection import chi2, f_classif, mutual_info_classif, RFE, mutual_info_regression
from sklearn.linear_model import LogisticRegression, Lasso, Ridge, RidgeClassifier, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from scipy.stats import pearsonr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.svm import SVC, SVR
import warnings
from pandas.errors import PerformanceWarning
from sklearn.exceptions import DataConversionWarning, ConvergenceWarning
pd.options.mode.use_inf_as_na = True
warnings.filterwarnings('ignore', category=PerformanceWarning)
warnings.filterwarnings('ignore', category=DataConversionWarning)
warnings.filterwarnings('ignore', category=ConvergenceWarning)

import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
from load_tools import *
import time
from tqdm import tqdm
import argparse
import warnings
from pandas.errors import PerformanceWarning
pd.options.mode.use_inf_as_na = True
warnings.filterwarnings('ignore', category=PerformanceWarning)

parser = argparse.ArgumentParser(description='Normalize basketball-reference.com data')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-s', '--sourcedir', type=str, help='Source dataset directory')
parser.add_argument('-m', '--mode', type=str, default='all', help='')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
# TGT_DIR = args.targetdir
MODE = args.mode



def __score_pearsonr__(X,y):
   corr = X.corrwith(y, axis=0, method='pearson').T
   return corr

def __score_spearmanr__(X,y):
    corr = X.corrwith(y, axis=0, method='spearman').T
    return corr

def __score_f_classif__(X,y):
   anova_scores = f_classif(X, y)
   return pd.Series(anova_scores[0], index=X.columns)

def __score_mutual_info_classif__(X,y):
   mutual_info_scores = mutual_info_classif(X, y)
   return pd.Series(mutual_info_scores, index=X.columns)

def __score_mutual_info_regression__(X,y):
    mutual_info_scores = mutual_info_regression(X, y)
    return pd.Series(mutual_info_scores, index=X.columns)

def __score_RFE_classification__(X,y):
   rfe = RFE(estimator=LogisticRegression(), n_features_to_select=1)
   rfe.fit(X, y)
   rfe_rank = rfe.ranking_
   return pd.Series(rfe_rank, index=X.columns)

def __score_RFE_regression__(X,y):
    rfe = RFE(estimator=RandomForestRegressor(), n_features_to_select=1)
    rfe.fit(X, y)
    rfe_rank = rfe.ranking_
    return pd.Series(rfe_rank, index=X.columns)


def __score_Lasso__(X,y):
   lasso = Lasso(alpha=0.1)
   lasso.fit(X, y)
   lasso_coef = lasso.coef_[0]
   return pd.Series(lasso_coef, index=X.columns)


def __score_SVR__(X,y):
    svr = SVR(kernel="linear")
    svr.fit(X, y)
    svr_coef = svr.coef_[0]
    return pd.Series(svr_coef, index=X.columns)

def __score_SVC__(X,y):
    svc = SVC(kernel="linear")
    svc.fit(X, y)
    svc_coef = svc.coef_[0]
    return pd.Series(svc_coef, index=X.columns)

def __score_Ridge__(X,y):
    ridge = Ridge(alpha=0.1)
    ridge.fit(X, y)
    ridge_coef = ridge.coef_[0]
    return pd.Series(ridge_coef, index=X.columns)

def __score_RidgeClassifier__(X,y):
    ridge = RidgeClassifier(alpha=0.1)
    ridge.fit(X, y)
    ridge_coef = ridge.coef_[0]
    return pd.Series(ridge_coef, index=X.columns)

def __score_RandomForestClassifier__(X,y):
   rf = RandomForestClassifier()
   rf.fit(X, y)
   rf_importances = rf.feature_importances_
   return pd.Series(rf_importances, index=X.columns)

def __score_RandomForestRegressor__(X,y):
    rf = RandomForestRegressor()
    rf.fit(X, y)
    rf_importances = rf.feature_importances_
    return pd.Series(rf_importances, index=X.columns)

def __score_LogisticRegression__(X,y):
    lr = LogisticRegression()
    lr.fit(X, y)
    lr_coef = lr.coef_[0]
    return pd.Series(lr_coef, index=X.columns)

def __score_LinearRegression__(X,y):
    lr = LinearRegression()
    lr.fit(X, y)
    lr_coef = lr.coef_[0]
    return pd.Series(lr_coef, index=X.columns)

def __score_PCA__(X,y):
   pca = PCA(n_components=1)
   X_scaled = StandardScaler().fit_transform(X)
   pca.fit(X_scaled, y)
   pca_importances = pca.components_
   return pd.Series(pca_importances, index=X.columns)

def __score_VarianceThreshold__(X,y=None):
   sel = VarianceThreshold(threshold=(.8 * (1 - .8)))
   sel.fit_transform(X)
   sel_importances = sel.variances_
   return pd.Series(sel_importances, index=X.columns)

METHODS_CLASSIF_DICT = {
    # 'Variance Threshold': __score_VarianceThreshold__,
    'Pearson': __score_pearsonr__,
    'Spearman': __score_spearmanr__,
    'ANOVA': __score_f_classif__,
    'Mutual Information': __score_mutual_info_classif__,
    # 'Lasso': __score_Lasso__,
    'Ridge': __score_RidgeClassifier__,
    'Logistic Regression': __score_LogisticRegression__,
    # 'Random Forest': __score_RandomForestClassifier__,
    # 'SVC': __score_SVC__,


}

METHODS_REGRESSION_DICT = {
    # 'Variance Threshold': __score_VarianceThreshold__,
    'Pearson': __score_pearsonr__,
    'Spearman': __score_spearmanr__,
    'Mutual Information': __score_mutual_info_regression__,
    # 'Ridge': __score_Ridge__,
    # 'Linear Regression': __score_LinearRegression__,
    'Random Forest': __score_RandomForestRegressor__,
    'SVR': __score_SVR__,

}

def get_feature_scores():
    """
    Usage:
        python3 08_features_scores.py -s ../07-data-compiled/dataset-ss0110-mnmx-7fg
    """
    # Load the dataset
    FEATURES,LABELS = load_dataset(SRC_DIR)
    FEATURES = FEATURES.dropna()
    FEATURES = FEATURES.T.drop_duplicates().T # Drop duplicate columns
    LABELS = LABELS.loc[FEATURES.index]

    for LABEL_NAME in LABELS.columns:
        if LABEL_NAME == 'W/L':
            METHOD_DICT = METHODS_CLASSIF_DICT
        else:
            METHOD_DICT = METHODS_REGRESSION_DICT
        METHD_SCORE_DF_DICT = {}
        TQDM_METHODS_DICT_ITEMS = tqdm(METHOD_DICT.items(),ncols=100)
        for METHOD_FUNC_NAME, METHOD_FUNC in TQDM_METHODS_DICT_ITEMS:
            TQDM_METHODS_DICT_ITEMS.set_description(f'Processing {LABEL_NAME} - {METHOD_FUNC_NAME}')
            X = FEATURES
            y = LABELS[LABEL_NAME]
            corr = METHOD_FUNC(X,y) 
            METHD_SCORE_DF_DICT[METHOD_FUNC_NAME] = corr
        FEATURES_SCORES = pd.concat(METHD_SCORE_DF_DICT.values(), axis=1, keys = METHD_SCORE_DF_DICT.keys())

        # FS_ABS_RANKED = FEATURES_SCORES.abs().rank(method='min',ascending=False)
        FS_ABS_RANKED = pd.DataFrame(RobustScaler().fit_transform(FEATURES_SCORES.abs()),
                                     index=FEATURES_SCORES.index,
                                     columns=FEATURES_SCORES.columns)
        # FS_ABS_RANKED = FEATURES_SCORES.abs().rank(method='min',ascending=False)
        FS_ABS_RANKED['mean'] = FS_ABS_RANKED.mean(axis=1)
        FS_ABS_RANKED = FS_ABS_RANKED.sort_values('mean',ascending=False)

        make_directory('/'.join([SRC_DIR,'features_scores']))
        make_directory('/'.join([SRC_DIR,'features_scores_ranked']))
        FEATURES_SCORES.to_csv('/'.join([SRC_DIR,'features_scores',f'{LABEL_NAME.replace("/","")}.csv']))
        FS_ABS_RANKED.to_csv('/'.join([SRC_DIR,'features_scores_ranked',f'{LABEL_NAME.replace("/","")}.csv']))


if __name__ == '__main__':
    get_feature_scores()
