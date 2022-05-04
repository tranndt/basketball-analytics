import sys
sys.path.insert(0,"../../")

from library import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import *
from bs4.element import PageElement

def new_session(headers=None):
    session = requests.Session()
    if headers:
        session.headers.update(headers)
    return session

def get_url(url):
    content = new_session().get(url).text
    return content

def strip_html_comment(string): 
    import re
    return re.sub("<!--|-->","",string)

def parse_table(source, trow_selector):
    soup = source if isinstance(source,(BeautifulSoup,PageElement)) else BeautifulSoup(source,"html.parser")
    row_tags = soup.select(trow_selector)
    parsed_rows = [parse_trow(row) for row in row_tags]
    return pd.DataFrame(parsed_rows)

def parse_trow(source):
    soup = source if isinstance(source,(BeautifulSoup,PageElement)) else BeautifulSoup(source,"html.parser")
    return {ele["data-stat"]:ele.text for ele in soup.select('th,td')}     # values = soup.get_text(sep).split(sep)

def parse_box_scores(source,teams):
    away,home = teams
    box_scores_meta = {
        'four_factors'  : f'#four_factors > tbody > tr',
        'line_score'    : f'#line_score > tbody > tr',
        'away-basic'    : f'#box-{away}-game-basic > tbody > tr:not(.thead)',
        'away-advanced' : f'#box-{away}-game-advanced > tbody > tr:not(.thead)',
        'home-basic'    : f'#box-{home}-game-basic > tbody > tr:not(.thead)',
        'home-advanced' : f'#box-{home}-game-advanced > tbody > tr:not(.thead)',
        # 'away-basic'    : f'#box-{away}-game-basic > tfoot > tr:not(.thead)',
        **{
            f'away-{period}-basic': f'#box-{away}-{period}-basic > tbody > tr:not(.thead)'
                for period in ['q1','q2','q3','q4','h1','h2']
        },
        **{
            f'home-{period}-basic': f'#box-{home}-{period}-basic > tbody > tr:not(.thead)'
                for period in ['q1','q2','q3','q4','h1','h2']
        },          
    }
    tables = {  
        name : parse_table(source,selector) for name,selector in box_scores_meta.items() 
    }
    return tables

def get_box_scores(match_code,write_to_folder=None):
    flushif(True,f"\r{match_code}")
    page_content = get_url(f'https://www.basketball-reference.com/boxscores/{match_code}.html')
    source = BeautifulSoup(strip_html_comment(str(page_content)),"html.parser")
    tables = parse_box_scores(source,(d['Visitor'],d['Home']))
    for name,table in tables.items():
        assert(not table.empty)
        if write_to_folder:
            write_dataframe(table,f"{write_to_folder}/{match_code}/{name}.csv")
    return tables

season = pd.read_csv("../../data/21-22/results.csv")
for i,d in season.iterrows():
    get_box_scores(d['Code'],write_to_folder='../../data/21-22/box_scores')