import sqlite3
import httpx
import pandas as pd
import concurrent.futures
import json
import threading

# Thread-local storage for httpx clients
_thread_local = threading.local()

def get_client():
    """Get or create a thread-local httpx client"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = httpx.Client(timeout=30.0)
    return _thread_local.client

## Get current teams

def get_current_teams():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams"
    params = {
        "limit": 1000
    }
    response = get_client().get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    teams_list = data.get('sports', [{}])[0].get('leagues',[{}])[0].get('teams',[])
    teams_list = [team['team'] for team in teams_list]

    all_teams =[]
    for team in teams_list:
        team_dict = {
            'id' : team.get('id'),
            'uid' : team.get('uid'),
            'slug' : team.get('slug'),
            'abbreviation' : team.get('abbreviation'),
            'displayName' : team.get('displayName'),
            'name': team.get('name'),
            'nickname' : team.get('nickname'),
            'location' : team.get('location'),
            'color' : team.get('color'),
            'alternateColor' : team.get('alternateColor'),
            'logos' : team.get('logos',[]),
            
            }
        all_teams.append(team_dict)
    return all_teams

current_teams = get_current_teams()

conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()
cursor.execute('SELECT year FROM seasons ORDER BY year DESC')
years = [row[0] for row in cursor.fetchall()]
conn.close()


# Get conferences per year AKA groups
def get_conference_urls_per_year(year):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/{year}/types/2/groups/50/children"
    params = {
        "lang": "en",
        "region": "us",
        'limit' : 100
    }
    response = get_client().get(url, params=params)
    data = response.json()
    urls = data.get('items',[])
    urls = [url.get('$ref') for url in urls]
    return urls


all_conference_urls = []

# Using ThreadPoolExecutor to fetch conference URLs in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = executor.map(get_conference_urls_per_year, years)
    
    for urls in results:
        all_conference_urls.extend(urls)


def get_conference_data(conference_url):
    response = httpx.get(conference_url)
    response.raise_for_status()
    data = response.json()

    season = conference_url.split('seasons/')[-1].split('/')[0]
    conf_dict = {
        'season_id' : f"{season}-{data.get('id')}",
        'id' : data.get('id'),
        'season' : season,
        'name' : data.get('name'),
        'abbreviation' : data.get('abbreviation'),
        'shortName' : data.get('shortName'),
        'midsizeName' : data.get('midsizeName'),
        'logos' : data.get('logos',[]),
        'slug' : data.get('slug'),
        'parent' : '50'
        }
    if 'children' in data:
        conf_dict['has_children'] = True
    else:
        conf_dict['has_children'] = False
        
    return conf_dict


all_conferences = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(get_conference_data, all_conference_urls)
    for conference in results:
        all_conferences.append(conference)


def add_child_conferences(conf):
    season = conf['season']
    parent = conf['id']
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/{season}/types/2/groups/{parent}/children?lang=en&region=us"
    response = get_client().get(url)
    response.raise_for_status()

    data = response.json()

    child_urls = [x['$ref'] for x in data.get('items',[])]

    # Helper function to fetch individual child conference
    def fetch_child_conference(child_url):
        response = get_client().get(child_url)
        response.raise_for_status()
        data = response.json()

        conf_dict = {
            'season_id' : f"{season}-{data.get('id')}",
            'id' : data.get('id'),
            'season' : season,
            'name' : data.get('name'),
            'abbreviation' : data.get('abbreviation'),
            'shortName' : data.get('shortName'),
            'midsizeName' : data.get('midsizeName'),
            'logos' : data.get('logos',[]),
            'slug' : data.get('slug'),
            'parent' : f"{parent}"
        }
        if 'children' in data:
            print(season, data.get('id'))
            conf_dict['has_children'] = True
        else:
            conf_dict['has_children'] = False

        return conf_dict

    # Parallelize child conference fetching
    child_confs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(fetch_child_conference, child_urls)
        child_confs.extend(results)

    return child_confs

# Filter conferences that have children
has_children = [conf for conf in all_conferences if conf['has_children']]

# Multithreaded execution
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = executor.map(add_child_conferences, has_children)

    for child_list in results:
        all_conferences.extend(child_list)

# Sort all_conferences by season_id to ensure consistent ordering across runs
all_conferences.sort(key=lambda x: x['season_id'])




def get_teams_per_conference_per_season(conf_row):
    season = conf_row['season']
    conference_id = conf_row['id']
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/{season}/types/2/groups/{conference_id}/teams?lang=en&region=us"
    params = {
        'limit' : 100,
        'region' : 'us',
        'lang' : 'en'
    }

    response = get_client().get(url, params=params)
    response.raise_for_status()

    data = response.json()

    team_urls = [x['$ref'] for x in data.get('items',[])]
    
    
    # Helper to fetch individual team details
    def get_team_details(team_url):
        team_response = get_client().get(team_url)
        team_response.raise_for_status()
        
        team_data = team_response.json()
        team_id = team_data.get('id')
        
        return {
            'season_conf_team' : f"{season}-{conference_id}-{team_id}",
            'season' : season,
            'conference_id' : conference_id,
            'team_id' : team_id,
            'guid' : team_data.get('guid'),
            'uid' : team_data.get('uid'),
            'slug' : team_data.get('slug'),
            'location' : team_data.get('location'),
            'name' : team_data.get('name'),
            'abbreviation' : team_data.get('abbreviation'),
            'displayName' : team_data.get('displayName'),
            'shortDisplayName' : team_data.get('shortDisplayName'),
            'color' : team_data.get('color'),
            'alternateColor' : team_data.get('alternateColor'),
            'logos' : team_data.get('logos', []),
            'venue_id' : team_data.get('venue',{}).get('id'),
        }

    teams_list = []
    # Using ThreadPoolExecutor specifically for parsing the team details
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(get_team_details, team_urls)
        teams_list.extend(results)

    return teams_list

all_teams_list = []





# Multithreaded execution across conferences
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    # Map the function over the conferences and convert to list to ensure all threads complete
    conference_results = list(executor.map(get_teams_per_conference_per_season, all_conferences[900:]))

    for conference_teams in conference_results:
        if conference_teams:
            # display(pd.DataFrame(conference_teams))
            # Accumulate all teams into the main teams_list
            all_teams_list.extend(conference_teams)


# Connect to database and insert/update data
conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Batch insert/update current teams
teams_data = [
    (team['id'], team['uid'], team['slug'], team['abbreviation'], team['displayName'],
     team['name'], team['nickname'], team['location'], team['color'], team['alternateColor'],
     json.dumps(team['logos']))
    for team in current_teams
]
cursor.executemany('''
    INSERT OR REPLACE INTO teams (id, uid, slug, abbreviation, displayName, name, nickname, location, color, alternateColor, logos)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', teams_data)

# Batch insert/update conferences
conferences_data = [
    (conf['season_id'], conf['id'], conf['season'], conf['name'], conf['abbreviation'],
     conf['shortName'], conf['midsizeName'], json.dumps(conf['logos']), conf['slug'],
     conf['parent'], int(conf['has_children']))
    for conf in all_conferences
]
cursor.executemany('''
    INSERT OR REPLACE INTO conferences (season_id, id, season, name, abbreviation, shortName, midsizeName, logos, slug, parent, has_children)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', conferences_data)

# Batch insert/update team seasons
team_seasons_data = [
    (ts['season_conf_team'], ts['season'], ts['conference_id'],
     ts['team_id'], ts['guid'], ts['uid'], ts['slug'],
     ts['location'], ts['name'], ts['abbreviation'],
     ts['displayName'], ts['shortDisplayName'], ts['color'],
     ts['alternateColor'], json.dumps(ts['logos']), ts['venue_id'])
    for ts in all_teams_list
]
cursor.executemany('''
    INSERT OR REPLACE INTO team_seasons (season_conf_team, season, conference_id, team_id, guid, uid, slug, location, name, abbreviation, displayName, shortDisplayName, color, alternateColor, logos, venue_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', team_seasons_data)

conn.commit()
conn.close()

print(f"Successfully inserted {len(current_teams)} teams, {len(all_conferences)} conferences, and {len(all_teams_list)} team-season records into the database.")
