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
parser.add_argument('-s', '--sourcedir', type=str, default='../data/', help='Source directory')
parser.add_argument('-t', '--targetdir', type=str, default='../data-parsed/', help='Save to directory')
parser.add_argument('-m', '--mode', type=str, default='gamelogs', help='Scraping mode: gamelogs or boxscores')

args = parser.parse_args()
debug = args.debug
SRC_DIR = args.sourcedir
TGT_DIR = args.targetdir
MODE = args.mode

def parse_all_team_gamelogs_from_source_dir():
    """
    Description:
        Parse all team gamelogs from sourcedir
    Summary:
        1. Load team_seasons_html.txt
        2. Parse all team gamelogs
        3. Save the parsed gamelogs
    Usage: 
        python3 02_parse_script.py -m gamelogs -s ../01-data-html/ -t ../02-data-parsed/
    """
    _FAILS_ = []
    SRC_TM_SS_HTML_TXT = f'{SRC_DIR}/team_seasons_html.txt'
    TGT_TM_SS_GL_HTML_TXT = f'{TGT_DIR}/team_seasons_gamelogs_html.txt'
    # Check if parsed csv team_seasons.txt exists
    TGT_TM_SS_GL_HTML_LIST = []
    if file_exists(TGT_TM_SS_GL_HTML_TXT):
        TGT_TM_SS_GL_HTML_LIST = load_file(TGT_TM_SS_GL_HTML_TXT).split('\n')      
    # Check if source html team_seasons.txt exists
    if not file_exists(SRC_TM_SS_HTML_TXT):
        print(f'{SRC_TM_SS_HTML_TXT} does not exist. You should scrape it first')
        return None
    # Load team_seasons.txt
    TM_SS_HTML_LIST = load_file(SRC_TM_SS_HTML_TXT).split('\n')
    # Parse all team gamelogs
    TQDM_TM_SS_HTML_LIST = tqdm(TM_SS_HTML_LIST)
    for TM_SS_HTML in TQDM_TM_SS_HTML_LIST:
        TQDM_TM_SS_HTML_LIST.set_description(TM_SS_HTML)
        TM_SS_DIR = TM_SS_HTML.strip('.html')
        SRC_TM_SS_DIR = f'{SRC_DIR}/{TM_SS_DIR}'
        TGT_TM_SS_DIR = f'{TGT_DIR}/{TM_SS_DIR}'
        TM_NAME = re.search(r'/teams/(?P<team>\w+)/(?P<season>\d+)',TM_SS_DIR).groups()[0]
        # Load gamelogs html
        for GL_HTML in ['gamelog.html','gamelog-advanced.html']:
            SRC_TM_SS_GL_HTML = f'{SRC_TM_SS_DIR}/{GL_HTML}'
            TM_SS_GL_HTML = f'{TM_SS_DIR}/{GL_HTML}'
            try:
                # Disregard if the file does not exist
                if not file_exists(SRC_TM_SS_GL_HTML):
                    print(f'HTML {SRC_TM_SS_GL_HTML} does not exist')
                    continue
                # Check if the file has been parsed, then skip
                if TM_SS_GL_HTML in TGT_TM_SS_GL_HTML_LIST:
                    print(f'{TM_SS_GL_HTML} has been parsed. Skipping...')
                    continue
                # Else parse the file
                GL_TBL_DICT = parse_all_team_gamelogs_tables_from_file(SRC_TM_SS_GL_HTML)
                make_directory(f'{TGT_TM_SS_DIR}')
                for TBL_ID, DF in GL_TBL_DICT.items():
                    DF.insert(3,('Match','Tm'),TM_NAME)
                    DF.insert(4,('Match','Tm_html_id'),TM_SS_HTML)
                    DF.to_csv(f'{TGT_TM_SS_DIR}/{TBL_ID}.csv')
                # Save the parsed file
                TGT_TM_SS_GL_HTML_LIST.append(TM_SS_GL_HTML)
                save_file(TGT_TM_SS_GL_HTML_TXT,'\n'.join(TGT_TM_SS_GL_HTML_LIST))
            except Exception as e:
                print(f'Error parsing {SRC_TM_SS_GL_HTML}: {e}')
                _FAILS_.append(SRC_TM_SS_GL_HTML)
                continue
    if _FAILS_:
        print(f'Failed to parse {len(_FAILS_)} files: {_FAILS_}')
    else:
        print(f'All {len(TGT_TM_SS_GL_HTML_LIST)} files parsed successfully')


def parse_all_boxscores_from_source_dir():
    """
    python3 02_parse_script.py -m boxscores -s ../01-data-html/boxscores/ -t ../02-data-parsed/
    """
    # Get all html files from sourcedir
    _FAILS_= []
    BS_HTML_LIST = get_all_files(SRC_DIR, file_type='.html')
    BS_HTML_LIST = sorted(BS_HTML_LIST,reverse=True)
    TQDM_BS_HTML_LIST = tqdm(BS_HTML_LIST)
    print(f'Found {len(BS_HTML_LIST)} html files in {SRC_DIR}')

    # Parse these html files
    for BS_HTML in TQDM_BS_HTML_LIST:
        TQDM_BS_HTML_LIST.set_description(BS_HTML)
        BS_DIR = get_file_name(BS_HTML)
        # Check if the file has been parsed, then skip
        TGT_BS_DIR = f'{TGT_DIR}/{BS_DIR}'
        if folder_exists(TGT_BS_DIR):
            print(f'{TGT_BS_DIR} exists. Skipping...')
            continue
        # Else load and parse the file
        try:
            HTML_TEXT = load_file(f'{SRC_DIR}/{BS_HTML}')
            HTML_TEXT = re.sub("<!--|-->","\n",HTML_TEXT)
            BS_TBL_DICT = parse_all_boxscores_tables(HTML_TEXT)
            # Save the parsed tables
            make_directory(TGT_BS_DIR)
            for TBL_ID, DF in BS_TBL_DICT.items():
                DF.to_csv(f'{TGT_BS_DIR}/{TBL_ID}.csv')
        except Exception as e:
            print(f'Error parsing {BS_HTML}: {e}')
            _FAILS_.append(BS_HTML)
            continue
    if _FAILS_:
        print(f'Failed to parse {len(_FAILS_)} files: {_FAILS_}')
    else:
        print(f'All {len(BS_HTML_LIST)} files parsed successfully')


if __name__ == "__main__":
    if MODE == 'gamelogs':
        parse_all_team_gamelogs_from_source_dir()
    elif MODE == 'boxscores':
        parse_all_boxscores_from_source_dir()
    else:
        print(f'Invalid mode: {MODE}. Valid modes: gamelogs or boxscores')
        sys.exit(1)







