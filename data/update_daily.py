#!/usr/bin/env python3
"""
Daily update script for NCAA Basketball database.
Runs games, predictions, and odds updates.

Usage:
    python3 data/update_daily.py [--days N] [--quiet]

Arguments:
    --days N    Number of days to look back for games (default: 7)
    --quiet     Suppress verbose output
"""

import sys
import time
from datetime import datetime
from update_games import update_games_daily
from update_predictions import update_predictions
from update_odds import update_odds

def print_header():
    """Print script header"""
    print("=" * 60)
    print("NCAA Basketball Database - Daily Update")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def print_summary(games_stats, predictions_stats, odds_stats, total_duration):
    """Print summary of all updates"""
    print("\n" + "=" * 60)
    print("UPDATE SUMMARY")
    print("=" * 60)

    print("\nGames & Boxscores:")
    print(f"  Games added: {games_stats['games_added']}")
    print(f"  API calls: {games_stats['api_calls']}")
    print(f"  Duration: {games_stats['duration_seconds']:.1f}s")
    if games_stats['errors'] > 0:
        print(f"  Errors: {games_stats['errors']}")

    print("\nPredictions:")
    print(f"  Predictions added: {predictions_stats['predictions_added']}")
    print(f"  API calls: {predictions_stats['api_calls']}")
    print(f"  Duration: {predictions_stats['duration_seconds']:.1f}s")

    print("\nOdds:")
    print(f"  Odds entries added: {odds_stats['odds_added']}")
    print(f"  API calls: {odds_stats['api_calls']}")
    print(f"  Duration: {odds_stats['duration_seconds']:.1f}s")

    total_calls = (games_stats['api_calls'] +
                   predictions_stats['api_calls'] +
                   odds_stats['api_calls'])

    print("\nTotals:")
    print(f"  Total API calls: {total_calls}")
    print(f"  Total duration: {total_duration:.1f}s")

    print("\n" + "=" * 60)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

def main():
    """Main update function"""
    # Parse command line arguments
    days_lookback = 7
    verbose = True

    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days_lookback = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Error: --days requires an integer argument")
            sys.exit(1)

    if '--quiet' in sys.argv:
        verbose = False

    start_time = time.time()

    if verbose:
        print_header()

    try:
        # 1. Update games and boxscores
        games_stats = update_games_daily(days_lookback=days_lookback, verbose=verbose)

        # 2. Update predictions
        predictions_stats = update_predictions(verbose=verbose)

        # 3. Update odds
        odds_stats = update_odds(verbose=verbose)

        # Calculate total duration
        total_duration = time.time() - start_time

        # Print summary
        if verbose:
            print_summary(games_stats, predictions_stats, odds_stats, total_duration)

        return 0

    except KeyboardInterrupt:
        print("\n\nUpdate interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nERROR: Update failed with exception:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
