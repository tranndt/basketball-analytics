import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
import time
from tqdm import tqdm


"""
Usage:
    python3 02b_parse_correction_script.py
"""
# Correct the NA keywords by replacing ['Not With Team','Player Suspended','DNP'] with NA
DATA_PARSED_FOLDER = '../02-data-parsed/boxscores/'
TQDM_FOLDERS = tqdm(sorted(get_all_folders(DATA_PARSED_FOLDER)))
for boxscores_folder in TQDM_FOLDERS:
    TQDM_FOLDERS.set_description('Processing %s' % boxscores_folder)
    for boxscores_file in get_all_files(os.path.join(DATA_PARSED_FOLDER, boxscores_folder)):
        if boxscores_file.startswith(('box-away-game-basic','box-home-game-basic',
                                        'box-away-game-advanced','box-home-game-advanced'
                                        'box-away-h1-basic','box-home-h1-basic',
                                        'box-away-h2-basic','box-home-h2-basic',
                                        'box-away-q1-basic','box-home-q1-basic',
                                        'box-away-q2-basic','box-home-q2-basic',
                                        'box-away-q3-basic','box-home-q3-basic',
                                        'box-away-q4-basic','box-home-q4-basic')):
            df = pd.read_csv(os.path.join(DATA_PARSED_FOLDER, boxscores_folder, boxscores_file),index_col=0)
            for na_keywords in ['Did Not Play','Did Not Dress','Coach\'s Decision','','Not With Team','Player Suspended','DNP']:
                df.replace(na_keywords,np.nan,inplace=True)
            df.to_csv(os.path.join(DATA_PARSED_FOLDER, boxscores_folder, boxscores_file))