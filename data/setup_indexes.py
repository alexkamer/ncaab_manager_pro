import sqlite3

def setup_indexes_and_logging():
    """Add database indexes for performance and create update_log table"""
    conn = sqlite3.connect('data/ncaab.db')
    cursor = conn.cursor()

    print("Creating indexes...")

    # Create indexes for common queries
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_games_date ON games(date)",
        "CREATE INDEX IF NOT EXISTS idx_games_season ON games(season_year)",
        "CREATE INDEX IF NOT EXISTS idx_team_seasons_season ON team_seasons(season)",
        "CREATE INDEX IF NOT EXISTS idx_conferences_season ON conferences(season)",
        "CREATE INDEX IF NOT EXISTS idx_predictions_event ON predictions(event_id)",
        "CREATE INDEX IF NOT EXISTS idx_odds_event ON odds(event_id)",
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)
        print(f"  ✓ {index_sql.split('idx_')[1].split(' ON')[0]}")

    print("\nCreating update_log table...")

    # Create update_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS update_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            table_name TEXT,
            operation TEXT,
            records_added INTEGER,
            records_updated INTEGER,
            api_calls INTEGER,
            duration_seconds REAL,
            error_count INTEGER
        )
    ''')

    conn.commit()
    conn.close()

    print("✓ update_log table created")
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    setup_indexes_and_logging()
