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
import warnings
import base


class AllSeasonsIndexHTML(base.BBRefHTML):
    def __init__(self, href='/leagues/', content_only=True) -> None:
        super().__init__(href, content_only)
        if href != "/leagues/":
            warnings.warn(f"href='{href}' may be invalid for {self.__class__.__name__}",stacklevel=0)

    def seasons_hrefs(self):
        seasons_list = [a['href'] for th in self.html_soup_.find_all('th', {'data-stat': 'season'}) for a in th.find_all('a')]
        return seasons_list
        
class SeasonIndexHTML(base.BBRefHTML):
    def __init__(self, href='', content_only=True) -> None:
        super().__init__(href, content_only)
        if not re.search(r"\b([A-Z]{3}_\d{4}\b)", href):
            warnings.warn(f"href='{href}' may be invalid for {self.__class__.__name__}",stacklevel=0)

    def schedule_href(self):
        return f"{self.href_.strip('.html')}_games.html"

class SeasonScheduleHTML(base.BBRefHTML):
    def __init__(self, href='', content_only=True) -> None:
        super().__init__(href, content_only)
        if not re.search(r"(\b[A-Z]{3}_\d{4}_games\b)", href):
            warnings.warn(f"href='{href}' may be invalid for {self.__class__.__name__}",stacklevel=0)

    def monthly_schedule_hrefs(self):
        filter_div = self.html_soup_.find('div',{'class':'filter'}) 
        if filter_div:
            return [a['href'] for a in filter_div.select('a')]
        else:
            return []