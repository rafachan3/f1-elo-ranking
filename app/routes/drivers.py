"""
Driver routes - profile and comparison pages.
"""
from flask import Blueprint, render_template, request
import pandas as pd
import plotly.graph_objects as go

from app import db
from app.models import (
    DriverEloRanking, 
    DriverEloProgression, 
    DriverTeamHistory, 
    RaceResult
)
from utils.visualization import DriverVisualizationUtils

drivers_bp = Blueprint('drivers', __name__)


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


@drivers_bp.route('/driver/<int:driver_id>')
def driver_profile(driver_id):
    """Individual driver profile page."""
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


@drivers_bp.route('/compare', methods=['GET'])
def compare_drivers():
    """Driver comparison page."""
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
