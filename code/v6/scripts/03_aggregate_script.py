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
parser.add_argument('-s', '--sourcedir', type=str, default='../data-parsed/', help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, default='../data-aggregated/', help='Save to directory')
parser.add_argument('-m', '--mode', type=str, default='all', help='')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir
MODE = args.mode

def __compute_days_between_rows__(df,window=2):
    df = pd.to_datetime(df.copy())
    return df.diff(window-1).dt.days # -1 because diff() computes the difference between the current and the previous row

def __compute_cumulative_avg_stats__(df):
    return df.expanding().mean(),df.expanding().std()

def __compute_rolling_avg_stats__(df, window=5):
    return df.rolling(window).mean(),df.rolling(window).std()

def __compute_pts_total__(df):
    return df.sum(axis=1)

def __compute_pts_spread__(df):
    return df.apply(lambda x: x.iloc[0] - x.iloc[1],axis=1)

def __compute_venue_streak_count__(series):
    idx_sequence = []
    count = 0
    for i in range(len(series)):
        if i == 0 or series.iloc[i] != series.iloc[i-1]:
            count = 0
        else:
            count += 1
        idx_sequence.append(count)
    return pd.Series(idx_sequence,index=series.index)

def __compute_h2h_avg_stats__(TGL_DF):
    TGL_H2H_CUMU_AVG_STATS_DF_LIST = []
    TGL_H2H_CUMU_STD_STATS_DF_LIST = []
    for opp_id in TGL_DF[('Match','Opp_id')].unique():
        QUERY_DF_I = TGL_DF[TGL_DF[('Match','Opp_id')] == opp_id].drop('Match',level=0,axis=1)
        QUERY_DF_H2H_CUMU_AVG_DF,QUERY_DF_H2H_CUMU_STD_DF = __compute_cumulative_avg_stats__(QUERY_DF_I)
        TGL_H2H_CUMU_AVG_STATS_DF_LIST.append(QUERY_DF_H2H_CUMU_AVG_DF)
        TGL_H2H_CUMU_STD_STATS_DF_LIST.append(QUERY_DF_H2H_CUMU_STD_DF)
    TGL_H2H_CUMU_AVG_STATS_DF = pd.concat(TGL_H2H_CUMU_AVG_STATS_DF_LIST,axis=0).sort_index()
    TGL_H2H_CUMU_STD_STATS_DF = pd.concat(TGL_H2H_CUMU_STD_STATS_DF_LIST,axis=0).sort_index()
    return TGL_H2H_CUMU_AVG_STATS_DF, TGL_H2H_CUMU_STD_STATS_DF

def compute_gamelog_stats_regular_season():
    """
    Description:
        Compute gamelog stats
    Summary:
        1. Load all gamelog csv
        2. Compute the expanding and rolling stats
        3. Save the computed gamelogs csv
    Usage:
        python3 03_aggregate_script.py -s ../data-parsed/ -t ../data-aggregated/
    
    """
    _FAILS_ = []
    # Get all gamelog files
    SRC_TGL_CSV_LIST = get_all_files_recursive(f'{SRC_DIR}/teams', file_type=('tgl_basic.csv','tgl_advanced.csv')) # get only regular season gamelog files
    if debug:
        SRC_TGL_CSV_LIST = SRC_TGL_CSV_LIST[:100]

    TQDM_SRC_TGL_CSV_LIST = tqdm(SRC_TGL_CSV_LIST,ncols=150,dynamic_ncols=False)
    for SRC_TGL_CSV in TQDM_SRC_TGL_CSV_LIST:
        TQDM_SRC_TGL_CSV_LIST.set_description(SRC_TGL_CSV)       
        try:
            # Load the gamelog csv
            TGL_DF = pd.read_csv(SRC_TGL_CSV,header=[0,1])
            TGL_DF = TGL_DF.drop(
                columns=[
                    ('Unnamed: 0_level_0','Unnamed: 0_level_1')
                ]).rename(
                columns={
                    'Boxscores_html_id':'Boxscores_id',
                    'Tm_html_id':'Team_id',
                    'Opp_html_id':'Opp_id',
                },level=1
            )
            TGL_IDX = pd.MultiIndex.from_arrays([TGL_DF.index,TGL_DF[('Match','Team_id')]],names=['index','Team_id'])
            TGL_DF.set_index(TGL_IDX,inplace=True)
            # Compute the expanding and rolling stats
            TGL_MDATE_DF = TGL_DF[('Match','Date')]
            TM_HM_AW = TGL_DF[('Match','H/A')]
            TGL_VEN_STRK_CNT = __compute_venue_streak_count__(TGL_DF[('Match','H/A')]).rename(('Match','Venue_Strk_Cnt'))
            TGL_DAYS_BTW_2GM = __compute_days_between_rows__(TGL_MDATE_DF,window=2).rename(('Match','Days_Btw_2GM'))
            TGL_DAYS_BTW_3GM = __compute_days_between_rows__(TGL_MDATE_DF,window=3).rename(('Match','Days_Btw_3GM'))
            TGL_DAYS_BTW_4GM = __compute_days_between_rows__(TGL_MDATE_DF,window=4).rename(('Match','Days_Btw_4GM'))
            TGL_DAYS_BTW_GM_DF = pd.concat([TM_HM_AW,TGL_VEN_STRK_CNT,TGL_DAYS_BTW_2GM,TGL_DAYS_BTW_3GM,TGL_DAYS_BTW_4GM],axis=1).droplevel(0,axis=1)
            # Compute the total points, spread points
            TGL_RESULT_DF = TGL_DF['Result'].copy()
            TGL_PTS_TOTAL = __compute_pts_total__(TGL_RESULT_DF[['Tm','Opp']]).rename('Pts_Total')
            TGL_PTS_SPREAD = __compute_pts_spread__(TGL_RESULT_DF[['Tm','Opp']]).rename('Pts_Spread')
            TGL_RESULT_DF = pd.concat([TGL_RESULT_DF,TGL_PTS_TOTAL,TGL_PTS_SPREAD],axis=1)
            # Compute the expanding and rolling stats
            TGL_STATS_DF = TGL_DF.drop('Match',level=0,axis=1)
            TGL_STATS_CUMU_AVG_DF,TGL_STATS_CUMU_STD_DF        = __compute_cumulative_avg_stats__(TGL_STATS_DF)
            TGL_STATS_ROLL_04_AVG_DF, TGL_STATS_ROLL_04_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=4)
            TGL_STATS_ROLL_08_AVG_DF, TGL_STATS_ROLL_08_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=8)
            TGL_STATS_ROLL_12_AVG_DF, TGL_STATS_ROLL_12_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=12)
            TGL_STATS_ROLL_16_AVG_DF, TGL_STATS_ROLL_16_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=16)
            TGL_STATS_ROLL_20_AVG_DF, TGL_STATS_ROLL_20_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_DF,window=20)
            # Compute the home/away stats
            TGL_STATS_AW_DF = TGL_DF[TGL_DF[('Match','H/A')] == 0].drop('Match',level=0,axis=1)
            TGL_STATS_HM_DF = TGL_DF[TGL_DF[('Match','H/A')] == 1].drop('Match',level=0,axis=1)
            TGL_STATS_AW_CUMU_AVG_DF, TGL_STATS_AW_CUMU_STD_DF      = __compute_cumulative_avg_stats__(TGL_STATS_AW_DF)
            TGL_STATS_AW_ROLL_04_AVG_DF,TGL_STATS_AW_ROLL_04_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_AW_DF,window=4)
            TGL_STATS_AW_ROLL_08_AVG_DF,TGL_STATS_AW_ROLL_08_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_AW_DF,window=8)
            TGL_STATS_AW_ROLL_12_AVG_DF,TGL_STATS_AW_ROLL_12_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_AW_DF,window=12)
            TGL_STATS_AW_ROLL_16_AVG_DF,TGL_STATS_AW_ROLL_16_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_AW_DF,window=16)
            TGL_STATS_AW_ROLL_20_AVG_DF,TGL_STATS_AW_ROLL_20_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_AW_DF,window=20)
            TGL_STATS_HM_CUMU_AVG_DF, TGL_STATS_HM_CUMU_STD_DF      = __compute_cumulative_avg_stats__(TGL_STATS_HM_DF)
            TGL_STATS_HM_ROLL_04_AVG_DF,TGL_STATS_HM_ROLL_04_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_HM_DF,window=4)
            TGL_STATS_HM_ROLL_08_AVG_DF,TGL_STATS_HM_ROLL_08_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_HM_DF,window=8)
            TGL_STATS_HM_ROLL_12_AVG_DF,TGL_STATS_HM_ROLL_12_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_HM_DF,window=12)
            TGL_STATS_HM_ROLL_16_AVG_DF,TGL_STATS_HM_ROLL_16_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_HM_DF,window=16)
            TGL_STATS_HM_ROLL_20_AVG_DF,TGL_STATS_HM_ROLL_20_STD_DF = __compute_rolling_avg_stats__(TGL_STATS_HM_DF,window=20)
            # Compute the h2h stats
            TGL_STATS_H2H_CUMU_AVG_DF, TGL_STATS_H2H_CUMU_STD_DF    = __compute_h2h_avg_stats__(TGL_DF)

            # Save the computed gamelogs csv
            TGL_DICT = {
                'facts_venue_rest_days' : TGL_DAYS_BTW_GM_DF,   'facts_gm_results'   : TGL_RESULT_DF,
                'stats_cumu_avg'    : TGL_STATS_CUMU_AVG_DF,    'stats_cumu_std'    : TGL_STATS_CUMU_STD_DF,
                'stats_roll_04_avg' : TGL_STATS_ROLL_04_AVG_DF, 'stats_roll_04_std' : TGL_STATS_ROLL_04_STD_DF,
                'stats_roll_08_avg' : TGL_STATS_ROLL_08_AVG_DF, 'stats_roll_08_std' : TGL_STATS_ROLL_08_STD_DF,
                'stats_roll_12_avg' : TGL_STATS_ROLL_12_AVG_DF, 'stats_roll_12_std' : TGL_STATS_ROLL_12_STD_DF,
                'stats_roll_16_avg' : TGL_STATS_ROLL_16_AVG_DF, 'stats_roll_16_std' : TGL_STATS_ROLL_16_STD_DF,
                'stats_roll_20_avg' : TGL_STATS_ROLL_20_AVG_DF, 'stats_roll_20_std' : TGL_STATS_ROLL_20_STD_DF,
                'stats_hm_cumu_avg' : TGL_STATS_HM_CUMU_AVG_DF, 'stats_hm_cumu_std' : TGL_STATS_HM_CUMU_STD_DF,
                'stats_hm_roll_04_avg' : TGL_STATS_HM_ROLL_04_AVG_DF, 'stats_hm_roll_04_std' : TGL_STATS_HM_ROLL_04_STD_DF,
                'stats_hm_roll_08_avg' : TGL_STATS_HM_ROLL_08_AVG_DF, 'stats_hm_roll_08_std' : TGL_STATS_HM_ROLL_08_STD_DF,
                'stats_hm_roll_12_avg' : TGL_STATS_HM_ROLL_12_AVG_DF, 'stats_hm_roll_12_std' : TGL_STATS_HM_ROLL_12_STD_DF,
                'stats_hm_roll_16_avg' : TGL_STATS_HM_ROLL_16_AVG_DF, 'stats_hm_roll_16_std' : TGL_STATS_HM_ROLL_16_STD_DF,
                'stats_hm_roll_20_avg' : TGL_STATS_HM_ROLL_20_AVG_DF, 'stats_hm_roll_20_std' : TGL_STATS_HM_ROLL_20_STD_DF,
                'stats_aw_cumu_avg' : TGL_STATS_AW_CUMU_AVG_DF, 'stats_aw_cumu_std' : TGL_STATS_AW_CUMU_STD_DF,
                'stats_aw_roll_04_avg' : TGL_STATS_AW_ROLL_04_AVG_DF, 'stats_aw_roll_04_std' : TGL_STATS_AW_ROLL_04_STD_DF,
                'stats_aw_roll_08_avg' : TGL_STATS_AW_ROLL_08_AVG_DF, 'stats_aw_roll_08_std' : TGL_STATS_AW_ROLL_08_STD_DF,
                'stats_aw_roll_12_avg' : TGL_STATS_AW_ROLL_12_AVG_DF, 'stats_aw_roll_12_std' : TGL_STATS_AW_ROLL_12_STD_DF,
                'stats_aw_roll_16_avg' : TGL_STATS_AW_ROLL_16_AVG_DF, 'stats_aw_roll_16_std' : TGL_STATS_AW_ROLL_16_STD_DF,
                'stats_aw_roll_20_avg' : TGL_STATS_AW_ROLL_20_AVG_DF, 'stats_aw_roll_20_std' : TGL_STATS_AW_ROLL_20_STD_DF,
                'stats_h2h_cumu_avg'   : TGL_STATS_H2H_CUMU_AVG_DF, 'stats_h2h_cumu_std': TGL_STATS_H2H_CUMU_STD_DF,
            }
            # Extract the team and season from the directory
            TGL_STATS_DIR = SRC_TGL_CSV.replace(SRC_DIR,'').replace('.csv','')
            make_directory(f'{TGT_DIR}/{TGL_STATS_DIR}')
            for TBL_ID, DF in TGL_DICT.items():
                DF.to_csv(f'{TGT_DIR}/{TGL_STATS_DIR}/{TBL_ID}.csv',index=True)
                  
        except Exception as e:
            print(f'Error computing stats for {SRC_TGL_CSV}: {e}\n{e.__traceback__}')
            _FAILS_.append(SRC_TGL_CSV)
            
            continue
        if debug:
            time.sleep(1)
    if _FAILS_:
        print(f'Failed to compute stats for {len(_FAILS_)}/{len(SRC_TGL_CSV_LIST)} files: {_FAILS_}')
    else:
        print(f'All {len(SRC_TGL_CSV_LIST)} files computed successfully')

if __name__ == '__main__':
    if MODE == 'all':
        compute_gamelog_stats_regular_season()
    else:
        raise ValueError(f'Invalid mode: {MODE}')

    


    
