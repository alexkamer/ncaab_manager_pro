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
cursor.execute("SELECT id FROM games")
event_ids = cursor.fetchall()
event_ids = sorted([int(x[0]) for x in event_ids])
conn.close()


def get_odds_for_game(event_id):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{event_id}/competitions/{event_id}/odds/"

    try:
        response = get_client().get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        # Log error to file
        with open('data/odds_errors.log', 'a') as f:
            f.write(f"Error fetching odds for event {event_id}: {e}\n")
        return []

    odds_df = []


    for provider in data.get('items',[]):
        provider_id = provider.get('provider',{}).get('id')
        away_team_odds = provider.get('awayTeamOdds',{})
        home_team_odds = provider.get('homeTeamOdds',{})

        try:
            away_team_id = away_team_odds.get('team',{}).get('$ref').split('/teams/')[-1].split('?')[0]
            home_team_id = home_team_odds.get('team',{}).get('$ref').split('/teams/')[-1].split('?')[0]
        except:
            away_team_id = None
            home_team_id = None


        odds_dict = {
            'event_provider_id' : f"{event_id}_{provider_id}",
            'event_id' : event_id,
            'provider_id' : provider_id,
            'provider_name' : provider.get('provider',{}).get('name'),
            'details' : provider.get('details'),
            'over_under' : provider.get('overUnder'),
            'spread' : provider.get('spread'),
            'over_odds' : provider.get('overOdds'),
            'under_odds' : provider.get('underOdds'),
            'away_team_favorite' : away_team_odds.get('favorite'),
            'away_team_underdog' : away_team_odds.get('underdog'),
            'away_team_moneyline' : away_team_odds.get('moneyLine'),
            'away_team_spread_odds' : away_team_odds.get('spreadOdds'),
            'away_team_spread' : away_team_odds.get('current',{}).get('pointSpread',{}).get('american'),
            'away_team_id' : away_team_id,
            'home_team_favorite' : home_team_odds.get('favorite'),
            'home_team_underdog' : home_team_odds.get('underdog'),
            'home_team_moneyline' : home_team_odds.get('moneyLine'),
            'home_team_spread_odds' : home_team_odds.get('spreadOdds'),
            'home_team_spread' : home_team_odds.get('current',{}).get('pointSpread',{}).get('american'),
            'home_team_id' : home_team_id
        }

        odds_df.append(odds_dict)


    return odds_df




all_odds = []

# Using ThreadPoolExecutor to fetch rosters in parallel
# You can adjust max_workers if needed
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(get_odds_for_game, event_ids[40000:])

    for odds in results:
        if odds:  # Only append if it's not None
            all_odds.extend(odds)


# Connect to database and insert/update data
conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Batch insert/update odds
odds_data = [
    (o['event_provider_id'], o['event_id'], o.get('provider_id'), o.get('provider_name'),
     o.get('details'), o.get('over_under'), o.get('spread'), o.get('over_odds'), o.get('under_odds'),
     o.get('away_team_favorite'), o.get('away_team_underdog'), o.get('away_team_moneyline'),
     o.get('away_team_spread_odds'), o.get('away_team_spread'), o.get('away_team_id'),
     o.get('home_team_favorite'), o.get('home_team_underdog'), o.get('home_team_moneyline'),
     o.get('home_team_spread_odds'), o.get('home_team_spread'), o.get('home_team_id'))
    for o in all_odds
]
cursor.executemany('''
    INSERT OR REPLACE INTO odds (event_provider_id, event_id, provider_id, provider_name, details, over_under, spread, over_odds, under_odds, away_team_favorite, away_team_underdog, away_team_moneyline, away_team_spread_odds, away_team_spread, away_team_id, home_team_favorite, home_team_underdog, home_team_moneyline, home_team_spread_odds, home_team_spread, home_team_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', odds_data)

conn.commit()
conn.close()

print(f"Successfully inserted {len(odds_data)} odds records into the database.")


