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
    Query database for games eligible for odds:
    - Games in next 7 days (upcoming)
    - That don't already have odds
    """
    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM games
        WHERE date BETWEEN date('now') AND date('now', '+7 days')
        AND id NOT IN (SELECT DISTINCT event_id FROM odds)
    """)

    eligible_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    return eligible_ids

def fetch_odds(event_id):
    """
    Fetch odds data for a single event.
    Returns list of odds dicts (one per provider) or empty list if not available.
    """
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{event_id}/competitions/{event_id}/odds"
    params = {
        'lang': 'en',
        'region': 'us'
    }

    try:
        response = get_client().get(url, params=params)
        response.raise_for_status()
        data = response.json()

        odds_list = []

        for item in data.get('items', []):
            provider = item.get('provider', {})
            details = item.get('details')
            over_under = item.get('overUnder')
            spread = item.get('spread')
            over_odds = item.get('overOdds')
            under_odds = item.get('underOdds')

            # Extract home/away odds
            home_odds = {}
            away_odds = {}

            for team_odds in item.get('homeTeamOdds', {}).get('items', []):
                home_odds = {
                    'favorite': team_odds.get('favorite'),
                    'underdog': team_odds.get('underdog'),
                    'moneyline': team_odds.get('moneyLine'),
                    'spread_odds': team_odds.get('spreadOdds'),
                    'spread': team_odds.get('spread', {}).get('displayValue'),
                    'team_id': team_odds.get('team', {}).get('id')
                }

            for team_odds in item.get('awayTeamOdds', {}).get('items', []):
                away_odds = {
                    'favorite': team_odds.get('favorite'),
                    'underdog': team_odds.get('underdog'),
                    'moneyline': team_odds.get('moneyLine'),
                    'spread_odds': team_odds.get('spreadOdds'),
                    'spread': team_odds.get('spread', {}).get('displayValue'),
                    'team_id': team_odds.get('team', {}).get('id')
                }

            odds_dict = {
                'event_provider_id': f"{event_id}_{provider.get('id')}",
                'event_id': event_id,
                'provider_id': provider.get('id'),
                'provider_name': provider.get('name'),
                'details': details,
                'over_under': over_under,
                'spread': spread,
                'over_odds': over_odds,
                'under_odds': under_odds,
                'away_team_favorite': away_odds.get('favorite'),
                'away_team_underdog': away_odds.get('underdog'),
                'away_team_moneyline': away_odds.get('moneyline'),
                'away_team_spread_odds': away_odds.get('spread_odds'),
                'away_team_spread': away_odds.get('spread'),
                'away_team_id': away_odds.get('team_id'),
                'home_team_favorite': home_odds.get('favorite'),
                'home_team_underdog': home_odds.get('underdog'),
                'home_team_moneyline': home_odds.get('moneyline'),
                'home_team_spread_odds': home_odds.get('spread_odds'),
                'home_team_spread': home_odds.get('spread'),
                'home_team_id': home_odds.get('team_id')
            }

            odds_list.append(odds_dict)

        return odds_list

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # 404 is normal - not all games have odds
            return []
        else:
            with open('data/odds_errors.log', 'a') as f:
                f.write(f"Error fetching odds for {event_id}: {e}\n")
            return []
    except Exception as e:
        with open('data/odds_errors.log', 'a') as f:
            f.write(f"Error fetching odds for {event_id}: {e}\n")
        return []

def insert_odds(odds_data):
    """Insert odds into database"""
    if not odds_data:
        return

    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()

    odds_tuples = [
        (o['event_provider_id'], o['event_id'], o.get('provider_id'),
         o.get('provider_name'), o.get('details'), o.get('over_under'),
         o.get('spread'), o.get('over_odds'), o.get('under_odds'),
         o.get('away_team_favorite'), o.get('away_team_underdog'),
         o.get('away_team_moneyline'), o.get('away_team_spread_odds'),
         o.get('away_team_spread'), o.get('away_team_id'),
         o.get('home_team_favorite'), o.get('home_team_underdog'),
         o.get('home_team_moneyline'), o.get('home_team_spread_odds'),
         o.get('home_team_spread'), o.get('home_team_id'))
        for o in odds_data
    ]

    cursor.executemany('''
        INSERT OR REPLACE INTO odds (event_provider_id, event_id, provider_id, provider_name,
        details, over_under, spread, over_odds, under_odds, away_team_favorite, away_team_underdog,
        away_team_moneyline, away_team_spread_odds, away_team_spread, away_team_id, home_team_favorite,
        home_team_underdog, home_team_moneyline, home_team_spread_odds, home_team_spread, home_team_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', odds_tuples)

    conn.commit()
    conn.close()

def update_odds(verbose=True):
    """
    Main function to update odds table.

    Returns:
        Dictionary with update statistics
    """
    start_time = time.time()

    if verbose:
        print("\n=== Updating Odds ===\n")

    # 1. Get eligible game IDs
    eligible_ids = get_eligible_game_ids()

    if not eligible_ids:
        if verbose:
            print("✓ No games need odds")
        return {
            'odds_added': 0,
            'api_calls': 0,
            'duration_seconds': time.time() - start_time,
            'errors': 0
        }

    if verbose:
        print(f"Checking odds for {len(eligible_ids)} games...")

    # 2. Fetch odds in parallel
    all_odds = []
    not_found_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_odds, eligible_ids)

        for odds_list in results:
            if odds_list:
                all_odds.extend(odds_list)
            else:
                not_found_count += 1

    if verbose:
        print(f"\n✓ Found {len(all_odds)} odds entries")
        if not_found_count > 0:
            print(f"  ℹ {not_found_count} games without odds (normal)")

    # 3. Insert into database
    if all_odds:
        insert_odds(all_odds)
        if verbose:
            print(f"  ✓ Inserted {len(all_odds)} odds entries")

    duration = time.time() - start_time

    # Log the update
    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO update_log (table_name, operation, records_added, records_updated,
                                api_calls, duration_seconds, error_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('odds', 'daily_update', len(all_odds), 0, len(eligible_ids), duration, 0))
    conn.commit()
    conn.close()

    if verbose:
        print(f"\n✓ Odds update complete in {duration:.1f} seconds")

    return {
        'odds_added': len(all_odds),
        'api_calls': len(eligible_ids),
        'duration_seconds': duration,
        'errors': 0
    }

if __name__ == "__main__":
    # Test the update function
    stats = update_odds(verbose=True)
    print(f"\nUpdate Statistics:")
    print(f"  Odds added: {stats['odds_added']}")
    print(f"  API calls: {stats['api_calls']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")
