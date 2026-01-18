"""
Database utility functions.
"""
from sqlalchemy import inspect


def update_database_from_df(db, DriverEloRanking, df):
    """
    Update database from a pandas DataFrame.
    
    Args:
        db: SQLAlchemy database instance
        DriverEloRanking: The model class for driver rankings
        df: DataFrame containing driver ranking data
    """
    # Define column mapping between DataFrame and model
    column_mapping = {
        'Driver': 'driver',
        'f1_driver_id': 'f1_driver_id',
        'Elo Rating': 'elo_rating',
        'Lower Bound': 'lower_bound',
        'Upper Bound': 'upper_bound',
        'Confidence Score': 'confidence_score',
        'Reliability Grade': 'reliability_grade',
        'Race Count': 'race_count',
        'Rating Volatility': 'rating_volatility',
        'First Year': 'first_year',
        'Last Year': 'last_year',
        'Career Span': 'career_span',
        'Flag Level': 'flag_level'
    }
    
    # Get the current model columns using SQLAlchemy inspector
    inspector = inspect(DriverEloRanking)
    model_columns = [c.key for c in inspector.columns if c.key != 'id']
    
    for _, row in df.iterrows():
        # Convert DataFrame row to model column names
        record_data = {}
        for df_col, model_col in column_mapping.items():
            if model_col in model_columns and df_col in row:
                record_data[model_col] = row[df_col]
        
        if not record_data.get('driver'):
            continue
            
        existing_record = db.session.query(DriverEloRanking).filter_by(
            driver=record_data['driver']
        ).first()
        
        if existing_record:
            # Check if any values have changed
            record_changed = any(
                getattr(existing_record, col) != val
                for col, val in record_data.items()
                if col in model_columns
            )
            
            if record_changed:
                # Update only the columns that exist in both
                for col, val in record_data.items():
                    if col in model_columns:
                        setattr(existing_record, col, val)
        else:
            # Create new record only if we have all required data
            if all(col in record_data for col in model_columns):
                new_record = DriverEloRanking(**record_data)
                db.session.add(new_record)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating database: {str(e)}")
        raise
