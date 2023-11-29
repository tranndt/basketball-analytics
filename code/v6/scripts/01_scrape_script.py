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
parser.add_argument('-o', '--outdir', type=str, default='../data/', help='Save to directory')
parser.add_argument('-ss', '--start_season', type=int, default=0, help='Start season')
parser.add_argument('-es', '--end_season', type=int, default=None, help='End season')
parser.add_argument('-m', '--mode', type=str, default='boxscores_html', help='Scraping mode: boxscores_html or boxscores_hrefs')

args = parser.parse_args()
sleep = args.sleep
debug = args.debug
outdir = args.outdir
start_season = args.start_season
end_season = args.end_season
mode = args.mode

# Scraping all boxscores hrefs
def scrape_boxscores_hrefs(start_season=0,end_season=None):
    # fetch season boxscores list
    game_hrefs = []
    seasons_hrefs = req_all_seasons_hrefs()[start_season:end_season]
    for season_href in tqdm(seasons_hrefs,position=0, leave=True):
        season_games_hrefs = req_season_games_hrefs(season_href,sleep)
        game_hrefs += sorted(season_games_hrefs,reverse=True)
        save_file(outdir + 'boxscores.txt', '\n'.join(game_hrefs))
        time.sleep(sleep)

# Scraping all boxscores
def scrape_boxscores_html(start_season=0,end_season=None):
    # Check if boxscores hrefs list exists, if not scrape it
    if not file_exists(outdir + 'boxscores.txt'):
        print('boxscores.txt not found. Scraping boxscores hrefs...')
        scrape_boxscores_hrefs(start_season,end_season)
    else:
        print('boxscores.txt found. Scraping boxscores html...')
    # Load boxscores hrefs list
    game_hrefs = load_file(outdir + 'boxscores.txt').split('\n')
    game_hrefs_tqdm = tqdm(game_hrefs,position=0, leave=True)
    for game_href in game_hrefs_tqdm:
        game_hrefs_tqdm.set_description(f'{game_href}')
        # Check if we already have the boxscores
        if file_exists(outdir + game_href):
            continue
        # Else fetch the game html
        try:
            html_soup = request_html_soup(HOME_PAGE + game_href)
            html_text = content_div_only(html_soup).prettify()
            save_file(outdir + game_href, html_text)
            time.sleep(sleep)
        except Exception as e:
            print(f'Error getting boxscores for game {game_href}: {e}')

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
        scrape_boxscores_html(start_season,end_season)
    elif mode == 'teams_hrefs':
        scrape_teams_hrefs()
    elif mode == 'team_seasons_hrefs':
        scrape_team_seasons_hrefs()
    elif mode == 'gamelogs_html':
        scrape_team_season_gamelogs_html()
    else:
        print('Invalid mode. Use boxscores_html, boxscores_hrefs, teams_hrefs, team_seasons_hrefs, or gamelogs_html')

# code/v6/scripts/scrape.py