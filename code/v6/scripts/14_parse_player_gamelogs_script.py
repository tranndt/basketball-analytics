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
parser.add_argument('-s', '--sourcedir', type=str, help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, help='Save to directory')

args = parser.parse_args()
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir

def __parse_player_gamelog_basic_advanced_table__(html_text):
    #    1. Extract links from table - # 2. Insert links into table
    DF_PLYR_GL = parse_html_table(html_text)
    df_gamelog_basic_links = parse_html_table(html_text,extract_links='body').applymap(lambda x: x[-1])

    DF_PLYR_GL.insert(3,'Boxscore_id',df_gamelog_basic_links['Date'])
    DF_PLYR_GL.insert(6,'Tm_id',df_gamelog_basic_links['Tm'])
    DF_PLYR_GL.insert(9,'Opp_id',df_gamelog_basic_links['Opp'])
    # 2.5 Remove this one edge case where the boxscore_id is invalid
    DF_PLYR_GL = DF_PLYR_GL[~DF_PLYR_GL['Boxscore_id'].isin(['/boxscores/201606190CLE.html'])] # Fix for 201606190CLE - This game does not exist, 201606190GSW is the correct game

    # 3. Remove unnnecessary header rows
    GAME_FILTER = DF_PLYR_GL.loc[:,'Rk'].astype(str).str.isnumeric().fillna(False)
    DF_PLYR_GL = DF_PLYR_GL.loc[GAME_FILTER]
    DF_PLYR_GL.insert(2,'GP',DF_PLYR_GL.loc[:,'G'].astype(str).str.isnumeric().fillna(False).astype(int))
    # 4. Rename H/A, convert to boolean
    GAME_HM_AW = DF_PLYR_GL.pop('Unnamed: 5').isna().astype(int)
    DF_PLYR_GL.insert(8,'H/A',GAME_HM_AW)
    # 5. Rename W/L, split into 2 columns, convert to boolean and int
    GAME_RESULT = DF_PLYR_GL.pop('Unnamed: 7').str.extract(r'([WL]) \(([+-]\d+)\)',expand=True)
    DF_PLYR_GL.insert(11,'W/L',GAME_RESULT[0].replace({'W':1,'L':0}))
    DF_PLYR_GL.insert(12,'Pts_diff',GAME_RESULT[1].astype(int))
    # 6. Convert MP to float, and Inactive game stats to nan
    GP_FILTER = DF_PLYR_GL.loc[:,'GP'].astype(bool)
    # Deal with cases where MP is nan 
    if DF_PLYR_GL['MP'].notna().sum() > 0: # Added later to fix the all NAN case
        DF_PLYR_GL.loc[GP_FILTER & DF_PLYR_GL['MP'].notna(),'MP'] = DF_PLYR_GL.loc[GP_FILTER & DF_PLYR_GL['MP'].notna(),'MP'].str.split(':').apply(lambda x:float(x[0]) + float(x[1])/60)
    DF_PLYR_GL.loc[~GP_FILTER,'GS':] = np.nan
    # 7. Convert +/- to float (in basic table)
    if '+/-' in DF_PLYR_GL.columns:
        DF_PLYR_GL['+/-'] = DF_PLYR_GL['+/-'].astype(float)
    return DF_PLYR_GL


def parse_failed_player_gamelogs(SRC_DIR,TGT_DIR):
    __FIXED__ = []
    TQDM_PLAYER_LIST = tqdm(load_file('../00-data-facts/failed_player_gamelogs.txt').split('\n'))
    # TGT_DIR = '../01-data-html/players/'
    for player_html in TQDM_PLAYER_LIST:
        TQDM_PLAYER_LIST.set_description(player_html)
        html_text,html_soup = load_html(player_html)
        html_text = clean_html_text(html_text)
        html_soup = bs4.BeautifulSoup(html_text, 'html.parser')
        if '/gamelog/' in player_html:
            html_regular = html_soup.find('table', {'id': 'pgl_basic'})
            html_playoffs = html_soup.find('table', {'id': 'pgl_basic_playoffs'})
        elif '/gamelog-advanced/' in player_html:
            html_regular = html_soup.find('table', {'id': 'pgl_advanced'})
            html_playoffs = html_soup.find('table', {'id': 'pgl_advanced_playoffs'})
        if html_regular:
            tgl_name = '/pgl_basic_regular/' if '/gamelog/' in player_html else '/pgl_advanced_regular/'
            tgt_file = player_html.replace(SRC_DIR,TGT_DIR).replace('/gamelog/',tgl_name).replace('/gamelog-advanced/',tgl_name).replace('.html','.csv')
            if not file_exists(tgt_file):
                # make_directory(tgt_dir)
                PGL_REG = __parse_player_gamelog_basic_advanced_table__(html_regular.prettify())
                PGL_REG.to_csv(tgt_file,index=False)
                __FIXED__.append(tgt_file)
        if html_playoffs:
            tgl_name = '/pgl_basic_playoffs/' if '/gamelog/' in player_html else '/pgl_advanced_playoffs/'
            tgt_file = player_html.replace(SRC_DIR,TGT_DIR).replace('/gamelog/',tgl_name).replace('/gamelog-advanced/',tgl_name).replace('.html','.csv')
            if not file_exists(tgt_file):
                # make_directory(tgt_dir)
                PGL_POFF = __parse_player_gamelog_basic_advanced_table__(html_playoffs.prettify())
                PGL_POFF.to_csv(tgt_file,index=False)
                __FIXED__.append(tgt_file)
    if __FIXED__:
        fixed_str = '\n'.join(__FIXED__)
        print(f'Fixed {len(__FIXED__)} files: {fixed_str}')
        # save_file('../00-data-facts/fixed_player_gamelogs.txt',fixed_str)

def parse_all_player_gamelogs_from_dir(SRC_DIR,TGT_DIR):
    __FAILS__ = []
    __FIXED__ = []
    player_list = load_file('../00-data-facts/players_hrefs.txt').split('\n')
    TRANGE = trange(len(player_list),ncols=150)
    for alphabet_dir in sorted(get_all_folders(SRC_DIR)): # alphabet from a-z
        for player_dir in sorted(get_all_folders('/'.join([SRC_DIR,alphabet_dir]))): # player_id such as bookede01
            for gamelog_type in sorted(get_all_folders('/'.join([SRC_DIR,alphabet_dir,player_dir]))): # gamelog or gamelog-advanced
                for gamelog_year_html in sorted(get_all_files('/'.join([SRC_DIR,alphabet_dir,player_dir,gamelog_type]),file_type='html')):
                    TRANGE.set_description('/'.join([SRC_DIR,alphabet_dir,player_dir,gamelog_type,gamelog_year_html]) + f'({len(__FIXED__)})',refresh=True)
                    try:
                        html_text,html_soup = load_html('/'.join([SRC_DIR,alphabet_dir,player_dir,gamelog_type,gamelog_year_html]))
                        html_text = clean_html_text(html_text)
                        html_soup = bs4.BeautifulSoup(html_text, 'html.parser')
                        if gamelog_type == 'gamelog':
                            html_regular = html_soup.find('table', {'id': 'pgl_basic'})
                            html_playoffs = html_soup.find('table', {'id': 'pgl_basic_playoffs'})
                        elif gamelog_type == 'gamelog-advanced':
                            html_regular = html_soup.find('table', {'id': 'pgl_advanced'})
                            html_playoffs = html_soup.find('table', {'id': 'pgl_advanced_playoffs'})
                        if html_regular:
                            tgl_name = 'pgl_basic_regular' if gamelog_type == 'gamelog' else 'pgl_advanced_regular'
                            tgt_dir = '/'.join([TGT_DIR,alphabet_dir,player_dir,tgl_name])
                            tgt_file = '/'.join([TGT_DIR,alphabet_dir,player_dir,tgl_name,gamelog_year_html.replace('.html','.csv')])
                            if not file_exists(tgt_file):
                                make_directory(tgt_dir)
                                PGL_REG = __parse_player_gamelog_basic_advanced_table__(html_regular.prettify())
                                PGL_REG.to_csv(tgt_file,index=False)
                                __FIXED__.append(tgt_file)
                        if html_playoffs:
                            tgl_name = 'pgl_basic_playoffs' if gamelog_type == 'gamelog' else 'pgl_advanced_playoffs'
                            tgt_dir = '/'.join([TGT_DIR,alphabet_dir,player_dir,tgl_name])
                            tgt_file = '/'.join([TGT_DIR,alphabet_dir,player_dir,tgl_name,gamelog_year_html.replace('.html','.csv')])
                            if not file_exists(tgt_file):
                                make_directory(tgt_dir)
                                PGL_POFF = __parse_player_gamelog_basic_advanced_table__(html_playoffs.prettify())
                                PGL_POFF.to_csv(tgt_file,index=False)
                                __FIXED__.append(tgt_file)
                    except Exception as e:
                        print(f'Error parsing {gamelog_year_html}: {e}')
                        __FAILS__.append('/'.join([SRC_DIR,alphabet_dir,player_dir,gamelog_type,gamelog_year_html]))
                        continue
            TRANGE.update(1)

    if __FAILS__:
        fails_str = '\n'.join(__FAILS__)
        print(f'Failed to parse {len(__FAILS__)} files: {__FAILS__}')
        save_file('../00-data-facts/failed_player_gamelogs.txt',fails_str)
    if __FIXED__:
        fixed_str = '\n'.join(__FIXED__)
        print(f'Fixed {len(__FIXED__)} files: {__FIXED__}')
        save_file('../00-data-facts/fixed_player_gamelogs.txt',fixed_str)

if __name__ == '__main__':
    """
    Usage:
        python3 14_parse_player_gamelogs_script.py -s ../01-data-html/players/ -t ../02-data-parsed/players/
    """
    SRC_DIR = args.sourcedir
    TGT_DIR = args.targetdir
    # parse_all_player_gamelogs_from_dir(SRC_DIR,TGT_DIR)
    parse_failed_player_gamelogs(SRC_DIR,TGT_DIR)