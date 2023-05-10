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
import scripts.base
import inspect
import difflib
from collections import defaultdict

import base
import seasons

class SyncManager:
    STATUS_CODE = dict(
        STATUS_ERROR_SAVING_FILE   = -10,
        STATUS_INVALID_HREF        = -2,
        STATUS_ONLINE_NOT_EXISTED  = -1,
        STATUS_NO_NEW_UPDATES      = 0,
        STATUS_PULLED_NEW_FROM_ONLINE  = 1,
        STATUS_NEW_UPDATES_UNRESOLVED  = 2,
        STATUS_NEW_UPDATES_OVERWRITEN  = 3,
    )

    def __init__(self,local_path) -> None:
        self.local_path_ = local_path
        
    def is_setup(self):
        # Check to see if there is existing database already set up at the location
        return Path(self.local_path_).exists()

    def sync_all(self, categories = None):
        # Check if DB is set up
        if not self.is_setup():
            # set up
            pass

        # Sync the category/folder required
        for category in categories:
            category_dict = {
                'seasons'   : self.sync_all_seasons,
                # 'teams'     : self.sync_teams,
                # 'players'   : self.sync_players,
                # 'boxscores' : self.sync_boxscores,
            }
            try: 
                sync_f = category_dict[category]
                sync_f()
            except KeyError as e:
                print(f'\'{category}\' is not a valid category. Pleas choose from {set(category_dict.keys())}')

    def local(self,page): # fetch
        pass

    def pull(self,page): # fetch
        pass

    def save(self,page): # fetch
        pass

    def info(self,page): # fetch
        pass

    def sync(self, page, update=True):
        if isinstance(page,str):
            page = base.BBRefHTML(page)

        if not page.online():
            if not page.local():
                return      SyncManager.STATUS_CODE['STATUS_INVALID_HREF']
            return          SyncManager.STATUS_CODE['STATUS_ONLINE_NOT_EXISTED']
        else:
            if not page.local():
                saved = page.save()
                if not saved:
                    return  SyncManager.STATUS_CODE['STATUS_ERROR_SAVING_FILE'] 
                return      SyncManager.STATUS_CODE['STATUS_PULLED_NEW_FROM_ONLINE'] 
            else:
                delta = page.delta()
                if not delta:
                    return  SyncManager.STATUS_CODE['STATUS_NO_NEW_UPDATES']
                elif not update:
                    return  SyncManager.STATUS_CODE['STATUS_NEW_UPDATES_UNRESOLVED']
                else:
                    saved = page.save()
                    if not saved:
                        return  SyncManager.STATUS_CODE['STATUS_ERROR_SAVING_FILE'] 
                    return      SyncManager.STATUS_CODE['STATUS_NEW_UPDATES_OVERWRITEN'] 

    # Sync seasons folder
    def sync_all_seasons(self,recursive=False):
        # Check for seasons index file, retrieve it if necessary
        # For children hrefs, sync, gather syncing info
        sync_results = defaultdict(list)
        all_seasons_index_page = seasons.AllSeasonsIndexHTML()
        sync_status = self.sync_page(all_seasons_index_page) # sync main index page
        sync_results[sync_status].extend(all_seasons_index_page.href_)
        if recursive:
            for season_href in all_seasons_index_page.seasons_hrefs():
                season_sync_results = self.sync_season(season_href,recursive=recursive) # sync each season index page
                sync_results = SyncManager.merge_sync_results(sync_results,season_sync_results)
        return sync_results
    
    def merge_sync_results(*args):
        merged_results = defaultdict(list)
        for d in args:
            for k,v in d.items():
                merged_results[k].extend(v)
        return merged_results

    def sync_season(self,href,recursive=False):
        sync_results = defaultdict(list)
        season_index_page = seasons.SeasonIndexHTML(href)
        sync_status = self.sync_page(season_index_page) # sync season_index_page
        sync_results[sync_status].extend(href)

        # sync season schedule
        if recursive:
            if season_index_page.schedule_href():
                season_schedule_href = season_index_page.schedule_href()
                season_schedule_sync_results = self.sync_season_schedule(season_schedule_href,recursive=recursive) # sync season_schedule_page 
                sync_results = SyncManager.merge_sync_results(sync_results,season_schedule_sync_results)
            # sync other pages if necessary
        return sync_results
    
    def sync_season_schedule(self,href,recursive=False):
        sync_results = defaultdict(list)
        season_schedule_page = seasons.SeasonScheduleHTML(href)
        sync_status = self.sync_page(season_schedule_page) # sync season_schedule_page 
        sync_results[sync_status].extend(season_schedule_page.href_)

        # sync monthly schedule if available 
        if recursive:
            if season_schedule_page.monthly_schedule_hrefs():
                for monthly_schedule_href in season_schedule_page.monthly_schedule_hrefs():
                    monthly_schedule_page = seasons.SeasonScheduleHTML(monthly_schedule_href)
                    sync_status = self.sync_page(monthly_schedule_page) # sync season_schedule_page 
                    sync_results[sync_status].extend(monthly_schedule_page.href_)

        return sync_results

    def sync_boxscores(self):
        # Sync boxscores folder
        pass


    # def sync_teams(self):
    #     # Sync teams folder
    #     # Check for seasons index file, retrieve it if necessary


    #     # For children hrefs, sync, gather syncing info

    #     # return syncing info
    #     pass

    # def sync_players(self):
    #     # Sync players folder
    #     pass








