import pandas as pd
import numpy as np
import sys
import os
import bs4
from IPython.display import display_html,clear_output, HTML
import re
from datetime import datetime
import ast
import itertools
from tqdm import tqdm,trange
from file_tools import *
from request_tools import *
from parse_tools import *



def load_index_df(filename):
    if filename.endswith('full_index.csv'):
        IDX_DF_SRC = pd.read_csv(filename,index_col=[0,1,2,3],header=[0,1])
    else:
        IDX_DF_SRC = pd.read_csv(filename,index_col=[0,1],header=[0,1])
    IDX_DF = pd.DataFrame(index=IDX_DF_SRC.index)
    for col in IDX_DF_SRC.columns.levels[0]:
        IDX_DF[col] = list(zip(IDX_DF_SRC[col]['index'],IDX_DF_SRC[col]['Team_id']))
    return IDX_DF

def load_all_index_df_of_type(idx_directory,idx_type='team_opp_main_index.csv'):
    all_idx_df_dict = {}
    for league in get_all_folders(idx_directory):
        for season in get_all_folders('/'.join([idx_directory,league])):
            for filename in get_all_files('/'.join([idx_directory,league,season]),file_type=idx_type):
                idx_df = load_index_df('/'.join([idx_directory,league,season,filename]))
                all_idx_df_dict[f'/{league}/{season}.html'] = idx_df
    all_idx_df = pd.concat(all_idx_df_dict.values(),keys=all_idx_df_dict.keys(),axis=0).sort_index()
    return all_idx_df

def load_index_dict(directory):
    IDX_DICT = {}
    for filename in os.listdir(directory):
        if filename.endswith('_index.csv'):
            IDX_DICT[filename.replace('_index.csv','')] = load_index_df(os.path.join(directory,filename))
    return IDX_DICT

def load_league_seasons_dict(directory):
    LG_SS_HTML_DICT_STR = load_file(f'{directory}/league_seasons_html.txt')
    LG_SS_HTML_DICT = ast.literal_eval(LG_SS_HTML_DICT_STR)
    return LG_SS_HTML_DICT

def load_concat_df_from_dir(directory,**kwargs):
    df_list = []
    for filename in get_all_files(directory,'.csv'):
        df_i = pd.read_csv(os.path.join(directory,filename),**kwargs)
        df_list.append(df_i)
    df = pd.concat(df_list,axis=0)
    return df

def load_all_df_from_dir(directory,**kwargs):
    df_dict = {}
    for filename in get_all_files(directory,'.csv'):
        df_i = pd.read_csv(os.path.join(directory,filename),**kwargs)
        df_dict[filename.replace('.csv','')] = df_i
    # df = pd.concat(df_list,axis=0)
    return df_dict

def load_dataset(dataset_dir):
    # Load the dataset
    FEATURES = pd.read_csv(f'{dataset_dir}/features.csv', index_col=[0,1,2],header=[0,1,2])
    LABELS = pd.read_csv(f'{dataset_dir}/labels.csv', index_col=[0,1,2],header=[0,1]).droplevel(0,axis=1)
    return FEATURES, LABELS


def get_opp_stats_row_df(STATS_DF,IDX_DF,TM_IDX):
    OPP_IDX         = IDX_DF.loc[TM_IDX]
    OPP_STATS_DF    = STATS_DF.loc[OPP_IDX].to_frame().T
    OPP_STATS_DF.index = pd.MultiIndex.from_tuples([TM_IDX],names=['index','Team_id'])
    return OPP_STATS_DF

def get_opp_stats_df(STATS_DF,IDX_DF):
    OPP_STATS_DF_LIST = []
    for TM_IDX in STATS_DF.index:
        OPP_STATS_DF_LIST.append(get_opp_stats_row_df(STATS_DF,IDX_DF,TM_IDX))
    OPP_STATS_DF = pd.concat(OPP_STATS_DF_LIST,axis=0)
    return OPP_STATS_DF


def get_predictions_validation_set(preds):
    y_preds = preds.copy().T.drop_duplicates(keep='first').T
    y_true = y_preds[y_preds.columns[y_preds.columns.get_level_values(-2).isin(['y_true'])]]
    is_Val = y_preds[y_preds.columns[y_preds.columns.get_level_values(-2).isin(['is_Val'])]]
    y_preds = y_preds.drop(columns=['y_true','is_Val'],level=-2)

    y_preds_val = pd.DataFrame(index=y_preds.index,columns=y_preds.columns.droplevel(-1).unique())
    for column_indexer in y_preds_val.columns.unique():
        y_preds_val[column_indexer] = y_preds[column_indexer].mul(is_Val.values,axis=0).sum(axis=1)
    y_preds_val.insert(0,'y_true',y_true)
    return y_preds_val