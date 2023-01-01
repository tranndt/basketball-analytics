import sys

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import *
from bs4.element import PageElement
from base import *
import time
from IPython.display import display_html
import os

from sklearn.tree import *
from sklearn.ensemble import *
from sklearn.linear_model import *
from sklearn.model_selection import train_test_split

def fetch_hrefs_list(source,allowed_hrefs=('/players','/teams','/leagues','/boxscores')):
    soup = BeautifulSoup(fetch_html(source),features='lxml')
    hrefs = [a['href'] for a in soup.find_all("a",href=True) if a['href'].startswith(allowed_hrefs)]
    return hrefs

def update_hrefs_index(hrefs_index=None,hrefs=[],host="https://basketball-reference.com",output=None):
    if isinstance(hrefs,str):
        hrefs = [hrefs]
    for href in hrefs:
        if href not in pd.unique(hrefs_index['host_href']):
            local_href = f"./{host.strip('https://')}{href}" if href.endswith('.html') else f"./{host.strip('https://')}{href}index.html"
            hrefs_index.loc[len(hrefs_index)] = {'host_href':href,'local_href':local_href,'last_updated':np.nan}
    if output is not None:
        hrefs_index.to_csv(output)
    return hrefs_index

def fetch_update_hrefs_index(hrefs_index,host = "https://basketball-reference.com",page="/",fetch_subpages=False,output=None,sleep=3.5):
    hrefs = fetch_hrefs_list(f"{host}{page}")
    hrefs_index = update_hrefs_index(hrefs_index,hrefs,host=host,output=output)
    if fetch_subpages:
        next_hrefs = hrefs
        prev_hrefs = [page]
        for href_i in next_hrefs:
            print(f"{len(prev_hrefs)}/{len(next_hrefs)}  {href_i}")
            if href_i not in prev_hrefs:
                all_hrefs_ij = fetch_hrefs_list(f"{host}{href_i}")
                hrefs_index = update_hrefs_index(hrefs_index,all_hrefs_ij,host=host,output=output)
                next_hrefs = (next_hrefs + all_hrefs_ij)[1:]
                prev_hrefs.append(href_i)
                time.sleep(sleep)
            else:
                next_hrefs = next_hrefs[1:]
    return hrefs_index

def fetch_update_hrefs_html(hrefs_index,host="https://basketball-reference.com",page="/",last_updated=1,sleep=3.5,output=None):
    update_rows = (hrefs_index['host_href'].str.startswith(page)
                    & ((pd.to_datetime(hrefs_index['last_updated']) <= pd.Timestamp.today() - last_updated * pd.Timedelta(1,'D')) | hrefs_index['last_updated'].isna()))
    for i,href_row in hrefs_index[update_rows].iterrows():
        hrefs_index.loc[i,'last_updated'] = pd.Timestamp.today()
        html_url = f"{host}{href_row['host_href']}"
        local_url = f"{href_row['local_href']}"
        write(fetch_html(html_url),local_url)
        hrefs_index.to_csv(output)
        time.sleep(sleep)
    return hrefs_index 



hrefs_index_filepath = 'basketball-reference.com/hrefs_index.csv'
hrefs_index = pd.read_csv(hrefs_index_filepath).drop(columns='Unnamed: 0')
hrefs_index = fetch_update_hrefs_index(hrefs_index,page="/",fetch_subpages=True,output=hrefs_index_filepath)
hrefs_index = fetch_update_hrefs_html(hrefs_index,page="/",last_updated=0,output=hrefs_index_filepath)