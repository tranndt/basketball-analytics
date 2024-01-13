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


