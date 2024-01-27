import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
import time
from tqdm import tqdm
import argparse
from parse_tools import *
from bs4 import BeautifulSoup, Comment


sleep = 3.5

def fetch_all_players_hrefs() -> list:
    players_hrefs = []
    # For letters in the alphabet
    TQDM_LETTERS = tqdm('abcdefghijklmnopqrstuvwxyz',ncols=150)
    for letter in TQDM_LETTERS:
        TQDM_LETTERS.set_description(letter)
        # Get the html soup for the letter page
        html_text, html_soup = request_html('/'.join([PLAYERS_PAGE,letter]))
        # For each player in the letter page
        if html_soup:
            for th in html_soup.find_all('th', {'data-stat': 'player'}):
                for a in th.find_all('a'):
                    players_hrefs.append(a['href'])
            save_file('../00-data-facts/players_hrefs.txt','\n'.join(players_hrefs))
        time.sleep(sleep)
    # Save the list of player hrefs to a file
    save_file('../00-data-facts/players_hrefs.txt','\n'.join(players_hrefs))
    return players_hrefs


def scrape_all_player_htmls(TGT_DIR) -> None:
    _FAILS_ = []
    # Load the list of player hrefs from a file
    players_hrefs = load_file('../00-data-facts/players_hrefs.txt').split('\n')
    # For each player href
    TQDM_PLAYER_HREFS = tqdm(players_hrefs,ncols=150)
    for player_href in TQDM_PLAYER_HREFS:
        # Get the html soup for the player page
        TQDM_PLAYER_HREFS.set_description(player_href)
        # If player page already scraped, skip
        if file_exists('/'.join([TGT_DIR,player_href])):
            continue
        try:
            html_text, html_soup = request_html('/'.join([HOME_PAGE,player_href]),content_only=True)
            save_file('/'.join([TGT_DIR,player_href]), html_text) 
        except Exception as e:
            # print(f'Error getting {player_href}: {e}')
            _FAILS_.append(player_href)
        time.sleep(sleep)
    if _FAILS_:
        fails = '\n'.join(_FAILS_)
        print(f"Failed to fetch {len(_FAILS_)} boxscores: {fails}")
    else:
        print('All boxscores fetched')


def extract_all_players_gamelog_hrefs(players_html_dir):
    def extract_player_gamelog_hrefs(html_soup):
            gamelog_hrefs = []
            # For each player in the letter page
            for a in html_soup.select('div[id="bottom_nav"] a[href*="gamelog"]'):
                if '/gamelog/' in a['href']:
                    gamelog_hrefs.append(a['href'])
                    gamelog_hrefs.append(re.sub('gamelog','gamelog-advanced',a['href']))
            return gamelog_hrefs
    
    # Load the list of player hrefs from a file
    ALL_PLAYERS_HREFS_LIST = load_file('../00-data-facts/players_hrefs.txt').split('\n')
    # For each player href
    _FAILS_ = []
    all_players_gamelog_hrefs_dict = {}
    TQDM_PLAYER_HREFS = tqdm(ALL_PLAYERS_HREFS_LIST,ncols=150)
    for player_href in TQDM_PLAYER_HREFS:
        # Get the html soup for the player page
        TQDM_PLAYER_HREFS.set_description(player_href)
        try:
            html_text,html_soup = load_html('/'.join([players_html_dir,player_href]))
            gamelog_hrefs       = extract_player_gamelog_hrefs(html_soup)
            all_players_gamelog_hrefs_dict[player_href] = gamelog_hrefs
            save_json('../00-data-facts/players_gamelog_hrefs.json', all_players_gamelog_hrefs_dict)
        except Exception as e:
            _FAILS_.append(player_href)
            continue
    if _FAILS_:
        fails = '\n'.join(_FAILS_)
        print(f"Failed to fetch {len(_FAILS_)} cases: {fails}")
    else:
        print('All cases extracted')


def scrape_all_players_gamelog_html(TGT_DIR):
    # Load the list of player gamelog hrefs from a file
    SRC_DIR = '../00-data-facts/players_gamelog_hrefs.json'
    players_gamelog_hrefs_dict = load_json(SRC_DIR)
    # For each player href
    _FAILS_ = []
    TQDM_PLAYER_HREFS = tqdm(players_gamelog_hrefs_dict.items(),ncols=150)
    for player_href,player_gamelog_href_list in TQDM_PLAYER_HREFS:
        # Get the html soup for the player page
        TQDM_PLAYER_HREFS.set_description(f'{player_href} ({len(player_gamelog_href_list)})')
        for player_gamelog_href in player_gamelog_href_list:
            try:
                html_text, html_soup = request_html('/'.join([HOME_PAGE,player_gamelog_href]),content_only=True)
                save_file('/'.join([TGT_DIR,player_gamelog_href+'.html']), html_text) 
            except Exception as e:
                print(f'Error getting {player_gamelog_href}: {e}')
                _FAILS_.append(player_gamelog_href)
            time.sleep(sleep)
    if _FAILS_:
        fails = '\n'.join(_FAILS_)
        print(f"Failed to fetch {len(_FAILS_)} cases: {fails}")
    else:
        print('All cases fetched')


def scrape_all():
    TGT_DIR = '../01-data-html/'
    # Fetch all players hrefs
    # players_hrefs = fetch_all_players_hrefs()
    # Scrape all player htmls
    scrape_all_player_htmls(TGT_DIR='../01-data-html/')
    # Extract all players gamelog hrefs from scraped htmls
    extract_all_players_gamelog_hrefs(players_html_dir='../01-data-html')
    # Scrape all players gamelog htmls from extracted hrefs
    scrape_all_players_gamelog_html(TGT_DIR='../01-data-html')


if __name__ == '__main__':
    """
    Usage:
        python3 13_scrape_player_gamelogs_script.py
    """
    scrape_all()