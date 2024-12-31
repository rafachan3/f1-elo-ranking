from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from data_processor import F1DataProcessor
from database_utils import update_database_from_df
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
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

@app.route('/rankings')
def complete_rankings():
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
        "rankings.html",
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

@app.route('/')
def home():
    # Fetch data from database
    drivers = DriverEloRanking.query.all()
    df = pd.DataFrame([{col.name: getattr(driver, col.name) for col in DriverEloRanking.__table__.columns} for driver in drivers])

    # Graph 1: Top Drivers by ELO Rating
    top_drivers = df.nlargest(10, 'elo_rating')
    bar_chart = px.bar(
        top_drivers,
        x='driver',
        y=top_drivers['elo_rating'].round(0),
        labels={'elo_rating': 'ELO Rating', 'driver': 'Driver'},
        text=top_drivers['elo_rating'].round(0)
    )
    bar_chart.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=None,
        yaxis_title='ELO Rating',
        hovermode=False
    )

    # Graph 2: ELO Trends by Era
    df['era'] = (df['first_year'] // 10) * 10
    era_group = df.groupby('era').agg({'elo_rating': ['mean', 'max']}).reset_index()
    era_group.columns = ['Era', 'Average ELO', 'Top ELO']

    line_chart = go.Figure()
    line_chart.add_trace(go.Scatter(
        x=era_group['Era'], 
        y=era_group['Average ELO'].round(0), 
        mode='lines+markers',
        name='Average ELO', 
        hovertemplate='Era: %{x}<br>Average ELO: %{y:,.0f}'
    ))
    line_chart.add_trace(go.Scatter(
        x=era_group['Era'], 
        y=era_group['Top ELO'].round(0), 
        mode='lines+markers',
        name='Top ELO', 
        hovertemplate='Era: %{x}<br>Top ELO: %{y:,.0f}'
    ))
    line_chart.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=None,
        xaxis_title='Decade',
        yaxis_title='ELO Rating',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
        )
    )

    # Graph 3: Driver Reliability Grades Distribution
    reliability_group = df.groupby('reliability_grade').agg({'elo_rating': 'mean', 'driver': 'count'}).reset_index()
    reliability_group.columns = ['Reliability Grade', 'Average ELO', 'Driver Count']

    # Define the desired order for reliability grades
    grade_order = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F']

    # Define color mapping
    grade_colors = {
        'A+': '#198754',  # Dark green
        'A': '#28a745',   # Standard green
        'B+': '#0d6efd',  # Dark blue
        'B': '#3d8bfd',   # Standard blue
        'C+': '#fd7e14',  # Dark orange
        'C': '#ffc107',   # Standard yellow
        'D+': '#dc3545',  # Dark red
        'D': '#e35d6a',   # Standard red
        'F': '#343a40'    # Dark grey
    }

    # Reorder the DataFrame based on the custom order
    reliability_group['Reliability Grade'] = pd.Categorical(
        reliability_group['Reliability Grade'], 
        categories=grade_order, 
        ordered=True
    )
    reliability_group = reliability_group.sort_values('Reliability Grade')

    pie_chart = px.pie(
        reliability_group,
        values='Driver Count',
        names='Reliability Grade',
        labels={'Driver Count': 'Driver Count', 'Reliability Grade': 'Reliability Grade'},
        category_orders={'Reliability Grade': grade_order},
        color='Reliability Grade',
        color_discrete_map=grade_colors
    )
    pie_chart.update_traces(
        hovertemplate='Grade: %{label}<br>Count: %{value:,.0f}'
    )
    pie_chart.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=None
    )

    # Graph 4: Career Longevity vs. ELO
    # Calculate average ELO rating and count for each career span length
    career_span_data = df.groupby('career_span').agg({
        'elo_rating': 'mean',
        'driver': 'count'  # Count number of drivers
    }).reset_index()

    career_span_data.columns = ['career_span', 'avg_elo', 'driver_count']
    career_span_data['avg_elo'] = career_span_data['avg_elo'].round(0)

    # Create a color scale that can handle any number of points
    import numpy as np
    n_points = len(career_span_data)
    colors = [f'hsl({h},70%,50%)' for h in np.linspace(0, 300, n_points)]

    scatter_chart = go.Figure()

    # Calculate circle sizes with a better scaling function
    min_size = 10
    max_size = 50
    min_count = career_span_data['driver_count'].min()
    max_count = career_span_data['driver_count'].max()

    def scale_size(count):
        if max_count == min_count:
            return (min_size + max_size) / 2
        scaled = (count - min_count) / (max_count - min_count)
        return min_size + (max_size - min_size) * scaled

    career_span_data['point_size'] = career_span_data['driver_count'].apply(scale_size)

    scatter_chart.add_trace(go.Scatter(
        x=career_span_data['career_span'],
        y=career_span_data['avg_elo'],
        mode='markers',
        marker=dict(
            size=career_span_data['point_size'],
            color=colors,
            line=dict(width=1, color='darkgray')
        ),
        hovertemplate='Career Span: %{x} years<br>Average ELO: %{y:,.0f}<br>Drivers: %{customdata}<extra></extra>',
        customdata=career_span_data['driver_count']
    ))

    scatter_chart.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=None,
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            title='Career Span (Years)',
            range=[-1, career_span_data['career_span'].max() + 1]
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            title='ELO Rating'
        )
    )

    return render_template('index.html',
                           bar_chart=bar_chart.to_html(full_html=False),
                           line_chart=line_chart.to_html(full_html=False),
                           pie_chart=pie_chart.to_html(full_html=False),
                           scatter_chart=scatter_chart.to_html(full_html=False))

@app.route('/methodology')
def methodology():
    return render_template('methodology.html')

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
        print("Database already exists. No action needed. Update the database manually if needed.")  

    # Start the Flask development server
    app.run(debug=True)