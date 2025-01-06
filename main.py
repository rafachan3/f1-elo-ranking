from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_mail import Mail, Message
from data_processor import F1DataProcessor
from database_utils import update_database_from_df
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from visualization_utils import DriverVisualizationUtils
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
import os
from forms import ContactForm

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["FLASK_SECRET_KEY"]
Bootstrap5(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///f1-driver-elo-rankings.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# SQLAlchemy Model
class DriverEloRanking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver = db.Column(db.String(250), nullable=False)
    f1_driver_id = db.Column(db.Integer, nullable=False)  # Changed from driver_id
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

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

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

@app.route('/search')
def search_drivers():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('home'))

    # Search for exact or close matches
    exact_match = DriverEloRanking.query.filter(
        db.func.lower(DriverEloRanking.driver) == db.func.lower(query)
    ).first()

    if exact_match:
        return redirect(url_for('driver_profile', driver_id=exact_match.id))

    # If no exact match, search for similar names
    similar_drivers = DriverEloRanking.query.filter(
        db.func.lower(DriverEloRanking.driver).like(f"%{query.lower()}%")
    ).all()

    return render_template('search_results.html', drivers=similar_drivers, query=query)

@app.route('/driver/<int:driver_id>')
def driver_profile(driver_id):
    driver = DriverEloRanking.query.get_or_404(driver_id)

    processor = F1DataProcessor()
    processor.load_data()
    processor.process_races()

    # Get career data with proper joins
    career_data = pd.merge(
        processor.results,
        processor.races[['raceId', 'year', 'round', 'name']],
        on='raceId'
    )
    
    career_data = pd.merge(
        career_data,
        processor.constructors[['constructorId', 'name']].rename(columns={'name': 'team'}),
        on='constructorId'
    )

    # Get all drivers' ELO progression
    all_elo_progression = processor.get_all_drivers_elo_progression()

    # Add ELO data to career_data
    career_data = pd.merge(
        career_data,
        all_elo_progression[['year', 'driverId', 'elo_rating']],
        on=['year', 'driverId'],
        how='left'
    )

    # Filter for this driver
    driver_data = career_data[career_data['driverId'] == driver.f1_driver_id].copy()
    
    if not driver_data.empty:
        try:
            # Get ELO progression for charts
            driver_elo_progression = processor.get_driver_elo_progression(driver.f1_driver_id)
            
            if not driver_elo_progression.empty:
                # Initialize visualization utils and generate charts
                viz_utils = DriverVisualizationUtils()
                
                charts = {
                    'elo_history_chart': viz_utils.create_elo_history_chart(driver_elo_progression, driver.driver),
                    'team_elo_chart': viz_utils.create_team_elo_chart(driver_data, driver.driver),
                    'era_performance_chart': viz_utils.create_era_performance_chart(driver_elo_progression),
                    'confidence_chart': viz_utils.create_confidence_chart(driver)
                }

                teammate_comparisons = viz_utils.get_teammate_comparisons(driver_data, career_data, processor.drivers)

                return render_template(
                    'driver_profile.html',
                    driver=driver,
                    elo_history_chart=charts['elo_history_chart'].to_html(full_html=False),
                    team_elo_chart=charts['team_elo_chart'].to_html(full_html=False),
                    era_performance_chart=charts['era_performance_chart'].to_html(full_html=False),
                    confidence_chart=charts['confidence_chart'].to_html(full_html=False),
                    teammate_comparisons=teammate_comparisons
                )
            else:
                return "No ELO progression data available", 404
                
        except Exception as e:
            print(f"Error processing driver data: {str(e)}")
            return f"Error processing driver data: {str(e)}", 500
    else:
        return "No career data found for driver", 404
    
@app.route('/compare', methods=['GET'])
def compare_drivers():
    # Get all drivers for the dropdown
    drivers = DriverEloRanking.query.order_by(DriverEloRanking.driver).all()
    
    # Get selected driver IDs from query parameters
    selected_ids = request.args.getlist('drivers')
    selected_ids = [int(id) for id in selected_ids if id.isdigit()]
    
    comparison_data = None
    if selected_ids:
        processor = F1DataProcessor()
        processor.load_data()
        processor.process_races()
        
        comparison_data = []
        for driver_id in selected_ids:
            driver = DriverEloRanking.query.get(driver_id)
            if driver:
                print(f"Processing driver {driver.driver} (ID: {driver.f1_driver_id})")
                print(f"Database ELO: {driver.elo_rating}")
                
                # Get race-by-race progression
                driver_data = processor.get_driver_race_progression(driver.f1_driver_id)
                if not driver_data.empty:
                    print(f"Last calculated ELO: {driver_data['elo_rating'].iloc[-1]}")
                    driver_data['Driver'] = driver.driver
                    comparison_data.append(driver_data)
        
        if comparison_data:
            comparison_data = pd.concat(comparison_data, ignore_index=True)
    
    return render_template(
        'compare.html',
        drivers=drivers,
        selected_ids=selected_ids,
        comparison_chart=create_comparison_chart(comparison_data) if comparison_data is not None else None
    )


def create_comparison_chart(comparison_data):
    if comparison_data.empty:
        return None
        
    fig = go.Figure()
    
    for driver in comparison_data['Driver'].unique():
        driver_data = comparison_data[comparison_data['Driver'] == driver]
        
        fig.add_trace(go.Scatter(
            x=driver_data['race_number'],
            y=driver_data['elo_rating'],
            name=driver,
            mode='lines+markers',
            hovertemplate=(
                'Race: %{customdata[0]}<br>' +
                'Date: %{customdata[1]}<br>' +
                'ELO: %{y:.0f}<br>' +
                'Position: %{customdata[2]}'
            ),
            customdata=driver_data[['race_name', 'race_date', 'position']]
        ))
    
    fig.update_layout(
        title='Driver ELO Rating Progression by Race',
        xaxis_title='Race Number',
        yaxis_title='ELO Rating',
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
        )
    )
    
    return fig.to_html(full_html=False)

# Mail config
MAIL_SERVER=os.environ['MAIL_SERVER']
MAIL_PORT=os.environ['MAIL_PORT']
MAIL_USERNAME = os.environ['MAIL_USERNAME']
MAIL_PASSWORD = os.environ['MAIL_PASSWORD']

app.config.update(
   MAIL_SERVER=MAIL_SERVER,
   MAIL_PORT=MAIL_PORT,
   MAIL_USE_TLS=True,
   MAIL_USE_SSL=False,
   MAIL_USERNAME=MAIL_USERNAME,
   MAIL_PASSWORD=MAIL_PASSWORD,
   MAIL_DEFAULT_SENDER=MAIL_USERNAME
)

mail = Mail(app)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
   form = ContactForm()
   if form.validate_on_submit():
       msg = Message(
           subject=f"F1 ELO Contact Form: {form.subject.data}",
           recipients=[os.environ['MAIL_RECIPIENT']],
           body=f"""
From: {form.name.data} <{form.email.data}>
Subject: {dict(form.subject.choices).get(form.subject.data)}

Message:
{form.message.data}
""",
           reply_to=form.email.data
       )
       try:
           mail.send(msg)
           flash('Thank you for your message! I will get back to you soon.', 'success')
       except Exception as e:
           app.logger.error(f"Email error: {str(e)}")
           flash('An error occurred sending your message. Please try again later.', 'danger')
       return redirect(url_for('contact'))
   return render_template('contact.html', form=form)

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