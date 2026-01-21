import pandas as pd
import httpx
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
# conn = sqlite3.connect('ncaab.db')

cursor = conn.cursor()

# Fetch pairs of season and team_id
cursor.execute("SELECT id FROM games")
event_ids = cursor.fetchall()
event_ids = sorted([int(x[0]) for x in event_ids])
conn.close()

def get_prediction_for_game(event_id):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{event_id}/competitions/{event_id}/predictor?lang=en&region=us"

    try:
        response = get_client().get(url=url)
        # This will raise HTTPStatusError if the response is 4xx or 5xx
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Check specifically for 404 (Not Found), 403 (Forbidden), and 504 (Gateway Timeout)
        if e.response.status_code in [404, 403, 504]:
            return None
        # Re-raise for any other HTTP errors we aren't expecting
        raise e
    except Exception as e:
        # Log other errors to file
        with open('data/prediction_errors.log', 'a') as f:
            f.write(f"Error fetching prediction for event {event_id}: {e}\n")
        return None
        
    data = response.json()

    predict_dict = {
        'event_id' : event_id,
        'name' : data.get('name'),
        'short_name' : data.get('shortName'),
    }

    for team in ['homeTeam', 'awayTeam']:
        team_data = data.get(team,{}) 
        try:
            team_id = team_data.get('team',{}).get('$ref').split('/teams/')[-1].split('?')[0]
            predict_dict.update({
                f'{team}_team_id' : team_id,
            })

            for stat in team_data.get('statistics',[]):
                predict_dict.update({
                    f'{team}_{stat.get('name')}' : stat.get('value'),
                    f'{team}_{stat.get('name')}_display' : stat.get('displayValue')
                })
        except:
            pass
    return predict_dict


all_predictions = []

# Using ThreadPoolExecutor to fetch rosters in parallel
# You can adjust max_workers if needed
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(get_prediction_for_game, event_ids[40000:])

    for prediction in results:
        if prediction:  # Only append if it's not None
            all_predictions.append(prediction)


# Connect to database and insert/update data
conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Batch insert/update predictions
predictions_data = [
    (p['event_id'], p.get('name'), p.get('short_name'),
     p.get('homeTeam_team_id'), p.get('homeTeam_gameProjection'), p.get('homeTeam_gameProjection_display'),
     p.get('homeTeam_teamChanceLoss'), p.get('homeTeam_teamChanceLoss_display'),
     p.get('awayTeam_team_id'), p.get('awayTeam_gameProjection'), p.get('awayTeam_gameProjection_display'),
     p.get('awayTeam_teamChanceLoss'), p.get('awayTeam_teamChanceLoss_display'))
    for p in all_predictions
]
cursor.executemany('''
    INSERT OR REPLACE INTO predictions (event_id, name, short_name, homeTeam_team_id, homeTeam_gameProjection, homeTeam_gameProjection_display, homeTeam_teamChanceLoss, homeTeam_teamChanceLoss_display, awayTeam_team_id, awayTeam_gameProjection, awayTeam_gameProjection_display, awayTeam_teamChanceLoss, awayTeam_teamChanceLoss_display)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', predictions_data)

conn.commit()
conn.close()

print(f"Successfully inserted {len(predictions_data)} predictions into the database.")