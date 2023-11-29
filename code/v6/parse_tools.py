import pandas as pd
import numpy as np
import sys
import os
import bs4
from IPython.display import display_html,clear_output, HTML
import re
from datetime import datetime
import ast
import itertools
from tqdm import tqdm,trange
from file_tools import *
from request_tools import *

def iter_tables(tables,sleep=2):
    if isinstance(tables,dict):
        tables_list = tables.items()
    elif isinstance(tables,(list,tuple)):
        tables_list = enumerate(tables)
    tables_list = tqdm(tables_list)
    for table_id, table in tables_list:
        tables_list.set_description(table_id)
        display_html(table)
        time.sleep(sleep)
        clear_output()

def convert_time_to_minutes(time_str):
    if pd.notnull(time_str) and re.match(r'\d{1,2}:\d{2}',time_str):
        minutes, seconds = time_str.split(':')
        return float(minutes) + float(seconds) / 60.0
    else:
        return pd.NA

def convert_series_dtype(series):
    # backend = {'numpy':np, 'pyarrow':pa}[backend]
    try:    return series.astype(pd.Int32Dtype())
    except: pass
    try:    return series.astype(pd.Float32Dtype())
    except: pass
    try:    return series.astype(str).apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    except: pass
    try:
        if series.str.contains('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}').all():
            return series.apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
        elif series.str.contains('\d{4}-\d{2}-\d{2}').all():
            return pd.to_datetime(series, format='%Y-%m-%d')
        elif series.str.isnumeric().all():
            return series.astype(pd.Int32Dtype())
        elif series.str.isnumeric().any():
            return series.astype(pd.Float32Dtype())
    except: pass
    return series 

def parse_html_table(html_text,**kwargs):
    return pd.concat(pd.read_html(html_text,flavor='bs4',**kwargs))

def parse_as_html_table_with_hrefs(html_text,columns=None):
    df_hrefs = parse_html_table(html_text,extract_links='all')
    # For each column in df, split the column into two columns, one for the text and one for the href
    org_columns = df_hrefs.columns 
    for col in df_hrefs.columns:
        col_name = col[1][0]
        df_hrefs[[col_name,col_name+'_href']] = pd.DataFrame(df_hrefs[col].tolist(), index=df_hrefs.index)
    # Drop the original columns and any empty columns
    df_hrefs = df_hrefs.drop(columns=org_columns)
    df_hrefs.dropna(axis=1,how='all',inplace=True)
    return df_hrefs

def __parse_boxscores_tables_type1__(html_text):
    html_soup = parse_html_soup(html_text)
    parsed_boxscores_tables = {}
    for table_elmt in html_soup.find_all('table'):
        table_id = table_elmt.get('id')
        if table_id in ['line_score','four_factors']:
            df = parse_as_html_table_with_hrefs(str(table_elmt))
            df.columns = df.columns.str.lower()
            df.rename({'':'team','_href':'team_href'},axis=1,inplace=True)
            parsed_boxscores_tables[table_id] = df
    return parsed_boxscores_tables


def __parse_boxscores_tables_type2__(html_text):
    # parse box scores that starts with box
    table_away_home_teams = __parse_game_info_tables__(html_text)['info-away-home-teams']
    away,home = table_away_home_teams['team_id']
    away_href,home_href = table_away_home_teams['team_href']

    html_soup = parse_html_soup(html_text)
    parsed_boxscores_tables = {}
    for table_elmt in html_soup.find_all('table'):
        table_id = table_elmt.get('id')
        if table_id and table_id.startswith('box'):
            if away in table_id:
                table_id = re.sub(away,'away',table_id)
                team = away
                team_href = away_href
            elif home in table_id:
                table_id = re.sub(home,'home',table_id)
                team = home
                team_href = home_href

            df_team_stats = parse_as_html_table_with_hrefs(table_elmt.prettify())
            df_team_stats.columns = df_team_stats.columns.str.lower()
            for na_keywords in ['Did Not Play','Did Not Dress','Coach\'s Decision','']:
                df_team_stats.replace(na_keywords, pd.NA,inplace=True)

            df_team_totals = df_team_stats[df_team_stats['starters'] == 'Team Totals'].copy()
            df_team_totals.rename(columns={'starters':'team','starters_href':'team_href'},inplace=True)
            df_team_totals[['team','team_href']] = [team,team_href]

            df_players_stats = df_team_stats[~df_team_stats['starters'].isin(('Reserves','Team Totals'))].copy()
            df_players_stats = df_players_stats.apply(convert_series_dtype)
            df_players_stats.rename(columns={'starters':'player','starters_href':'player_href'},inplace=True)
            df_players_stats.insert(0,'team',team)
            df_players_stats.insert(1,'team_href',team_href)
            df_players_stats['mp'] = df_players_stats['mp'].apply(convert_time_to_minutes)

            parsed_boxscores_tables[table_id] = df_players_stats
            parsed_boxscores_tables[table_id+'-total'] = df_team_totals
    return parsed_boxscores_tables

def __parse_game_info_tables__(html_text):
    html_soup = parse_html_soup(html_text)
    away,home = html_soup.select('div .scorebox strong a')
    df_game_info = []
    for team_type, team_element in zip(('away','home'),(away,home)):
        team_name = team_element.text
        team_href = team_element['href']
        team_id,season = re.search(r'/teams/(?P<team>\w+)/(?P<season>\d+)\.html',team_href).groups()
        df_game_info.append([team_id, team_href, team_name.strip(), season, team_type])
    df_game_info = pd.DataFrame(df_game_info,columns = ['team_id', 'team_href', 'team_name', 'season', 'team_type'])
    return {'info-away-home-teams': df_game_info}    
    
def parse_all_boxscores_tables(html_text):
    parsed_boxscores_tables = {
        **__parse_game_info_tables__(html_text),
        **__parse_boxscores_tables_type1__(html_text),
        **__parse_boxscores_tables_type2__(html_text),
    }
    return parsed_boxscores_tables

def parse_all_boxscores_tables_from_file(file_name):
    html_text = load_file(file_name)
    html_text = clean_html_text(html_text)
    return parse_all_boxscores_tables(html_text)


# Parse Game Logs Logic

def __parse_team_gamelogs_basic__(html_text):
    df_gamelog_basic = parse_html_table(html_text)
    # Rename columns
    df_gamelog_basic.rename(
        columns={'Unnamed: 3_level_1':'H/A', 
            **{f'Unnamed: {i}_level_0':'Match' for i in range(5)},
            **{f'Unnamed: {i}_level_0':'Result' for i in range(5,8)}},
        inplace=True)
    # Drop columns
    df_gamelog_basic.drop(
        columns=[('Unnamed: 24_level_0', 'Unnamed: 24_level_1'),
                ('Match','Rk')], inplace=True)
    # Filter out rows that are not games
    game_filter = df_gamelog_basic.loc[:,('Match','G')].astype(str).str.isnumeric().fillna(False)
    df_gamelog_basic = df_gamelog_basic.loc[game_filter,:]
    # Extract opponent hrefs
    df_hrefs = parse_html_table(html_text,extract_links='body')
    boxscores_hrefs = df_hrefs.loc[game_filter,'Unnamed: 2_level_0']
    opponent_hrefs = df_hrefs.loc[game_filter,'Unnamed: 4_level_0']
    df_gamelog_basic.insert(2,('Match','Boxscores_html_id'),[href[0][-1] for href in boxscores_hrefs.values])
    df_gamelog_basic.insert(3,('Match','H/A'),df_gamelog_basic.pop(('Match','H/A')))
    df_gamelog_basic.insert(5,('Match','Opp_html_id'),[href[0][-1] for href in opponent_hrefs.values])
    # Convert columns to numeric
    df_gamelog_basic.loc[:,('Match','H/A')] = df_gamelog_basic[('Match','H/A')].isna().astype(int)
    df_gamelog_basic.loc[:,('Result','W/L')] = df_gamelog_basic[('Result','W/L')].str.startswith('W').astype(int)
    df_gamelog_basic = df_gamelog_basic.apply(convert_series_dtype)
    df_gamelog_basic.reset_index(drop=True,inplace=True)

    return df_gamelog_basic

def __parse_team_gamelogs_advanced__(html_text):
    df_gamelog_advanced = parse_html_table(html_text)
    # Rename columns
    df_gamelog_advanced.rename(
        columns={'Unnamed: 3_level_1':'H/A', 
            **{f'Unnamed: {i}_level_0':'Match' for i in range(5)},
            **{f'Unnamed: {i}_level_0':'Result' for i in range(5,8)}},
        inplace=True)
    # Drop columns
    df_gamelog_advanced.drop(
        columns=[('Unnamed: 23_level_0', 'Unnamed: 23_level_1'),
                ('Unnamed: 18_level_0', 'Unnamed: 18_level_1'),
                ('Match','Rk')], inplace=True)
    # Filter out rows that are not games
    game_filter = df_gamelog_advanced.loc[:,('Match','G')].astype(str).str.isnumeric().fillna(False)
    df_gamelog_advanced = df_gamelog_advanced.loc[game_filter,:]
    # Extract opponent hrefs
    df_hrefs = parse_html_table(html_text,extract_links='body')
    boxscores_hrefs = df_hrefs.loc[game_filter,'Unnamed: 2_level_0']
    opponent_hrefs = df_hrefs.loc[game_filter,'Unnamed: 4_level_0']
    df_gamelog_advanced.insert(2,('Match','Boxscores_html_id'),[href[0][-1] for href in boxscores_hrefs.values])
    df_gamelog_advanced.insert(3,('Match','H/A'),df_gamelog_advanced.pop(('Match','H/A')))
    df_gamelog_advanced.insert(5,('Match','Opp_html_id'),[href[0][-1] for href in opponent_hrefs.values])
    # Convert columns to numeric
    df_gamelog_advanced.loc[:,('Match','H/A')] = df_gamelog_advanced[('Match','H/A')].isna().astype(int)
    df_gamelog_advanced.loc[:,('Result','W/L')] = df_gamelog_advanced[('Result','W/L')].str.startswith('W').astype(int)
    df_gamelog_advanced = df_gamelog_advanced.apply(convert_series_dtype)
    df_gamelog_advanced.reset_index(drop=True,inplace=True)
    return df_gamelog_advanced

def parse_all_team_gamelogs_tables(html_text):
    all_team_gamelogs_tables = {}
    for _id in ['tgl_basic','tgl_basic_playoffs','tgl_advanced','tgl_advanced_playoffs']:
        html_soup = parse_html_soup(html_text)
        tgl_table = html_soup.find('table', {'id': _id})
        if tgl_table:
            tgl_html = tgl_table.prettify()
            if _id in ['tgl_basic','tgl_basic_playoffs']:
                all_team_gamelogs_tables[_id] = __parse_team_gamelogs_basic__(tgl_html)
            elif _id in ['tgl_advanced', 'tgl_advanced_playoffs']:
                all_team_gamelogs_tables[_id] = __parse_team_gamelogs_advanced__(tgl_html)
    return all_team_gamelogs_tables

def parse_all_team_gamelogs_tables_from_file(file_name):
    html_text = load_file(file_name)
    html_text = clean_html_text(html_text)
    return parse_all_team_gamelogs_tables(html_text)

def parse_team_html_id(html_dir):
    # Check to see if the pattern starts with keywords 'teams','boxscores','players','leagues'
    # If not, return None
    if not re.match(r'(.*)/teams/(.*)/(.*)',html_dir):
        return None
    # Otherwise, parse the directory
    pattern = r'(.*)(/teams/([A-Z]{3})/([0-9]{4}))(.*)'
    match = re.match(pattern,html_dir)
    return {
        'head': match.group(1),
        'body': match.group(2),
        'foot': match.group(5),
    }