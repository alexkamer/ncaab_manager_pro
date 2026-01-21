import httpx
import sqlite3
import concurrent.futures
import threading
import time

# Thread-local storage for httpx clients
_thread_local = threading.local()

def get_client():
    """Get or create a thread-local httpx client"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = httpx.Client(timeout=30.0)
    return _thread_local.client

def get_eligible_game_ids():
    """
    Query database for games eligible for predictions:
    - Games in next 7 days (upcoming)
    - Games in last 2 days (recently completed - get final predictions)
    - That don't already have predictions
    """
    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM games
        WHERE date BETWEEN date('now', '-2 days') AND date('now', '+7 days')
        AND id NOT IN (SELECT event_id FROM predictions)
    """)

    eligible_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    return eligible_ids

def fetch_prediction(event_id):
    """
    Fetch prediction data for a single event.
    Returns prediction dict or None if not available.
    """
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{event_id}/competitions/{event_id}/predictor"
    params = {
        'lang': 'en',
        'region': 'us'
    }

    try:
        response = get_client().get(url, params=params)
        response.raise_for_status()
        data = response.json()

        prediction_dict = {
            'event_id': event_id,
            'name': data.get('name'),
            'short_name': data.get('shortName')
        }

        # Extract home team prediction
        home_team = data.get('homeTeam', {})
        prediction_dict.update({
            'homeTeam_team_id': home_team.get('team', {}).get('id'),
            'homeTeam_gameProjection': home_team.get('gameProjection'),
            'homeTeam_gameProjection_display': home_team.get('gameProjectionDisplay'),
            'homeTeam_teamChanceLoss': home_team.get('teamChanceLoss'),
            'homeTeam_teamChanceLoss_display': home_team.get('teamChanceLossDisplay')
        })

        # Extract away team prediction
        away_team = data.get('awayTeam', {})
        prediction_dict.update({
            'awayTeam_team_id': away_team.get('team', {}).get('id'),
            'awayTeam_gameProjection': away_team.get('gameProjection'),
            'awayTeam_gameProjection_display': away_team.get('gameProjectionDisplay'),
            'awayTeam_teamChanceLoss': away_team.get('teamChanceLoss'),
            'awayTeam_teamChanceLoss_display': away_team.get('teamChanceLossDisplay')
        })

        return prediction_dict

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # 404 is normal - not all games have predictions
            return None
        else:
            with open('data/prediction_errors.log', 'a') as f:
                f.write(f"Error fetching prediction for {event_id}: {e}\n")
            return None
    except Exception as e:
        with open('data/prediction_errors.log', 'a') as f:
            f.write(f"Error fetching prediction for {event_id}: {e}\n")
        return None

def insert_predictions(predictions_data):
    """Insert predictions into database"""
    if not predictions_data:
        return

    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()

    predictions_tuples = [
        (p['event_id'], p.get('name'), p.get('short_name'),
         p.get('homeTeam_team_id'), p.get('homeTeam_gameProjection'),
         p.get('homeTeam_gameProjection_display'), p.get('homeTeam_teamChanceLoss'),
         p.get('homeTeam_teamChanceLoss_display'), p.get('awayTeam_team_id'),
         p.get('awayTeam_gameProjection'), p.get('awayTeam_gameProjection_display'),
         p.get('awayTeam_teamChanceLoss'), p.get('awayTeam_teamChanceLoss_display'))
        for p in predictions_data
    ]

    cursor.executemany('''
        INSERT OR REPLACE INTO predictions (event_id, name, short_name, homeTeam_team_id,
        homeTeam_gameProjection, homeTeam_gameProjection_display, homeTeam_teamChanceLoss,
        homeTeam_teamChanceLoss_display, awayTeam_team_id, awayTeam_gameProjection,
        awayTeam_gameProjection_display, awayTeam_teamChanceLoss, awayTeam_teamChanceLoss_display)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', predictions_tuples)

    conn.commit()
    conn.close()

def update_predictions(verbose=True):
    """
    Main function to update predictions table.

    Returns:
        Dictionary with update statistics
    """
    start_time = time.time()

    if verbose:
        print("\n=== Updating Predictions ===\n")

    # 1. Get eligible game IDs
    eligible_ids = get_eligible_game_ids()

    if not eligible_ids:
        if verbose:
            print("✓ No games need predictions")
        return {
            'predictions_added': 0,
            'api_calls': 0,
            'duration_seconds': time.time() - start_time,
            'errors': 0
        }

    if verbose:
        print(f"Checking predictions for {len(eligible_ids)} games...")

    # 2. Fetch predictions in parallel
    all_predictions = []
    not_found_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_prediction, eligible_ids)

        for prediction in results:
            if prediction is not None:
                all_predictions.append(prediction)
            else:
                not_found_count += 1

    if verbose:
        print(f"\n✓ Found {len(all_predictions)} predictions")
        if not_found_count > 0:
            print(f"  ℹ {not_found_count} games without predictions (normal)")

    # 3. Insert into database
    if all_predictions:
        insert_predictions(all_predictions)
        if verbose:
            print(f"  ✓ Inserted {len(all_predictions)} predictions")

    duration = time.time() - start_time

    # Log the update
    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO update_log (table_name, operation, records_added, records_updated,
                                api_calls, duration_seconds, error_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('predictions', 'daily_update', len(all_predictions), 0, len(eligible_ids), duration, 0))
    conn.commit()
    conn.close()

    if verbose:
        print(f"\n✓ Predictions update complete in {duration:.1f} seconds")

    return {
        'predictions_added': len(all_predictions),
        'api_calls': len(eligible_ids),
        'duration_seconds': duration,
        'errors': 0
    }

if __name__ == "__main__":
    # Test the update function
    stats = update_predictions(verbose=True)
    print(f"\nUpdate Statistics:")
    print(f"  Predictions added: {stats['predictions_added']}")
    print(f"  API calls: {stats['api_calls']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")
