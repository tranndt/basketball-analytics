import sys
sys.path.insert(0,'../')
from file_tools import *
from request_tools import *
import time
from tqdm import tqdm
import argparse
from parse_tools import *

# Parsing script arguments: 
parser = argparse.ArgumentParser(description='Scrape basketball-reference.com')
parser.add_argument('-sl', '--sleep', type=int, default=3, help='Sleep time between requests')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
parser.add_argument('-t', '--targetdir', type=str, default='../data-html/', help='Save to directory')
parser.add_argument('-ss', '--start_season', type=int, default=0, help='Start season')
parser.add_argument('-es', '--end_season', type=int, default=None, help='End season')
parser.add_argument('-m', '--mode', type=str, default='boxscores_html', help='Scraping mode: boxscores_html or boxscores_hrefs')

args = parser.parse_args()
sleep = args.sleep
debug = args.debug
outdir = args.targetdir
start_season = args.start_season
end_season = args.end_season
mode = args.mode

# function to get all seasons
def __request_all_seasons_hrefs__() -> list:
    seasons = []
    html_soup = request_html_soup(SEASONS_PAGE)
    try:
        for th in html_soup.find_all('th', {'data-stat': 'season'}):
            for a in th.find_all('a'):
                seasons.append(a['href'])
    except Exception as e:
        print(f'Error getting seasons: {e}')
    return seasons

def __request_season_games_hrefs__(season_href,sleep=3) -> list:
    games = []
    html_soup = request_html_soup(HOME_PAGE + season_href.strip('.html')+'_games.html')
    filter_div = html_soup.find('div',{'class':'filter'}) 
    schedule_table = html_soup.find('table', {'id': 'schedule'})
    try:
        if filter_div is None:
            for td in html_soup.find_all('td', {'data-stat': 'box_score_text'}):
                for a in td.find_all('a'):
                    games.append(a['href'])
        else:
            month_hrefs = [a['href'] for a in filter_div.select('a')]
            for month_href in month_hrefs:
                html_soup = request_html_soup(HOME_PAGE + month_href)
                schedule_table = html_soup.find('table', {'id': 'schedule'})
                for td in schedule_table.find_all('td', {'data-stat': 'box_score_text'}):
                    for a in td.find_all('a'):
                        games.append(a['href'])
                time.sleep(sleep)
    except Exception as e:
        print(f'Error getting boxscores for season {season_href}: {e}')
    return games

def __request_game_boxscores_hrefs__(game_href) -> dict:
    boxscores = []
    try:
        html_soup = request_html_soup(HOME_PAGE + game_href)
        filter_div = html_soup.find('div',{'class':'filter'})
        if filter_div is not None:
            filter_hrefs = [a['href'] for a in filter_div.select('a')]
            for filter_href in filter_hrefs:
                boxscores.append(filter_href)
        else:
            boxscores.append(game_href)
    except Exception as e:
        print(f'Error getting boxscores hrefs for game {game_href}: {e}')
    return boxscores

# Scraping all boxscores hrefs
def scrape_boxscores_hrefs(start_season=0,end_season=None):
    # fetch season boxscores list
    game_hrefs = {}
    seasons_hrefs = __request_all_seasons_hrefs__()[start_season:end_season]
    for season_href in tqdm(seasons_hrefs,position=0, leave=True,ncols=150):
        season_games_hrefs = __request_season_games_hrefs__(season_href,sleep)
        game_hrefs[season_href] = sorted(season_games_hrefs,reverse=False)
        # save_file(outdir + 'boxscores.txt', '\n'.join(game_hrefs))
        save_json(outdir, game_hrefs)
        time.sleep(sleep)

# # Scraping all boxscores
# def scrape_boxscores_html(start_season=0,end_season=None):
#     # Check if boxscores hrefs list exists, if not scrape it
#     if not file_exists(outdir + 'boxscores.txt'):
#         print('boxscores.txt not found. Scraping boxscores hrefs...')
#         scrape_boxscores_hrefs(start_season,end_season)
#     else:
#         print('boxscores.txt found. Scraping boxscores html...')
#     # Load boxscores hrefs list
#     game_hrefs = load_file(outdir + 'boxscores.txt').split('\n')
#     game_hrefs_tqdm = tqdm(game_hrefs,position=0, leave=True,ncols=150)
#     for game_href in game_hrefs_tqdm:
#         game_hrefs_tqdm.set_description(f'{game_href}')
#         # Check if we already have the boxscores
#         if file_exists(outdir + game_href):
#             continue
#         # Else fetch the game html
#         try:
#             html_soup = request_html_soup(HOME_PAGE + game_href)
#             html_text = content_div_only(html_soup).prettify()
#             save_file(outdir + game_href, html_text)
#             time.sleep(sleep)
#         except Exception as e:
#             print(f'Error getting boxscores for game {game_href}: {e}')

def scrape_all_boxscores_html(TARGET_DIR, sleep=3):
    _FAILS_ = []
    SS_BOXSCORES = load_json('../00-data-facts/boxscores_hrefs.json')
    if SS_BOXSCORES is None:
        print('No boxscores found')
        return
    TQDM_SS_BOXSCORES_KEYS = tqdm(SS_BOXSCORES.keys(),position=0, leave=True, ncols=150)
    for SEASON_HTML in  TQDM_SS_BOXSCORES_KEYS:
        TQDM_SS_BOXSCORES_KEYS.set_description(f'{SEASON_HTML}')
        TQDM_SS_BOXSCORES_LIST = tqdm(SS_BOXSCORES[SEASON_HTML],position=1, leave=False,ncols=150)
        for BOXSCORES_HTML in TQDM_SS_BOXSCORES_LIST:
            if file_exists('/'.join([TARGET_DIR,BOXSCORES_HTML])):
                continue
            try:
                HTML_SOUP = request_html_soup(HOME_PAGE + BOXSCORES_HTML)
                HTML_TEXT = content_div_only(HTML_SOUP).prettify()
                save_file('/'.join([TARGET_DIR,BOXSCORES_HTML]), HTML_TEXT)
                time.sleep(sleep)
            except Exception as e:
                print(f'Error getting boxscores for game {BOXSCORES_HTML}: {e}')
                _FAILS_.append(BOXSCORES_HTML)
    
    if _FAILS_:
        print(f'Failed to fetch {len(_FAILS_)} boxscores')
    else:
        print('All boxscores fetched')

def scrape_teams_hrefs():
    """
    Scrape all teams hrefs
    Usage: python3 scrape.py -m teams_hrefs
    """
    html_text = request_html_text(TEAMS_PAGE)
    html_text = clean_html_text(html_text)
    html_soup = parse_html_soup(html_text)
    teams_all_df = parse_html_table(html_soup.prettify(),extract_links='body')
    teams_all_hrefs_list = [href for _,href in teams_all_df['Franchise'] if href is not None]
    teams_active = html_soup.find('table', {'id': 'teams_active'})
    teams_active_df = parse_html_table(teams_active.prettify(),extract_links='body')
    teams_active_hrefs_list = [href for _,href in teams_active_df['Franchise'] if href is not None]
    save_file(f'{outdir}/teams_active.txt', '\n'.join(teams_active_hrefs_list))
    save_file(f'{outdir}/teams.txt', '\n'.join(teams_all_hrefs_list))

def scrape_team_seasons_hrefs():
    """
    Scrape all team seasons hrefs
    Usage: python3 scrape.py -m team_seasons_hrefs
    """
    # Load teams list
    if not file_exists(outdir + 'teams.txt'):
        print('teams.txt not found. Scraping teams hrefs...')
        scrape_teams_hrefs(start_season,end_season)
    else:
        print('teams.txt found. Scraping team seasons hrefs...')

    teams_list = load_file(f'{outdir}/teams.txt').split('\n')
    tqdm_team_list = tqdm(teams_list)
    all_team_seasons_hrefs_list = []
    fails = []
    # For each team, scrape the team seasons hrefs
    for team in tqdm_team_list:
        tqdm_team_list.set_description(team)
        html_text = request_html_text(HOME_PAGE + team)
        html_text = clean_html_text(html_text)
        try:
            team_seasons_df = parse_html_table(html_text,extract_links='body')
            team_seasons_hrefs_list = [href for _,href in team_seasons_df['Season']]
            all_team_seasons_hrefs_list += team_seasons_hrefs_list
        except Exception as e:
            print(f'Error parsing {team}: {e}')
            fails.append(team)
        time.sleep(sleep)
    save_file(f'{outdir}/team_seasons.txt', '\n'.join(all_team_seasons_hrefs_list))

def scrape_team_season_gamelogs_html():
    """
    Scrape all team seasons gamelogs html
    Usage: python3 scrape.py -m gamelogs_html
    """
    # Load team seasons list
    if not file_exists(outdir + 'team_seasons.txt'):
        print('team_seasons.txt not found. Scraping team seasons hrefs...')
        scrape_team_seasons_hrefs()
    else:
        print('team_seasons.txt found. Scraping team seasons gamelogs html...')

    team_seasons_list = load_file(f'{outdir}/team_seasons.txt').split('\n')
    tqdm_team_seasons_list = tqdm(team_seasons_list)
    fails = []
    # For each team season, scrape the basic and advanced game logs
    for team_season in tqdm_team_seasons_list:
        for gl in ['/gamelog','/gamelog-advanced']:
            url = team_season.strip('.html') + gl
            tqdm_team_seasons_list.set_description(url)
            if file_exists(f'{outdir}{url}.html'):
                continue
            try:
                html_soup = request_html_soup(HOME_PAGE + url)
                html_soup = content_div_only(html_soup)
                html_text = clean_html_text(html_soup.prettify())
                save_file(f'{outdir}{url}.html', html_text)
            except Exception as e:
                print(f'Error scraping {url}: {e}')
                fails.append(url)
            time.sleep(sleep)
    if fails:
        print(f'Failed to scrape {len(fails)} team seasons: {fails}')


if __name__ == "__main__":
    if mode == 'boxscores_hrefs':
        scrape_boxscores_hrefs(start_season,end_season)
    elif mode == 'boxscores_html':
        scrape_all_boxscores_html(outdir)
    elif mode == 'teams_hrefs':
        scrape_teams_hrefs()
    elif mode == 'team_seasons_hrefs':
        scrape_team_seasons_hrefs()
    elif mode == 'gamelogs_html':
        scrape_team_season_gamelogs_html()
    else:
        print('Invalid mode. Use boxscores_html, boxscores_hrefs, teams_hrefs, team_seasons_hrefs, or gamelogs_html')

# code/v6/scripts/scrape.py