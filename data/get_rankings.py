import httpx
import pandas as pd
import concurrent.futures
import sqlite3
import threading

# Thread-local storage for httpx clients
_thread_local = threading.local()

def get_client():
    """Get or create a thread-local httpx client"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = httpx.Client(timeout=30.0)
    return _thread_local.client

conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Fetch pairs of season and team_id
cursor.execute("SELECT year FROM seasons")
seasons_list = cursor.fetchall()
seasons_list = [season[0] for season in seasons_list]
conn.close()

def get_rankings_urls_for_season(season):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/{season}/rankings?lang=en&region=us"
    response = get_client().get(url)
    response.raise_for_status()
    data = response.json()

    return [ranking['$ref'] for ranking in data['items']]

season_ranking_urls = []

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(get_rankings_urls_for_season, seasons_list)

    for result in results:
        season_ranking_urls.extend(result)

def get_weekly_ranking_data(weekly_ranking_url):
    response = get_client().get(weekly_ranking_url)
    response.raise_for_status()
    week_data = response.json()

    ranking_provider_id = week_data.get('id')
    ranking_provider_name = week_data.get('name')
    ranking_provider_type = week_data.get('type')

    occurrence_number = week_data.get('occurrence',{}).get('number')
    occurrence_displayValue = week_data.get('occurrence',{}).get('displayValue')
    headline = week_data.get('headline')
    short_headline = week_data.get('shortHeadline')
    season = week_data.get('season',{}).get('year')
    season_displayName = week_data.get('season',{}).get('displayName')
    

    all_ranking_data = []
    for ranked_team in week_data.get('ranks',[]):
        try:
            team_id = ranked_team['team']['$ref'].split('/teams/')[-1].split('?')[0]
            team_dict = {
                'season_week_team': f"{season}_{occurrence_number}_{team_id}",
                'season' : season,
                'week' : occurrence_number,
                'team_id' : team_id,
                'week_displayValue' : occurrence_displayValue,
                'headline' : headline,
                'short_headline' : short_headline,
                'season_displayName' : season_displayName,
                'ranking_provider_id' : ranking_provider_id,
                'ranking_provider_name' : ranking_provider_name,
                'ranking_provider_type' : ranking_provider_type,
                'current_rank' : ranked_team.get('current'),
                'previous_rank' : ranked_team.get('previous'),
                'first_place_votes' : ranked_team.get('firstPlaceVotes'),
                'points' : ranked_team.get('points'),
                'trend' : ranked_team.get('trend'),
                'record_summary' : ranked_team.get('record',{}).get('summary'),
                'ranked_type' : 'Ranked',

            }

            for record in ranked_team.get('record',{}).get('stats',[]):
                if record.get('name') == 'wins':
                    team_dict['record_wins'] = record.get('value')
                elif record.get('name') == 'losses':
                    team_dict['record_losses'] = record.get('value')
                elif record.get('name') == 'ties':
                    team_dict['record_ties'] = record.get('value')
            all_ranking_data.append(team_dict)
        except:
            continue
    
    for others in week_data.get('others',[]):
        try:
            team_id = others['team']['$ref'].split('/teams/')[-1].split('?')[0]
            team_dict = {
                'season_week_team': f"{season}_{occurrence_number}_{team_id}",
                'season' : season,
                'week' : occurrence_number,
                'team_id' : team_id,
                'week_displayValue' : occurrence_displayValue,
                'headline' : headline,
                'short_headline' : short_headline,
                'season_displayName' : season_displayName,
                'ranking_provider_id' : ranking_provider_id,
                'ranking_provider_name' : ranking_provider_name,
                'ranking_provider_type' : ranking_provider_type,
                'current_rank' : others.get('current'),
                'previous_rank' : others.get('previous'),
                'first_place_votes' : others.get('firstPlaceVotes'),
                'points' : others.get('points'),
                'trend' : others.get('trend'),
                'record_summary' : others.get('record',{}).get('summary'),
                'ranked_type' : 'Others',

            }

            for record in others.get('record',{}).get('stats',[]):
                if record.get('name') == 'wins':
                    team_dict['record_wins'] = record.get('value')
                elif record.get('name') == 'losses':
                    team_dict['record_losses'] = record.get('value')
                elif record.get('name') == 'ties':
                    team_dict['record_ties'] = record.get('value')
            all_ranking_data.append(team_dict)
        except:
            continue
    
    for droppedOut in week_data.get('droppedOut',[]):
        try:
            team_id = droppedOut['team']['$ref'].split('/teams/')[-1].split('?')[0]
            team_dict = {
                'season_week_team': f"{season}_{occurrence_number}_{team_id}",
                'season' : season,
                'week' : occurrence_number,
                'team_id' : team_id,
                'week_displayValue' : occurrence_displayValue,
                'headline' : headline,
                'short_headline' : short_headline,
                'season_displayName' : season_displayName,
                'ranking_provider_id' : ranking_provider_id,
                'ranking_provider_name' : ranking_provider_name,
                'ranking_provider_type' : ranking_provider_type,
                'current_rank' : droppedOut.get('current'),
                'previous_rank' : droppedOut.get('previous'),
                'first_place_votes' : droppedOut.get('firstPlaceVotes'),
                'points' : droppedOut.get('points'),
                'trend' : droppedOut.get('trend'),
                'record_summary' : droppedOut.get('record',{}).get('summary'),
                'ranked_type' : 'Dropped Out',

            }

            for record in droppedOut.get('record',{}).get('stats',[]):
                if record.get('name') == 'wins':
                    team_dict['record_wins'] = record.get('value')
                elif record.get('name') == 'losses':
                    team_dict['record_losses'] = record.get('value')
                elif record.get('name') == 'ties':
                    team_dict['record_ties'] = record.get('value')
            all_ranking_data.append(team_dict)
        except:
            continue    
    
    return all_ranking_data 
        


def get_season_ranking_data(season_ranking_url):
    response = get_client().get(season_ranking_url)
    response.raise_for_status()
    data = response.json()

    ranking_provider_id = data.get('id')
    ranking_provider_name = data.get('name')
    ranking_provider_type = data.get('type')
    
    weekly_ranking_urls = data.get('rankings',[])
    weekly_ranking_urls = [weekly_ranking_url.get('$ref') for weekly_ranking_url in weekly_ranking_urls]




    ranking_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(get_weekly_ranking_data, weekly_ranking_urls)

        for result in results:
            ranking_data.extend(result)

    return ranking_data




all_ranking_data = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(get_season_ranking_data, season_ranking_urls)

    for result in results:
        all_ranking_data.extend(result)


# Connect to database and insert/update data
conn = sqlite3.connect('data/ncaab.db')
cursor = conn.cursor()

# Batch insert/update rankings
rankings_data = [
    (r['season_week_team'], r['season'], r['week'], r['team_id'], r.get('week_displayValue'),
     r.get('headline'), r.get('short_headline'), r.get('season_displayName'),
     r.get('ranking_provider_id'), r.get('ranking_provider_name'), r.get('ranking_provider_type'),
     r.get('current_rank'), r.get('previous_rank'), r.get('first_place_votes'), r.get('points'),
     r.get('trend'), r.get('record_summary'), r.get('record_wins'), r.get('record_losses'),
     r.get('record_ties'), r.get('ranked_type'))
    for r in all_ranking_data
]
cursor.executemany('''
    INSERT OR REPLACE INTO rankings (season_week_team, season, week, team_id, week_displayValue, headline, short_headline, season_displayName, ranking_provider_id, ranking_provider_name, ranking_provider_type, current_rank, previous_rank, first_place_votes, points, trend, record_summary, record_wins, record_losses, record_ties, ranked_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', rankings_data)

conn.commit()
conn.close()

print(f"Successfully inserted {len(rankings_data)} ranking records into the database.")


