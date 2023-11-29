# function to get the html of a page
from bs4 import *
from bs4.element import PageElement
import time
import requests
import re

HOME_PAGE = 'https://www.basketball-reference.com'
SEASONS_PAGE = 'https://www.basketball-reference.com/leagues'
TEAMS_PAGE = 'https://www.basketball-reference.com/teams'
BOXSCORES_PAGE = 'https://www.basketball-reference.com/boxscores'

def request_html_text(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        return "Error"

# function to get the bs html of a page    
def request_html_soup(url):
    html_text = request_html_text(url)
    return parse_html_soup(html_text)

def clean_html_text(html_text):
    return re.sub(r'<!--|-->', '', html_text)

def parse_html_soup(html_text):
    return BeautifulSoup(html_text, 'html.parser')

def content_div_only(soup):
    return soup.find('div',{'id':'content'})

# function to get all seasons
def req_all_seasons_hrefs() -> list:
    seasons = []
    html_soup = request_html_soup(SEASONS_PAGE)
    try:
        for th in html_soup.find_all('th', {'data-stat': 'season'}):
            for a in th.find_all('a'):
                seasons.append(a['href'])
    except Exception as e:
        print(f'Error getting seasons: {e}')
    return seasons

def req_season_games_hrefs(season_href,sleep=3) -> list:
    games = []
    html_soup = request_html_soup(HOME_PAGE + season_href.strip('.html')+'_games.html')
    filter_div = html_soup.find('div',{'class':'filter'}) 
    schedule_table = html_soup.find('table', {'id': 'schedule'})
    try:
        if filter_div is None:
            for td in html_soup.find_all('td', {'data-stat': 'box_score_text'}):
                for a in td.find_all('a'):
                    games.append(a['href'])
        else:
            month_hrefs = [a['href'] for a in filter_div.select('a')]
            for month_href in month_hrefs:
                html_soup = request_html_soup(HOME_PAGE + month_href)
                schedule_table = html_soup.find('table', {'id': 'schedule'})
                for td in schedule_table.find_all('td', {'data-stat': 'box_score_text'}):
                    for a in td.find_all('a'):
                        games.append(a['href'])
                time.sleep(sleep)
    except Exception as e:
        print(f'Error getting boxscores for season {season_href}: {e}')
    return games

def req_game_boxscores_hrefs(game_href) -> dict:
    boxscores = []
    try:
        html_soup = request_html_soup(HOME_PAGE + game_href)
        filter_div = html_soup.find('div',{'class':'filter'})
        if filter_div is not None:
            filter_hrefs = [a['href'] for a in filter_div.select('a')]
            for filter_href in filter_hrefs:
                boxscores.append(filter_href)
        else:
            boxscores.append(game_href)
    except Exception as e:
        print(f'Error getting boxscores hrefs for game {game_href}: {e}')
    return boxscores
