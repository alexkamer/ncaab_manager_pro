import httpx
import pandas as pd
import sqlite3
import concurrent.futures
import threading

# Thread-local storage for httpx clients
_thread_local = threading.local()

def get_client():
    """Get or create a thread-local httpx client"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = httpx.Client(timeout=30.0)
    return _thread_local.client

conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Fetch pairs of season and team_id
cursor.execute("SELECT season, team_id FROM team_seasons")
team_seasons_list = cursor.fetchall()

conn.close()

def get_base_coach_info(coach_url, season, team_id):
    coach_response = get_client().get(coach_url)
    coach_response.raise_for_status()

    coach_data = coach_response.json()

    coach_id = coach_data.get('id')
    if coach_id:
        return {
            'season_id' : f"{season}-{coach_id}",
            'season' : season,
            'team_id' : team_id,
            'firstName' : coach_data.get('firstName'),
            'lastName' : coach_data.get('lastName')
        }
    else:
        return {}

def get_team_coach_for_year(team_season):
    season = team_season[0]
    team_id = team_season[1]

    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/{season}/teams/{team_id}/coaches?lang=en&region=us"
    response = get_client().get(url)
    response.raise_for_status()
    data = response.json()

    coach_urls = [item['$ref'] for item in data.get('items',[])]
    coach_df = []
    for coach_url in coach_urls:
        coach_df.append(get_base_coach_info(coach_url, season, team_id))
    return coach_df



yearly_coach_data = []

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(get_team_coach_for_year, team_seasons_list[7000:])

    for result in results:
        yearly_coach_data.extend(result)


# Connect to database and insert/update data
conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Batch insert/update coaches
coaches_data = [
    (coach['season_id'], coach['season'], coach['team_id'], coach['firstName'], coach['lastName'])
    for coach in yearly_coach_data
    if coach  # Filter out empty dictionaries
]
cursor.executemany('''
    INSERT OR REPLACE INTO coaches (season_id, season, team_id, firstName, lastName)
    VALUES (?, ?, ?, ?, ?)
''', coaches_data)

conn.commit()
conn.close()

print(f"Successfully inserted {len(coaches_data)} coach records into the database.")