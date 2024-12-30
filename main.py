from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from data_processor import F1DataProcessor
from database_utils import update_database_from_df
import os

app = Flask(__name__)
Bootstrap5(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///f1-driver-elo-rankings.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# SQLAlchemy Model
class DriverEloRanking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver = db.Column(db.String(250), nullable=False)
    elo_rating = db.Column(db.Float, nullable=False)
    lower_bound = db.Column(db.Float, nullable=False)
    upper_bound = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Integer, nullable=False)
    reliability_grade = db.Column(db.String(10), nullable=False)
    race_count = db.Column(db.Integer, nullable=False)
    rating_volatility = db.Column(db.Float, nullable=False)
    is_established = db.Column(db.Boolean, nullable=False)
    first_year = db.Column(db.Integer, nullable=False)
    last_year = db.Column(db.Integer, nullable=False)
    career_span = db.Column(db.Integer, nullable=False)
    flag_level = db.Column(db.String(50), nullable=False)

@app.route('/')
def home():
    # Get filter parameters from request
    experience_filter = request.args.get('experience')
    reliability_filter = request.args.get('reliability', '').replace(' ', '+')  # Replace space with + to handle URL encoding
    min_elo = request.args.get('min_elo', type=float)
    max_elo = request.args.get('max_elo', type=float)
    year_from = request.args.get('year_from', type=int)
    year_to = request.args.get('year_to', type=int)
    search_query = request.args.get('search', '').strip()

    # Get all drivers ordered by Elo rating to calculate absolute rankings
    all_drivers = DriverEloRanking.query.order_by(DriverEloRanking.elo_rating.desc()).all()
    rankings_dict = {driver.id: idx + 1 for idx, driver in enumerate(all_drivers)}

    # Start with base query
    query = DriverEloRanking.query

    # Apply filters
    if experience_filter:
        query = query.filter(DriverEloRanking.flag_level == experience_filter)
    if reliability_filter:
        query = query.filter(DriverEloRanking.reliability_grade == reliability_filter)
    if min_elo is not None:
        query = query.filter(DriverEloRanking.elo_rating >= min_elo)
    if max_elo is not None:
        query = query.filter(DriverEloRanking.elo_rating <= max_elo)
    if year_from is not None:
        query = query.filter(DriverEloRanking.last_year >= year_from)
    if year_to is not None:
        query = query.filter(DriverEloRanking.first_year <= year_to)
    if search_query:
        query = query.filter(DriverEloRanking.driver.ilike(f"%{search_query}%"))

     # Get filtered and ordered results
    drivers = query.order_by(DriverEloRanking.elo_rating.desc()).all()
    
    # Add ranking to each driver
    for driver in drivers:
        driver.ranking = rankings_dict[driver.id]

    # Get dropdown options (reliability grades in fixed order)
    experiences = [exp[0] for exp in db.session.query(DriverEloRanking.flag_level).distinct()]
    reliability_grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F']
    year_range = db.session.query(
        db.func.min(DriverEloRanking.first_year),
        db.func.max(DriverEloRanking.last_year)
    ).first()

    return render_template(
        "index.html",
        drivers=query.order_by(DriverEloRanking.elo_rating.desc()).all(),
        experiences=experiences,
        reliability_grades=reliability_grades,
        year_range=year_range,
        filters={
            'experience': experience_filter,
            'reliability': reliability_filter,
            'min_elo': min_elo,
            'max_elo': max_elo,
            'year_from': year_from,
            'year_to': year_to,
            'search': search_query
        }
    )

def init_database():
    # Generate the rankings DataFrame
    processor = F1DataProcessor()
    processor.load_data()
    processor.process_races()
    rankings = processor.calculate_rankings()

    # Create tables and populate database
    db.create_all()  # Create the tables
    update_database_from_df(db, DriverEloRanking, rankings)  # Populate the database
    print("Database created and populated successfully.")

if __name__ == "__main__":
    # Check if the database file exists in the instance folder
    db_path = os.path.join(app.instance_path, 'f1-driver-elo-rankings.db')
    
    if not os.path.exists(db_path):
        print("Database not found. Creating and populating it for the first time...")
        with app.app_context():
            init_database()
    else:
        print("Database already exists. No action needed.")

    # Start the Flask development server
    app.run(debug=True)