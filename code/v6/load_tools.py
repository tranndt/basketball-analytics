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

def load_dataset(dataset_dir):
    # Load the dataset
    FEATURES = pd.read_csv(f'{dataset_dir}/features.csv', index_col=[0,1,2],header=[0,1,2])
    LABELS = pd.read_csv(f'{dataset_dir}/labels.csv', index_col=[0,1,2],header=[0,1]).droplevel(0,axis=1)
    return FEATURES, LABELS
