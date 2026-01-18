"""
Script to update the database with fresh ELO calculations.

Run this script to recalculate all ELO ratings and update the database.
This is useful when:
- New race data is added to the CSV files
- You want to refresh all calculations
- You need to rebuild the database

Usage:
    python update_db.py
    
For Heroku:
    heroku run python update_db.py
"""
import sys

from app import create_app, db
from app.models import (
    DriverEloRanking, 
    DriverEloProgression, 
    RaceResult, 
    DriverTeamHistory, 
    AppStats
)
from app.services import populate_database


def update_rankings(force_rebuild=False):
    """Update the database with fresh calculations.
    
    Args:
        force_rebuild: If True, clears all existing data before repopulating.
    """
    app = create_app()
    
    with app.app_context():
        print("Starting database update...")
        
        if force_rebuild:
            print("Force rebuild requested. Clearing existing data...")
            RaceResult.query.delete()
            DriverTeamHistory.query.delete()
            DriverEloProgression.query.delete()
            DriverEloRanking.query.delete()
            AppStats.query.delete()
            db.session.commit()
        
        # Repopulate database
        populate_database()
        
        print("Database update completed successfully.")
        
        # Print summary
        driver_count = DriverEloRanking.query.count()
        progression_count = DriverEloProgression.query.count()
        race_count = RaceResult.query.count()
        
        print(f"\nDatabase Summary:")
        print(f"  - Drivers: {driver_count}")
        print(f"  - ELO Progression Records: {progression_count}")
        print(f"  - Race Results: {race_count}")


if __name__ == "__main__":
    force = '--force' in sys.argv or '-f' in sys.argv
    
    if force:
        confirm = input("This will delete all existing data. Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    update_rankings(force_rebuild=force)
