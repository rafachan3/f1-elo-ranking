from main import app, db, DriverEloRanking
from data_processor import F1DataProcessor
from database_utils import update_database_from_df

def update_rankings():
    with app.app_context():
        print("Starting database update...")
        
        # Generate new rankings
        processor = F1DataProcessor()
        processor.load_data()
        processor.process_races()
        rankings = processor.calculate_rankings()
        
        # Update database with new rankings
        update_database_from_df(db, DriverEloRanking, rankings)
        print("Database update completed successfully.")

if __name__ == "__main__":
    update_rankings()