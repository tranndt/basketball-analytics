# %%
import sys
# sys.path.insert(0,"../../")

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import *
from bs4.element import PageElement
import time
from base import *

folder = f"code/v3/"
host = f'basketball-reference.com'

# %% [markdown]
# All Franchises

# %%
def parse_all_franchises(soup):
    teams_active = parse_table(soup,'#teams_active tbody tr')
    teams_active = teams_active[teams_active['franch_name'].notna()]
    teams_active['active'] = True
    teams_defunct = parse_table(soup,'#teams_defunct tbody tr')
    teams_defunct = teams_defunct[teams_defunct['franch_name'].notna()]
    teams_defunct['active'] = False
    teams_all = pd.concat([teams_active,teams_defunct],ignore_index=True)
    return teams_all

# url = f'basketball-reference.com/teams/'
# soup = BeautifulSoup(fetch_html(f"{url}"))
# all_franchises = parse_all_franchises(soup)

# if not os.path.isdir(f"{url}"): 
#     os.makedirs(f"{url}")
# all_franchises.to_csv(f"{url}/index.csv")

all_franchises = pd.read_csv(f'{folder}basketball-reference.com/teams/index.csv')
all_franchises

# %% [markdown]
# All Season Summary

# %%
def parse_all_franchise_seasons(soup):
    team_table = parse_table(soup,f'#content tbody tr')
    team_table['playoffs'] = team_table['team_name'].str.endswith("*")
    team_table['team_name'] = team_table['team_name'].str.replace("*","",regex=False)
    return team_table

# for i,franchise_i in all_franchises.iterrows():
#     host = f'basketball-reference.com'
#     url = f"{host}{franchise_i['franch_name_href']}"
#     soup = BeautifulSoup(fetch_html(f"{url}"))
#     all_franchise_seasons = parse_all_franchise_seasons(soup)
#     if not os.path.isdir(f"{url}"): 
#         os.makedirs(f"{url}")
#     # all_franchise_seasons.to_csv(f"{url}/index.csv")
#     print(f"{url}/index.csv")
#     time.sleep(3.2)

# %%
# all_franchise_seasons = pd.read_csv('basketball-reference.com/teams/GSW/index.csv').drop(columns='Unnamed: 0')
# all_franchise_seasons

# %% [markdown]
# Season Game Logs

# %%
def parse_season_gamelogs_basic(soup):
    team_table_regular = parse_table(soup,f'#tgl_basic > tbody > tr:not(.thead)')
    team_table_playoffs = parse_table(soup,f'#tgl_basic_playoffs > tbody > tr:not(.thead)')
    return team_table_regular,team_table_playoffs

def parse_season_gamelogs_advanced(soup):
    team_table_regular = parse_table(soup,f'#tgl_advanced > tbody > tr:not(.thead)')
    team_table_playoffs = parse_table(soup,f'#tgl_advanced_playoffs > tbody > tr:not(.thead)')
    return team_table_regular,team_table_playoffs


# for i,franchise_i in all_franchises.iterrows():
#     url_i = f"{folder}{host}{franchise_i['franch_name_href']}"
#     franchise_i_seasons = pd.read_csv(f'{url_i}index.csv').drop(columns='Unnamed: 0')

#     for j,season_j in franchise_i_seasons.iterrows():
#         for gl_type in ['gamelog','gamelog-advanced']:
#             url_j = f"{host}{season_j['season_href'].strip('.html')}/{gl_type}"
#             print(f"{url_j}")
#             if not os.path.isdir(f"{folder}{url_j}"): 
#                 os.makedirs(f"{folder}{url_j}")
#                 soup = BeautifulSoup(fetch_html(f"{url_j}"),features='lxml')
#                 if gl_type == 'gamelog':
#                     season_j_gamelogs_regular, season_j_gamelogs_playoffs = parse_season_gamelogs_basic(soup)
#                 else:
#                     season_j_gamelogs_regular, season_j_gamelogs_playoffs = parse_season_gamelogs_advanced(soup)

#                 if not season_j_gamelogs_regular.empty:
#                     season_j_gamelogs_regular.to_csv(f"{folder}{url_j}/regular.csv")
#                 if not season_j_gamelogs_playoffs.empty:
#                     season_j_gamelogs_playoffs.to_csv(f"{folder}{url_j}/playoffs.csv")
#                 time.sleep(3.2)


## 

def find_season_urls(team=''):
    folder = f"code/v3/"

    all_franchises = pd.read_csv(f"{folder}basketball-reference.com/teams/index.csv")
    franchises = all_franchises[all_franchises['franch_name_href'].str.contains(team)]
    host = f'basketball-reference.com'
    urls = []
    for i,franchise_i in franchises.iterrows():
        url_i = f"{host}{franchise_i['franch_name_href']}"
        franchise_i_seasons = pd.read_csv(f'{folder}{url_i}index.csv').drop(columns='Unnamed: 0')
        for j,season_j in franchise_i_seasons.iterrows():
            url_j = f"{season_j['season_href']}"
            urls.append(url_j)
    return urls

def shift_values(x,n=1,pad=np.nan):
    if isinstance(x,pd.Series):
        x.loc[:] = [pad]*n + list(x.values[:-n])
    elif isinstance(x,pd.DataFrame):
        x = pd.concat([pd.DataFrame(columns=x.columns,index=range(n)),x.iloc[:-n]],ignore_index=True)
    return x


# for season_j in find_season_urls():
#     url_j = f"{host}{season_j.strip('.html')}"
#     print(url_j)

#     if not os.path.isdir(f"{folder}{url_j}/gamelog-prior") and os.path.isfile(f'{folder}{url_j}/gamelog/regular.csv'):
#         os.makedirs(f"{folder}{url_j}/gamelog-prior")
#         team_basic = pd.read_csv(f'{folder}{url_j}/gamelog/regular.csv').drop(columns=['Unnamed: 0','ranker','x'])
#         team_advanced = pd.read_csv(f'{folder}{url_j}/gamelog-advanced/regular.csv').drop(columns=['Unnamed: 0','ranker','x'])

#         team_basic.loc[:,'game_location'] = team_basic['game_location'] != '@'
#         team_basic.loc[:,'game_result'] = team_basic['game_result'] == 'W'
#         team_basic.loc[:,'net_pts'] = team_basic['pts'] - team_basic['opp_pts']
#         team_advanced.loc[:,'net_rtg'] = team_advanced['off_rtg'] - team_advanced['def_rtg']

#         # Game info
#         game_info = team_basic.columns[:7]
#         team_prior = team_basic.loc[:,game_info].copy()
#         team_prior.insert(2,"team_id",season_j[7:10])
#         team_prior.insert(3,"team_id_href",season_j)
#         team_prior['rest_days_prior'] = pd.to_datetime(team_basic['date_game']).diff().apply(lambda x: x/np.timedelta64(1, 'D')).fillna(0).astype('int64')
#         # team_prior = team_prior

#         # Total/H/A/H2H W%
#         home_record_prior   = shift_values(team_basic.loc[(team_basic['game_location']),'game_result'].expanding().mean())
#         away_record_prior   = shift_values(team_basic.loc[(~team_basic['game_location']),'game_result'].expanding().mean())
#         team_prior.loc[:,'result_prior'] =  shift_values(team_basic['game_result'].expanding().mean())
#         team_prior.loc[:,'location_result_prior'] = pd.concat([home_record_prior,away_record_prior]).sort_index()
#         for opp in pd.unique(team_prior['opp_id']):
#             team_prior.loc[(team_prior['opp_id']==opp),'h2h_result_prior'] = shift_values(team_basic['game_result'][team_basic['opp_id']==opp].expanding().mean())

#         # Team Basic & Advanced Stats
#         basic_stats = team_basic.columns[7:]
#         advanced_stats = team_advanced.columns[9:]
#         team_prior.loc[:,basic_stats] = shift_values(team_basic.loc[:,basic_stats].expanding().mean())
#         team_prior.loc[:,advanced_stats] = shift_values(team_advanced.loc[:,advanced_stats].expanding().mean())

#         # L10 Stats (Delta)
#         team_prior.loc[:,'result_last10_delta'] =  shift_values(team_basic['game_result'].rolling(10).mean())
#         team_prior = team_prior.join(shift_values(team_basic.loc[:,basic_stats].rolling(10).mean()) - team_prior.loc[:,basic_stats],rsuffix="_last10_delta")
#         team_prior = team_prior.join(shift_values(team_advanced.loc[:,advanced_stats].rolling(10).mean()) - team_prior.loc[:,advanced_stats],rsuffix="_last10_delta")

#         team_prior.to_csv(f'{folder}{url_j}/gamelog-prior/regular.csv')
#         ## time.sleep(5)



# for season_j in find_season_urls():
#     url_j = f"{host}{season_j.strip('.html')}"
#     print(url_j)

#     if not os.path.isdir(f"{folder}{url_j}/gamelog-prior-all") and os.path.isfile(f'{folder}{url_j}/gamelog-prior/regular.csv'):
#         os.makedirs(f"{folder}{url_j}/gamelog-prior-all")
#         team_j_prior = pd.read_csv(f'{folder}{url_j}/gamelog-prior/regular.csv').drop(columns="Unnamed: 0")
#         team_j_prior_all = pd.DataFrame()
#         for opp_k in pd.unique(team_j_prior['opp_id_href']):
#             url_k = f"{host}{opp_k.strip('.html')}"
#             opp_k_prior = pd.read_csv(f'{folder}{url_k}/gamelog-prior/regular.csv').drop(columns="Unnamed: 0")
#             team_j_opp_k_prior = team_j_prior.merge(opp_k_prior,how='inner',on='date_game_href',suffixes=['_teamA','_teamB'])
#             team_j_prior_all = pd.concat([team_j_prior_all,team_j_opp_k_prior],ignore_index=True).sort_values(by='game_season_teamA')
#             team_j_prior_all.to_csv(f'{folder}{url_j}/gamelog-prior-all/regular.csv')


# Write gamelog-prior-all to csv
# for j,season_j in enumerate(find_season_urls()):
#     url_j = f"{host}{season_j.strip('.html')}"
#     print(url_j)

#     infile = f"{folder}{url_j}/gamelog-prior-all/regular.csv"
#     outfile = f"{folder}data/gamelog-prior-all/regular.csv"

#     if os.path.isfile(infile):
#         if j == 0:
#             write(read_csv_as_str(infile,skip_header=False),outfile,'w')
#         else:
#             write(read_csv_as_str(infile,skip_header=True),outfile,'a')

# Write gamelog-all to csv
for j,season_j in enumerate(find_season_urls()):
    url_j = f"{host}{season_j.strip('.html')}"
    print(url_j)

    infile_basic = f"{folder}{url_j}/gamelog/regular.csv"
    infile_advanced = f"{folder}{url_j}/gamelog-advanced/regular.csv"
    temp_file = f"{folder}{url_j}/gamelog-all/regular.csv"
    outfile = f"{folder}data/gamelog-all/regular.csv"

    if os.path.isfile(infile_basic) and os.path.isfile(infile_advanced):
        if not os.path.isdir(f"{folder}{url_j}/gamelog-all"):
            os.makedirs(f"{folder}{url_j}/gamelog-all")

        gamelog_basic = pd.read_csv(infile_basic).drop(columns=['Unnamed: 0','ranker','x'])
        gamelog_advanced = pd.read_csv(infile_advanced).drop(columns=['Unnamed: 0','ranker','x'])
        gamelog_all = gamelog_basic.merge(gamelog_advanced,how='inner',on='date_game_href',suffixes=['','_advanced'])
        gamelog_all.insert(2,"team_id",season_j[7:10])
        gamelog_all.insert(3,"team_id_href",season_j)
        gamelog_all['net_pts'] = gamelog_all['pts'] - gamelog_all['opp_pts']
        gamelog_all['net_rtg'] = gamelog_all['off_rtg'] - gamelog_all['def_rtg']
        gamelog_all.to_csv(temp_file)
        
        if j == 0:
            write(read_csv_as_str(temp_file,skip_header=False),outfile,'w')
        else:
            write(read_csv_as_str(temp_file,skip_header=True),outfile,'a')