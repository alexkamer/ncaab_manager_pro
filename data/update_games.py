import httpx
import sqlite3
import json
import concurrent.futures
import threading
import time
import os
from discover_completed_games import discover_new_completed_games

# Thread-local storage for httpx clients
_thread_local = threading.local()

def get_db_path():
    """Get database path that works from project root or data/ directory"""
    return 'ncaab.db' if os.path.exists('ncaab.db') else 'data/ncaab.db'

def get_client():
    """Get or create a thread-local httpx client"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = httpx.Client(timeout=30.0)
    return _thread_local.client

def get_game_stats(event_id):
    """
    Fetch complete game data including boxscores from ESPN API.
    Returns (game_info_dict, team_boxscores_list, player_boxscores_list)
    """
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary"
    params = {
        'event': event_id,
        'limit': 250
    }

    try:
        response = get_client().get(url=url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        with open('data/event_errors.log', 'a') as f:
            f.write(f"Error fetching event {event_id}: {e}\n")
        return None, None, None

    game_header = data.get('header', {})
    base_comp_info = game_header.get('competitions', [{}])[0]

    # Double-check completion status
    if not base_comp_info.get('status', {}).get('type', {}).get('completed'):
        return None, None, None

    # Extract game info
    game_info_dict = {
        'id': game_header.get('id'),
        'uid': game_header.get('uid'),
        'season_year': game_header.get('season', {}).get('year'),
        'season_type': game_header.get('season', {}).get('type'),
        'week': game_header.get('week'),
        'game_note': game_header.get('gameNote'),
        'timeValid': game_header.get('timeValid'),
        'date': base_comp_info.get('date'),
        'is_neutral_site': base_comp_info.get('neutralSite'),
        'is_conference_competition': base_comp_info.get('conferenceCompetition'),
        'event_status_id': base_comp_info.get('status', {}).get('type', {}).get('id'),
        'event_status_name': base_comp_info.get('status', {}).get('type', {}).get('name'),
        'event_status_state': base_comp_info.get('status', {}).get('type', {}).get('state'),
        'event_status_completed': base_comp_info.get('status', {}).get('type', {}).get('completed'),
        'event_status_description': base_comp_info.get('status', {}).get('type', {}).get('description'),
        'event_status_detail': base_comp_info.get('status', {}).get('type', {}).get('detail'),
        'event_status_short_detail': base_comp_info.get('status', {}).get('type', {}).get('shortDetail'),
        'event_tournament_id': base_comp_info.get('tournamentId'),
        'venue_id': data.get('gameInfo', {}).get('venue', {}).get('id'),
        'attendance': data.get('gameInfo', {}).get('attendance'),
        'officials': data.get('gameInfo', {}).get('officials')
    }

    # Extract team info from competitors
    for competitor in base_comp_info.get('competitors', []):
        home_away = competitor.get('homeAway')
        game_info_dict.update({
            f'{home_away}_team_id': competitor.get('id'),
            f'{home_away}_team_winner': competitor.get('winner'),
            f'{home_away}_team_score': competitor.get('score'),
            f'{home_away}_linescores': competitor.get('linescores', []),
            f'{home_away}_team_records': competitor.get('record', []),
            f'{home_away}_team_guid': competitor.get('team', {}).get('guid'),
            f'{home_away}_team_uid': competitor.get('team', {}).get('uid'),
            f'{home_away}_team_location': competitor.get('team', {}).get('location'),
            f'{home_away}_team_name': competitor.get('team', {}).get('name'),
            f'{home_away}_team_abbreviation': competitor.get('team', {}).get('abbreviation'),
            f'{home_away}_team_nickname': competitor.get('team', {}).get('nickname'),
            f'{home_away}_team_displayName': competitor.get('team', {}).get('displayName'),
            f'{home_away}_team_color': competitor.get('team', {}).get('color'),
            f'{home_away}_team_alternate_color': competitor.get('team', {}).get('alternateColor'),
            f'{home_away}_team_logos': competitor.get('team', {}).get('logos', []),
            f'{home_away}_team_conference_id': competitor.get('team', {}).get('groups', {}).get('id'),
            f'{home_away}_team_conference_slug': competitor.get('team', {}).get('groups', {}).get('slug')
        })

    # Extract team boxscores
    team_boxscores = data.get('boxscore', {}).get('teams', [])
    team_boxscores_df = []

    for team in team_boxscores:
        team_dict = {
            'event_team_id': f"{event_id}_{team.get('team', {}).get('id')}",
            'event_id': event_id,
            'team_id': team.get('team', {}).get('id'),
            'home_away': team.get('homeAway')
        }

        for stat in team.get('statistics', []):
            stat_key = stat.get('name').replace("-", "_")
            team_dict.update({
                stat_key: stat.get('displayValue')
            })

        team_boxscores_df.append(team_dict)

    # Extract player boxscores
    player_boxscores = data.get('boxscore', {}).get('players', [])
    player_boxscores_df = []

    for team in player_boxscores:
        team_id = team.get('team', {}).get('id')
        stat_labels = team.get('statistics', [{}])[0].get('labels', [])

        for athlete in team.get('statistics', [{}])[0].get('athletes', []):
            athlete_id = athlete.get('athlete', {}).get('id')

            athlete_dict = {
                'event_athlete_id': f"{event_id}_{athlete_id}",
                'event_id': event_id,
                'athlete_id': athlete_id,
                'team_id': team_id,
                'athlete_name': athlete.get('athlete', {}).get('displayName'),
                'athlete_headshot': athlete.get('athlete', {}).get('headshot', {}).get('href'),
                'athlete_jersey': athlete.get('athlete', {}).get('jersey'),
                'athlete_position_name': athlete.get('athlete', {}).get('position', {}).get('name'),
                'athlete_position_abbreviation': athlete.get('athlete', {}).get('position', {}).get('abbreviation'),
                'athlete_position_display_name': athlete.get('athlete', {}).get('position', {}).get('displayName'),
                'athlete_starter': athlete.get('starter'),
                'athlete_did_not_play': athlete.get('didNotPlay'),
                'athlete_ejected': athlete.get('ejected')
            }

            for index, stat_value in enumerate(athlete.get('stats', [])):
                athlete_dict.update({
                    stat_labels[index]: stat_value
                })

            player_boxscores_df.append(athlete_dict)

    return game_info_dict, team_boxscores_df, player_boxscores_df

def insert_game_data(games_data, team_boxscores_data, player_boxscores_data):
    """Insert game data into database"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Insert games
    games_tuples = [
        (g['id'], g['uid'], g['season_year'], g['season_type'], g['week'], g.get('game_note'),
         g.get('timeValid'), g.get('date'), g.get('is_neutral_site'), g.get('is_conference_competition'),
         g.get('event_status_id'), g.get('event_status_name'), g.get('event_status_state'),
         g.get('event_status_completed'), g.get('event_status_description'), g.get('event_status_detail'),
         g.get('event_status_short_detail'), g.get('event_tournament_id'), g.get('venue_id'),
         g.get('attendance'), json.dumps(g.get('officials')),
         g.get('home_team_id'), g.get('home_team_winner'), g.get('home_team_score'),
         json.dumps(g.get('home_linescores')), json.dumps(g.get('home_team_records')),
         g.get('home_team_guid'), g.get('home_team_uid'), g.get('home_team_location'),
         g.get('home_team_name'), g.get('home_team_abbreviation'), g.get('home_team_nickname'),
         g.get('home_team_displayName'), g.get('home_team_color'), g.get('home_team_alternate_color'),
         json.dumps(g.get('home_team_logos')), g.get('home_team_conference_id'), g.get('home_team_conference_slug'),
         g.get('away_team_id'), g.get('away_team_winner'), g.get('away_team_score'),
         json.dumps(g.get('away_linescores')), json.dumps(g.get('away_team_records')),
         g.get('away_team_guid'), g.get('away_team_uid'), g.get('away_team_location'),
         g.get('away_team_name'), g.get('away_team_abbreviation'), g.get('away_team_nickname'),
         g.get('away_team_displayName'), g.get('away_team_color'), g.get('away_team_alternate_color'),
         json.dumps(g.get('away_team_logos')), g.get('away_team_conference_id'), g.get('away_team_conference_slug'))
        for g in games_data
    ]

    cursor.executemany('''
        INSERT OR REPLACE INTO games (id, uid, season_year, season_type, week, game_note, timeValid, date,
        is_neutral_site, is_conference_competition, event_status_id, event_status_name, event_status_state,
        event_status_completed, event_status_description, event_status_detail, event_status_short_detail,
        event_tournament_id, venue_id, attendance, officials, home_team_id, home_team_winner, home_team_score,
        home_linescores, home_team_records, home_team_guid, home_team_uid, home_team_location, home_team_name,
        home_team_abbreviation, home_team_nickname, home_team_displayName, home_team_color, home_team_alternate_color,
        home_team_logos, home_team_conference_id, home_team_conference_slug, away_team_id, away_team_winner,
        away_team_score, away_linescores, away_team_records, away_team_guid, away_team_uid, away_team_location,
        away_team_name, away_team_abbreviation, away_team_nickname, away_team_displayName, away_team_color,
        away_team_alternate_color, away_team_logos, away_team_conference_id, away_team_conference_slug)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', games_tuples)

    # Insert team boxscores
    team_boxscores_tuples = [
        (tb['event_team_id'], tb['event_id'], tb['team_id'], tb.get('home_away'),
         tb.get('fieldGoalsMade'), tb.get('fieldGoalsAttempted'), tb.get('fieldGoalPct'),
         tb.get('threePointFieldGoalsMade'), tb.get('threePointFieldGoalsAttempted'), tb.get('threePointFieldGoalPct'),
         tb.get('freeThrowsMade'), tb.get('freeThrowsAttempted'), tb.get('freeThrowPct'),
         tb.get('totalRebounds'), tb.get('offensiveRebounds'), tb.get('defensiveRebounds'),
         tb.get('assists'), tb.get('steals'), tb.get('blocks'), tb.get('turnovers'),
         tb.get('teamTurnovers'), tb.get('totalTurnovers'), tb.get('technicalFouls'),
         tb.get('flagrantFouls'), tb.get('fouls'), tb.get('largestLead'))
        for tb in team_boxscores_data
    ]

    cursor.executemany('''
        INSERT OR REPLACE INTO team_boxscores (event_team_id, event_id, team_id, home_away,
        fieldGoalsMade, fieldGoalsAttempted, fieldGoalPct, threePointFieldGoalsMade,
        threePointFieldGoalsAttempted, threePointFieldGoalPct, freeThrowsMade, freeThrowsAttempted,
        freeThrowPct, totalRebounds, offensiveRebounds, defensiveRebounds, assists, steals, blocks,
        turnovers, teamTurnovers, totalTurnovers, technicalFouls, flagrantFouls, fouls, largestLead)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', team_boxscores_tuples)

    # Insert player boxscores
    player_boxscores_tuples = [
        (pb['event_athlete_id'], pb['event_id'], pb['athlete_id'], pb['team_id'],
         pb.get('athlete_name'), pb.get('athlete_headshot'), pb.get('athlete_jersey'),
         pb.get('athlete_position_name'), pb.get('athlete_position_abbreviation'),
         pb.get('athlete_position_display_name'), pb.get('athlete_starter'),
         pb.get('athlete_did_not_play'), pb.get('athlete_ejected'),
         pb.get('MIN'), pb.get('FG'), pb.get('3PT'), pb.get('FT'),
         pb.get('OREB'), pb.get('DREB'), pb.get('REB'), pb.get('AST'),
         pb.get('STL'), pb.get('BLK'), pb.get('TO'), pb.get('PF'), pb.get('PTS'))
        for pb in player_boxscores_data
    ]

    cursor.executemany('''
        INSERT OR REPLACE INTO player_boxscores (event_athlete_id, event_id, athlete_id, team_id,
        athlete_name, athlete_headshot, athlete_jersey, athlete_position_name, athlete_position_abbreviation,
        athlete_position_display_name, athlete_starter, athlete_did_not_play, athlete_ejected, MIN, FG, "3PT",
        FT, OREB, DREB, REB, AST, STL, BLK, "TO", PF, PTS)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', player_boxscores_tuples)

    conn.commit()
    conn.close()

def update_games(event_ids, verbose=True):
    """
    Fetch and insert games for a specific list of event IDs.

    Args:
        event_ids: List of ESPN event IDs to fetch
        verbose: Print progress messages

    Returns:
        Dictionary with update statistics
    """
    start_time = time.time()

    if not event_ids:
        if verbose:
            print("\n✓ No games to fetch")
        return {
            'games_added': 0,
            'api_calls': 0,
            'duration_seconds': 0,
            'errors': 0
        }

    if verbose:
        print(f"\nFetching game data for {len(event_ids)} games...")

    all_games = []
    all_team_boxscores = []
    all_player_boxscores = []
    error_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(get_game_stats, event_ids)

        for game_info, team_stats, player_stats in results:
            if game_info is None:
                error_count += 1
            elif len(team_stats) == 0:
                # Skip incomplete games
                pass
            else:
                all_games.append(game_info)
                all_team_boxscores.extend(team_stats)
                all_player_boxscores.extend(player_stats)

    if verbose:
        print(f"\n✓ Fetched {len(all_games)} complete games")
        if error_count > 0:
            print(f"  ⚠ {error_count} errors (see data/event_errors.log)")

    # Insert into database
    if all_games:
        if verbose:
            print(f"\nInserting into database...")
        insert_game_data(all_games, all_team_boxscores, all_player_boxscores)
        if verbose:
            print(f"  ✓ {len(all_games)} games")
            print(f"  ✓ {len(all_team_boxscores)} team boxscores")
            print(f"  ✓ {len(all_player_boxscores)} player boxscores")

    duration = time.time() - start_time

    # Log the update
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO update_log (table_name, operation, records_added, records_updated,
                                api_calls, duration_seconds, error_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('games', 'backfill', len(all_games), 0, len(event_ids), duration, error_count))
    conn.commit()
    conn.close()

    if verbose:
        print(f"\n✓ Games update complete in {duration:.1f} seconds")

    return {
        'games_added': len(all_games),
        'api_calls': len(event_ids),
        'duration_seconds': duration,
        'errors': error_count
    }

def update_games_daily(days_lookback=7, verbose=True):
    """
    Main function to update games table with new completed games.

    Args:
        days_lookback: Number of days to look back for new games
        verbose: Print progress messages

    Returns:
        Dictionary with update statistics
    """
    start_time = time.time()

    if verbose:
        print("\n=== Updating Games & Boxscores ===\n")

    # 1. Discover new completed games
    new_game_ids = discover_new_completed_games(days_lookback=days_lookback, verbose=verbose)

    if not new_game_ids:
        if verbose:
            print("\n✓ No new games to fetch")
        return {
            'games_added': 0,
            'api_calls': 0,
            'duration_seconds': time.time() - start_time,
            'errors': 0
        }

    # 2. Fetch game data in parallel
    if verbose:
        print(f"\nFetching game data for {len(new_game_ids)} games...")

    all_games = []
    all_team_boxscores = []
    all_player_boxscores = []
    error_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(get_game_stats, new_game_ids)

        for game_info, team_stats, player_stats in results:
            if game_info is None:
                error_count += 1
            elif len(team_stats) == 0:
                # Skip incomplete games
                pass
            else:
                all_games.append(game_info)
                all_team_boxscores.extend(team_stats)
                all_player_boxscores.extend(player_stats)

    if verbose:
        print(f"\n✓ Fetched {len(all_games)} complete games")
        if error_count > 0:
            print(f"  ⚠ {error_count} errors (see data/event_errors.log)")

    # 3. Insert into database
    if all_games:
        if verbose:
            print(f"\nInserting into database...")
        insert_game_data(all_games, all_team_boxscores, all_player_boxscores)
        if verbose:
            print(f"  ✓ {len(all_games)} games")
            print(f"  ✓ {len(all_team_boxscores)} team boxscores")
            print(f"  ✓ {len(all_player_boxscores)} player boxscores")

    duration = time.time() - start_time

    # Log the update
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO update_log (table_name, operation, records_added, records_updated,
                                api_calls, duration_seconds, error_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('games', 'daily_update', len(all_games), 0, len(new_game_ids), duration, error_count))
    conn.commit()
    conn.close()

    if verbose:
        print(f"\n✓ Games update complete in {duration:.1f} seconds")

    return {
        'games_added': len(all_games),
        'api_calls': len(new_game_ids),
        'duration_seconds': duration,
        'errors': error_count
    }

if __name__ == "__main__":
    # Test the update function
    stats = update_games_daily(days_lookback=7, verbose=True)
    print(f"\nUpdate Statistics:")
    print(f"  Games added: {stats['games_added']}")
    print(f"  API calls: {stats['api_calls']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")
    print(f"  Errors: {stats['errors']}")
