from bs4 import *
import time
import requests
import re
import numpy as np
import pandas as pd
import json
import pickle
from pathlib import Path
import sys
import os
sys.path.insert(0,'../../')
import scripts.base as base
import inspect
import difflib


BBREF_HOME = 'https://www.basketball-reference.com'
local_host = './data'

def save(a,filepath,mode='w'):
    if not Path(filepath).exists():
        Path(filepath).parent.mkdir(parents=True,exist_ok=True)
    with open(filepath,mode) as f:
        f.write(a)

def load(filepath,mode='r'):
    data = None
    if Path(filepath).exists():
        with open(filepath,mode) as f:
            data = f.read()
    return data

def fetch(html_url,source=''):
    try:
        full_url = f'{source}{html_url}'
        data = load(full_url)
        return re.sub("<!--|-->","\n",data) 
    except IsADirectoryError:
        try:
            full_url = f'{source}{html_url}.html'
            data = load(full_url)
            return re.sub("<!--|-->","\n",data)
        except Exception as e:
            print(f'Failed to fetch \'{full_url}\' due to error: {e}') 
    except Exception as e:
        print(f'Failed to fetch \'{full_url}\' due to error: {e}')
    return None

def pull(html_url,source=''):
    try:
        full_url = f'{source}{html_url}' if html_url.startswith("https://") else f'https://{source}{html_url}'
        session = requests.Session().get(full_url)
        if session.status_code >= 400:
            raise Exception(f'error code: {session.status_code}')
        return re.sub("<!--|-->","\n",session.text)
    except Exception as e:
        print(f'Failed to pull \'{full_url}\' due to error: {e}')
        return None

def soup(html_text):
    try:
        return BeautifulSoup(html_text,features='html.parser')
    except Exception as e:
        return None

def set_option(option: str, value):
    """
    Sets global option with the given value.
    """
    try:
        globals()[option] = value
        print(f"{option} set to {value} in the current module.")
    except Exception as e:
        print(f"Error setting variable: {e}")

class BBRefHTML:
    def __init__(self,href='',content_only=True) -> None:
        # Init the object
        self.href_ = href
        self.html_url_ = f'{BBREF_HOME}{href}'
        self.local_host_ = local_host
        self.content_only_ = content_only
        self.html_text_ = None
        self.html_soup_ = None
        self.html_text_local_ = None
        self.html_soup_local_ = None

    def local(self):
        self.html_text_  = fetch(self.html_url_,source=self.local_host_)
        self.html_soup_  = soup(self.html_text_)
        if self.content_only_ and self.html_soup_:
            self.html_soup_ = self.content_div()
            self.html_text_ = str(self.html_soup_)
        return self.html_soup_
    
    def online(self):
        if self.html_soup_local_ is None:
            self.html_text_local_ = self.html_text_ #local version
            self.html_soup_local_ = self.html_soup_
            self.html_text_  = pull(self.html_url_) #online version
            self.html_soup_  = soup(self.html_text_)
        if self.content_only_ and self.html_soup_:
            self.html_soup_ = self.content_div()
            self.html_text_ = str(self.html_soup_)
        return self.html_soup_
    
    def save(self):
        try:
            save_url = f"{local_host}/{self.html_url_}" 
            if not self.html_url_.endswith('.html'):
                save_url += ".html"
            if self.content_only_ and self.html_soup_ and self.content_div():
                html_text = str(self.content_div())
            else:
                html_text = self.html_text_
            save(html_text,f'{save_url}')
            return True
        except Exception as e:
            print(f'Could not save {str(self)} to \'{self.local_host_}\', due to error: {e}')
            return False
    
    def delta(self, element_selector=None):
        # Find the difference between the online and local version
        local_element = self.html_soup_local_
        online_element = self.html_soup_
        if element_selector:
            local_element = local_element.select_one(element_selector)
            online_element = online_element.select_one(element_selector)
        if local_element is None or online_element is None:
            print("One or both of the elements could not be found.")
            return None
        local_lines = local_element.prettify().splitlines()
        online_lines = online_element.prettify().splitlines()
        differences = list(difflib.unified_diff(local_lines, online_lines))
        return differences
    
    def content_div(self):
        try:
            if self.html_soup_.get('id') == 'content':
                return self.html_soup_
            else:
                return self.html_soup_.find('div',{'id':'content'})
        except Exception as e:
            print(f'Could not get content from {str(self)} due to error: {e}')
            return None
    
    def filter_div(self):
        try:
            return self.html_soup_.find('div',{'class':'filter'}) 
        except Exception as e:
            print(f'Could not get filter from {str(self)} due to error: {e}')
            return None
        
    def render(self,limit=None):
        from IPython.display import display,HTML
        display(HTML(self.html_text_[:limit]))

    def sync(self,update=True):
        # The goal is to sync an html file between the local version and the online version. 
        # It first try to pulls and saves the file from the web if the file doesnt exist yet in the local database. 
        # Otherwise it checks for the differences and notify of the differences if exists, or lack thereof. 
        # It then prompts to the user if they want to go ahead and pull the updated version
        # STATUS_CODES
        STATUS_ERROR_SAVING_FILE   = -10
        STATUS_ONLINE_NOT_EXISTED  = -1
        STATUS_NO_NEW_UPDATES      = 0
        STATUS_PULLED_NEW_FROM_ONLINE  = 1
        STATUS_NEW_UPDATES_UNRESOLVED  = 2
        STATUS_NEW_UPDATES_OVERWRITEN  = 3

        local_file_exists = self.local()
        # If local files doesn't exist
        if not local_file_exists:
            online_file_exists = self.online()
            if not online_file_exists:
                return STATUS_ONLINE_NOT_EXISTED
            else:
                saved = self.save()
                if saved:
                    return STATUS_PULLED_NEW_FROM_ONLINE
                else:
                    return STATUS_ERROR_SAVING_FILE
        else:
            online_file_exists = self.online()
            if not online_file_exists:
                return STATUS_ONLINE_NOT_EXISTED
            else:
                delta = self.delta()
                if not delta:
                    return STATUS_NO_NEW_UPDATES
                else:
                    for diff_line in delta:
                        print(diff_line)
                    if not update:
                        return STATUS_NEW_UPDATES_UNRESOLVED
                    else:
                        saved = self.save()
                        if saved:
                            return STATUS_NEW_UPDATES_OVERWRITEN
                        else:
                            return STATUS_ERROR_SAVING_FILE
                        
    def __str__(self) -> str:
        return f'{self.__class__.__name__}(\'{self.href_}\')'
