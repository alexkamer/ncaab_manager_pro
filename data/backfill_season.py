#!/usr/bin/env python3
"""
Backfill all games for a specific season.
This script discovers and fetches all completed games for the current or specified season.
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
from discover_completed_games import discover_new_completed_games
from update_games import update_games

def backfill_season(season_year=None, season_start_month=None):
    """
    Backfill all games for a season.

    Args:
        season_year: Season year (e.g., 2026 for 2025-26 season). Defaults to current season.
        season_start_month: Optional start date override (YYYY-MM format).
                          If not provided, looks up actual dates from seasons table.
    """

    if season_year is None:
        season_year = datetime.now().year
        if datetime.now().month < 7:  # Before July, we're in the previous season
            season_year += 1

    print(f"\n{'='*60}")
    print(f"BACKFILLING SEASON {season_year-1}-{str(season_year)[-2:]}")
    print(f"{'='*60}\n")

    # Try to get actual season dates from database if no override provided
    if season_start_month is None:
        db_path = 'ncaab.db' if os.path.exists('ncaab.db') else 'data/ncaab.db'
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT startDate, endDate FROM seasons WHERE year = ?", (season_year,))
            result = cursor.fetchone()
            conn.close()

            if result:
                # Parse ISO dates from database
                season_start_date = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                season_end_date = datetime.fromisoformat(result[1].replace('Z', '+00:00'))
                print(f"Using dates from seasons table:")
                print(f"  Start: {season_start_date.date()}")
                print(f"  End: {season_end_date.date()}")
            else:
                # Fallback to default if season not in database
                print(f"⚠ Season {season_year} not found in database, using defaults")
                season_start_date = datetime.strptime(f"{season_year-1}-11-01", "%Y-%m-%d")
                season_end_date = datetime.strptime(f"{season_year}-04-30", "%Y-%m-%d")
        except Exception as e:
            print(f"⚠ Could not read seasons table: {e}")
            print(f"  Using default dates")
            season_start_date = datetime.strptime(f"{season_year-1}-11-01", "%Y-%m-%d")
            season_end_date = datetime.strptime(f"{season_year}-04-30", "%Y-%m-%d")
    else:
        # Use provided start month override
        season_start_date = datetime.strptime(f"{season_start_month}-01", "%Y-%m-%d")
        season_end_date = datetime.strptime(f"{season_year}-04-30", "%Y-%m-%d")
        print(f"Using provided start date: {season_start_date.date()}")

    # Add buffer days for inclusive boundaries
    season_start = season_start_date - timedelta(days=1)

    # Determine if this is the current season
    current_year = datetime.now().year
    if datetime.now().month < 7:
        current_year += 1

    if season_year == current_year:
        # Current season - go until today (plus buffer day)
        season_end = datetime.now() + timedelta(days=1)
        print(f"Backfilling through: {datetime.now().date()} (today)")
    else:
        # Historical season - use end date from database (plus buffer day)
        season_end = season_end_date + timedelta(days=1)

    print(f"Search range: {season_start.date()} to {season_end.date()}\n")

    # Step 1: Discover all completed games for the season
    new_game_ids = discover_new_completed_games(
        start_date=season_start,
        end_date=season_end,
        verbose=True
    )

    if not new_game_ids:
        print("\n✓ No new games found. Database is up to date!")
        return

    print(f"\n{'='*60}")
    print(f"FETCHING GAME DATA")
    print(f"{'='*60}\n")

    # Step 2: Fetch full game data for discovered games
    print(f"Fetching detailed data for {len(new_game_ids)} games...")
    print("This includes game stats, team boxscores, and player boxscores.\n")

    update_games(event_ids=new_game_ids, verbose=True)

    # Recalculate current year for final message
    current_year_check = datetime.now().year
    if datetime.now().month < 7:
        current_year_check += 1

    print(f"\n{'='*60}")
    print(f"✓ BACKFILL COMPLETE")
    print(f"{'='*60}\n")
    print(f"Added {len(new_game_ids)} games to the database.")
    print(f"Database should now have all completed games for season {season_year-1}-{str(season_year)[-2:]}.")

    if season_year != current_year_check:
        season_end_display = datetime.strptime(f"{season_year}-04-30", "%Y-%m-%d")
        print(f"\nNote: Historical season backfill limited to {season_end_display.date()}")
    print()

if __name__ == "__main__":
    # Allow command line arguments
    season_year = None
    season_start = None  # Will auto-lookup from seasons table if not provided

    if len(sys.argv) > 1:
        season_year = int(sys.argv[1])

    if len(sys.argv) > 2:
        season_start = sys.argv[2]

    backfill_season(season_year=season_year, season_start_month=season_start)
