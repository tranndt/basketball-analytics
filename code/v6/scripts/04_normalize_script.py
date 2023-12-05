import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
from load_tools import *
import time
from tqdm import tqdm
import argparse

# Filter Runtime Warnings
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

parser = argparse.ArgumentParser(description='Normalize basketball-reference.com data')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-s', '--sourcedir', type=str, default='../03-data-aggregated/', help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, default='../04-data-normalized/', help='Target directory')
parser.add_argument('-m', '--mode', type=str, default='all', help='')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir
MODE = args.mode

def normalize_gamelogs_stats_regular_season():
    """
    Description:
        Normalize gamelog stats relative to the current season, organized by round
    Summary:

    Usage:
        python3 04_normalize_script.py -s ../03-data-aggregated/ -t ../04-data-normalized/
    
    """
    # Load list of league seasons
    LG_FACTS_DIR = '../00-data-facts/'

    LG_SS_HTML_DICT = load_league_seasons_dict(LG_FACTS_DIR)
    if not LG_SS_HTML_DICT:
        print('league_seasons_html.txt not found. Please scrape it first.')
        return

    # For every league_season, get all team_seasons belonging to the league
    TQDM_LG_SS_HTML_DICT = tqdm(list(LG_SS_HTML_DICT.items()),position=0, leave=True,ncols=125)
    for LG_SS_HTML, LG_TM_HTML_LIST in TQDM_LG_SS_HTML_DICT:
        TQDM_LG_SS_HTML_DICT.set_description(f'{LG_SS_HTML}')
        LG_SS_DIR = parse_league_id(LG_SS_HTML)['body']
        # Normalize these stats type by league round
        for TGL_STATS_TYPE in [ 
            'tgl_basic/stats_cumu_avg', 'tgl_basic/stats_roll_04_avg','tgl_basic/stats_roll_08_avg', 
            'tgl_basic/stats_roll_12_avg', 'tgl_basic/stats_roll_16_avg', 'tgl_basic/stats_roll_20_avg',
            'tgl_basic/stats_hm_cumu_avg', 'tgl_basic/stats_hm_roll_04_avg','tgl_basic/stats_hm_roll_08_avg',
            'tgl_basic/stats_hm_roll_12_avg', 'tgl_basic/stats_hm_roll_16_avg', 'tgl_basic/stats_hm_roll_20_avg',
            'tgl_basic/stats_aw_cumu_avg',  'tgl_basic/stats_aw_roll_04_avg','tgl_basic/stats_aw_roll_08_avg',
            'tgl_basic/stats_aw_roll_12_avg', 'tgl_basic/stats_aw_roll_16_avg', 'tgl_basic/stats_aw_roll_20_avg',
            # 'tgl_basic/stats_h2h_cumu_avg',
            'tgl_advanced/stats_cumu_avg', 'tgl_advanced/stats_roll_04_avg','tgl_advanced/stats_roll_08_avg',
            'tgl_advanced/stats_roll_12_avg', 'tgl_advanced/stats_roll_16_avg', 'tgl_advanced/stats_roll_20_avg',
            'tgl_advanced/stats_hm_cumu_avg', 'tgl_advanced/stats_hm_roll_04_avg','tgl_advanced/stats_hm_roll_08_avg',
            'tgl_advanced/stats_hm_roll_12_avg', 'tgl_advanced/stats_hm_roll_16_avg', 'tgl_advanced/stats_hm_roll_20_avg',
            'tgl_advanced/stats_aw_cumu_avg',  'tgl_advanced/stats_aw_roll_04_avg','tgl_advanced/stats_aw_roll_08_avg',
            'tgl_advanced/stats_aw_roll_12_avg', 'tgl_advanced/stats_aw_roll_16_avg', 'tgl_advanced/stats_aw_roll_20_avg',
            # 'tgl_advanced/stats_h2h_cumu_avg',
        ]:
            # Get the corresponding season gamelogs stats for each team belonging to the league
            LG_TGL_STATS_PER_TM_LIST = []
            for TM_SS_HTML_ID in LG_TM_HTML_LIST:
                TM_SS_DIR = parse_team_season_id(TM_SS_HTML_ID)['body']
                TGL_STATS_DF = pd.read_csv(f'{SRC_DIR}/{TM_SS_DIR}/{TGL_STATS_TYPE}.csv',header=[0,1],index_col=[0,1])
                LG_TGL_STATS_PER_TM_LIST.append(TGL_STATS_DF)

            # Create a table for each round in the league season
            make_directory(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/unnorm')
            make_directory(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/norm_minmax')
            make_directory(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/norm_standard')
            make_directory(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/norm_robust')
            make_directory(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/norm_ranking')
            for RD_INDEX in range(max([len(i) for i in LG_TGL_STATS_PER_TM_LIST])):
                LG_TGL_STATS_PER_RD_DF = []
                for TGL_STATS_TM in LG_TGL_STATS_PER_TM_LIST:
                    if RD_INDEX >= len(TGL_STATS_TM):
                        continue
                    RD_DF = TGL_STATS_TM.iloc[RD_INDEX].to_frame().T
                    RD_DF.index.names = ['index','Team_id']    
                    LG_TGL_STATS_PER_RD_DF.append(RD_DF)
                LG_TGL_STATS_PER_RD_DF = pd.concat(LG_TGL_STATS_PER_RD_DF,axis=0)
                LG_TGL_STATS_PER_RD_NORM_MNMX_DF  = __normalize_league_gamelogs_stats_minmax__(LG_TGL_STATS_PER_RD_DF)
                LG_TGL_STATS_PER_RD_NORM_STD_DF   = __normalize_league_gamelogs_stats_standard__(LG_TGL_STATS_PER_RD_DF)
                LG_TGL_STATS_PER_RD_NORM_RBST_DF  = __normalize_league_gamelogs_stats_robust__(LG_TGL_STATS_PER_RD_DF)
                LG_TGL_STATS_PER_RD_NORM_RANK_DF  = __normalize_league_gamelogs_stats_ranking__(LG_TGL_STATS_PER_RD_DF)

                # Save each df
                RD_NM = f'{RD_INDEX:02d}'
                LG_TGL_STATS_PER_RD_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/unnorm/{RD_NM}.csv')
                LG_TGL_STATS_PER_RD_NORM_MNMX_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/norm_minmax/{RD_NM}.csv')
                LG_TGL_STATS_PER_RD_NORM_STD_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/norm_standard/{RD_NM}.csv')
                LG_TGL_STATS_PER_RD_NORM_RBST_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/norm_robust/{RD_NM}.csv')
                LG_TGL_STATS_PER_RD_NORM_RANK_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/norm_ranking/{RD_NM}.csv')

        # Facts dataframe, no need to normalize
        for TGL_STATS_TYPE in [ 
            'tgl_basic/facts_gm_results', 'tgl_basic/facts_venue_rest_days',
        ]:
            # Get the corresponding season gamelogs stats for each team belonging to the league
            LG_TGL_FACTS_PER_TM_LIST = []
            for TM_SS_HTML_ID in LG_TM_HTML_LIST:
                TM_SS_DIR = parse_team_season_id(TM_SS_HTML_ID)['body']
                TGL_STATS_DF = pd.read_csv(f'{SRC_DIR}/{TM_SS_DIR}/{TGL_STATS_TYPE}.csv',header=[0],index_col=[0,1]) # header=[0] compared to header=[0,1]
                LG_TGL_FACTS_PER_TM_LIST.append(TGL_STATS_DF)

            # Create a table for each round in the league season
            make_directory(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/facts')
            for RD_INDEX in range(max([len(i) for i in LG_TGL_FACTS_PER_TM_LIST])):
                LG_TGL_FACTS_PER_RD_DF = []
                for TGL_STATS_TM in LG_TGL_FACTS_PER_TM_LIST:
                    if RD_INDEX >= len(TGL_STATS_TM):
                        continue
                    RD_DF = TGL_STATS_TM.iloc[RD_INDEX].to_frame().T
                    RD_DF.index.names = ['index','Team_id']    
                    LG_TGL_FACTS_PER_RD_DF.append(RD_DF)
                LG_TGL_FACTS_PER_RD_DF = pd.concat(LG_TGL_FACTS_PER_RD_DF,axis=0)

                # Save each df
                RD_NM = f'{RD_INDEX:02d}'
                LG_TGL_FACTS_PER_RD_DF.to_csv(f'{TGT_DIR}/{LG_SS_DIR}/{TGL_STATS_TYPE}/facts/{RD_NM}.csv')



def __normalize_league_gamelogs_stats_minmax__(df):
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler((-1,1))
    df_norm = df.copy()
    df_norm.loc[:,:] = scaler.fit_transform(df_norm)
    return df_norm

def __normalize_league_gamelogs_stats_standard__(df):
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    df_norm = df.copy()
    df_norm.loc[:,:] = scaler.fit_transform(df_norm)
    return df_norm

def __normalize_league_gamelogs_stats_robust__(df):
    from sklearn.preprocessing import RobustScaler
    scaler = RobustScaler()
    df_norm = df.copy()
    df_norm.loc[:,:] = scaler.fit_transform(df_norm)
    return df_norm

def __normalize_league_gamelogs_stats_ranking__(df):
    return df.copy().rank(axis=0,method='min',ascending=False)


if __name__ == '__main__':
    if MODE == 'all':
        normalize_gamelogs_stats_regular_season()
    else:
        print(f'Invalid mode: {MODE}')
        exit(1)