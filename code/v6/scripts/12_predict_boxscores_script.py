import sys

from sklearn.preprocessing import StandardScaler
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
parser.add_argument('-s', '--sourcedir', type=str, help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, help='Target directory')
parser.add_argument('-m', '--mode', type=str, default='all', help='')

args = parser.parse_args()
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir
MODE = args.mode


def predict_boxscores_players_pts_total_by_era():
    """
    Usage:
        python3 12_predict_boxscores_script.py -m by-era -s ../07-data-compiled/03-boxscores-players-stats-1st-vs-2nd-half-1997-2023/ -t ../08-experiments/03-boxscores-players-stats-1st-vs-2nd-half-1997-2023/predict-players-pts-total/
    
    """
    DATA_DICT = load_all_df_from_dir(SRC_DIR,index_col=[0,1,2],header=[0,1])
    boxscores_players_1st_half = DATA_DICT['boxscores_players_1st_half']
    boxscores_players_2nd_half = DATA_DICT['boxscores_players_2nd_half']

    # Filter by minutes played
    MIN_H1_MP = 5; MIN_GM_MP = 20
    MP_FILTER = (boxscores_players_1st_half[('H1','mp')] >= MIN_H1_MP) & (boxscores_players_2nd_half[('GM','mp')] >= MIN_GM_MP)

    # Filter by appearances
    MIN_CAPS = 50
    player_appearances = boxscores_players_2nd_half[('GM','mp')].groupby('player_id').count()
    player_appearances = player_appearances[player_appearances >= MIN_CAPS]
    MIN_CAPS_FILTER = boxscores_players_2nd_half[('GM','mp')].index.get_level_values('player_id').isin(player_appearances.index)

    # Apply filters
    X_BXSC_PLYR = boxscores_players_1st_half.loc[(MP_FILTER & MIN_CAPS_FILTER)].drop(columns=['Opp_H1'])
    Y_BXSC_PLYR = boxscores_players_2nd_half.loc[(MP_FILTER & MIN_CAPS_FILTER),('GM','pts')]

    # Filter by year
    YEAR_FILTER = Y_BXSC_PLYR.index.to_frame()['team_id'].str[-9:-5].astype(int)
    # Predict 1997-2003 data
    X = {
        'by-era-1997-2009': X_BXSC_PLYR.loc[YEAR_FILTER<2010],
        'by-era-2010-2023': X_BXSC_PLYR.loc[YEAR_FILTER>=2010],
    }
    Y = {
        'by-era-1997-2009': Y_BXSC_PLYR.loc[YEAR_FILTER<2010],
        'by-era-2010-2023': Y_BXSC_PLYR.loc[YEAR_FILTER>=2010],
    }
    model_stack = ModelStackCV(models=ModelStackCV.MODELS_REGRESSION,model_params=ModelStackCV.MODEL_PARAMS_REGRESSION)
    predictions,scores = model_stack.run_experiment(
        X=X, y=Y, cv=3, scaler=StandardScaler(),score_names=ModelStackCV.SCORES_REGRESSION,
        save_dir = os.path.join(TGT_DIR,'by-era')
    )



def predict_boxscores_players_pts_total_by_individual():
    """
    Usage:
        python3 12_predict_boxscores_script.py -m by-players -s ../07-data-compiled/03-boxscores-players-stats-1st-vs-2nd-half-1997-2023/ -t ../08-experiments/03-boxscores-players-stats-1st-vs-2nd-half-1997-2023/predict-players-pts-total/

    """
    DATA_DICT = load_all_df_from_dir(SRC_DIR,index_col=[0,1,2],header=[0,1])
    boxscores_players_1st_half = DATA_DICT['boxscores_players_1st_half']
    boxscores_players_2nd_half = DATA_DICT['boxscores_players_2nd_half']

    # Filter by minutes played
    MIN_H1_MP = 5; MIN_GM_MP = 20
    MP_FILTER = (boxscores_players_1st_half[('H1','mp')] >= MIN_H1_MP) & (boxscores_players_2nd_half[('GM','mp')] >= MIN_GM_MP)

    # Filter by appearances
    MIN_CAPS = 50
    player_appearances = boxscores_players_2nd_half[('GM','mp')].groupby('player_id').count()
    player_appearances = player_appearances[player_appearances >= MIN_CAPS]
    MIN_CAPS_FILTER = boxscores_players_2nd_half[('GM','mp')].index.get_level_values('player_id').isin(player_appearances.index)

    # Apply filters
    X_BXSC_PLYR = boxscores_players_1st_half.loc[(MP_FILTER & MIN_CAPS_FILTER)].drop(columns=['Opp_H1'])
    Y_BXSC_PLYR = boxscores_players_2nd_half.loc[(MP_FILTER & MIN_CAPS_FILTER),('GM','pts')]

    # Predict by players
    X = { player_id:data for player_id,data in X_BXSC_PLYR.groupby('player_id')}
    Y = { player_id:data for player_id,data in Y_BXSC_PLYR.groupby('player_id')}
    model_stack = ModelStackCV(models=ModelStackCV.MODELS_REGRESSION,model_params=ModelStackCV.MODEL_PARAMS_REGRESSION)
    predictions,scores = model_stack.run_experiment(
        X=X, y=Y, cv=3, scaler=StandardScaler(),score_names=ModelStackCV.SCORES_REGRESSION,
        save_dir=os.path.join(TGT_DIR,'by-players')
    )

def predict_boxscores_players_pts_total_ou_by_pts_ou_level():
    """
    Usage:
        python3 12_predict_boxscores_script.py -m by-pts-ou -s ../07-data-compiled/03-boxscores-players-stats-1st-vs-2nd-half-1997-2023/ -t ../08-experiments/03-boxscores-players-stats-1st-vs-2nd-half-1997-2023/predict-players-pts-total/
    """
    DATA_DICT = load_all_df_from_dir(SRC_DIR,index_col=[0,1,2],header=[0,1])
    boxscores_players_1st_half = DATA_DICT['boxscores_players_1st_half']
    boxscores_players_2nd_half = DATA_DICT['boxscores_players_2nd_half']

    # Filter by minutes played
    MIN_H1_MP = 5; MIN_GM_MP = 20
    MP_FILTER = (boxscores_players_1st_half[('H1','mp')] >= MIN_H1_MP) & (boxscores_players_2nd_half[('GM','mp')] >= MIN_GM_MP)

    # Filter by appearances
    MIN_CAPS = 50
    player_appearances = boxscores_players_2nd_half[('GM','mp')].groupby('player_id').count()
    player_appearances = player_appearances[player_appearances >= MIN_CAPS]
    MIN_CAPS_FILTER = boxscores_players_2nd_half[('GM','mp')].index.get_level_values('player_id').isin(player_appearances.index)


    # Apply filters
    X_BXSC_PLYR = boxscores_players_1st_half.loc[MP_FILTER & MIN_CAPS_FILTER].drop(columns=['Opp_H1'])
    Y_BXSC_PLYR = boxscores_players_2nd_half.loc[(MP_FILTER & MIN_CAPS_FILTER),('GM','pts')]

    X_BXSC_PLYR = X_BXSC_PLYR.sample(frac=0.1,random_state=0)
    Y_BXSC_PLYR = Y_BXSC_PLYR.loc[X_BXSC_PLYR.index]
    # Save index
    X_BXSC_PLYR.index.to_frame().reset_index(drop=True).to_csv(os.path.join(TGT_DIR,'by-pts-ou','index.csv'))

    PTS_OU_LEVELS = [10.5,14.5,19.5,24.5]
    # Predict by players
    X = {f'pts_ou_{ou}':X_BXSC_PLYR[X_BXSC_PLYR[('H1','pts')]<ou] for ou in PTS_OU_LEVELS} # Select only players who scored less than the ou before the break
    Y = {f'pts_ou_{ou}':(Y_BXSC_PLYR[X_BXSC_PLYR[('H1','pts')]<ou]>ou).astype(int) for ou in PTS_OU_LEVELS} # Convert the ou to a binary classification problem
    model_stack = ModelStackCV(models=ModelStackCV.MODELS_CLASSIFICATION,model_params=ModelStackCV.MODEL_PARAMS_CLASSIFICATION)
    predictions,scores = model_stack.run_experiment(
        X=X, y=Y, cv=3, scaler=StandardScaler(),score_names=ModelStackCV.SCORES_CLASSIFICATION,
        save_dir=os.path.join(TGT_DIR,'by-pts-ou')
    )


if __name__ == '__main__':
    if args.mode == 'by-era':
        predict_boxscores_players_pts_total_by_era()
    elif args.mode == 'by-players':
        predict_boxscores_players_pts_total_by_individual()
    elif args.mode == 'by-pts-ou':
        predict_boxscores_players_pts_total_ou_by_pts_ou_level()
    else:
        raise ValueError('Invalid mode')




