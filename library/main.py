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

TEAM_CODE = {
'Atlanta Hawks':'ATL',
 'Boston Celtics':'BOS',
 'Brooklyn Nets':'BRK',
 'Charlotte Hornets':'CHO',
 'Chicago Bulls':'CHI',
 'Cleveland Cavaliers':'CLE',
 'Dallas Mavericks':'DAL',
 'Denver Nuggets':'DEN',
 'Detroit Pistons':'DET',
 'Golden State Warriors':'GSW',
 'Houston Rockets':'HOU',
 'Indiana Pacers':'IND',
 'Los Angeles Clippers':'LAC',
 'Los Angeles Lakers':'LAL',
 'Memphis Grizzlies':'MEM',
 'Miami Heat':'MIA',
 'Milwaukee Bucks':'MIL',
 'Minnesota Timberwolves':'MIN',
 'New Orleans Pelicans':'NOP',
 'New York Knicks':'NYK',
 'Oklahoma City Thunder':'OKC',
 'Orlando Magic':'ORL',
 'Philadelphia 76ers':'PHI',
 'Phoenix Suns':'PHO',
 'Portland Trail Blazers':'POR',
 'Sacramento Kings':'SAC',
 'San Antonio Spurs':'SAS',
 'Toronto Raptors':'TOR',
 'Utah Jazz':'UTA',
 'Washington Wizards':'WAS'
}

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