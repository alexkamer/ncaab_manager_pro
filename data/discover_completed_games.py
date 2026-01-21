import httpx
import sqlite3
from datetime import datetime, timedelta
import threading

# Thread-local storage for httpx clients
_thread_local = threading.local()

def get_client():
    """Get or create a thread-local httpx client"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = httpx.Client(timeout=30.0)
    return _thread_local.client

def generate_month_list(start_date, end_date):
    """Generate list of YYYYMM strings for date range"""
    months = []
    current = start_date.replace(day=1)
    end = end_date.replace(day=1)

    while current <= end:
        months.append(current.strftime('%Y%m'))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return months

def fetch_events_for_month(year_month):
    """
    Fetch all event IDs for a given month (YYYYMM format).
    Returns list of event IDs with their completion status.
    """
    base_url = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events"
    params = {
        'dates': year_month,
        'groups': '50',
        'limit': 1000
    }

    try:
        response = get_client().get(url=base_url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"  Error fetching events for {year_month}: {e}")
        return []

    page_count = data.get('pageCount', 1)
    all_events = []

    # Process first page
    all_events.extend(data.get('items', []))

    # Process additional pages if they exist
    if page_count > 1:
        for page in range(2, page_count + 1):
            params['page'] = page
            try:
                response = get_client().get(url=base_url, params=params)
                response.raise_for_status()
                page_data = response.json()
                all_events.extend(page_data.get('items', []))
            except Exception as e:
                print(f"  Error fetching page {page} for {year_month}: {e}")
                continue

    # Extract event IDs from $ref URLs
    event_ids = []
    for event in all_events:
        ref = event.get('$ref', '')
        if ref:
            event_id = ref.split('/events/')[-1].split('?')[0]
            event_ids.append(event_id)

    return event_ids

def get_existing_game_ids(start_date):
    """Query database for existing game IDs since start_date"""
    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM games
        WHERE date >= ?
    """, (start_date.isoformat(),))

    existing_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    return set(existing_ids)

def check_if_completed(event_id):
    """
    Check if a single event is completed by fetching its summary.
    Returns event_id if completed, None otherwise.
    """
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary"
    params = {'event': event_id}

    try:
        response = get_client().get(url=url, params=params)
        response.raise_for_status()
        data = response.json()

        # Check completion status
        completed = data.get('header', {}).get('competitions', [{}])[0].get('status', {}).get('type', {}).get('completed', False)

        if completed:
            return event_id
        else:
            return None

    except Exception as e:
        # Silently skip errors (404s for invalid events, etc.)
        return None

def discover_new_completed_games(days_lookback=7, verbose=True):
    """
    Discover completed games in last N days without pre-generation.
    Returns only event IDs not already in database.

    Args:
        days_lookback: Number of days to look back (default 7)
        verbose: Print progress messages (default True)

    Returns:
        List of new completed game IDs
    """
    if verbose:
        print(f"\n=== Discovering Completed Games (last {days_lookback} days) ===\n")

    # 1. Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_lookback)

    if verbose:
        print(f"Date range: {start_date.date()} to {end_date.date()}")

    # 2. Generate months to check
    months_to_check = generate_month_list(start_date, end_date)
    if verbose:
        print(f"Months to check: {', '.join(months_to_check)}")

    # 3. Fetch all events for these months
    if verbose:
        print(f"\nFetching events from ESPN API...")

    all_event_ids = []
    for year_month in months_to_check:
        if verbose:
            print(f"  Fetching {year_month}...", end=' ')
        events = fetch_events_for_month(year_month)
        all_event_ids.extend(events)
        if verbose:
            print(f"({len(events)} events)")

    if verbose:
        print(f"\nTotal events discovered: {len(all_event_ids)}")

    # 4. Filter out games already in database
    existing_ids = get_existing_game_ids(start_date)
    if verbose:
        print(f"Games already in database: {len(existing_ids)}")

    # 5. Get potentially new games
    potentially_new = set(all_event_ids) - existing_ids
    if verbose:
        print(f"Potentially new events: {len(potentially_new)}")

    if len(potentially_new) == 0:
        if verbose:
            print("\n✓ No new games to check")
        return []

    # 6. Check which ones are actually completed
    if verbose:
        print(f"\nChecking completion status for {len(potentially_new)} events...")

    import concurrent.futures
    completed_game_ids = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(check_if_completed, list(potentially_new))

        for result in results:
            if result is not None:
                completed_game_ids.append(result)

    if verbose:
        print(f"\n✓ Found {len(completed_game_ids)} new completed games")

    return completed_game_ids

if __name__ == "__main__":
    # Test the discovery function
    new_games = discover_new_completed_games(days_lookback=7, verbose=True)

    if new_games:
        print(f"\nNew completed game IDs:")
        for game_id in new_games[:10]:  # Show first 10
            print(f"  - {game_id}")
        if len(new_games) > 10:
            print(f"  ... and {len(new_games) - 10} more")
