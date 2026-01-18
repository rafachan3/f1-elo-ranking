"""
Rankings routes - complete rankings page with filters.
"""
from flask import Blueprint, render_template, request

from app import db
from app.models import DriverEloRanking

rankings_bp = Blueprint('rankings', __name__)


@rankings_bp.route('/rankings')
def complete_rankings():
    """Complete rankings page with filtering options."""
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
