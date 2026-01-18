"""
SQLAlchemy database models.
"""
from datetime import datetime
from app import db


class DriverEloRanking(db.Model):
    """Main driver ELO ranking model."""
    id = db.Column(db.Integer, primary_key=True)
    driver = db.Column(db.String(250), nullable=False)
    f1_driver_id = db.Column(db.Integer, nullable=False)
    elo_rating = db.Column(db.Float, nullable=False)
    lower_bound = db.Column(db.Float, nullable=False)
    upper_bound = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Integer, nullable=False)
    reliability_grade = db.Column(db.String(10), nullable=False)
    race_count = db.Column(db.Integer, nullable=False)
    rating_volatility = db.Column(db.Float, nullable=False)
    first_year = db.Column(db.Integer, nullable=False)
    last_year = db.Column(db.Integer, nullable=False)
    career_span = db.Column(db.Integer, nullable=False)
    flag_level = db.Column(db.String(50), nullable=False)


class DriverEloProgression(db.Model):
    """Stores pre-computed ELO progression data for each driver."""
    id = db.Column(db.Integer, primary_key=True)
    f1_driver_id = db.Column(db.Integer, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    elo_rating = db.Column(db.Float, nullable=False)
    
    __table_args__ = (
        db.Index('idx_driver_year', 'f1_driver_id', 'year'),
    )


class DriverTeamHistory(db.Model):
    """Stores driver team history with ELO ratings."""
    id = db.Column(db.Integer, primary_key=True)
    f1_driver_id = db.Column(db.Integer, nullable=False, index=True)
    team = db.Column(db.String(250), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    elo_rating = db.Column(db.Float, nullable=False)
    
    __table_args__ = (
        db.Index('idx_driver_team_year', 'f1_driver_id', 'team', 'year'),
    )


class RaceResult(db.Model):
    """Stores race results for driver comparisons."""
    id = db.Column(db.Integer, primary_key=True)
    f1_driver_id = db.Column(db.Integer, nullable=False, index=True)
    race_number = db.Column(db.Integer, nullable=False)
    race_name = db.Column(db.String(250), nullable=False)
    race_date = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer, nullable=True)
    elo_rating = db.Column(db.Float, nullable=False)
    team = db.Column(db.String(250), nullable=True)


class AppStats(db.Model):
    """Stores pre-computed application statistics."""
    id = db.Column(db.Integer, primary_key=True)
    stat_key = db.Column(db.String(50), unique=True, nullable=False)
    stat_value = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
