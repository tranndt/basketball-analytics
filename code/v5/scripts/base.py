from bs4 import *
from bs4.element import PageElement
import time
import requests
import re
import numpy as np
import pandas as pd
from tqdm import tqdm, trange
import json
import pickle
from pathlib import Path

HOME_PAGE = 'https://www.basketball-reference.com'
SEASONS_PAGE = 'https://www.basketball-reference.com/leagues'
TEAMS_PAGE = 'https://www.basketball-reference.com/teams'
BOXSCORES_PAGE = 'https://www.basketball-reference.com/boxscores'
LOCAL_HOST = '/Volumes/Seagate Portable Disk/University of Manitoba/Data Science/Datasets/basketball-analytics/'



def fetch_html(url,source=None):
    if source:
        try:
            data = load(f'{source}{url}')
            return re.sub("<!--|-->","\n",data)
        except:
            print(f'Failed to fetch \'{url}\' from local. Try to fetch online instead')
    else:
        try:
            if not url.startswith("https://"):
                url = "https://"+url
            session = requests.Session().get(url)
            if session.status_code >= 400:
                return None
            return re.sub("<!--|-->","\n",session.text)
        except:
            print(f'Failed to fetch {url} from web. Please double check url.')
    return None

def bs4_soup(text):
    try:
        return BeautifulSoup(text,features='html.parser')
    except Exception as e:
        print(f'Could not make soup, due to {e}')
        return None

def save(a,filepath,mode='w',file_type=None):
    if not Path(filepath).exists():
        Path(filepath).parent.mkdir(parents=True,exist_ok=True)
    if file_type is None:
        with open(filepath,mode) as f:
            f.write(a)
    elif file_type.endswith('json'):
        with open(filepath,mode) as f:
            json.dump(a,f)
    elif file_type.endswith('pkl'):
        with open(filepath,mode) as f:
            pickle.dump(a,f)       

def load(filepath,mode='r',file_type=None):
    if file_type is None:
        with open(filepath,mode) as f:
            data = f.read()
    elif file_type.endswith('json'):
        with open(filepath,mode) as f:
            data = json.load(f)
    elif file_type.endswith('pkl'):
        with open(filepath,mode) as f:
            data = pickle.load(f)    
    return data

import importlib
def set_module_variable(module_name: str, variable_name: str, value):
    """
    Sets a variable in the specified module with the given value.

    :param module_name: The name of the module.
    :param variable_name: The name of the variable to set.
    :param value: The value to set for the variable.
    """
    try:
        module = importlib.import_module(module_name)
        setattr(module, variable_name, value)
        print(f"{variable_name} set to {value} in {module_name} module.")
    except ImportError:
        print(f"Unable to import module: {module_name}")
    except Exception as e:
        print(f"Error setting variable: {e}")

from typing import Iterable
def to_list(var):
    if not isinstance(var, Iterable) or isinstance(var, str):
        return [var]
    else:
        return var
    
import functools
import os

class Checkpoint:
    """
    Example Usage:
    -------
    ```
    checkpoint = Checkpoint(levels=3)
    for i in range(10):
        if checkpoint.skip_this_point(i):
            # Skip points prior to checkpoint
            continue
        for j in range(10):
            if checkpoint.skip_this_point(i,j):
                # Skip points prior to checkpoint
                continue
            for k in range(10):
                if checkpoint.skip_this_point(i,j,k):
                    # Skip points prior to checkpoint
                    continue
                # Only executes when the checkpoint is reached
                # Do something
                print(i,j,k)
                time.sleep(0.5)
                # Update and save
                checkpoint.update(i,j,k)
                checkpoint.save()
    # Delete when task is finished
    checkpoint.delete()
    ```
    """
    def __init__(self,path='.',levels=3) -> None:
        self.path_ = path
        self.checkpoint_path_ = f'{self.path_}/checkpoint.pkl'
        self.num_updates_ = 0
        if Path(self.checkpoint_path_).exists():
            self.checkpoints_ = list(load(self.checkpoint_path_,mode='rb',file_type='.pkl'))
            self.levels_ = len(self.checkpoints_)
        else:
            self.checkpoints_ = [0]*levels
            self.levels_ = levels


    def __getitem__(self,index):
        return self.checkpoints_[index]

    def skip_this_point(self,*args):
        arg_pairs = list(zip(args,self.checkpoints_))
        clauses = []
        for i,(arg,chkpt) in enumerate(arg_pairs):
            if i < len(arg_pairs) - 1:
                clauses.append(arg==chkpt)
            else:
                clauses.append(arg<chkpt)
        result = functools.reduce(lambda x,y: x and y, clauses)  # AND all of the clauses together
        return result

    def update(self,*args):
        self.checkpoints_ = args
        self.num_updates_ += 1
        return self

    def reset(self):
        self.checkpoints_ = [0]*len(self.checkpoints_)
        self.num_updates_ = 0
        return self

    def save(self):
        save(self.checkpoints_,self.checkpoint_path_,mode='wb',file_type='.pkl')
        return self

    def delete(self):
        if Path(self.checkpoint_path_).exists():
            os.remove(self.checkpoint_path_)
        return self

    def __str__(self) -> str:
        return str(vars(self))
    
    def example_usage():
        return Checkpoint.__doc__