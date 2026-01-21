#!/usr/bin/env python3
"""
Backfill all games for a specific season.
This script discovers and fetches all completed games for the current or specified season.
"""

import sys
from datetime import datetime
from discover_completed_games import discover_new_completed_games
from update_games import update_games

def backfill_season(season_year=None, season_start_month="2025-11"):
    """
    Backfill all games for a season.

    Args:
        season_year: Season year (e.g., 2026 for 2025-26 season). Defaults to current season.
        season_start_month: Start date for the season (YYYY-MM format)
    """

    if season_year is None:
        season_year = datetime.now().year
        if datetime.now().month < 7:  # Before July, we're in the previous season
            season_year += 1

    print(f"\n{'='*60}")
    print(f"BACKFILLING SEASON {season_year-1}-{str(season_year)[-2:]}")
    print(f"{'='*60}\n")

    # Calculate days lookback from season start to now
    season_start = datetime.strptime(f"{season_start_month}-01", "%Y-%m-%d")
    days_since_season_start = (datetime.now() - season_start).days

    print(f"Season started: {season_start.date()}")
    print(f"Days since season start: {days_since_season_start}")
    print(f"Looking back {days_since_season_start} days to find all games...\n")

    # Step 1: Discover all completed games for the season
    new_game_ids = discover_new_completed_games(
        days_lookback=days_since_season_start,
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

    print(f"\n{'='*60}")
    print(f"✓ BACKFILL COMPLETE")
    print(f"{'='*60}\n")
    print(f"Added {len(new_game_ids)} games to the database.")
    print(f"Database should now have all completed games for season {season_year}.\n")

if __name__ == "__main__":
    # Allow command line arguments
    season_year = None
    season_start = "2025-11"  # Default: November 2025 for 2025-26 season

    if len(sys.argv) > 1:
        season_year = int(sys.argv[1])

    if len(sys.argv) > 2:
        season_start = sys.argv[2]

    backfill_season(season_year=season_year, season_start_month=season_start)
