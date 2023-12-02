import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
import time
from tqdm import tqdm
import argparse
import warnings
from pandas.errors import PerformanceWarning
pd.options.mode.use_inf_as_na = True
warnings.filterwarnings('ignore', category=PerformanceWarning)

parser = argparse.ArgumentParser(description='Normalize basketball-reference.com data')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-s', '--sourcedir', type=str, default='../data-parsed/', help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, default='../data-indexed/', help='Target directory')
parser.add_argument('-m', '--mode', type=str, default='all', help='')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir
MODE = args.mode


def parse_matchday_team_opponent_games_index(TM_SS_HTML_LIST):
    # LG_SS_DIR = parse_league_id(LG_SS_HTML)['body']
    TGL_BASIC_INFO_DF_LIST = []
    for TM_SS_HTML in TM_SS_HTML_LIST:
        TM_SS_DIR = parse_team_season_id(TM_SS_HTML)['body'] # teams/BOS/2023
        TGL_BASIC_DF = pd.read_csv(f'{SRC_DIR}/{TM_SS_DIR}/tgl_basic.csv',header=[0,1]).rename(columns={'Unnamed: 0_level_0':'Match','Unnamed: 0_level_1':'index'})['Match']
        TGL_BASIC_DF = TGL_BASIC_DF.set_index('Boxscores_html_id',drop=False).rename(columns={'Tm_html_id':'Team_id','Boxscores_html_id':'Boxscores_id'})[['index','Team_id','H/A','Boxscores_id']]
        TGL_BASIC_INFO_DF_LIST.append(TGL_BASIC_DF)
    TM_MDAY_IDX_DF = pd.concat(TGL_BASIC_INFO_DF_LIST).sort_index(axis=0)

    TGL_BASIC_INFO_DF_LIST = []
    for BS_INDEX in sorted(pd.unique(TM_MDAY_IDX_DF.index)):
        BS_TM_DF = TM_MDAY_IDX_DF.loc[BS_INDEX]
        TGL_BASIC_INFO_DF_LIST.append(pd.concat([BS_TM_DF,BS_TM_DF.iloc[::-1]],axis=1,keys=['Team','Opp']))
        
    TM_OPP_GM_IDX_DF = pd.concat(TGL_BASIC_INFO_DF_LIST)
    TM_OPP_GM_IDX_DF.set_index(pd.MultiIndex.from_frame(TM_OPP_GM_IDX_DF['Team']),inplace=True,drop=False)
    DUMMY_IDX = pd.DataFrame([[-1]*len(TM_OPP_GM_IDX_DF.columns)],
                            columns=TM_OPP_GM_IDX_DF.columns,
                            index=pd.MultiIndex.from_tuples([(-1,-1,-1,-1)],
                            names=['index','Team_id','H/A','Boxscores_id']))
    TM_OPP_GM_IDX_DF = pd.concat([DUMMY_IDX,TM_OPP_GM_IDX_DF]).sort_index(axis=0)
    return TM_OPP_GM_IDX_DF

def parse_team_previous_games_index(TM_OPP_GM_IDX_DF):
    TM_GM_IDX_DF = TM_OPP_GM_IDX_DF.loc[:,('Team',slice(None))].copy()
    TM_PREV_GM_IDX_DF = []
    for team in set(pd.unique(TM_GM_IDX_DF[('Team','Team_id')])).difference([-1]):
        SRC_TM_GM_IDX_SUB_DF        = TM_GM_IDX_DF.loc[(slice(None),team),:]
        if len(SRC_TM_GM_IDX_SUB_DF) == 0:
            continue
        TRF_TM_GM_IDX_SUB_DF_LIST   = [SRC_TM_GM_IDX_SUB_DF.rename(columns={'Team':f'Team_Curr_Gm'})]
        for i in range(1,len(SRC_TM_GM_IDX_SUB_DF)):
            GM_NO = f'0{i}' if i < 10 else f'{i}'
            TM_GM_IDX_SHFTD_DF_I = SRC_TM_GM_IDX_SUB_DF.copy().shift(i,fill_value=-1) 
            TM_GM_IDX_SHFTD_DF_I.rename(columns={'Team':f'Team_Prev_Gm_{GM_NO}'},inplace=True)
            TRF_TM_GM_IDX_SUB_DF_LIST.append(TM_GM_IDX_SHFTD_DF_I)
        TM_GM_IDX_DF_PER_TM = pd.concat(TRF_TM_GM_IDX_SUB_DF_LIST,axis=1)
        TM_PREV_GM_IDX_DF.append(TM_GM_IDX_DF_PER_TM)

    TM_PREV_GM_IDX_DF = pd.concat(TM_PREV_GM_IDX_DF).fillna(-1).sort_index(axis=0)
    for i,col in enumerate(TM_PREV_GM_IDX_DF.columns):
        if col[1] in ['index','H/A']:
            INT_COL = TM_PREV_GM_IDX_DF.pop(col).astype(int)
            TM_PREV_GM_IDX_DF.insert(i,col,INT_COL)
    return TM_PREV_GM_IDX_DF

def parse_team_previous_opponents_index(TM_OPP_GM_IDX_DF,TM_PREV_GM_IDX_DF):
    OPP_IDX_FACTS_DF = TM_OPP_GM_IDX_DF.loc[:,('Opp',slice(None))].copy()
    TM_PREV_OPP_IDX_DF = []
    for col in TM_PREV_GM_IDX_DF.columns.levels[0]:
        OPP_IDX = OPP_IDX_FACTS_DF.loc[pd.MultiIndex.from_frame(TM_PREV_GM_IDX_DF[col])]
        OPP_IDX.index = TM_PREV_GM_IDX_DF.index
        OPP_IDX.rename(columns={'Opp':col.replace('Gm','Gm_Opp')},inplace=True)
        TM_PREV_OPP_IDX_DF.append(OPP_IDX)
    TM_PREV_OPP_IDX_DF = pd.concat(TM_PREV_OPP_IDX_DF,axis=1).fillna(-1).sort_index(axis=0)
    for i,col in enumerate(TM_PREV_OPP_IDX_DF.columns):
        if col[1] in ['index','H/A']:
            INT_COL = TM_PREV_OPP_IDX_DF.pop(col).astype(int)
            TM_PREV_OPP_IDX_DF.insert(i,col,INT_COL)
    return TM_PREV_OPP_IDX_DF

def parse_team_venue_previous_games_index(TM_OPP_GM_IDX_DF):
    TM_GM_IDX_DF = TM_OPP_GM_IDX_DF.loc[:,('Team',slice(None))].copy()
    TM_VEN_PREV_GM_IDX_DF_LIST = []
    for TM in set(pd.unique(TM_GM_IDX_DF[('Team','Team_id')])).difference([-1]):
        for VEN in [0,1]:
            TM_VEN_PREV_GM_IDX_SUBDF = TM_GM_IDX_DF.loc[(slice(None),TM,VEN,slice(None)),:]
            TM_PREV_VEN_GM_IDX_SUBDF_LIST = [TM_VEN_PREV_GM_IDX_SUBDF.rename(columns={'Team':f'Team_Curr_Gm'})]
            for i in range(1,len(TM_VEN_PREV_GM_IDX_SUBDF)):
                TM_VEN_PREV_GM_IDX_SUBDF_I = TM_VEN_PREV_GM_IDX_SUBDF.copy().shift(i,fill_value=-1) 
                GM_NO = f'0{i}' if i < 10 else f'{i}'
                TM_VEN_PREV_GM_IDX_SUBDF_I.rename(columns={'Team':f'Team_Ven_Prev_Gm_{GM_NO}'},inplace=True)
                TM_PREV_VEN_GM_IDX_SUBDF_LIST.append(TM_VEN_PREV_GM_IDX_SUBDF_I)
            TM_VEN_PREV_GM_IDX_SUBDF = pd.concat(TM_PREV_VEN_GM_IDX_SUBDF_LIST,axis=1)
            TM_VEN_PREV_GM_IDX_DF_LIST.append(TM_VEN_PREV_GM_IDX_SUBDF)
    TM_VEN_PREV_GM_IDX_DF = pd.concat(TM_VEN_PREV_GM_IDX_DF_LIST).fillna(-1).sort_index(axis=0)
    for i,col in enumerate(TM_VEN_PREV_GM_IDX_DF.columns):
        if col[1] in ['index','H/A']:
            INT_COL = TM_VEN_PREV_GM_IDX_DF.pop(col).astype(int)
            TM_VEN_PREV_GM_IDX_DF.insert(i,col,INT_COL)
    return TM_VEN_PREV_GM_IDX_DF


def parse_team_opponent_previous_h2h_index(TM_OPP_GM_IDX_DF):
    TEAMS = set(pd.unique(TM_OPP_GM_IDX_DF[('Team','Team_id')])).difference([-1])
    TM_OPP_H2H_IDX_DF_LIST = []
    for TM_ID in TEAMS:
        for OPP_ID in TEAMS:
            MATCH_UP_FILTER = (TM_OPP_GM_IDX_DF[('Team','Team_id')] == TM_ID) & (TM_OPP_GM_IDX_DF[('Opp','Team_id')] == OPP_ID)
            TM_OPP_H2H_SUBSET_DF  =  TM_OPP_GM_IDX_DF[MATCH_UP_FILTER].sort_index()
            if len(TM_OPP_H2H_SUBSET_DF) == 0:
                continue
            TM_OPP_H2H_SUBSET_DF_SHFTD_LIST  = [TM_OPP_H2H_SUBSET_DF.rename(columns={'Team':'Team_Curr_H2H_Gm','Opp':'Opp_Curr_H2H_Gm'})]
            for i in range(1,len(TM_OPP_H2H_SUBSET_DF)):
                TM_OPP_H2H_SUBSET_DF_SHFTD = TM_OPP_H2H_SUBSET_DF.shift(i,fill_value=-1)
                GM_NO = f'0{i}' if i < 10 else f'{i}'
                TM_OPP_H2H_SUBSET_DF_SHFTD.rename(columns={'Team':f'Team_Prev_H2H_Gm_{GM_NO}','Opp':f'Opp_Prev_H2H_Gm_{GM_NO}'},inplace=True)
                TM_OPP_H2H_SUBSET_DF_SHFTD_LIST.append(TM_OPP_H2H_SUBSET_DF_SHFTD)
            TM_IDX_H2H_FACTS_SHIFTED_DF = pd.concat(TM_OPP_H2H_SUBSET_DF_SHFTD_LIST,axis=1).fillna(-1)
            TM_OPP_H2H_IDX_DF_LIST.append(TM_IDX_H2H_FACTS_SHIFTED_DF)
    TM_OPP_PREV_H2H_IDX_DF = pd.concat(TM_OPP_H2H_IDX_DF_LIST).fillna(-1).sort_index(axis=0)
    for i,col in enumerate(TM_OPP_PREV_H2H_IDX_DF.columns):
        if col[1] in ['index','H/A']:
            INT_COL = TM_OPP_PREV_H2H_IDX_DF.pop(col).astype(int)
            TM_OPP_PREV_H2H_IDX_DF.insert(i,col,INT_COL)
    # Split into a Team and Opp DF
    TM_COLS = [col for col in TM_OPP_PREV_H2H_IDX_DF.columns if col[0].startswith('Team')]
    OPP_COLS = [col for col in TM_OPP_PREV_H2H_IDX_DF.columns if col[0].startswith('Opp')]
    TM_PREV_H2H_IDX_DF = TM_OPP_PREV_H2H_IDX_DF[TM_COLS]
    OPP_PREV_H2H_IDX_DF = TM_OPP_PREV_H2H_IDX_DF[OPP_COLS]
    return TM_PREV_H2H_IDX_DF,OPP_PREV_H2H_IDX_DF

def parse_opponent_previous_games_index(TM_OPP_GM_IDX_DF,TM_PREV_VEN_GM_IDX_DF):
    DUMMY_IDX_VAL = (-1,-1,-1,-1)
    OPP_IDX_FACTS_DF = TM_OPP_GM_IDX_DF.loc[:,('Opp',slice(None))].drop([DUMMY_IDX_VAL]).copy()
    OPP_PREV_GM_IDX_DF = TM_PREV_VEN_GM_IDX_DF.loc[pd.MultiIndex.from_frame(OPP_IDX_FACTS_DF)]
    OPP_PREV_GM_IDX_DF.index = TM_PREV_VEN_GM_IDX_DF.index

    ORG_COL_NAMES = OPP_PREV_GM_IDX_DF.columns.levels[0]
    NEW_COL_NAMES = [col_name.replace('Team','Opp') for col_name in ORG_COL_NAMES]
    OPP_PREV_GM_IDX_DF.rename(columns=dict(zip(ORG_COL_NAMES,NEW_COL_NAMES)),inplace=True)
    return OPP_PREV_GM_IDX_DF

def parse_opponent_previous_opponents_index(TM_OPP_GM_IDX_DF,TM_PREV_OPP_IDX_DF):
    DUMMY_IDX_VAL = (-1,-1,-1,-1)
    OPP_IDX_FACTS_DF = TM_OPP_GM_IDX_DF.loc[:,('Opp',slice(None))].drop([DUMMY_IDX_VAL]).copy()
    OPP_PREV_OPP_IDX_DF         = TM_PREV_OPP_IDX_DF.loc[pd.MultiIndex.from_frame(OPP_IDX_FACTS_DF)].copy()
    OPP_PREV_OPP_IDX_DF.index   = TM_PREV_OPP_IDX_DF.index

    ORG_COL_NAMES = TM_PREV_OPP_IDX_DF.columns.levels[0]
    NEW_COL_NAMES = [col_name.replace('Team','Opp') for col_name in ORG_COL_NAMES]
    OPP_PREV_OPP_IDX_DF.rename(columns=dict(zip(ORG_COL_NAMES,NEW_COL_NAMES)),inplace=True)
    return OPP_PREV_OPP_IDX_DF

def parse_opponent_venue_previous_games_index(TM_OPP_GM_IDX_DF,TM_PREV_VEN_GM_IDX_DF):
    DUMMY_IDX_VAL = (-1,-1,-1,-1)
    OPP_IDX_FACTS_DF = TM_OPP_GM_IDX_DF.loc[:,('Opp',slice(None))].drop([DUMMY_IDX_VAL]).copy()
    OPP_VEN_PREV_GM_IDX_DF = TM_PREV_VEN_GM_IDX_DF.loc[pd.MultiIndex.from_frame(OPP_IDX_FACTS_DF)]
    OPP_VEN_PREV_GM_IDX_DF.index = TM_PREV_VEN_GM_IDX_DF.index
    ORG_COL_NAMES = OPP_VEN_PREV_GM_IDX_DF.columns.levels[0]
    NEW_COL_NAMES = [col_name.replace('Team','Opp') for col_name in ORG_COL_NAMES]
    OPP_VEN_PREV_GM_IDX_DF.rename(columns=dict(zip(ORG_COL_NAMES,NEW_COL_NAMES)),inplace=True)
    return OPP_VEN_PREV_GM_IDX_DF


def parse_all_index():
    """
    Description:
    ------------
    Parse all index files

    Summary:
    --------
    Parse all of the following index files:
    - team_opp_games_index.csv
    - team_prev_games_index.csv
    - team_prev_opp_index.csv
    - team_ven_prev_index.csv
    - team_prev_h2h_index.csv
    - opp_prev_games_index.csv
    - opp_prev_opp_index.csv
    - opp_ven_prev_index.csv
    - opp_prev_h2h_index.csv

    Usage:
    ------
    python3 05_indexing_script.py -m all -s ../data-parsed/ -t ../data-indexed/

    """
    LG_SS_HTML_DICT_STR = load_file(f'{SRC_DIR}/league_seasons_html.txt')
    LG_SS_HTML_DICT = ast.literal_eval(LG_SS_HTML_DICT_STR)
    TQDM_LG_SS_HTML_DICT_KEYS = tqdm(list(LG_SS_HTML_DICT.keys()),ncols=150)
    for LG_SS_HTML in TQDM_LG_SS_HTML_DICT_KEYS:
        TQDM_LG_SS_HTML_DICT_KEYS.set_description(f'{LG_SS_HTML}')
        TM_SS_HTML_LIST = LG_SS_HTML_DICT[LG_SS_HTML]
        TM_OPP_GM_IDX_DF        = parse_matchday_team_opponent_games_index(TM_SS_HTML_LIST)
        TM_PREV_GM_IDX_DF       = parse_team_previous_games_index(TM_OPP_GM_IDX_DF)
        TM_PREV_OPP_IDX_DF      = parse_team_previous_opponents_index(TM_OPP_GM_IDX_DF,TM_PREV_GM_IDX_DF)
        TM_VEN_PREV_GM_IDX_DF   = parse_team_venue_previous_games_index(TM_OPP_GM_IDX_DF)
        OPP_PREV_GM_IDX_DF      = parse_opponent_previous_games_index(TM_OPP_GM_IDX_DF,TM_PREV_GM_IDX_DF)
        OPP_PREV_OPP_IDX_DF     = parse_opponent_previous_opponents_index(TM_OPP_GM_IDX_DF,TM_PREV_OPP_IDX_DF)
        OPP_VEN_PREV_GM_IDX_DF  = parse_opponent_venue_previous_games_index(TM_OPP_GM_IDX_DF,TM_VEN_PREV_GM_IDX_DF)
        TM_PREV_H2H_IDX_DF,OPP_PREV_H2H_IDX_DF = parse_team_opponent_previous_h2h_index(TM_OPP_GM_IDX_DF)
        
        # Clean up the index
        TM_OPP_GM_IDX_DF = TM_OPP_GM_IDX_DF.drop((-1,-1,-1,-1))
        TM_PREV_GM_IDX_DF = TM_PREV_GM_IDX_DF.droplevel([2,3],axis=0).drop(columns=['H/A','Boxscores_id'],level=1)
        TM_PREV_OPP_IDX_DF = TM_PREV_OPP_IDX_DF.droplevel([2,3],axis=0).drop(columns=['H/A','Boxscores_id'],level=1)
        TM_VEN_PREV_GM_IDX_DF = TM_VEN_PREV_GM_IDX_DF.droplevel([2,3],axis=0).drop(columns=['H/A','Boxscores_id'],level=1)
        TM_PREV_H2H_IDX_DF = TM_PREV_H2H_IDX_DF.droplevel([2,3],axis=0).drop(columns=['H/A','Boxscores_id'],level=1)
        OPP_PREV_GM_IDX_DF = OPP_PREV_GM_IDX_DF.droplevel([2,3],axis=0).drop(columns=['H/A','Boxscores_id'],level=1)
        OPP_PREV_OPP_IDX_DF = OPP_PREV_OPP_IDX_DF.droplevel([2,3],axis=0).drop(columns=['H/A','Boxscores_id'],level=1)
        OPP_VEN_PREV_GM_IDX_DF = OPP_VEN_PREV_GM_IDX_DF.droplevel([2,3],axis=0).drop(columns=['H/A','Boxscores_id'],level=1)
        OPP_PREV_H2H_IDX_DF = OPP_PREV_H2H_IDX_DF.droplevel([2,3],axis=0).drop(columns=['H/A','Boxscores_id'],level=1)

        # Save the index
        LG_SS_DIR = parse_league_id(LG_SS_HTML)['body']
        make_directory(f'{TGT_DIR}/{LG_SS_DIR}')
        TM_OPP_GM_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/team_opp_games_index.csv',index=True)
        TM_PREV_GM_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/team_prev_games_index.csv',index=True)
        TM_PREV_OPP_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/team_prev_opp_index.csv',index=True)
        TM_VEN_PREV_GM_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/team_ven_prev_index.csv',index=True)
        TM_PREV_H2H_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/team_prev_h2h_index.csv',index=True)
        OPP_PREV_GM_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/opp_prev_games_index.csv',index=True)
        OPP_PREV_OPP_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/opp_prev_opp_index.csv',index=True)
        OPP_VEN_PREV_GM_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/opp_ven_prev_index.csv',index=True)
        OPP_PREV_H2H_IDX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/opp_prev_h2h_index.csv',index=True)

# Run the script
if __name__ == '__main__':
    if MODE == 'all':
        parse_all_index()
    else:
        print(f'Unknown mode: {MODE}')

