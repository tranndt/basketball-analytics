import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
import time
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description='Normalize basketball-reference.com data')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-s', '--sourcedir', type=str, default='../data/', help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, default='../data-parsed/', help='Target directory')
parser.add_argument('-m', '--mode', type=str, default='norm_gamelogs_stats', help='')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir
MODE = args.mode

def normalize_gamelogs_stats_regular_season():
    """
    Description:
        Normalize gamelog stats
    Summary:

    Usage:
        python3 04_normalize_script.py -m norm_gamelogs_stats -s ../data-computed/ -t ../data-normalized/
    
    """
    # Load list of league seasons
    all_league_seasons_html_dict = {}
    if file_exists(f'{SRC_DIR}/league_seasons_html.txt'):
        all_league_seasons_html_dict = load_file(f'{SRC_DIR}/league_seasons_html.txt')
        all_league_seasons_html_dict = ast.literal_eval(all_league_seasons_html_dict)
    else:
        print('league_seasons_html.txt not found. Please scrape it first.')
        return

    # For every league_season, get all team_seasons belonging to the league
    for league, LEAG_TM_SS_HTML_LIST in list(all_league_seasons_html_dict.items()):
        # For each stats type
        for TGL_STATS_TYPE in [ 'tgl_basic/stats_expd_avg','tgl_basic/stats_roll_05_avg','tgl_basic/stats_roll_10_avg',
                                    'tgl_basic/stats_roll_15_avg', 'tgl_basic/stats_roll_20_avg',
                                    'tgl_advanced/stats_expd_avg','tgl_advanced/stats_roll_05_avg','tgl_advanced/stats_roll_10_avg',
                                    'tgl_advanced/stats_roll_15_avg', 'tgl_advanced/stats_roll_20_avg']:
            # Get the corresponding season gamelogs stats for each team belonging to the league
            LEAG_TGL_STATS_PER_TM_SS_LIST = []
            for TM_SS_HTML_ID in LEAG_TM_SS_HTML_LIST:
                TM_SS_DIR = parse_team_html_id(TM_SS_HTML_ID)['body']
                TGL_STATS_DF = pd.read_csv(f'{SRC_DIR}/{TM_SS_DIR}/{TGL_STATS_TYPE}.csv',header=[0,1])
                TGL_STATS_DF.insert(0,'Team_id',TM_SS_HTML_ID)
                LEAG_TGL_STATS_PER_TM_SS_LIST.append(TGL_STATS_DF)

            # Create a table for each round in the league season
            for RD_INDEX in range(len(LEAG_TGL_STATS_PER_TM_SS_LIST[0])):
                LEAG_TGL_STATS_PER_RD_DF = []
                for TGL_STATS_TM in LEAG_TGL_STATS_PER_TM_SS_LIST:
                    if RD_INDEX >= len(TGL_STATS_TM):
                        continue
                    LEAG_TGL_STATS_PER_RD_DF.append(TGL_STATS_TM.iloc[RD_INDEX])
                LEAG_TGL_STATS_PER_RD_DF = pd.concat(LEAG_TGL_STATS_PER_RD_DF,axis=1).T.set_index('Team_id',append=True)
                LEAG_TGL_STATS_PER_RD_NORM_MNMX_DF  = __normalize_league_gamelogs_stats_minmax__(LEAG_TGL_STATS_PER_RD_DF)
                LEAG_TGL_STATS_PER_RD_NORM_STD_DF   = __normalize_league_gamelogs_stats_standard__(LEAG_TGL_STATS_PER_RD_DF)
                LEAG_TGL_STATS_PER_RD_NORM_RBST_DF  = __normalize_league_gamelogs_stats_robust__(LEAG_TGL_STATS_PER_RD_DF)
                LEAG_TGL_STATS_PER_RD_NORM_RANK_DF  = __normalize_league_gamelogs_stats_ranking__(LEAG_TGL_STATS_PER_RD_DF)

                # Save each df
                make_directory(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/raw')
                make_directory(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/norm_minmax')
                make_directory(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/norm_standard')
                make_directory(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/norm_robust')
                make_directory(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/norm_ranking')
                LEAG_TGL_STATS_PER_RD_DF.to_csv(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/raw/{RD_INDEX}.csv')
                LEAG_TGL_STATS_PER_RD_NORM_MNMX_DF.to_csv(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/norm_minmax/{RD_INDEX}.csv')
                LEAG_TGL_STATS_PER_RD_NORM_STD_DF.to_csv(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/norm_standard/{RD_INDEX}.csv')
                LEAG_TGL_STATS_PER_RD_NORM_RBST_DF.to_csv(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/norm_robust/{RD_INDEX}.csv')
                LEAG_TGL_STATS_PER_RD_NORM_RANK_DF.to_csv(f'{TGT_DIR}/{league}/{TGL_STATS_TYPE}/norm_ranking/{RD_INDEX}.csv')


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
    if MODE == 'norm_gamelogs_stats':
        normalize_gamelogs_stats_regular_season()
    else:
        print(f'Invalid mode: {MODE}')
        exit(1)