"""
Application services for database initialization and population.
"""
import pandas as pd
from datetime import datetime

from app import db
from app.models import (
    DriverEloRanking, 
    DriverEloProgression, 
    DriverTeamHistory, 
    RaceResult, 
    AppStats
)
from utils.database import update_database_from_df


def init_db(app):
    """
    Initialize the database and create all tables.
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if initialization succeeded
    """
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Check if we need to populate the data
            if not DriverEloRanking.query.first():
                print("Database empty. Running initial data population...")
                populate_database()
            
            print("Database initialized successfully!")
            return True
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            return False


def populate_database():
    """Populate the database with computed ELO rankings and progressions."""
    from core import F1DataProcessor
    
    print("Loading and processing F1 data...")
    processor = F1DataProcessor()
    processor.load_data()
    processor.process_races()
    
    # Calculate and store rankings
    print("Calculating rankings...")
    rankings = processor.calculate_rankings()
    update_database_from_df(db, DriverEloRanking, rankings)
    
    # Store app statistics
    print("Storing app statistics...")
    stats_data = [
        ('drivers_count', len(rankings)),
        ('years_covered', int(rankings['Last Year'].max() - rankings['First Year'].min())),
        ('races_count', len(processor.races)),
        ('data_points', len(rankings) * len(rankings.columns))
    ]
    
    for key, value in stats_data:
        stat = AppStats.query.filter_by(stat_key=key).first()
        if stat:
            stat.stat_value = value
            stat.updated_at = datetime.utcnow()
        else:
            stat = AppStats(stat_key=key, stat_value=value)
            db.session.add(stat)
    
    # Store ELO progressions for each driver
    print("Storing ELO progressions...")
    all_progressions = processor.get_all_drivers_elo_progression()
    
    # Clear existing progressions
    DriverEloProgression.query.delete()
    
    for _, row in all_progressions.iterrows():
        progression = DriverEloProgression(
            f1_driver_id=int(row['driverId']),
            year=int(row['year']),
            elo_rating=float(row['elo_rating'])
        )
        db.session.add(progression)
    
    # Store race results for comparison feature
    print("Storing race results...")
    RaceResult.query.delete()
    DriverTeamHistory.query.delete()
    
    # Get race-by-race progression for each driver
    for driver_id in processor.drivers_dict.keys():
        driver = processor.drivers_dict[driver_id]
        if driver.race_count == 0:
            continue
        
        race_progression = processor.get_driver_race_progression(driver_id)
        if race_progression.empty:
            continue
        
        # Get team info for each race
        driver_results = processor.results[processor.results['driverId'] == driver_id].copy()
        driver_results = pd.merge(
            driver_results,
            processor.races[['raceId', 'name', 'date', 'year']],
            on='raceId'
        )
        driver_results = pd.merge(
            driver_results,
            processor.constructors[['constructorId', 'name']].rename(columns={'name': 'team'}),
            on='constructorId'
        )
        driver_results = driver_results.sort_values('date')
        
        # Store race results
        for idx, (_, row) in enumerate(race_progression.iterrows()):
            # Find matching race in driver_results
            matching_race = driver_results[
                (driver_results['name'] == row['race_name']) &
                (driver_results['date'] == row['race_date'])
            ]
            team = matching_race['team'].iloc[0] if not matching_race.empty else None
            
            result = RaceResult(
                f1_driver_id=driver_id,
                race_number=int(row['race_number']),
                race_name=row['race_name'],
                race_date=str(row['race_date']),
                year=int(row['year']),
                position=int(row['position']) if pd.notna(row['position']) else None,
                elo_rating=float(row['elo_rating']),
                team=team
            )
            db.session.add(result)
        
        # Store team history (aggregated by year)
        team_years = driver_results.groupby(['year', 'team']).agg({
            'raceId': 'count'
        }).reset_index()
        
        for _, team_row in team_years.iterrows():
            # Get average ELO for that year from progression
            year_elo = race_progression[race_progression['year'] == team_row['year']]['elo_rating']
            avg_elo = year_elo.mean() if not year_elo.empty else 1500.0
            
            team_history = DriverTeamHistory(
                f1_driver_id=driver_id,
                team=team_row['team'],
                year=int(team_row['year']),
                elo_rating=float(avg_elo)
            )
            db.session.add(team_history)
    
    db.session.commit()
    print("Database population completed!")
