import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
import time
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description='Scrape basketball-reference.com')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-s', '--sourcedir', type=str, help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, help='Save to directory')

args = parser.parse_args()
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir


def compile_player_gamelog_index_by_season():
    pass

