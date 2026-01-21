import sqlite3

def create_database():
    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()

    # Create seasons table with year as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seasons (
            year INTEGER PRIMARY KEY,
            startDate TEXT,
            endDate TEXT,
            displayName TEXT
        )
    ''')

    # Create season_types table with season_id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS season_types (
            season_id TEXT PRIMARY KEY,
            year INTEGER,
            type_id INTEGER,
            name TEXT,
            startDate TEXT,
            endDate TEXT,
            FOREIGN KEY (year) REFERENCES seasons(year)
        )
    ''')

    # Create teams table with id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id TEXT PRIMARY KEY,
            uid TEXT,
            slug TEXT,
            abbreviation TEXT,
            displayName TEXT,
            name TEXT,
            nickname TEXT,
            location TEXT,
            color TEXT,
            alternateColor TEXT,
            logos TEXT
        )
    ''')

    # Create conferences table with season_id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conferences (
            season_id TEXT PRIMARY KEY,
            id TEXT,
            season TEXT,
            name TEXT,
            abbreviation TEXT,
            shortName TEXT,
            midsizeName TEXT,
            logos TEXT,
            slug TEXT,
            parent TEXT,
            has_children INTEGER,
            FOREIGN KEY (season) REFERENCES seasons(year)
        )
    ''')

    # Create team_seasons table with season_conf_team as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_seasons (
            season_conf_team TEXT PRIMARY KEY,
            season TEXT,
            conference_id TEXT,
            team_id TEXT,
            guid TEXT,
            uid TEXT,
            slug TEXT,
            location TEXT,
            name TEXT,
            abbreviation TEXT,
            displayName TEXT,
            shortDisplayName TEXT,
            color TEXT,
            alternateColor TEXT,
            logos TEXT,
            venue_id TEXT,
            FOREIGN KEY (season) REFERENCES seasons(year),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')

    # Create players table with id as primary key (current active players)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            uid TEXT,
            guid TEXT,
            firstName TEXT,
            lastName TEXT,
            displayName TEXT,
            shortName TEXT,
            weight REAL,
            displayWeight TEXT,
            height REAL,
            displayHeight TEXT,
            birthPlace_city TEXT,
            birthPlace_state TEXT,
            birthPlace_country TEXT,
            experience_years INTEGER,
            experience_displayValue TEXT,
            experience_abbreviation TEXT,
            jersey TEXT,
            hand_type TEXT,
            hand_abbreviation TEXT,
            hand_displayValue TEXT
        )
    ''')

    # Create player_seasons table with season_player_id as primary key (historical rosters)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_seasons (
            season_player_id TEXT PRIMARY KEY,
            season TEXT,
            player_id TEXT,
            uid TEXT,
            guid TEXT,
            firstName TEXT,
            lastName TEXT,
            fullName TEXT,
            displayName TEXT,
            shortName TEXT,
            weight REAL,
            displayWeight TEXT,
            height REAL,
            displayHeight TEXT,
            birthPlace_city TEXT,
            birthPlace_state TEXT,
            birthPlace_country TEXT,
            slug TEXT,
            headshot TEXT,
            jersey TEXT,
            hand_type TEXT,
            hand_abbreviation TEXT,
            hand_displayValue TEXT,
            flag_href TEXT,
            position_id TEXT,
            position_name TEXT,
            position_abbreviation TEXT,
            position_displayValue TEXT,
            team_id TEXT,
            experience_years INTEGER,
            experience_displayValue TEXT,
            experience_abbreviation TEXT,
            FOREIGN KEY (season) REFERENCES seasons(year),
            FOREIGN KEY (player_id) REFERENCES players(id),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')

    # Create coaches table with season_id as primary key (coaches per season)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coaches (
            season_id TEXT PRIMARY KEY,
            season TEXT,
            team_id TEXT,
            firstName TEXT,
            lastName TEXT,
            FOREIGN KEY (season) REFERENCES seasons(year),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')

    # Create rankings table with season_week_team as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rankings (
            season_week_team TEXT PRIMARY KEY,
            season TEXT,
            week INTEGER,
            team_id TEXT,
            week_displayValue TEXT,
            headline TEXT,
            short_headline TEXT,
            season_displayName TEXT,
            ranking_provider_id TEXT,
            ranking_provider_name TEXT,
            ranking_provider_type TEXT,
            current_rank INTEGER,
            previous_rank INTEGER,
            first_place_votes INTEGER,
            points REAL,
            trend TEXT,
            record_summary TEXT,
            record_wins INTEGER,
            record_losses INTEGER,
            record_ties INTEGER,
            ranked_type TEXT,
            FOREIGN KEY (season) REFERENCES seasons(year),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')

    # Create games table with id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            uid TEXT,
            season_year INTEGER,
            season_type INTEGER,
            week INTEGER,
            game_note TEXT,
            timeValid INTEGER,
            date TEXT,
            is_neutral_site INTEGER,
            is_conference_competition INTEGER,
            event_status_id TEXT,
            event_status_name TEXT,
            event_status_state TEXT,
            event_status_completed INTEGER,
            event_status_description TEXT,
            event_status_detail TEXT,
            event_status_short_detail TEXT,
            event_tournament_id TEXT,
            venue_id TEXT,
            attendance INTEGER,
            officials TEXT,
            home_team_id TEXT,
            home_team_winner INTEGER,
            home_team_score INTEGER,
            home_linescores TEXT,
            home_team_records TEXT,
            home_team_guid TEXT,
            home_team_uid TEXT,
            home_team_location TEXT,
            home_team_name TEXT,
            home_team_abbreviation TEXT,
            home_team_nickname TEXT,
            home_team_displayName TEXT,
            home_team_color TEXT,
            home_team_alternate_color TEXT,
            home_team_logos TEXT,
            home_team_conference_id TEXT,
            home_team_conference_slug TEXT,
            away_team_id TEXT,
            away_team_winner INTEGER,
            away_team_score INTEGER,
            away_linescores TEXT,
            away_team_records TEXT,
            away_team_guid TEXT,
            away_team_uid TEXT,
            away_team_location TEXT,
            away_team_name TEXT,
            away_team_abbreviation TEXT,
            away_team_nickname TEXT,
            away_team_displayName TEXT,
            away_team_color TEXT,
            away_team_alternate_color TEXT,
            away_team_logos TEXT,
            away_team_conference_id TEXT,
            away_team_conference_slug TEXT,
            FOREIGN KEY (season_year) REFERENCES seasons(year),
            FOREIGN KEY (home_team_id) REFERENCES teams(id),
            FOREIGN KEY (away_team_id) REFERENCES teams(id)
        )
    ''')

    # Create team_boxscores table with event_team_id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_boxscores (
            event_team_id TEXT PRIMARY KEY,
            event_id TEXT,
            team_id TEXT,
            home_away TEXT,
            fieldGoalsMade TEXT,
            fieldGoalsAttempted TEXT,
            fieldGoalPct TEXT,
            threePointFieldGoalsMade TEXT,
            threePointFieldGoalsAttempted TEXT,
            threePointFieldGoalPct TEXT,
            freeThrowsMade TEXT,
            freeThrowsAttempted TEXT,
            freeThrowPct TEXT,
            totalRebounds TEXT,
            offensiveRebounds TEXT,
            defensiveRebounds TEXT,
            assists TEXT,
            steals TEXT,
            blocks TEXT,
            turnovers TEXT,
            teamTurnovers TEXT,
            totalTurnovers TEXT,
            technicalFouls TEXT,
            flagrantFouls TEXT,
            fouls TEXT,
            largestLead TEXT,
            FOREIGN KEY (event_id) REFERENCES games(id),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')

    # Create player_boxscores table with event_athlete_id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_boxscores (
            event_athlete_id TEXT PRIMARY KEY,
            event_id TEXT,
            athlete_id TEXT,
            team_id TEXT,
            athlete_name TEXT,
            athlete_headshot TEXT,
            athlete_jersey TEXT,
            athlete_position_name TEXT,
            athlete_position_abbreviation TEXT,
            athlete_position_display_name TEXT,
            athlete_starter INTEGER,
            athlete_did_not_play INTEGER,
            athlete_ejected INTEGER,
            MIN TEXT,
            FG TEXT,
            "3PT" TEXT,
            FT TEXT,
            OREB TEXT,
            DREB TEXT,
            REB TEXT,
            AST TEXT,
            STL TEXT,
            BLK TEXT,
            "TO" TEXT,
            PF TEXT,
            PTS TEXT,
            FOREIGN KEY (event_id) REFERENCES games(id),
            FOREIGN KEY (athlete_id) REFERENCES players(id),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')

    # Create predictions table with event_id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            event_id TEXT PRIMARY KEY,
            name TEXT,
            short_name TEXT,
            homeTeam_team_id TEXT,
            homeTeam_gameProjection REAL,
            homeTeam_gameProjection_display TEXT,
            homeTeam_teamChanceLoss REAL,
            homeTeam_teamChanceLoss_display TEXT,
            awayTeam_team_id TEXT,
            awayTeam_gameProjection REAL,
            awayTeam_gameProjection_display TEXT,
            awayTeam_teamChanceLoss REAL,
            awayTeam_teamChanceLoss_display TEXT,
            FOREIGN KEY (event_id) REFERENCES games(id),
            FOREIGN KEY (homeTeam_team_id) REFERENCES teams(id),
            FOREIGN KEY (awayTeam_team_id) REFERENCES teams(id)
        )
    ''')

    # Create odds table with event_provider_id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS odds (
            event_provider_id TEXT PRIMARY KEY,
            event_id TEXT,
            provider_id TEXT,
            provider_name TEXT,
            details TEXT,
            over_under REAL,
            spread REAL,
            over_odds INTEGER,
            under_odds INTEGER,
            away_team_favorite INTEGER,
            away_team_underdog INTEGER,
            away_team_moneyline INTEGER,
            away_team_spread_odds INTEGER,
            away_team_spread TEXT,
            away_team_id TEXT,
            home_team_favorite INTEGER,
            home_team_underdog INTEGER,
            home_team_moneyline INTEGER,
            home_team_spread_odds INTEGER,
            home_team_spread TEXT,
            home_team_id TEXT,
            FOREIGN KEY (event_id) REFERENCES games(id),
            FOREIGN KEY (away_team_id) REFERENCES teams(id),
            FOREIGN KEY (home_team_id) REFERENCES teams(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database and tables created successfully.")

if __name__ == "__main__":
    create_database()
