import pandas as pd
import httpx
import sqlite3
import concurrent.futures
import threading
import json

# Thread-local storage for httpx clients
_thread_local = threading.local()

def get_client():
    """Get or create a thread-local httpx client"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = httpx.Client(timeout=30.0)
    return _thread_local.client


def get_current_players():
    base_url = "https://sports.core.api.espn.com/v3/sports/basketball/mens-college-basketball/athletes"
    params = {
        'limit' : 1000,
        'active' : True
    }
    base_response = get_client().get(base_url, params=params)
    base_response.raise_for_status()
    base_data = base_response.json()
    page_count = base_data.get('pageCount', 1)
    players = []
    for page in range(1, page_count + 1):
        params['page'] = page
        response = get_client().get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        for player in data.get('items',[]):
            player_dict = {
                'id' : player.get('id'),
                'uid' : player.get('uid'),
                'guid' : player.get('guid'),
                'firstName' : player.get('firstName'),
                'lastName' : player.get('lastName'),
                'displayName' : player.get('displayName'),
                'shortName' : player.get('shortName'),
                'weight' : player.get('weight'),
                'displayWeight' : player.get('displayWeight'),
                'height' : player.get('height'),
                'displayHeight' : player.get('displayHeight'),
                'birthPlace_city' : player.get('birthPlace',{}).get('city'),
                'birthPlace_state' : player.get('birthPlace',{}).get('state'),
                'birthPlace_country' : player.get('birthPlace',{}).get('country'),
                'experience_years' : player.get('experience',{}).get('years'),
                'experience_displayValue' : player.get('experience',{}).get('displayValue'),
                'experience_abbreviation' : player.get('experience',{}).get('abbreviation'),
                'jersey' : player.get('jersey'),
                'hand_type' : player.get('hand',{}).get('type'),
                'hand_abbreviation' : player.get('hand',{}).get('abbreviation'),
                'hand_displayValue' : player.get('hand',{}).get('displayValue'),

            }
            players.append(player_dict)
    return players

        
    
# current_players = get_current_players()

def get_player_info(player_url):
    response = get_client().get(player_url)
    data = response.json()
    season = player_url.split("seasons/")[1].split("/")[0]
    player_id = player_url.split("athletes/")[1].split("?")[0]
    player_dict = {
        'season_player_id' : f"{season}-{player_id}",
        'season': season,
        'player_id': player_id,
        'uid' : data.get('uid'),
        'guid' : data.get('guid'),
        'firstName': data.get('firstName'),
        'lastName' : data.get('lastName'),
        'fullName' : data.get('fullName'),
        'displayName' : data.get('displayName'),
        'shortName' : data.get('shortName'),
        'weight' : data.get('weight'),
        'displayWeight' : data.get('displayWeight'),
        'height' : data.get('height'),
        'displayHeight' : data.get('displayHeight'),
        'birthPlace_city' : data.get('birthPlace',{}).get('city'),
        'birthPlace_state' : data.get('birthPlace',{}).get('state'),
        'birthPlace_country' : data.get('birthPlace',{}).get('country'),
        'slug' : data.get('slug'),
        'headshot' : data.get('headshot',{}).get('href', f"https://a.espncdn.com/i/headshots/mens-college-basketball/players/full/{player_id}.png"),
        'jersey' : data.get('jersey'),
        'hand_type' : data.get('hand',{}).get('type'),
        'hand_abbreviation' : data.get('hand',{}).get('abbreviation'),
        'hand_displayValue' : data.get('hand',{}).get('displayValue'),
        'flag_href' : data.get('flag',{}).get('href'),
        'position_id' : data.get('position',{}).get('id'),
        'position_name' : data.get('position',{}).get('name'),
        'position_abbreviation' : data.get('position',{}).get('abbreviation'),
        'position_displayValue' : data.get('position',{}).get('displayValue'),
        'experience_years' : data.get('experience',{}).get('years'),
        'experience_displayValue' : data.get('experience',{}).get('displayValue'),
        'experience_abbreviation' : data.get('experience',{}).get('abbreviation')

    }
    try:
        player_dict['team_id'] = data.get('team',{}).get('$ref').split('/teams/')[1].split('?')[0]
    except:
        player_dict['team_id'] = None
    return player_dict

def get_roster_for_team_for_season(season, team):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/{season}/teams/{team}/athletes"
    params = {
        "lang": "en",
        "region": "us",
        "limit" : 150
    }
    response = get_client().get(url, params=params)
    data = response.json()
    player_urls = [player['$ref'] for player in data.get('items',[])]

    players = []

    # Using ThreadPoolExecutor to fetch player info in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(get_player_info, player_urls)

        for player_dict in results:
            players.append(player_dict)

    return players


import sqlite3

conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Fetch pairs of season and team_id
cursor.execute("SELECT year, team_id FROM team_seasons")
team_seasons_list = cursor.fetchall()

conn.close()

# team_seasons_list will be a list of tuples: [(2025, '123'), (2025, '456'), ...]
print(f"Found {len(team_seasons_list)} team-season records.")

def process_team_roster(team_pair):
    # Unpack the tuple based on your SQL query (season, team_id)
    season, team_id = team_pair
    return get_roster_for_team_for_season(season, team_id)

players = []

# Using ThreadPoolExecutor to fetch rosters in parallel
# You can adjust max_workers if needed
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(process_team_roster, team_seasons_list)

    for roster in results:
        players.extend(roster)


# Connect to database and insert/update data
conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# # Batch insert/update current players
# current_players_data = [
#     (p['id'], p['uid'], p['guid'], p['firstName'], p['lastName'], p['displayName'],
#      p['shortName'], p['weight'], p['displayWeight'], p['height'], p['displayHeight'],
#      p['birthPlace_city'], p['birthPlace_state'], p['birthPlace_country'],
#      p['experience_years'], p['experience_displayValue'], p['experience_abbreviation'],
#      p['jersey'], p['hand_type'], p['hand_abbreviation'], p['hand_displayValue'])
#     for p in current_players
# ]
# cursor.executemany('''
#     INSERT OR REPLACE INTO players (id, uid, guid, firstName, lastName, displayName, shortName, weight, displayWeight, height, displayHeight, birthPlace_city, birthPlace_state, birthPlace_country, experience_years, experience_displayValue, experience_abbreviation, jersey, hand_type, hand_abbreviation, hand_displayValue)
#     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# ''', current_players_data)

# Batch insert/update player seasons
player_seasons_data = [
    (p['season_player_id'], p['season'], p['player_id'], p['uid'], p['guid'],
     p['firstName'], p['lastName'], p['fullName'], p['displayName'], p['shortName'],
     p['weight'], p['displayWeight'], p['height'], p['displayHeight'],
     p['birthPlace_city'], p['birthPlace_state'], p['birthPlace_country'],
     p['slug'], p['headshot'], p['jersey'], p['hand_type'], p['hand_abbreviation'],
     p['hand_displayValue'], p['flag_href'], p['position_id'], p['position_name'],
     p['position_abbreviation'], p['position_displayValue'], p['team_id'],
     p['experience_years'], p['experience_displayValue'], p['experience_abbreviation'])
    for p in players
]
cursor.executemany('''
    INSERT OR REPLACE INTO player_seasons (season_player_id, season, player_id, uid, guid, firstName, lastName, fullName, displayName, shortName, weight, displayWeight, height, displayHeight, birthPlace_city, birthPlace_state, birthPlace_country, slug, headshot, jersey, hand_type, hand_abbreviation, hand_displayValue, flag_href, position_id, position_name, position_abbreviation, position_displayValue, team_id, experience_years, experience_displayValue, experience_abbreviation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', player_seasons_data)

conn.commit()
conn.close()

print(f"Successfully inserted  current players and {len(players)} player-season records into the database.")