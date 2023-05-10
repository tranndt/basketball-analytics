from bs4 import BeautifulSoup
from pathlib import Path
import os
import warnings
from tqdm import tqdm,trange
from datetime import datetime
from collections import defaultdict
from IPython.display import display,HTML,display_html,clear_output
import hashlib
import time
import requests
import re
import numpy as np
import pandas as pd
import ast

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

def save(a,filepath,mode='w'):
    try:
        if not Path(filepath).exists():
            Path(filepath).parent.mkdir(parents=True,exist_ok=True)
        with open(filepath,mode) as f:
            f.write(a)
        return True
    except Exception as e:
        print(f'Failed to save file to {filepath} due to error: {e}')
        return False

def load(filepath,mode='r'):
    data = None
    if Path(filepath).exists():
        with open(filepath,mode) as f:
            data = f.read()
    return data

def soup(html_text):
    try:
        return BeautifulSoup(html_text,features='html.parser')
    except Exception as e:
        return None
    

def paths_join(*args):
    path = '/'.join([path.strip('/') for path in args])
    if args[0].startswith('/'):
        return '/'+path
    return path
    
class PageHTML:
    def get_subclasses():
        return [
        AllBoxscoresIndexHTML, BoxscoresStatsHTML, BoxscoresPbpHTML, BoxscoresShotchartHTML,BoxscoresPlusMinusHTML,
        AllSeasonsIndexHTML, SeasonIndexHTML, SeasonScheduleIndexHTML, SeasonScheduleMonthlyHTML,
        AllTeamsIndexHTML, TeamIndexHTML, TeamSeasonIndexHTML, TeamSeasonGamelogHTML,
        AllPlayersIndexHTML, PlayersAlphabetHTML, PlayerIndexHTML
    ]

    def __init__(self, file_href='',content_only=False, host='https://www.basketball-reference.com',local='') -> None:
        self.params     = dict(file_href=file_href,content_only=content_only,host=host,local=local)
        self.content_only_ = content_only
        self.host_       = host
        self.local_      = local
        self.href_       = self.__href__(file_href,host=host) #self.__host_href__(self.file_href) 
        self.host_url_   = self.__host_url__(self.href_,host=host) 
        self.local_url_  = self.__local_url__(self.href_,local=local) 
        self.html_text_  = None
        self.content_type_    = None    
        if not PageHTML.is_valid_href(file_href=file_href):
            warnings.warn(f"href='{file_href}' may be invalid for {self.__class__.__name__}",stacklevel=0)

    def auto_instance(self):
        for subclass in PageHTML.get_subclasses():
            if subclass.is_valid_href(file_href=self.href_):
                return subclass(**self.params)
        return self   

    def __href__(self,file_href,host='https://www.basketball-reference.com'):
        return re.sub(fr'({host})|(__index__.html)','',file_href) 

    def __host_url__(self,file_href,host='https://www.basketball-reference.com'):
        if not file_href.startswith(host):
            return paths_join(host,file_href)
        return file_href
    
    def __local_url__(self,file_href,local=''):
        local_path = local
        if isinstance(local_path,BaseDatabaseManager):
            local_path = local.path()
        if not file_href.endswith('.html'):
            return paths_join(local_path,file_href,'__index__.html')
        else:
            return paths_join(local_path,file_href)


    def text(self):
        return self.html_text_
        
    def soup(self):
        return soup(self.html_text_)
    
    def content_only(self,content_only=True):
        self.content_only_ = content_only
        if content_only:
            try:
                html_soup = self.soup()
                if html_soup.get('id') != 'content':
                    self.html_text_ = str(html_soup.find('div',{'id':'content'}))
            except Exception as e:
                print(f'Failed to get soup content due to error: {e}')
        return self

    def set_local(self,local):
        self.local_ = local
        self.local_url_  = self.__local_url__(self.href_,local=local) 

    def diff(self,other):
        h1 = self.__hash__() 
        h2 = other.__hash__()
        if h1 is None or h2 is None:
            warnings.warn(f'One of {str(self)} or {str(other)} may not have been collected')
            return None
        else:
            return h1 != h2

    def fetch(self,warn=True,wait=0):
        # full_url = f'{self.host_url_}' if self.host_url_.startswith("https://") else f'https://{self.host_url_}'
        session = requests.Session().get(self.host_url_)
        time.sleep(wait)
        if session.status_code == 200:
            self.html_text_ = re.sub("<!--|-->","\n",session.text)
            self.content_type_ = 'online'
            self.content_only(self.content_only_)
            return True
        else:
            if warn:
                warnings.warn(f'Failed to fetch {self.host_url_} due to error: {session.status_code} {session.reason}.')
            return False
        
    def load(self,warn=True,wait=0):
        raw_html_text = load(self.local_url_)
        time.sleep(wait)
        if raw_html_text:
            self.html_text_ = re.sub("<!--|-->","\n",raw_html_text)
            self.content_type_ = 'local'
            self.content_only(self.content_only_)
            return True
        else:
            if warn:
                warnings.warn(f'Failed to load {self.local_url_}.')
            return False

    def save(self):
        if save(self.html_text_, self.local_url_):
            return True
        else:
            warnings.warn(f'Failed to save to {self.local_url_}.')
            return False

    def render(self, warn=True):
        if self.html_text_:
            display(HTML(self.html_text_))
        elif warn:
            warnings.warn(f'Empty content for {str(self)}. Have you called .fetch() or .load()?')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(\'{self.host_url_}\', content_type={self.content_type_})'

    def __hash__(self):
        if self.content_type_:
            return hashlib.md5(self.html_text_.encode()).hexdigest()
        else:
            return None
        

    def is_valid_href(file_href=None):
        return True

    def bottom_nav_hrefs(self):
        return [a['href'] for a in self.soup().select('div#bottom_nav li a')]
    
    def downstream_hrefs(self):
        return [
            '/leagues/',
            '/teams/',
            '/boxscores/',
            '/players/',
        ]
    
    def parse(self,extract_hrefs=True):
        parsed_tables = {}
        for i,table in enumerate(self.soup().find_all('table')):
            table_id = f'table_{i}'
            if table.get('id'):
                table_id = table.get('id')
            parsed_tables[table_id] = self.parse_table(table,extract_hrefs=extract_hrefs)
        return parsed_tables

    def parse_table(self,table,extract_hrefs=True):
        df_text = pd.concat(pd.read_html(str(table),flavor='bs4'))
        if isinstance(df_text.columns,pd.MultiIndex):
            df_text = df_text.droplevel(0,axis=1)

        if extract_hrefs:
            df_hrefs = pd.concat(pd.read_html(str(table),flavor='bs4',extract_links='all'))
            if isinstance(df_hrefs.columns,pd.MultiIndex):
                df_hrefs = df_hrefs.droplevel(0,axis=1)
            href_cols = []
            for i,col in enumerate(df_text.columns):
                text_col = df_text[col]
                href_cols.append(text_col)

                href_col = df_hrefs.iloc[:,i].apply(lambda x: x if pd.isnull(x) else x[1]).rename(f'{col}_href')
                if href_col.notnull().any():
                    href_cols.append(href_col)
            return pd.concat(href_cols,axis=1)
        return df_text

class AllTeamsIndexHTML(PageHTML):

    def __init__(self, file_href='/teams/', content_only=False, host='https://www.basketball-reference.com',local='') -> None:
        super().__init__(file_href=file_href,content_only=content_only,host=host,local=local)

    def is_valid_href(file_href):
        return re.search(r'/teams(/|\b)$',file_href)

    def teams_hrefs(self):
        teams_active = [a['href'] for a in self.soup().select('table#teams_active tr.full_table th a')]
        teams_defunct = [a['href'] for a in self.soup().select('table#teams_defunct tr.full_table th a')]
        return {
            'teams_active': teams_active,
            'teams_defunct': teams_defunct,
            'all': teams_active+ teams_defunct
        }

    def downstream_hrefs(self):
        return self.teams_hrefs()
        
class AllSeasonsIndexHTML(PageHTML):

    def __init__(self,file_href='/leagues/',content_only=False, host='https://www.basketball-reference.com',local='') -> None:
        super().__init__(file_href=file_href,content_only=content_only,host=host,local=local)
        self.main_hrefs = self.seasons_hrefs

    def is_valid_href(file_href):
        return re.search(r'/leagues(/|\b)$',file_href)

    def seasons_hrefs(self):
        return [a['href'] for th in self.soup().find_all('th', {'data-stat': 'season'}) for a in th.find_all('a')]

    def downstream_hrefs(self):
        return self.seasons_hrefs()

class AllPlayersIndexHTML(PageHTML):

    def __init__(self, file_href='/players/', content_only=False, host='https://www.basketball-reference.com',local='') -> None:
        super().__init__(file_href=file_href,content_only=content_only,host=host,local=local)

    def is_valid_href(file_href):
        return re.search(r'/players(/|\b)$',file_href)
    
    def players_alphabet_hrefs(self):
        return [a['href'] for a in self.soup().select('div#div_alphabet li a')]

    def downstream_hrefs(self):
        return self.players_alphabet_hrefs()
    
class AllBoxscoresIndexHTML(PageHTML):
    
    def __init__(self, file_href='/boxscores/', content_only=False, host='https://www.basketball-reference.com',local='') -> None:
        super().__init__(file_href=file_href,content_only=content_only,host=host,local=local)

    def is_valid_href(file_href):
        return re.search(r'/boxscores(\b|/|/\?month=(\d{1,2})&day=(\d{1,2})&year=(\d{4}))$',file_href)
    
    def boxscores_hrefs(self):
        return [a['href'] for a in self.soup().select('div.game_summaries p.links a') if a.text == 'Box Score']

    def downstream_hrefs(self):
        return self.boxscores_hrefs()

class SeasonIndexHTML(PageHTML):

    def is_valid_href(file_href):
        return bool(re.search(r"/leagues/([A-Z]{3}_\d{4}).html$", file_href))
    
    def schedule_href(self):
        return f"{self.href_.strip('.html')}_games.html"
    
    def downstream_hrefs(self):
        return [self.schedule_href()]

class SeasonScheduleIndexHTML(PageHTML):

    def is_valid_href(file_href):
        return bool(re.search(r"/leagues/([A-Z]{3})_(\d{4})_games.html$", file_href))
    
    def monthly_schedule_hrefs(self):
        return [a['href'] for a in self.soup().find('div',{'class':'filter'}) .select('a')]
        
    def boxscores_hrefs(self):
        return [a['href'] for th in self.soup().find_all('td',{'data-stat':'box_score_text'}) for a in th]

    def downstream_hrefs(self):
        return self.monthly_schedule_hrefs()
    
class SeasonScheduleMonthlyHTML(PageHTML):
    
    def is_valid_href(file_href):
        return bool(re.search(r"/leagues/([A-Z]{3}_\d{4}_games)(.+).html$", file_href))
    
    def monthly_schedule_hrefs(self):
        return [a['href'] for a in self.soup().find('div',{'class':'filter'}) .select('a')]
        
    def boxscores_hrefs(self):
        return [a['href'] for th in self.soup().find_all('td',{'data-stat':'box_score_text'}) for a in th]

    def downstream_hrefs(self):
        return self.boxscores_hrefs()

class BoxscoresStatsHTML(PageHTML):

    def is_valid_href(file_href):
        return bool(re.search(r'/boxscores/(\d{9}[A-Z]{3}).html$',file_href))
    
    def sub_boxscores_hrefs(self):
        return [a['href'] for a in self.soup().select('div.filter div:not(.current) a:not(.sr_preset)')]
    
    def downstream_hrefs(self):
        return self.sub_boxscores_hrefs()
    
class BoxscoresPbpHTML(BoxscoresStatsHTML):

    def is_valid_href(file_href):
        return bool(re.search(r'/boxscores/pbp/(\d{9}[A-Z]{3}).html$',file_href))
    
    def downstream_hrefs(self):
        return []

class BoxscoresShotchartHTML(BoxscoresStatsHTML):

    def is_valid_href(file_href):
        return bool(re.search(r'/boxscores/shot-chart/(\d{9}[A-Z]{3}).html$',file_href))

    def downstream_hrefs(self):
        return []
    
class BoxscoresPlusMinusHTML(BoxscoresStatsHTML):

    def is_valid_href(file_href):
        return bool(re.search(r'/boxscores/plus-minus/(\d{9}[A-Z]{3}).html$',file_href))
    
    def downstream_hrefs(self):
        return []

class TeamIndexHTML(PageHTML):

    def is_valid_href(file_href):
        return re.search(r'/teams/([A-Z]{3})(/|\b)$',file_href)
    
    def team_seasons_hrefs(self):
        return [a['href'] for a in self.soup().select('table th a')]
    
    def downstream_hrefs(self):
        return self.team_seasons_hrefs()

class TeamSeasonIndexHTML(PageHTML):

    def is_valid_href(file_href):
        return re.search(r'/teams/([A-Z]{3})/(\d{4}).html$',file_href)
    
    def gamelog_href(self):
        gamelog_href = f"{self.href_.strip('.html')}/gamelog/"
        if  gamelog_href in self.bottom_nav_hrefs():
            return gamelog_href
        else:
            return None
        
    def downstream_hrefs(self):
        return self.bottom_nav_hrefs()
        
class TeamSeasonGamelogHTML(PageHTML):

    def is_valid_href(file_href):
        return re.search(r'/teams/([A-Z]{3})/(\d{4})/(gamelog|gamelog-advanced)(/|\b)$',file_href)

    def downstream_hrefs(self):
        return []

class PlayersAlphabetHTML(PageHTML):

    def is_valid_href(file_href):
        return re.search(r'/players/(\w)(/|\b)$',file_href)
    
    def players_hrefs(self):
        return [a['href'] for a in self.soup().select('table#players th[data-stat="player"] a')]

    def downstream_hrefs(self):
        return self.players_hrefs()

class PlayerIndexHTML(PageHTML):

    def is_valid_href(file_href):
        return re.search(r'/players/(\w)/([a-z]{7}\d{2}).html$',file_href)

    def downstream_hrefs(self):
        return []

class SyncResult:
    SYNC_ERR_SAVING_FILE        = 'SYNC_ERR_SAVING_FILE'
    SYNC_ERR_INVALID_HREF       = 'SYNC_ERR_INVALID_HREF'
    SYNC_ERR_ONLINE_NOT_FOUND   = 'SYNC_ERR_ONLINE_NOT_FOUND'
    SYNC_STT_NO_CHANGES         = 'SYNC_STT_NO_CHANGES'
    SYNC_STT_NEW_FILE           = 'SYNC_STT_NEW_FILE'
    SYNC_STT_UPDATES_FOUND      = 'SYNC_STT_UPDATES_FOUND'
    SYNC_STT_UPDATED            = 'SYNC_STT_UPDATED'

    def __init__(self) -> None:
        self.results = defaultdict(list)

    def __getitem__(self,index):
        return self.results[index]
    
    def __setitem__(self,index,val):
        self.results[index].append(val)

    def update(self,*args):
        for arg in args:
            if isinstance(arg,self.__class__):
                d = arg.dict()
            else:
                d = arg
            for k,v in d.items():
                self.results[k].extend(v)
        return self.results
    
    def dict(self):
        return dict(self.results)

class BaseDatabaseManager:        
    def __init__(self, path) -> None:
        self.path_ = path

    def path(self):
        return self.path_
    
    def is_setup(self):
        return Path(self.path()).exists()

    def load(self, page, content_only=True, warn=False, wait=0, auto_instance=False):
        if isinstance(page,str):
            page = PageHTML(page,content_only=content_only,local=self)
        if auto_instance:
            page = page.auto_instance()
        if page.load(warn=warn,wait=wait):
            return page
        return None

    def fetch(self, page, content_only=True, warn=False, wait=0, auto_instance=False):
        if isinstance(page,str):
            page = PageHTML(page,content_only=content_only,local=self)
        if auto_instance:
            page = page.auto_instance()
        if page.fetch(warn=warn,wait=wait):
            return page
        return None

    def diff(self, file_href):
        local_page  = self.load(file_href)
        online_page = self.fetch(file_href)
        if local_page and online_page:
            return local_page.diff(online_page)
        return None

    def save(self, page):
        if not self.is_setup():
            Path(self.path()).parent.mkdir(parents=True,exist_ok=True)
        return page.save()

    def meta(self, file_href):
        page = self.load(file_href)
        if page:
            local_file_url = self.path() + page.__local_url__()
            return {
                "date_retrieved": datetime.fromtimestamp(os.path.getctime(local_file_url)).strftime('%d-%m-%Y'),
                "size": self.__str_size__(os.path.getsize(local_file_url)),
            }
        return None
    
    def __str_size__(self,size):
        if not size:
            return '0 KB'
        magnitude = np.log2(size)
        if magnitude <= 20:
            size_str = str(np.round(size/2**10,1)) + ' KB'
        elif magnitude <= 30:
            size_str = str(np.round(size/2**20,1)) + ' MB'
        else:
            size_str = str(np.round(size/2**30,1)) + ' GB'
        return size_str

    def info(self,subfolder=''):
        num_files = 0
        num_folders = 0
        folder_size = 0
        folder_path = self.path()+subfolder 
        for root, folders, files in os.walk(folder_path):
            for file in files:
                num_files += 1
                file_path = os.path.join(root,file)
                folder_size += os.path.getsize(file_path)
            for folder in folders:
                num_folders += 1
        return {
            "size": self.__str_size__(folder_size),
            "num_folders": num_folders, 
            "num_files": num_files, 
        }
    
    def browse(self,subfolder='', recursive=False):
        folder_path = self.path()+subfolder 
        result = {
            'root': folder_path,
            'folders': [],
            'files': []
        }
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                relative_root = re.search(rf'{folder_path}(.+|\b)', root).group(1)
                for folder in dirs:
                    folder_name = paths_join(relative_root, folder)
                    if not folder_name.startswith('/'):
                        folder_name = '/' + folder_name
                    result['folders'].append(folder_name)
                for file in files:
                    file_name = paths_join(relative_root, file)
                    if not file_name.startswith('/'):
                        file_name = '/' + file_name
                    result['files'].append(file_name)
        else:
            root, dirs, files = next(os.walk(folder_path))
            relative_root = re.search(rf'{folder_path}(.+|\b)', root).group(1)
            for folder in dirs:
                folder_name = paths_join(relative_root, folder)
                if not folder_name.startswith('/'):
                    folder_name = '/' + folder_name
                result['folders'].append(folder_name)
            for file in files:
                file_name = paths_join(relative_root, file)
                if not file_name.startswith('/'):
                    file_name = '/' + file_name
                result['files'].append(file_name)

        return result
                

    def sync(self,file_href,pull=True,new_files_only=False,content_only=False,warn=False,wait=0, auto_instance=False):
        local_page  = self.load(file_href,content_only=content_only,warn=warn,wait=0,auto_instance=auto_instance)
        if local_page and new_files_only:
            return          SyncResult.SYNC_STT_NO_CHANGES
        
        online_page = self.fetch(file_href,content_only=content_only,warn=warn,wait=wait,auto_instance=auto_instance)
        if not online_page:
            if not local_page:
                return      SyncResult.SYNC_ERR_INVALID_HREF
            return          SyncResult.SYNC_ERR_ONLINE_NOT_FOUND
        else:
            if not local_page:
                saved = self.save(online_page)
                if not saved:
                    return  SyncResult.SYNC_ERR_SAVING_FILE
                return      SyncResult.SYNC_STT_NEW_FILE
            else:
                diff = online_page.diff(local_page)
                if not diff:
                    return  SyncResult.SYNC_STT_NO_CHANGES
                elif not pull:
                    return  SyncResult.SYNC_STT_UPDATES_FOUND
                else:
                    saved = self.save(online_page)
                    if not saved:
                        return  SyncResult.SYNC_ERR_SAVING_FILE
                    return      SyncResult.SYNC_STT_UPDATED

    def sync_folder(self,folder_path='',recursive=False,pull=True,content_only=False,warn=False,wait=3):
        # Get the list of files using the browse function
        files_info = self.browse(folder_path, recursive=recursive)
        files_to_sync = files_info['files']

        # Sync each file using the sync function
        sync_results = SyncResult()
        files_to_sync = tqdm(files_to_sync)
        for file_href in files_to_sync:
            files_to_sync.set_description(f'Syncing: {file_href}')
            status_code = self.sync(file_href, pull=pull, content_only=content_only, warn=warn, wait=wait)
            sync_results[status_code] = file_href # Append
        return sync_results


class DatabaseManager(BaseDatabaseManager):
    def sync_downstream(self,href,pull=True,new_files_only=False,content_only=False,downstream=False,warn=False,wait=3,position=0):
        sync_results            = SyncResult()
        sync_status             = self.sync(href,pull=pull,new_files_only=new_files_only,content_only=content_only,warn=warn,wait=wait) # sync season_schedule_page 
        sync_results[sync_status].append(href)

        if downstream:
            this_level_page = self.load(href,auto_instance=True)
            downstream_hrefs = tqdm(this_level_page.downstream_hrefs(),leave=False,position=position+1)
            for downstream_href in downstream_hrefs:
                downstream_hrefs.set_description(downstream_href)
                sync_status = self.sync_downstream(downstream_href,pull=pull,new_files_only=new_files_only,content_only=content_only,downstream=downstream,warn=warn,wait=wait) # sync season_schedule_page 
                sync_results[sync_status].append(downstream_href)
        return sync_results