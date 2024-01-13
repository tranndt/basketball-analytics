import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
from parse_tools import *
from load_tools import *
import time
from tqdm import tqdm
import argparse
import warnings
from pandas.errors import PerformanceWarning
pd.options.mode.use_inf_as_na = True
warnings.filterwarnings('ignore', category=PerformanceWarning)

parser = argparse.ArgumentParser(description='Normalize basketball-reference.com data')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-c', '--config', type=str, default='config.yaml', help='Source config file')
parser.add_argument('-m', '--mode', type=str, default='all', help='')

args = parser.parse_args()
debug = args.debug
config_yaml = args.config

def __load_team_stats_df__(filename):
    return pd.read_csv(filename,index_col=[0,1],header=[0,1]).drop(columns='Source',level=0)

def __load_facts_df__(filename):
    df = pd.read_csv(filename,index_col=[0,1],header=[0])
    df.columns = pd.MultiIndex.from_product([['Match Info'],df.columns])
    return df

# def get_opp_stats_row_df(STATS_DF,IDX_DF,TM_IDX):
#     OPP_IDX         = IDX_DF.loc[TM_IDX]
#     OPP_STATS_DF    = STATS_DF.loc[OPP_IDX].to_frame().T
#     OPP_STATS_DF.index = pd.MultiIndex.from_tuples([TM_IDX],names=['index','Team_id'])
#     return OPP_STATS_DF

# def get_opp_stats_df(STATS_DF,IDX_DF):
#     OPP_STATS_DF_LIST = []
#     for TM_IDX in STATS_DF.index:
#         OPP_STATS_DF_LIST.append(get_opp_stats_row_df(STATS_DF,IDX_DF,TM_IDX))
#     OPP_STATS_DF = pd.concat(OPP_STATS_DF_LIST,axis=0)
#     return OPP_STATS_DF

def compile_dataset(config_yaml):
    """
    Usage:
        python3 07_compile_script.py -c compile_config.yaml
    """
    config = load_yaml(config_yaml)
    DATA_DIRS = config['data_dirs']
    IDX_DIR = DATA_DIRS['data_indexed_dir']
    FACTS_DIR = DATA_DIRS['data_facts_dir']
    SRC_DATA_CONFIG = config['src_data']
    SRC_DIR = SRC_DATA_CONFIG['src_dir']
    SEASONS = SRC_DATA_CONFIG['seasons']
    OPPONENT = SRC_DATA_CONFIG['opponent']
    FEATURE_GROUPS = SRC_DATA_CONFIG['feature_groups']
    LABEL_GROUPS = SRC_DATA_CONFIG['label_groups']
    TGT_DATA_CONFIG = config['tgt_data']
    TGT_DIR = TGT_DATA_CONFIG['tgt_dir']
    TGT_DATASET_NAME = TGT_DATA_CONFIG['dataset_name']

    # if season is a index range dict then load the start and end seasons index
    if isinstance(SEASONS,dict):
        LG_SS_HTML_DICT = load_league_seasons_dict(FACTS_DIR)
        LG_SS_HTML_DICT_KEYS = list(LG_SS_HTML_DICT.keys())[slice(SEASONS['start'],SEASONS['end'])]
    # else load the seasons list
    else:
        LG_SS_HTML_DICT_KEYS = list(SEASONS)
    TQDM_LG_SS_HTML_DICT_KEYS = tqdm(LG_SS_HTML_DICT_KEYS,ncols=150) # Skip latest season
    FEATURES_DF_DICT = {}
    LABELS_DF_DICT = {}
    for LG_SS_HTML in TQDM_LG_SS_HTML_DICT_KEYS:
        TQDM_LG_SS_HTML_DICT_KEYS.set_description(f'{LG_SS_HTML}')
        LG_SS_DIR  = parse_league_id(LG_SS_HTML)['body']
        OPP_IDX_DF = load_index_dict('/'.join([IDX_DIR,LG_SS_DIR]))['team_opp_main']['Opp_Curr_Gm']
        DATASETS = {}
        for SRC_FEATURE in FEATURE_GROUPS:
            SRC_DATASET_DIR =  '/'.join([SRC_DIR,LG_SS_DIR,SRC_FEATURE])# '{SRC_DIR}/{LG_SS_DIR}/{SRC_DATASET_NAME}'
            if 'facts' in SRC_FEATURE:
                TM_DATASET_DF = __load_facts_df__(f'{SRC_DATASET_DIR}.csv')
                DATASETS[f'Team_{SRC_FEATURE}']  = TM_DATASET_DF
                if OPPONENT:
                    OPP_DATASET_DF = get_opp_stats_df(TM_DATASET_DF,OPP_IDX_DF)
                    DATASETS[f'Opp_{SRC_FEATURE}'] = OPP_DATASET_DF
            else:
                TM_DATASET_DF = __load_team_stats_df__(f'{SRC_DATASET_DIR}.csv')
                DATASETS[f'Team_{SRC_FEATURE}']  = TM_DATASET_DF
                if OPPONENT:
                    OPP_DATASET_DF = get_opp_stats_df(TM_DATASET_DF,OPP_IDX_DF)
                    DATASETS[f'Opp_{SRC_FEATURE}'] = OPP_DATASET_DF
        FEATURES_SS_DF = pd.concat(DATASETS.values(),keys=DATASETS.keys(),axis=1)
        LABELS_SS_DF = __load_facts_df__(f'{SRC_DIR}/{LG_SS_DIR}/{LABEL_GROUPS}.csv')
        FEATURES_DF_DICT[LG_SS_HTML] = FEATURES_SS_DF
        LABELS_DF_DICT[LG_SS_HTML] = LABELS_SS_DF
    FEATURES_DF = pd.concat(FEATURES_DF_DICT.values(),keys=FEATURES_DF_DICT.keys(),axis=0)
    LABELS_DF = pd.concat(LABELS_DF_DICT.values(),keys=LABELS_DF_DICT.keys(),axis=0)

    make_directory('/'.join([TGT_DIR,TGT_DATASET_NAME]))
    FEATURES_DF.to_csv('/'.join([TGT_DIR,TGT_DATASET_NAME,'features.csv']))
    LABELS_DF.to_csv('/'.join([TGT_DIR,TGT_DATASET_NAME,'labels.csv']))

    config['src_data']['seasons'] = LG_SS_HTML_DICT_KEYS
    config['tgt_data']['features_shape'] = list(FEATURES_DF.shape)
    config['tgt_data']['labels_shape'] = list(LABELS_DF.shape)
    config['tgt_data']['compiled_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_yaml('/'.join([TGT_DIR,TGT_DATASET_NAME,'config.yaml']),config)


if __name__ == "__main__":
    compile_dataset(config_yaml)