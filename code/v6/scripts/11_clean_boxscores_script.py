
import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
from load_tools import *
import time
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description='Scrape basketball-reference.com')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-s', '--sourcedir', type=str, default='../02-data-parsed/boxscores/', help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, default='../03-data-aggregated/boxscores/', help='Save to directory')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir


#     """
#     Usage:
#         python3 11_clean_boxscores_script.py -s ../02-data-parsed/boxscores/ -t ../03-data-aggregated/boxscores/
#     """

def compile_boxscores_players(keys):
    boxscores_players = []
    for boxscores_id in sorted(get_all_folders(SRC_DIR),reverse=True):
        BOXSCORE_HREF = '/boxscores/' + boxscores_id + '.html'
        BOXSCORES_DFS = load_all_df_from_dir(os.path.join(SRC_DIR, boxscores_id))
        for key in sorted(BOXSCORES_DFS.keys()):
            if key in keys:
                df = BOXSCORES_DFS[key].copy()\
                    .drop(columns=['Unnamed: 0','team','player'])\
                    .rename(columns={'team_href':'team_id','player_href':'player_id'})\
                    .fillna(0)
                df.insert(0,'boxscore_id',BOXSCORE_HREF)
                boxscores_players.append(df)
    boxscores_players = pd.concat(boxscores_players).set_index(['boxscore_id','team_id','player_id'])
    for na_keywords in ['Did Not Play','Did Not Dress','Coach\'s Decision','','Not With Team','Player Suspended','DNP']:
        boxscores_players.replace(na_keywords,np.nan,inplace=True)
    return boxscores_players

def compile_boxscores_teams(keys):
    boxscores_teams = []
    for boxscores_id in sorted(get_all_folders(SRC_DIR),reverse=True):
        BOXSCORE_HREF = '/boxscores/' + boxscores_id + '.html'
        BOXSCORES_DFS = load_all_df_from_dir(os.path.join(SRC_DIR, boxscores_id))
        for key in sorted(BOXSCORES_DFS.keys()):
            if key in keys:
                df = BOXSCORES_DFS[key].copy()\
                    .drop(columns=['Unnamed: 0','team'])\
                    .rename(columns={'team_href':'team_id'})\
                    .fillna(0)
                df.insert(0,'boxscore_id',BOXSCORE_HREF)
                boxscores_teams.append(df)
    boxscores_teams = pd.concat(boxscores_teams).set_index(['boxscore_id','team_id'])
    return boxscores_teams

def compile_all_boxscores():
    boxscores_keys_dict = {
        # 'boxscores_players_G':['box-away-game-basic','box-home-game-basic'],
        # 'boxscores_players_1Q':['box-away-q1-basic','box-home-q1-basic'],
        # 'boxscores_players_2Q':['box-away-h1-basic','box-home-h1-basic'],
        # 'boxscores_players_3Q':['box-away-q3-basic','box-home-q3-basic'],
        # 'boxscores_players_H2':['box-away-h2-basic','box-home-h2-basic'],
        # 'boxscores_teams_G':['box-away-game-basic-total','box-home-game-basic-total'],
        # 'boxscores_teams_1Q':['box-away-q1-basic-total','box-home-q1-basic-total'],
        # 'boxscores_teams_2Q':['box-away-h1-basic-total','box-home-h1-basic-total'],
        # 'boxscores_teams_3Q':['box-away-q3-basic-total','box-home-q3-basic-total'],
        # 'boxscores_teams_H2':['box-away-h2-basic-total','box-home-h2-basic-total'],
        'boxscores_players_Q2':['box-away-q2-basic','box-home-q2-basic'],
        'boxscores_teams_Q2':['box-away-q2-basic-total','box-home-q2-basic-total'],
        'boxscores_players_Q3':['box-away-q3-basic','box-home-q3-basic'],
        'boxscores_teams_Q3':['box-away-q3-basic-total','box-home-q3-basic-total'],
        'boxscores_players_Q4':['box-away-q4-basic','box-home-q4-basic'],
        'boxscores_teams_Q4':['box-away-q4-basic-total','box-home-q4-basic-total'],
    }
    make_directory(TGT_DIR)
    TQDM_ITEMS = tqdm(boxscores_keys_dict.items())
    for boxscores_name, keys in TQDM_ITEMS:
        TQDM_ITEMS.set_description(boxscores_name)
        if boxscores_name.startswith('boxscores_teams'):
            boxscores_df = compile_boxscores_teams(keys)
        else:
            boxscores_df = compile_boxscores_players(keys)
        # Correct 3Q stats and percentages (3Q = 2Q + Q3)
        if boxscores_name == 'boxscores_players_3Q':
            boxscores_df_2Q = pd.read_csv(os.path.join(TGT_DIR, 'boxscores_players_2Q.csv'), index_col=[0,1,2]).astype(float)
            boxscores_df = boxscores_df + boxscores_df_2Q
            boxscores_df['fg%'] = (boxscores_df['fg']/boxscores_df['fga']).fillna(0)
            boxscores_df['3p%'] = (boxscores_df['3p']/boxscores_df['3pa']).fillna(0)
            boxscores_df['ft%'] = (boxscores_df['ft']/boxscores_df['fta']).fillna(0)
        elif boxscores_name == 'boxscores_teams_3Q':
            boxscores_df_2Q = pd.read_csv(os.path.join(TGT_DIR, 'boxscores_teams_2Q.csv'), index_col=[0,1]).astype(float)
            boxscores_df = boxscores_df + boxscores_df_2Q
            boxscores_df['fg%'] = (boxscores_df['fg']/boxscores_df['fga']).fillna(0)
            boxscores_df['3p%'] = (boxscores_df['3p']/boxscores_df['3pa']).fillna(0)
            boxscores_df['ft%'] = (boxscores_df['ft']/boxscores_df['fta']).fillna(0)
        boxscores_df.to_csv(os.path.join(TGT_DIR, boxscores_name + '.csv'))

if __name__ == "__main__":
    compile_all_boxscores()

