"""
Script to seed the Neon PostgreSQL database with F1 ELO data.

This script should be run LOCALLY (not on Vercel) to populate the Neon database
with all the computed ELO rankings, progressions, and race results.

Usage:
    1. Set your DATABASE_URL environment variable to your Neon connection string
    2. Run: python seed_neon.py

Example:
    export DATABASE_URL="postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require"
    python seed_neon.py
    
Or create a .env file with:
    DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
    FLASK_ENV=production
"""
import os
import sys

# Ensure we're using the production config with Neon
os.environ['FLASK_ENV'] = 'production'

# Check for DATABASE_URL
if not os.environ.get('DATABASE_URL'):
    print("ERROR: DATABASE_URL environment variable is required!")
    print("\nSet it to your Neon PostgreSQL connection string:")
    print("  export DATABASE_URL='postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require'")
    print("\nOr create a .env file with the DATABASE_URL variable.")
    sys.exit(1)

from app import create_app, db
from app.models import (
    DriverEloRanking, 
    DriverEloProgression, 
    RaceResult, 
    DriverTeamHistory, 
    AppStats
)
from app.services import populate_database


def seed_database(force_rebuild=False):
    """Seed the Neon database with F1 ELO data.
    
    Args:
        force_rebuild: If True, clears all existing data before seeding.
    """
    app = create_app()
    
    with app.app_context():
        print(f"Connecting to database...")
        print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        
        # Create tables if they don't exist
        print("\nCreating database tables...")
        db.create_all()
        print("Tables created successfully!")
        
        # Check if data already exists
        existing_drivers = DriverEloRanking.query.count()
        
        if existing_drivers > 0 and not force_rebuild:
            print(f"\nDatabase already has {existing_drivers} drivers.")
            print("Use --force flag to rebuild the database.")
            return
        
        if force_rebuild and existing_drivers > 0:
            print(f"\nForce rebuild requested. Clearing {existing_drivers} existing records...")
            RaceResult.query.delete()
            DriverTeamHistory.query.delete()
            DriverEloProgression.query.delete()
            DriverEloRanking.query.delete()
            AppStats.query.delete()
            db.session.commit()
            print("Existing data cleared.")
        
        # Populate the database with fresh calculations
        print("\n" + "="*50)
        print("Starting database population...")
        print("This may take a few minutes...")
        print("="*50 + "\n")
        
        populate_database()
        
        # Print summary
        print("\n" + "="*50)
        print("DATABASE SEEDING COMPLETED!")
        print("="*50)
        
        driver_count = DriverEloRanking.query.count()
        progression_count = DriverEloProgression.query.count()
        race_count = RaceResult.query.count()
        team_history_count = DriverTeamHistory.query.count()
        
        print(f"\nDatabase Summary:")
        print(f"  ✓ Drivers: {driver_count}")
        print(f"  ✓ ELO Progression Records: {progression_count}")
        print(f"  ✓ Race Results: {race_count}")
        print(f"  ✓ Team History Records: {team_history_count}")
        print("\nYour Neon database is now ready!")
        print("You can deploy to Vercel and it will use this data.")


if __name__ == "__main__":
    force = '--force' in sys.argv or '-f' in sys.argv
    
    if force:
        print("\n⚠️  WARNING: Force rebuild will delete all existing data!")
        confirm = input("Are you sure you want to continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    seed_database(force_rebuild=force)
