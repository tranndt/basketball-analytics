import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
import time
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description='Scrape basketball-reference.com')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-s', '--sourcedir', type=str, default='../data/', help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, default='../data-parsed/', help='Save to directory')
parser.add_argument('-m', '--mode', type=str, default='gamelogs_stats', help='')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir
MODE = args.mode

def __compute_days_between_rows__(df,window=2):
    df = pd.to_datetime(df.copy())
    return df.diff(window-1).dt.days # -1 because diff() computes the difference between the current and the previous row

def __compute_expanding_avg_stats__(df):
    return df.expanding().mean()

def __compute_expanding_std_stats__(df):
    return df.expanding().std()

def __compute_rolling_avg_stats__(df, window=5):
    return df.rolling(window).mean()

def __compute_rolling_std_stats__(df, window=5):
    return df.rolling(window).std()

def __compute_pts_total__(df, window=5):
    return df.sum(axis=1)

def __compute_pts_spread__(df):
    return df.apply(lambda x: x.iloc[0] - x.iloc[1],axis=1)


def compute_gamelog_stats_regular_season():
    """
    Description:
        Compute gamelog stats
    Summary:
        1. Load all gamelog csv
        2. Compute the expanding and rolling stats
        3. Save the computed gamelogs csv
    Usage:
        python3 03_compute_script.py -m gamelogs_stats -s ../data-parsed/ -t ../data-computed/
    
    """
    _FAILS_ = []
    # Get the list of computed gamelog files
    # TGT_TGL_CSV_COMP_TXT = f'{TGT_DIR}/tgl_csv_stats_computed.txt'
    # TGT_TGL_CSV_COMP_LIST = []
    # if file_exists(TGT_TGL_CSV_COMP_TXT):
    #     TGT_TGL_CSV_COMP_LIST = load_file(TGT_TGL_CSV_COMP_TXT).split('\n')

    # Get all gamelog files
    SRC_TGL_CSV_LIST = get_all_files_recursive(f'{SRC_DIR}/teams', file_type=('tgl_basic.csv','tgl_advanced.csv')) # get only regular season gamelog files
    if debug:
        SRC_TGL_CSV_LIST = SRC_TGL_CSV_LIST[:300]

    TQDM_SRC_TGL_CSV_LIST = tqdm(SRC_TGL_CSV_LIST,ncols=150,dynamic_ncols=False)
    for SRC_TGL_CSV in TQDM_SRC_TGL_CSV_LIST:
        TQDM_SRC_TGL_CSV_LIST.set_description(SRC_TGL_CSV)       
        try:
            # Check if the file has already been computed
            # if SRC_TGL_CSV in TGT_TGL_CSV_COMP_LIST:
            #     continue
            # Load the gamelog csv
            TGL_DF = pd.read_csv(SRC_TGL_CSV,header=[0,1])
            TGL_DF = TGL_DF.drop(columns=[('Unnamed: 0_level_0','Unnamed: 0_level_1')])
            # Compute the expanding and rolling stats
            TGL_MDATE_DF = TGL_DF[('Match','Date')]
            TGL_DAYS_BTW_2GM = __compute_days_between_rows__(TGL_MDATE_DF,window=2).rename(('Match','Days_Btw_2GM'))
            TGL_DAYS_BTW_3GM = __compute_days_between_rows__(TGL_MDATE_DF,window=3).rename(('Match','Days_Btw_3GM'))
            TGL_DAYS_BTW_4GM = __compute_days_between_rows__(TGL_MDATE_DF,window=4).rename(('Match','Days_Btw_4GM'))
            TGL_DAYS_BTW_GM_DF = pd.concat([TGL_DAYS_BTW_2GM,TGL_DAYS_BTW_3GM,TGL_DAYS_BTW_4GM],axis=1) 
            # Compute the total points, spread points
            TGL_RESULT_DF = TGL_DF['Result'].copy()
            TGL_PTS_TOTAL = __compute_pts_total__(TGL_RESULT_DF[['Tm','Opp']]).rename('Pts_Total')
            TGL_PTS_SPREAD = __compute_pts_spread__(TGL_RESULT_DF[['Tm','Opp']]).rename('Pts_Spread')
            TGL_RESULT_DF = pd.concat([TGL_RESULT_DF,TGL_PTS_TOTAL,TGL_PTS_SPREAD],axis=1)
            # Compute the expanding and rolling stats
            TGL_STATS_DF = TGL_DF.drop('Match',level=0,axis=1)
            TGL_STATS_EXPD_AVG_DF = __compute_expanding_avg_stats__(TGL_STATS_DF)
            TGL_STATS_EXPD_STD_DF = __compute_expanding_std_stats__(TGL_STATS_DF)
            TGL_STATS_ROLL_05_AVG_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=5)
            TGL_STATS_ROLL_05_STD_DF = __compute_rolling_std_stats__(TGL_STATS_DF,window=5)  
            TGL_STATS_ROLL_10_AVG_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=10)
            TGL_STATS_ROLL_10_STD_DF = __compute_rolling_std_stats__(TGL_STATS_DF,window=10)
            TGL_STATS_ROLL_15_AVG_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=15)
            TGL_STATS_ROLL_15_STD_DF = __compute_rolling_std_stats__(TGL_STATS_DF,window=15)
            TGL_STATS_ROLL_20_AVG_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=20)
            TGL_STATS_ROLL_20_STD_DF = __compute_rolling_std_stats__(TGL_STATS_DF,window=20)
            # Save the computed gamelogs csv
            TGL_DICT = {
                'info_days_btw_gms' : TGL_DAYS_BTW_GM_DF,
                'info_gm_results'   : TGL_RESULT_DF,
                'stats_expd_avg'    : TGL_STATS_EXPD_AVG_DF,
                'stats_expd_std'    : TGL_STATS_EXPD_STD_DF,
                'stats_roll_05_avg': TGL_STATS_ROLL_05_AVG_DF,
                'stats_roll_05_std': TGL_STATS_ROLL_05_STD_DF,
                'stats_roll_10_avg': TGL_STATS_ROLL_10_AVG_DF,
                'stats_roll_10_std': TGL_STATS_ROLL_10_STD_DF,
                'stats_roll_15_avg': TGL_STATS_ROLL_15_AVG_DF,
                'stats_roll_15_std': TGL_STATS_ROLL_15_STD_DF,
                'stats_roll_20_avg': TGL_STATS_ROLL_20_AVG_DF,
                'stats_roll_20_std': TGL_STATS_ROLL_20_STD_DF
            }
            # remove the root from the directory
            # Extract the team and season from the directory


            TGL_STATS_DIR = SRC_TGL_CSV.replace(SRC_DIR,'').replace('.csv','')
            make_directory(f'{TGT_DIR}/{TGL_STATS_DIR}')
            for TBL_ID, DF in TGL_DICT.items():
                DF.to_csv(f'{TGT_DIR}/{TGL_STATS_DIR}/{TBL_ID}.csv', index=False)
            
            # TGT_TGL_CSV_COMP_LIST.append(SRC_TGL_CSV)
            # save_file(TGT_TGL_CSV_COMP_TXT,'\n'.join(TGT_TGL_CSV_COMP_LIST))
        except Exception as e:
            print(f'Error computing stats for {SRC_TGL_CSV}: {e}')
            _FAILS_.append(SRC_TGL_CSV)
            continue
    if _FAILS_:
        print(f'Failed to compute stats for {len(_FAILS_)}/{len(SRC_TGL_CSV_LIST)} files: {_FAILS_}')
    else:
        print(f'All {len(SRC_TGL_CSV_LIST)} files computed successfully')

if __name__ == '__main__':
    if MODE == 'gamelogs_stats':
        compute_gamelog_stats_regular_season()
    else:
        raise ValueError(f'Invalid mode: {MODE}')

    
