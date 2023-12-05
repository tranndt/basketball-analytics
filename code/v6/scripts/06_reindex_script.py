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
parser.add_argument('-s', '--sourcedir', type=str, default='../data-normalized/', help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, default='../06-data-normalized-reindexed/', help='Target directory')
parser.add_argument('-m', '--mode', type=str, default='all', help='')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir
MODE = args.mode

def __load_season_stats_from_dir__(directory):
    df = load_concat_df_from_dir(directory,index_col=[0,1],header=[0,1])
    return df

def __load_season_facts_from_dir__(directory):
    df = load_concat_df_from_dir(directory,index_col=[0,1],header=[0])
    return df

def __get_opp_idx__(IDX_DF,TM_IDX):
    return IDX_DF.loc[TM_IDX,'Opp']

def __get_team_opp_stats_row_df__(STATS_DF,IDX_DF,TM_IDX):
    OPP_IDX = __get_opp_idx__(IDX_DF,TM_IDX)
    TM_STATS_DF = STATS_DF.loc[TM_IDX]
    OPP_STATS_DF = STATS_DF.loc[OPP_IDX]
    TM_OPP_STATS_DF = pd.concat([TM_STATS_DF,OPP_STATS_DF],keys=['Team_Stats','Opponent_Stats']).to_frame().T
    TM_OPP_STATS_DF.index = pd.MultiIndex.from_tuples([TM_IDX],names=['index','Team_id'])
    return TM_OPP_STATS_DF

def get_team_opp_stats_df(STATS_DF,IDX_DF):
    TM_OPP_STATS_DF_LIST = []
    for TM_IDX in STATS_DF.index:
        TM_OPP_STATS_DF_LIST.append(__get_team_opp_stats_row_df__(STATS_DF,IDX_DF,TM_IDX))
    TM_OPP_STATS_DF = pd.concat(TM_OPP_STATS_DF_LIST,axis=0)
    return TM_OPP_STATS_DF

def __reindex_stats__(STATS_DF,IDX_DF):
    STATS_DF_SRC = STATS_DF.copy()
    STATS_DF_REIDX = STATS_DF.copy()
    STATS_DF_REIDX.loc[(-1,'-1'),:] = pd.NA
    IDX = pd.MultiIndex.from_tuples(IDX_DF, names=['index', 'Team_id'])
    STATS_DF_REIDX = STATS_DF_REIDX.loc[IDX].reset_index(col_level=1, col_fill='Source')
    STATS_DF_REIDX.index = STATS_DF_SRC.index
    return STATS_DF_REIDX

# Reindex all of the stats dataframes from a given season
def reindex_all_seasons_stats():
    """
    Description:
    ------------
    Reindex all of the stats dataframes from a given season

    Summary:
    --------
    1. Load the league season dictionary
    2. For each league season
        2.1. Load the index dictionary
        2.2. For each normalization type
            2.2.1. For each team game level type

    Usage:
    ------
    python3 06_reindex_script.py -s ../04-data-normalized/ -t ../06-data-normalized-reindexed/
    
    """
    LG_FACTS_DIR = '../00-data-facts/'
    LG_IDX_DIR = '../05-data-indexed/'
    LG_SS_HTML_DICT = load_league_seasons_dict(LG_FACTS_DIR)
    LG_SS_HTML_DICT_KEYS = list(LG_SS_HTML_DICT.keys())
    if debug:
        LG_SS_HTML_DICT_KEYS = LG_SS_HTML_DICT_KEYS[1:5]

    TQDM_LG_SS_HTML_DICT_KEYS = tqdm(LG_SS_HTML_DICT_KEYS,ncols=150) # Skip latest season
    for LG_SS_HTML in TQDM_LG_SS_HTML_DICT_KEYS:
        TQDM_LG_SS_HTML_DICT_KEYS.set_description(f'{LG_SS_HTML}')
        LG_SS_DIR  = parse_league_id(LG_SS_HTML)['body']
        TM_OPP_MN_IDX = load_index_dict(f'{LG_IDX_DIR}/{LG_SS_DIR}')['team_opp_main']

        for NORM_TYPE_DIR in ['norm_standard','norm_minmax','norm_robust','norm_ranking','unnorm']:
            for TGL_TYPE_DIR in get_all_folders(f'{SRC_DIR}/{LG_SS_DIR}'):
                HM_AGG_TYPE_DIR,AW_AGG_TYPE_DIR = [],[]
                for AGG_TYPE_DIR in get_all_folders(f'{SRC_DIR}/{LG_SS_DIR}/{TGL_TYPE_DIR}'):
                    if 'hm' in AGG_TYPE_DIR:
                        HM_AGG_TYPE_DIR.append(AGG_TYPE_DIR)
                    elif 'aw' in AGG_TYPE_DIR:
                        AW_AGG_TYPE_DIR.append(AGG_TYPE_DIR)
                    elif 'facts' in AGG_TYPE_DIR:
                        TGL_FACTS_DF_REIDX = __load_season_facts_from_dir__('/'.join([SRC_DIR,LG_SS_DIR,TGL_TYPE_DIR,AGG_TYPE_DIR,'facts']))
                        make_directory('/'.join([TGT_DIR,LG_SS_DIR]))
                        TGL_REIDX_FNAME = f'{AGG_TYPE_DIR}_{TGL_TYPE_DIR}.csv'
                        TGL_FACTS_DF_REIDX.to_csv('/'.join([TGT_DIR,LG_SS_DIR,TGL_REIDX_FNAME]),index=True)
                    else:
                        TGL_STATS_AGG_NORM_DF = __load_season_stats_from_dir__('/'.join([SRC_DIR,LG_SS_DIR,TGL_TYPE_DIR,AGG_TYPE_DIR,NORM_TYPE_DIR]))
                        TGL_STATS_AGG_NORM_DF_REIDX = __reindex_stats__(TGL_STATS_AGG_NORM_DF,TM_OPP_MN_IDX['Team_Prev_Gm_01'])
                        make_directory('/'.join([TGT_DIR,LG_SS_DIR]))
                        TGL_REIDX_FNAME = f'{NORM_TYPE_DIR}_{TGL_TYPE_DIR}_{AGG_TYPE_DIR}.csv'
                        TGL_STATS_AGG_NORM_DF_REIDX.to_csv('/'.join([TGT_DIR,LG_SS_DIR,TGL_REIDX_FNAME]),index=True)
                for TGL_HM_TYPE, TGL_AW_TYPE in list(zip(sorted(HM_AGG_TYPE_DIR),sorted(AW_AGG_TYPE_DIR))):
                    TGL_HM_STATS_AGG_NORM_DF = __load_season_stats_from_dir__('/'.join([SRC_DIR,LG_SS_DIR,TGL_TYPE_DIR,TGL_HM_TYPE,NORM_TYPE_DIR]))
                    TGL_AW_STATS_AGG_NORM_DF = __load_season_stats_from_dir__('/'.join([SRC_DIR,LG_SS_DIR,TGL_TYPE_DIR,TGL_AW_TYPE,NORM_TYPE_DIR]))
                    TGL_VEN_STATS_AGG_NORM_DF = pd.concat([TGL_HM_STATS_AGG_NORM_DF,TGL_AW_STATS_AGG_NORM_DF],axis=0).sort_index()
                    TGL_VEN_STATS_AGG_NORM_DF_REIDX = __reindex_stats__(TGL_VEN_STATS_AGG_NORM_DF,TM_OPP_MN_IDX['Team_Ven_Prev_Gm_01'])
                    TGL_VEN_REIDX_FNAME = f'{NORM_TYPE_DIR}_{TGL_TYPE_DIR}_{TGL_HM_TYPE.replace("hm","ven")}.csv'
                    make_directory('/'.join([TGT_DIR,LG_SS_DIR]))
                    TGL_VEN_STATS_AGG_NORM_DF_REIDX.to_csv('/'.join([TGT_DIR,LG_SS_DIR,TGL_VEN_REIDX_FNAME]),index=True)

if __name__ == '__main__':
    if MODE == 'all':

        reindex_all_seasons_stats()
    else:
        print(f'Unknown mode: {MODE}')