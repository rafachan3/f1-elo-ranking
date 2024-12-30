from flask import Flask, render_template, redirect, url_for
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
    # Fetch all drivers, ordered by Elo rating
    drivers = DriverEloRanking.query.order_by(DriverEloRanking.elo_rating.desc()).all()
    return render_template("index.html", drivers=drivers)

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