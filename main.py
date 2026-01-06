from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_mail import Mail, Message
from config import get_config
from visualization_utils import DriverVisualizationUtils
import pandas as pd
from datetime import datetime
import os
from forms import ContactForm

# Initialize Flask app with configuration
app = Flask(__name__)
app.config.from_object(get_config())
Bootstrap5(app)

# Initialize database
db = SQLAlchemy(app)

# Initialize mail
mail = Mail(app)


# SQLAlchemy Models
class DriverEloRanking(db.Model):
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


@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}


def get_app_stats():
    """Get application statistics from database."""
    stats = {}
    for stat in AppStats.query.all():
        stats[stat.stat_key] = stat.stat_value
    return stats


@app.route('/rankings')
def complete_rankings():
    # Get filter parameters from request
    experience_filter = request.args.get('experience')
    reliability_filter = request.args.get('reliability', '').replace(' ', '+')
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

    # Get dropdown options
    experiences = [exp[0] for exp in db.session.query(DriverEloRanking.flag_level).distinct()]
    reliability_grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F']
    year_range = db.session.query(
        db.func.min(DriverEloRanking.first_year),
        db.func.max(DriverEloRanking.last_year)
    ).first()

    return render_template(
        "rankings.html",
        drivers=drivers,
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
    # Fetch data from database (fast - no CSV processing)
    drivers = DriverEloRanking.query.all()
    df = pd.DataFrame([{col.name: getattr(driver, col.name) for col in DriverEloRanking.__table__.columns} for driver in drivers])
    
    # Get pre-computed statistics from database
    stats = get_app_stats()
    if not stats:
        # Fallback if stats not computed yet
        stats = {
            'drivers_count': len(df),
            'years_covered': int(df['last_year'].max() - df['first_year'].min()) if not df.empty else 0,
            'races_count': 0,
            'data_points': len(df) * len(df.columns) if not df.empty else 0
        }
    
    # Initialize visualization utils
    viz_utils = DriverVisualizationUtils()
    
    # Generate charts from database data
    if not df.empty:
        bar_chart = viz_utils.create_top_drivers_chart(df)
        line_chart = viz_utils.create_era_trends_chart(df)
        pie_chart = viz_utils.create_reliability_distribution_chart(df)
        scatter_chart = viz_utils.create_career_longevity_chart(df)
        
        return render_template('index.html',
                             stats=stats,
                             bar_chart=bar_chart.to_html(full_html=False),
                             line_chart=line_chart.to_html(full_html=False),
                             pie_chart=pie_chart.to_html(full_html=False),
                             scatter_chart=scatter_chart.to_html(full_html=False))
    
    return render_template('index.html', stats=stats)


@app.route('/methodology')
def methodology():
    return render_template('methodology.html')


@app.route('/search')
def search_drivers():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('home'))

    exact_match = DriverEloRanking.query.filter(
        db.func.lower(DriverEloRanking.driver) == db.func.lower(query)
    ).first()

    if exact_match:
        return redirect(url_for('driver_profile', driver_id=exact_match.id))

    similar_drivers = DriverEloRanking.query.filter(
        db.func.lower(DriverEloRanking.driver).like(f"%{query.lower()}%")
    ).all()

    return render_template('search_results.html', drivers=similar_drivers, query=query)


@app.route('/driver/<int:driver_id>')
def driver_profile(driver_id):
    driver = DriverEloRanking.query.get_or_404(driver_id)
    
    # Get ELO progression from database
    elo_progression = DriverEloProgression.query.filter_by(
        f1_driver_id=driver.f1_driver_id
    ).order_by(DriverEloProgression.year).all()
    
    if not elo_progression:
        return "No ELO progression data available", 404
    
    # Convert to DataFrame
    driver_elo_progression = pd.DataFrame([{
        'year': p.year,
        'driverId': p.f1_driver_id,
        'elo_rating': p.elo_rating
    } for p in elo_progression])
    
    # Get team history from database
    team_history = DriverTeamHistory.query.filter_by(
        f1_driver_id=driver.f1_driver_id
    ).order_by(DriverTeamHistory.year).all()
    
    team_data = pd.DataFrame([{
        'year': t.year,
        'team': t.team,
        'elo_rating': t.elo_rating,
        'driverId': t.f1_driver_id
    } for t in team_history]) if team_history else pd.DataFrame()
    
    # Initialize visualization utils
    viz_utils = DriverVisualizationUtils()
    
    charts = {
        'elo_history_chart': viz_utils.create_elo_history_chart(driver_elo_progression, driver.driver),
        'era_performance_chart': viz_utils.create_era_performance_chart(driver_elo_progression),
        'confidence_chart': viz_utils.create_confidence_chart(driver)
    }
    
    # Add team chart if data available
    if not team_data.empty:
        charts['team_elo_chart'] = viz_utils.create_team_elo_chart(team_data, driver.driver)
    else:
        # Create empty chart placeholder
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.update_layout(title='Team ELO data not available')
        charts['team_elo_chart'] = fig
    
    # Get teammate comparisons from database
    teammate_comparisons = get_teammate_comparisons_from_db(driver.f1_driver_id)
    
    return render_template(
        'driver_profile.html',
        driver=driver,
        elo_history_chart=charts['elo_history_chart'].to_html(full_html=False),
        team_elo_chart=charts['team_elo_chart'].to_html(full_html=False),
        era_performance_chart=charts['era_performance_chart'].to_html(full_html=False),
        confidence_chart=charts['confidence_chart'].to_html(full_html=False),
        teammate_comparisons=teammate_comparisons
    )


def get_teammate_comparisons_from_db(f1_driver_id):
    """Get teammate comparisons from pre-computed race results."""
    # Get this driver's race results
    driver_results = RaceResult.query.filter_by(f1_driver_id=f1_driver_id).all()
    
    if not driver_results:
        return []
    
    # Build comparison data
    comparisons = {}
    driver_races_by_team = {}
    
    for result in driver_results:
        if result.team:
            key = (result.race_name, result.race_date, result.team)
            if key not in driver_races_by_team:
                driver_races_by_team[key] = result
    
    # Find teammates (other drivers in same team/race)
    for (race_name, race_date, team), driver_result in driver_races_by_team.items():
        teammate_results = RaceResult.query.filter(
            RaceResult.race_name == race_name,
            RaceResult.race_date == race_date,
            RaceResult.team == team,
            RaceResult.f1_driver_id != f1_driver_id
        ).all()
        
        for teammate_result in teammate_results:
            # Get teammate name
            teammate = DriverEloRanking.query.filter_by(
                f1_driver_id=teammate_result.f1_driver_id
            ).first()
            
            if teammate:
                teammate_name = teammate.driver
                if teammate_name not in comparisons:
                    comparisons[teammate_name] = {
                        'teammate': teammate_name,
                        'races': 0,
                        'wins': 0,
                        'elo_diffs': []
                    }
                
                comparisons[teammate_name]['races'] += 1
                if driver_result.position and teammate_result.position:
                    if driver_result.position < teammate_result.position:
                        comparisons[teammate_name]['wins'] += 1
                comparisons[teammate_name]['elo_diffs'].append(
                    driver_result.elo_rating - teammate_result.elo_rating
                )
    
    # Calculate final statistics
    result = []
    for name, data in comparisons.items():
        if data['races'] > 0:
            avg_elo_diff = sum(data['elo_diffs']) / len(data['elo_diffs']) if data['elo_diffs'] else 0
            result.append({
                'teammate': name,
                'races': data['races'],
                'win_percentage': (data['wins'] / data['races']) * 100,
                'elo_diff': round(avg_elo_diff, 1)
            })
    
    return sorted(result, key=lambda x: x['races'], reverse=True)[:5]


@app.route('/compare', methods=['GET'])
def compare_drivers():
    # Get all drivers for the dropdown
    drivers = DriverEloRanking.query.order_by(DriverEloRanking.driver).all()
    
    # Get selected driver IDs from query parameters
    selected_ids = request.args.getlist('drivers')
    selected_ids = [int(id) for id in selected_ids if id.isdigit()]
    
    comparison_data = None
    if selected_ids:
        comparison_data = []
        for driver_id in selected_ids:
            driver = DriverEloRanking.query.get(driver_id)
            if driver:
                # Get race progression from database
                race_results = RaceResult.query.filter_by(
                    f1_driver_id=driver.f1_driver_id
                ).order_by(RaceResult.race_number).all()
                
                if race_results:
                    driver_data = pd.DataFrame([{
                        'race_number': r.race_number,
                        'race_name': r.race_name,
                        'race_date': r.race_date,
                        'elo_rating': r.elo_rating,
                        'position': r.position,
                        'year': r.year,
                        'Driver': driver.driver
                    } for r in race_results])
                    comparison_data.append(driver_data)
        
        if comparison_data:
            comparison_data = pd.concat(comparison_data, ignore_index=True)
    
    viz_utils = DriverVisualizationUtils()
    comparison_chart = None
    if comparison_data is not None and not comparison_data.empty:
        comparison_chart = viz_utils.create_comparison_chart(comparison_data).to_html(full_html=False)
    
    return render_template(
        'compare.html',
        drivers=drivers,
        selected_ids=selected_ids,
        comparison_chart=comparison_chart
    )


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = Message(
            subject=f"F1 ELO Contact Form: {form.subject.data}",
            recipients=[app.config.get('MAIL_RECIPIENT')],
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


def init_db(app):
    """Initialize the database and create all tables."""
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
    from data_processor import F1DataProcessor
    from database_utils import update_database_from_df
    
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


if __name__ == "__main__":
    init_db(app)
    app.run(debug=True)
