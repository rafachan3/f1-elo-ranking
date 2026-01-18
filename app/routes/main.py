"""
Main routes - home page, methodology, and search.
"""
from flask import Blueprint, render_template, redirect, url_for, request
import pandas as pd

from app import db
from app.models import DriverEloRanking, AppStats
from utils.visualization import DriverVisualizationUtils

main_bp = Blueprint('main', __name__)


def get_app_stats():
    """Get application statistics from database."""
    stats = {}
    for stat in AppStats.query.all():
        stats[stat.stat_key] = stat.stat_value
    return stats


@main_bp.route('/')
def home():
    """Home page with dashboard and charts."""
    # Fetch data from database
    drivers = DriverEloRanking.query.all()
    df = pd.DataFrame([
        {col.name: getattr(driver, col.name) for col in DriverEloRanking.__table__.columns}
        for driver in drivers
    ])
    
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
        
        return render_template(
            'index.html',
            stats=stats,
            bar_chart=bar_chart.to_html(full_html=False),
            line_chart=line_chart.to_html(full_html=False),
            pie_chart=pie_chart.to_html(full_html=False),
            scatter_chart=scatter_chart.to_html(full_html=False)
        )
    
    return render_template('index.html', stats=stats)


@main_bp.route('/methodology')
def methodology():
    """Methodology explanation page."""
    return render_template('methodology.html')


@main_bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('privacy.html')


@main_bp.route('/terms')
def terms():
    """Terms of service page."""
    return render_template('terms.html')


@main_bp.route('/search')
def search_drivers():
    """Search for drivers by name."""
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('main.home'))

    # Check for exact match
    exact_match = DriverEloRanking.query.filter(
        db.func.lower(DriverEloRanking.driver) == db.func.lower(query)
    ).first()

    if exact_match:
        return redirect(url_for('drivers.driver_profile', driver_id=exact_match.id))

    # Find similar drivers
    similar_drivers = DriverEloRanking.query.filter(
        db.func.lower(DriverEloRanking.driver).like(f"%{query.lower()}%")
    ).all()

    return render_template('search_results.html', drivers=similar_drivers, query=query)
