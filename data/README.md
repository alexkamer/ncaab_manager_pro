# Data Scripts

This directory contains scripts for fetching and updating NCAA Basketball data from ESPN APIs.

## Main Scripts (Use These)

### Daily Updates
```bash
python3 update_daily.py [--days N] [--quiet]
```
**Purpose**: Run this daily to keep database up-to-date with recent games, predictions, and odds.
- Discovers completed games from last 7 days (or `--days N`)
- Fetches game stats, team boxscores, and player boxscores
- Updates predictions and odds
- Uses `groups=52` to capture all Division I games

**When to run**: Daily via cron job or manually

---

### Season Backfill
```bash
python3 backfill_season.py [YEAR] [YYYY-MM]
```
**Purpose**: Backfill all games for a complete season.
- Discovers all completed games for the specified season
- For current season: fetches through today
- For historical seasons: fetches through April 30th of that season
- Fetches complete game data including boxscores
- Uses `groups=52` to capture all Division I games

**Examples**:
```bash
# Current season (2025-26, default)
python3 backfill_season.py

# 2024-25 season (will stop at April 30, 2025)
python3 backfill_season.py 2025 2024-11

# 2023-24 season (will stop at April 30, 2024)
python3 backfill_season.py 2024 2023-11
```

**Important**: Historical season backfills automatically stop at April 30th to avoid pulling in games from the next season.

**When to run**:
- First time setup
- When missing historical data
- After discovering gaps in game data

---

## Helper Scripts (Don't Run Directly)

### `discover_completed_games.py`
Core discovery logic used by other scripts. Queries ESPN API with `groups=52` to find all completed Division I games.

### `update_games.py`
Game data fetching and database insertion logic. Contains:
- `update_games_daily()` - Used by update_daily.py
- `update_games(event_ids)` - Used by backfill_season.py

### `update_predictions.py`
Fetches game predictions from ESPN FPI.

### `update_odds.py`
Fetches betting odds from ESPN.

---

## Legacy/Deprecated

### `update_data.py`
**Status**: Legacy - needs refactoring
- Updates seasons table
- Uses old hardcoded paths
- Should be integrated into update_daily.py or removed

---

## Database Indexes

After setting up a new database, run:
```bash
sqlite3 ncaab.db < add_indexes.sql
```

This adds performance indexes for player statistics queries.

---

## Important Notes

1. **Groups Parameter**: All scripts now use `groups=52` instead of `groups=50`
   - Group 50 was missing early season games from November
   - Group 52 captures all Division I games including pre-season

2. **Database Path**: Scripts automatically detect whether running from project root or data/ directory

3. **Concurrency**: Scripts use ThreadPoolExecutor for parallel API calls (max 10 workers)

4. **Rate Limiting**: Be mindful of ESPN API rate limits when running large backfills
