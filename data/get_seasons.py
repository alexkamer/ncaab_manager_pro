import pandas as pd
import httpx
import sqlite3


def get_season_urls():
    url = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons"
    params = {
        "limit": 1000,
        'lang' : 'en',
        'region' : 'us'
    }

    response = httpx.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    for season in data.get('items',[]):
        yield season.get('$ref')

season_urls = list(get_season_urls())

import concurrent.futures

def get_season_data(season_url):
    response = httpx.get(season_url)
    response.raise_for_status()
    data = response.json()
    base_season_dict = {
        'year' : data.get('year'),
        'startDate' : data.get('startDate'),
        'endDate' : data.get('endDate'),
        'displayName': data.get('displayName'),      
    }

    season_types = []
    for season_type in data.get('types',{}).get('items',[]):
        season_type_dict = {
            'season_id' : f"{data.get('year')}-{season_type.get('id')}",
            'year' : data.get('year'),
            'type_id' : season_type.get('id'),
            'name' : season_type.get('name'),
            'startDate' : season_type.get('startDate'),
            'endDate' : season_type.get('endDate'),
        }
        season_types.append(season_type_dict)
    return base_season_dict, season_types

# Multithreaded execution
all_base_seasons = []
all_season_types = []

# Adjust max_workers as needed (default is usually number of processors * 5)
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    # map returns results in the same order as the input list
    results = executor.map(get_season_data, season_urls)
    
    for base_season_dict, season_types in results:
        all_base_seasons.append(base_season_dict)
        all_season_types.extend(season_types)


# Connect to database and insert/update data
conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Insert/update seasons data
for season in all_base_seasons:
    cursor.execute('''
        INSERT OR REPLACE INTO seasons (year, startDate, endDate, displayName)
        VALUES (?, ?, ?, ?)
    ''', (season['year'], season['startDate'], season['endDate'], season['displayName']))

# Insert/update season_types data
for season_type in all_season_types:
    cursor.execute('''
        INSERT OR REPLACE INTO season_types (season_id, year, type_id, name, startDate, endDate)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (season_type['season_id'], season_type['year'], season_type['type_id'],
          season_type['name'], season_type['startDate'], season_type['endDate']))

conn.commit()
conn.close()

print(f"Successfully inserted {len(all_base_seasons)} seasons and {len(all_season_types)} season types into the database.")
