import httpx
import sqlite3
import pandas as pd
import concurrent.futures
import threading
import json

# Thread-local storage for httpx clients
_thread_local = threading.local()

def get_client():
    """Get or create a thread-local httpx client"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = httpx.Client(timeout=30.0)
    return _thread_local.client


## UNCOMMENT FOR FIRST RUN, COMMENT OUT FOR SUBSEQUENT RUNS

# def get_event_ids_for_month(year, month):
#     base_url = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events"
#     params = {
#         'dates' : f"{year}{month}",
#         'groups' : '50',
#         'limit' : 1000
#     }
#     base_response = httpx.get(url=base_url, params=params)
#     base_response.raise_for_status()
#     base_data = base_response.json()
    
#     page_count = base_data.get('pageCount',1)

#     basic_event_urls = []

#     if page_count > 1:
#         for page in range(1,page_count+1):
#             url = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events"

#             params = {
#                 'dates' : f"{year}{month}",
#                 'groups' : '50',
#                 'limit' : 1000
#             }
#             page_response = httpx.get(url=url, params=params)
#             page_response.raise_for_status()
#             page_data = page_response.json()

#             basic_event_urls.extend([url['$ref'] for url in page_data.get('items',[])])
#     else:
#         basic_event_urls.extend([url['$ref'] for url in base_data.get('items',[])])
#     basic_event_ids = [x.split('/events/')[-1].split('?')[0] for x in basic_event_urls]
#     return basic_event_ids


# conn = sqlite3.connect('data/ncaab.db')
# conn = sqlite3.connect('ncaab.db')

# cursor = conn.cursor()

# # Fetch pairs of season and team_id
# cursor.execute("SELECT year FROM seasons")
# seasons_list = cursor.fetchall()
# seasons_list = sorted([int(x[0]) for x in seasons_list])
# conn.close()

# seasons_list = seasons_list[-26:] # Last 25 years, due to ESPN only including that need year prior, to get the months from first half of first season
# months = ['10', '11','12', '01', '02', '03', '04', '05', '06', '07', '08', '09']


# # Combine year and month into a list of tasks
# task_args = [(year, month) for year in seasons_list for month in months]

# def fetch_events(args):
#     year, month = args
#     return get_event_ids_for_month(year, month)

# basic_events_ids = []

# # Use ThreadPoolExecutor to run these in parallel
# with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
#     results = executor.map(fetch_events, task_args)
    
#     for result in results:
#         basic_events_ids.extend(result)

# with open("data/event_ids.txt", "w") as f:
# with open("event_ids.txt", "w") as f:
#     for s in basic_events_ids:
#         f.write(f"{s}\n")

########### UNCOMMENT OUT FOR FIRST RUN, COMMENT OUT FOR SUBSEQUENT RUNS ###########




# with open("data/event_ids.txt", "w") as f:
with open("data/event_ids.txt", "r") as f:
    event_ids = f.read().splitlines()

def get_game_stats(event_id):
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary"
    params = {
        'event': event_id,
        'limit' : 250
    }

    try:
        response = get_client().get(url=url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        # Log error to file
        with open('data/event_errors.log', 'a') as f:
            f.write(f"Error fetching event {event_id}: {e}\n")
        return None, None, None

    game_header = data.get('header',{})
    base_comp_info = game_header.get('competitions',[{}])[0]
    if not base_comp_info.get('status',{}).get('type',{}).get('completed'):
        return None, None, None
    game_info_dict = {
        'id' : game_header.get('id'),
        'uid' : game_header.get('uid'),
        'season_year' : game_header.get('season',{}).get('year'),
        'season_type' : game_header.get('season',{}).get('type'),
        'week' : game_header.get('week'),
        'game_note' : game_header.get('gameNote'),
        'timeValid' : game_header.get('timeValid'),
        'date' : base_comp_info.get('date'),
        'is_neutral_site' : base_comp_info.get('neutralSite'),
        'is_conference_competition' : base_comp_info.get('conferenceCompetition'),
        'event_status_id' : base_comp_info.get('status',{}).get('type',{}).get('id'),
        'event_status_name' : base_comp_info.get('status',{}).get('type',{}).get('name'),
        'event_status_state' : base_comp_info.get('status',{}).get('type',{}).get('state'),
        'event_status_completed' : base_comp_info.get('status',{}).get('type',{}).get('completed'),
        'event_status_description' : base_comp_info.get('status',{}).get('type',{}).get('description'),
        'event_status_detail' : base_comp_info.get('status',{}).get('type',{}).get('detail'),
        'event_status_short_detail' : base_comp_info.get('status',{}).get('type',{}).get('shortDetail'),
        'event_tournament_id' : base_comp_info.get('tournamentId'),
        'venue_id' : data.get('gameInfo',{}).get('venue',{}).get('id'),
        'attendance' : data.get('gameInfo',{}).get('attendance'),
        'officials' : data.get('gameInfo',{}).get('officials')

    }

    for competitor in base_comp_info.get('competitors',[]):
        home_away = competitor.get('homeAway')
        game_info_dict.update({
            f'{home_away}_team_id' : competitor.get('id'),
            f'{home_away}_team_winner' : competitor.get('winner'),
            f'{home_away}_team_score' : competitor.get('score'),
            f'{home_away}_linescores' : competitor.get('linescores',[]),
            f'{home_away}_team_records' : competitor.get('record',[]),
            f'{home_away}_team_guid' : competitor.get('team',{}).get('guid'),
            f'{home_away}_team_uid' : competitor.get('team',{}).get('uid'),
            f'{home_away}_team_location' : competitor.get('team',{}).get('location'),
            f'{home_away}_team_name' : competitor.get('team',{}).get('name'),
            f'{home_away}_team_abbreviation' : competitor.get('team',{}).get('abbreviation'),
            f'{home_away}_team_nickname' : competitor.get('team',{}).get('nickname'),
            f'{home_away}_team_displayName' : competitor.get('team',{}).get('displayName'),
            f'{home_away}_team_color    ' : competitor.get('team',{}).get('color'),
            f'{home_away}_team_alternate_color' : competitor.get('team',{}).get('alternateColor'),
            f'{home_away}_team_logos' : competitor.get('team',{}).get('logos',[]),
            f'{home_away}_team_conference_id' : competitor.get('team',{}).get('groups',{}).get('id'),
            f'{home_away}_team_conference_slug' : competitor.get('team',{}).get('groups',{}).get('slug')
            
        })


    team_boxscores = data.get('boxscore',{}).get('teams',[])
    team_boxscores_df = []
    for team in team_boxscores:
        team_dict = {
            'event_team_id' : f"{event_id}_{team.get('team',{}).get('id')}",
            'event_id' : event_id,
            'team_id' : team.get('team',{}).get('id'),
            'home_away' : team.get('homeAway')    
        }

        for stat in team.get('statistics', []):
            stat_key = stat.get('name').replace("-", "_")
            team_dict.update({
                stat_key : stat.get('displayValue')
            })

        team_boxscores_df.append(team_dict)

    
    player_boxscores = data.get('boxscore',{}).get('players',[])
    player_boxscores_df = []
    
    for team in player_boxscores:
        team_id = team.get('team',{}).get('id')
        stat_labels = team.get('statistics', [{}])[0].get('labels', [])
        for athlete in team.get('statistics', [{}])[0].get('athletes', []):
            athlete_id = athlete.get('athlete',{}).get('id')
            
            athlete_dict = {
                'event_athlete_id' : f"{event_id}_{athlete_id}",
                'event_id' : event_id,
                'athlete_id' : athlete_id,
                'team_id' : team_id,
                'athlete_name' : athlete.get('athlete',{}).get('displayName'),
                'athlete_headshot' : athlete.get('athlete',{}).get('headshot',{}).get('href'),
                'athlete_jersey' : athlete.get('athlete',{}).get('jersey'),
                'athlete_position_name' : athlete.get('athlete',{}).get('position', {}).get('name'),
                'athlete_position_abbreviation' : athlete.get('athlete',{}).get('position', {}).get('abbreviation'),
                'athlete_position_display_name' : athlete.get('athlete',{}).get('position', {}).get('displayName'),
                'athlete_starter' : athlete.get('starter'),
                'athlete_did_not_play' : athlete.get('didNotPlay'),
                'athlete_ejected' : athlete.get('ejected') 
            }
            
            for index, stat_value in enumerate(athlete.get('stats',[])):
                athlete_dict.update({
                    stat_labels[index] : stat_value
                })

            player_boxscores_df.append(athlete_dict)


    









    return game_info_dict, team_boxscores_df, player_boxscores_df



all_game_info_df = []
all_team_boxscores_df = []
all_player_boxscores_df = []

# Using ThreadPoolExecutor to fetch game stats in parallel
event_ids = list(set(event_ids))

events_to_process = event_ids[85000:]
total_events = len(events_to_process)
processed_count = 0
error_count = 0
skipped_count = 0

import sys

def print_progress_bar(current, total, errors, skipped, bar_length=50):
    """Print a progress bar to the console"""
    percent = current / total
    filled = int(bar_length * percent)
    bar = '█' * filled + '-' * (bar_length - filled)
    sys.stdout.write(f'\r[{bar}] {current}/{total} ({percent*100:.1f}%) | Errors: {errors} | Skipped: {skipped}')
    sys.stdout.flush()

print(f"Processing {total_events} events...")

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    # Map the get_game_stats function over your list of event_ids
    results = executor.map(get_game_stats, events_to_process)

    for game_info_dict, team_boxscores, player_boxscores in results:
        processed_count += 1

        if game_info_dict is None:
            error_count += 1
        elif len(team_boxscores) == 0:
            skipped_count += 1
        else:
            all_game_info_df.append(game_info_dict)
            all_team_boxscores_df.extend(team_boxscores)
            all_player_boxscores_df.extend(player_boxscores)

        # Only update progress bar every 10 events to reduce flicker
        if processed_count % 10 == 0 or processed_count == total_events:
            print_progress_bar(processed_count, total_events, error_count, skipped_count)

print(f"\n\nCompleted processing {processed_count} events.")
print(f"Found {len(all_game_info_df)} completed games.")
print(f"Errors: {error_count} | Skipped (incomplete): {skipped_count}")


# Connect to database and insert/update data
conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Batch insert/update games
games_data = [
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
    for g in all_game_info_df
]
cursor.executemany('''
    INSERT OR REPLACE INTO games (id, uid, season_year, season_type, week, game_note, timeValid, date, is_neutral_site, is_conference_competition, event_status_id, event_status_name, event_status_state, event_status_completed, event_status_description, event_status_detail, event_status_short_detail, event_tournament_id, venue_id, attendance, officials, home_team_id, home_team_winner, home_team_score, home_linescores, home_team_records, home_team_guid, home_team_uid, home_team_location, home_team_name, home_team_abbreviation, home_team_nickname, home_team_displayName, home_team_color, home_team_alternate_color, home_team_logos, home_team_conference_id, home_team_conference_slug, away_team_id, away_team_winner, away_team_score, away_linescores, away_team_records, away_team_guid, away_team_uid, away_team_location, away_team_name, away_team_abbreviation, away_team_nickname, away_team_displayName, away_team_color, away_team_alternate_color, away_team_logos, away_team_conference_id, away_team_conference_slug)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', games_data)

# Batch insert/update team boxscores
team_boxscores_data = [
    (tb['event_team_id'], tb['event_id'], tb['team_id'], tb.get('home_away'),
     tb.get('fieldGoalsMade'), tb.get('fieldGoalsAttempted'), tb.get('fieldGoalPct'),
     tb.get('threePointFieldGoalsMade'), tb.get('threePointFieldGoalsAttempted'), tb.get('threePointFieldGoalPct'),
     tb.get('freeThrowsMade'), tb.get('freeThrowsAttempted'), tb.get('freeThrowPct'),
     tb.get('totalRebounds'), tb.get('offensiveRebounds'), tb.get('defensiveRebounds'),
     tb.get('assists'), tb.get('steals'), tb.get('blocks'), tb.get('turnovers'),
     tb.get('teamTurnovers'), tb.get('totalTurnovers'), tb.get('technicalFouls'),
     tb.get('flagrantFouls'), tb.get('fouls'), tb.get('largestLead'))
    for tb in all_team_boxscores_df
]
cursor.executemany('''
    INSERT OR REPLACE INTO team_boxscores (event_team_id, event_id, team_id, home_away, fieldGoalsMade, fieldGoalsAttempted, fieldGoalPct, threePointFieldGoalsMade, threePointFieldGoalsAttempted, threePointFieldGoalPct, freeThrowsMade, freeThrowsAttempted, freeThrowPct, totalRebounds, offensiveRebounds, defensiveRebounds, assists, steals, blocks, turnovers, teamTurnovers, totalTurnovers, technicalFouls, flagrantFouls, fouls, largestLead)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', team_boxscores_data)

# Batch insert/update player boxscores
player_boxscores_data = [
    (pb['event_athlete_id'], pb['event_id'], pb['athlete_id'], pb['team_id'],
     pb.get('athlete_name'), pb.get('athlete_headshot'), pb.get('athlete_jersey'),
     pb.get('athlete_position_name'), pb.get('athlete_position_abbreviation'),
     pb.get('athlete_position_display_name'), pb.get('athlete_starter'),
     pb.get('athlete_did_not_play'), pb.get('athlete_ejected'),
     pb.get('MIN'), pb.get('FG'), pb.get('3PT'), pb.get('FT'),
     pb.get('OREB'), pb.get('DREB'), pb.get('REB'), pb.get('AST'),
     pb.get('STL'), pb.get('BLK'), pb.get('TO'), pb.get('PF'), pb.get('PTS'))
    for pb in all_player_boxscores_df
]
cursor.executemany('''
    INSERT OR REPLACE INTO player_boxscores (event_athlete_id, event_id, athlete_id, team_id, athlete_name, athlete_headshot, athlete_jersey, athlete_position_name, athlete_position_abbreviation, athlete_position_display_name, athlete_starter, athlete_did_not_play, athlete_ejected, MIN, FG, "3PT", FT, OREB, DREB, REB, AST, STL, BLK, "TO", PF, PTS)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', player_boxscores_data)

conn.commit()
conn.close()

print(f"Successfully inserted {len(games_data)} games, {len(team_boxscores_data)} team boxscores, and {len(player_boxscores_data)} player boxscores into the database.")