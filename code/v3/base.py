import sys
sys.path.insert(0,"../../")

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import *
from bs4.element import PageElement
import os

TEAM_CODE = {
    'Atlanta Hawks': 'ATL',
    'Boston Celtics': 'BOS',
    'Brooklyn Nets': 'BRK',
    'Charlotte Hornets': 'CHO',
    'Chicago Bulls': 'CHI',
    'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL',
    'Denver Nuggets': 'DEN',
    'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW',
    'Houston Rockets': 'HOU',
    'Indiana Pacers': 'IND',
    'Los Angeles Clippers': 'LAC',
    'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA',
    'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK',
    'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI',
    'Phoenix Suns': 'PHO',
    'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC',
    'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS'
}


def filedir_name(filepath):
    loc = filepath[::-1].find("/")
    if loc == -1:
        return "./",filepath
    else:
        return filepath[:-loc],filepath[-loc:]

def write(content,filepath,mode='w'):
    filedir,filename = filedir_name(filepath)
    if not os.path.isdir(filedir): 
        os.makedirs(filedir)
    with open(filepath, mode) as file:
        file.write(content)

def read_csv_as_str(filepath,skip_header=False):
    content = ""
    with open(filepath, 'r') as file:
        if skip_header:
            file.readline()
        content = file.read()
    return content


def new_session():
    return requests.Session()

def fetch_html(url,session=None):
    if not url.startswith("https://"):
        url = "https://"+url
    if session is None:
        session = requests.Session()
    return re.sub("<!--|-->","\n",session.get(url).text)




# def parse_trow(row):
#     return {ele["data-stat"]:ele.text for ele in row.select('th,td')}

def parse_trow(row,href=True):
    row_data = {}
    for ele in row.select('th,td'):
        row_data[ele['data-stat']] = ele.text 
        if href and ele.a:
            row_data[ele['data-stat'] + "_href"] = ele.a['href']
    return row_data

def parse_table(soup,selector,href=True):
    table_rows = soup.select(selector)
    parsed_tables = pd.DataFrame([parse_trow(row,href) for row in table_rows])
    return parsed_tables

# def parse_match_homeaway(soup,teamcode=True):
#     pattern = ".scorebox a"
#     away,home = [a.text for a in soup.select(pattern) if a.text in TEAM_CODE.keys()]
#     if teamcode:
#         away = TEAM_CODE[away]
#         home = TEAM_CODE[home]
#     return away,home

def parse_match_homeaway(soup):
    away,home = soup.select('#content .scorebox strong a')
    parsed_homeaway = pd.DataFrame([
        {'type':'away', 'team':away['href'][7:10] , 'name':away.text, 'team_href': away['href']},
        {'type':'home', 'team':home['href'][7:10] , 'name':home.text, 'team_href': home['href']}])
    return parsed_homeaway

def parse_match_boxscores(soup):
    away,home = parse_match_homeaway(soup)['team']
    patterns = {
        'four_factors'  : f'#four_factors > tbody > tr',
        'line_score'    : f'#line_score > tbody > tr',
        'away-basic'    : f'#box-{away}-game-basic > tbody > tr:not(.thead)',
        'away-advanced' : f'#box-{away}-game-advanced > tbody > tr:not(.thead)',
        'home-basic'    : f'#box-{home}-game-basic > tbody > tr:not(.thead)',
        'home-advanced' : f'#box-{home}-game-advanced > tbody > tr:not(.thead)',
        'away-basic-totals'    : f'#box-{away}-game-basic > tfoot > tr:not(.thead)',
        'away-advanced-totals' : f'#box-{away}-game-advanced > tfoot > tr:not(.thead)',
        'home-basic-totals'    : f'#box-{home}-game-basic > tfoot > tr:not(.thead)',
        'home-advanced-totals' : f'#box-{home}-game-advanced > tfoot > tr:not(.thead)', 
        **{ f'away-{period}-basic': f'#box-{away}-{period}-basic > tbody > tr:not(.thead)'
                for period in ['q1','q2','q3','q4','h1','h2']},
        **{ f'home-{period}-basic': f'#box-{home}-{period}-basic > tbody > tr:not(.thead)'
                for period in ['q1','q2','q3','q4','h1','h2']},          
        }
    boxscores_tables = {  
        name : parse_table(soup,selector,href=True) for name,selector in patterns.items() 
    }

    return boxscores_tables


# def parse_schedule(soup):
#     pattern = "#div_schedule tbody tr:not(.thead)"
#     schedule_rows = soup.select(pattern)
#     schedule_data = []
#     for row in schedule_rows:
#         row_data = {ele["data-stat"]:ele.text if ele["data-stat"] != 'box_score_text' 
#                     else ele.select_one('a')['href'].strip(r'/boxscores/|.html') for ele in row.select('th,td')}
#         schedule_data.append(row_data)
#     parsed_tables = pd.DataFrame(schedule_data)
#     return parsed_tables

def parse_schedule(soup):
    pattern = "#div_schedule tbody tr:not(.thead)"
    parsed_table =  parse_table(soup,pattern)
    return parsed_table