# %pip install bs4
# %pip install html5lib

from bs4 import *
from bs4.element import PageElement
import time
import requests
import re
import numpy as np
import pandas as pd
from tqdm import tqdm, trange
import json
import pickle
from pathlib import Path

HOME_PAGE = 'https://www.basketball-reference.com'
SEASONS_PAGE = 'https://www.basketball-reference.com/leagues'
TEAMS_PAGE = 'https://www.basketball-reference.com/teams'
BOXSCORES_PAGE = 'https://www.basketball-reference.com/boxscores'

def fetch_html(url,source=None):
    if source:
        try:
            data = load(url)
            return re.sub("<!--|-->","\n",data)
        except:
            print(f'Failed to fetch {url} from local. Please try to fetch online instead')
            return None
    else:
        try:
            if not url.startswith("https://"):
                url = "https://"+url
            session = requests.Session()
            return re.sub("<!--|-->","\n",session.get(url).text)
        except:
            print(f'Failed to fetch {url} from web. Please double check url.')
    return None

def make_soup(text):
    return BeautifulSoup(text,features='html.parser')

def save(a,filepath,mode='w',file_type=None):
    if not Path(filepath).exists():
        Path(filepath).parent.mkdir(parents=True,exist_ok=True)
    if file_type is None:
        with open(filepath,mode) as f:
            f.write(a)
    elif file_type.endswith('json'):
        with open(filepath,mode) as f:
            json.dump(a,f)
    elif file_type.endswith('pkl'):
        with open(filepath,mode) as f:
            pickle.dump(a,f)       

def load(filepath,mode='r',file_type=None):
    if file_type is None:
        with open(filepath,mode) as f:
            data = f.read()
    elif file_type.endswith('json'):
        with open(filepath,mode) as f:
            data = json.load(f)
    elif file_type.endswith('pkl'):
        with open(filepath,mode) as f:
            data = pickle.load(f)    
    return data


def fetch_seasons_hrefs(save_to=None,from_local=False):
    # fetch leagues page
    url = SEASONS_PAGE
    html_text = fetch_html(url,from_local)
    html_soup = make_soup(html_text)
    seasons_list = [a['href'] for th in html_soup.find_all('th', {'data-stat': 'season'}) for a in th.find_all('a')]
    if save_to:
        save_url = f"{save_to}{url}" if url.endswith('.html') else f"{save_to}{url}.html"
        save(html_text,save_url)
    return seasons_list

def fetch_season_boxscores_hrefs(season_href,save_to=None,from_local=False,sleep=0):
    # Load and save season schedule page
    # Check for filters. If so iterate through each filter to get the entire list. Else use the schedule on the current page
    url = f"{HOME_PAGE}{season_href.strip('.html')}_games.html"
    html_text = fetch_html(url,from_local)
    if html_text is None:
        return
    if save_to:
        save_url = f"{save_to}{url}" if url.endswith('.html') else f"{save_to}{url}.html"
        save(html_text,save_url)
        
    html_soup = make_soup(html_text)
    season_boxscores_hrefs = []
    filter_div = html_soup.find('div',{'class':'filter'}) 
    schedule_table = html_soup.find('table', {'id': 'schedule'})
    
    if filter_div is None:
        season_boxscores_hrefs = [a['href'] for th in schedule_table.find_all('td',{'data-stat':'box_score_text'}) for a in th]
    
    # If so iterate through each filter to get the entire list
    else: 
        month_hrefs = [a['href'] for a in filter_div.select('a')]
        for month_href in month_hrefs:
            url = f'{HOME_PAGE}{month_href}'
            html_text = fetch_html(url,from_local)
            if html_text is None:
                continue
            if save_to:
                save_url = f"{save_to}{url}" if url.endswith('.html') else f"{save_to}{url}.html"
                save(html_text,save_url)

            html_soup = make_soup(html_text)
            schedule_table = html_soup.find('table', {'id': 'schedule'})
            season_boxscores_hrefs += [a['href'] for th in schedule_table.find_all('td',{'data-stat':'box_score_text'}) for a in th]
            if sleep:
                time.sleep(sleep)
    return season_boxscores_hrefs

def fetch_match_boxscores(boxscore_href,save_to=None,from_local=None, sleep=0, content_only=True):
    url = f"{HOME_PAGE}{boxscore_href}"
    html_text = fetch_html(url,from_local)
    html_soup = make_soup(html_text)
    box_scores_hrefs = []
    filter_div = html_soup.find('div',{'class':'filter'})
    if filter_div is not None:
        filter_hrefs = [a['href'] for a in filter_div.select('a')]
        for filter_href in filter_hrefs:
            url = f'{HOME_PAGE}{filter_href}'
            html_text = fetch_html(url,from_local)
            if html_text is None:
                continue
            if content_only:
                html_text = str(make_soup(html_text).find('div',{'id':'content'}))
            if save_to:
                save_url = f"{save_to}{url}" if url.endswith('.html') else f"{save_to}{url}.html"
                save(html_text,save_url)
            if sleep:
                time.sleep(sleep)
            box_scores_hrefs.append(filter_href)

    else:
        url = f'{HOME_PAGE}{boxscore_href}'
        html_text = fetch_html(url,from_local)
        if html_text is None:
            pass
        else:
            if save_to:
                save_url = f"{save_to}{url}" if url.endswith('.html') else f"{save_to}{url}.html"
                save(html_text,save_url)
            box_scores_hrefs.append(boxscore_href)
    return box_scores_hrefs



if __name__ == "__main__":
    LOCAL_HOST = '/Volumes/Seagate Portable Disk/University of Manitoba/Data Science/Datasets/basketball-analytics/'
    checkpoint_path = f'{LOCAL_HOST}/checkpoint.pkl'
    # fetch seasons
    if Path(checkpoint_path).exists():
        i_chkpt,j_chkpt = load(checkpoint_path,mode='rb',file_type='.pkl')
        print(f'Resume from checkpoint = {i_chkpt,j_chkpt}')
    else:
        i_chkpt,j_chkpt = 0,0

    seasons_hrefs = fetch_seasons_hrefs(save_to=LOCAL_HOST,from_local=False)
    seasons_hrefs = tqdm(seasons_hrefs,position=0)
    for i,seasons_href in enumerate(seasons_hrefs):
        if i < i_chkpt: 
            continue
        # fetch season boxscores list
        seasons_hrefs.set_description(seasons_href)
        season_boxscores_hrefs = fetch_season_boxscores_hrefs(seasons_href,save_to=LOCAL_HOST,from_local=False, sleep=3)
        season_boxscores_hrefs = tqdm(season_boxscores_hrefs,position=1, leave=False)
        for j,season_boxscores_href in enumerate(season_boxscores_hrefs):
            if (i == i_chkpt) and (j < j_chkpt): 
                continue
            season_boxscores_hrefs.set_description(season_boxscores_href)
            # fetch match box scores
            match_boxscores = fetch_match_boxscores(season_boxscores_href,save_to=LOCAL_HOST,from_local=False, content_only = True,sleep=4)
            save((i,j),checkpoint_path,mode='wb',file_type='.pkl')
    

# source /Users/jasetran/Jase/UM/Git/basketball-analytics/.venv/bin/activate
# /Users/jasetran/Jase/UM/Git/basketball-analytics/.venv/bin/python /Users/jasetran/Jase/UM/Git/basketball-analytics/code/v5/scripts/scrape.py
