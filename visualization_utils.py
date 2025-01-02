import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class DriverVisualizationUtils:
    """Utility class for creating driver-related visualizations."""
 
    def create_elo_history_chart(self, driver_data, driver_name):
        """Create a line chart showing ELO rating progression over time."""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=driver_data['year'],
            y=driver_data['elo_rating'],
            mode='lines+markers',
            name='ELO Rating',
            line=dict(width=2),
            hovertemplate='Year: %{x}<br>ELO: %{y:.0f}'
        ))

        fig.update_layout(
            title=f'ELO Rating Progression - {driver_name}',
            xaxis_title='Year',
            yaxis_title='ELO Rating',
            hovermode='x unified',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)'
            )
        )

        return fig

    def create_team_elo_chart(self, team_data, driver_name):
        """Create a multi-line chart showing ELO progression by team."""
        if 'elo_rating' not in team_data.columns:
            # Create a basic ELO progression if elo_rating is missing
            team_data['elo_rating'] = team_data.groupby('team').cumcount() + 1500

        # Group data by team and year
        team_summary = team_data.groupby(['year', 'team'])['elo_rating'].mean().reset_index()

        fig = go.Figure()
        
        for team in team_summary['team'].unique():
            team_data_filtered = team_summary[team_summary['team'] == team].sort_values('year')
            
            fig.add_trace(go.Scatter(
                x=team_data_filtered['year'],
                y=team_data_filtered['elo_rating'],
                mode='lines+markers',
                name=team,
                hovertemplate='%{text}<br>ELO: %{y:.0f}',
                text=[f'{team} ({year})' for year in team_data_filtered['year']]
            ))

        fig.update_layout(
            title=f'ELO Rating by Team - {driver_name}',
            xaxis_title='Year',
            yaxis_title='ELO Rating',
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)'
            )
        )
        
        return fig

    def get_teammate_comparisons(self, driver_data, career_data, drivers_df):
        """Calculate head-to-head statistics against teammates."""
        comparisons = []
        driver_id = driver_data['driverId'].iloc[0]

        career_data = pd.merge(
            career_data,
            drivers_df[['driverId', 'forename', 'surname']],
            on='driverId',
            how='left'
        )
        career_data['driverRef'] = career_data['forename'] + ' ' + career_data['surname']

        for team in driver_data['team'].unique():
            team_races = career_data[career_data['team'] == team].copy()
            driver_races = driver_data[driver_data['team'] == team].copy()
            
            for teammate_id in team_races['driverId'].unique():
                if teammate_id == driver_id:
                    continue
                    
                teammate_races = team_races[team_races['driverId'] == teammate_id]
                
                # Get races where both drivers competed
                common_races = pd.merge(
                    driver_races[['raceId', 'team', 'positionOrder', 'year', 'elo_rating']],
                    teammate_races[['raceId', 'team', 'positionOrder', 'driverRef', 'elo_rating']],
                    on=['raceId', 'team'],
                    suffixes=('_driver', '_teammate')
                )
                
                if len(common_races) > 0:
                    # Calculate win percentage
                    wins = sum(common_races['positionOrder_driver'] < common_races['positionOrder_teammate'])
                    win_percentage = (wins / len(common_races)) * 100
                    
                    # Calculate average ELO difference
                    elo_differences = common_races['elo_rating_driver'] - common_races['elo_rating_teammate']
                    avg_elo_diff = round(float(elo_differences.mean()), 1)  # Round to 1 decimal place
                    
                    comparisons.append({
                        'teammate': teammate_races['driverRef'].iloc[0],
                        'races': len(common_races),
                        'win_percentage': win_percentage,
                        'elo_diff': avg_elo_diff if abs(avg_elo_diff) > 0.05 else 0.0  # Avoid -0.0 display
                    })

        return sorted(comparisons, key=lambda x: x['races'], reverse=True)[:5]

    def create_era_performance_chart(self, driver_data):
        """Create a bar chart showing average ELO rating by era (decade)."""
        driver_data['decade'] = (driver_data['year'] // 10) * 10
        era_avg = driver_data.groupby('decade')['elo_rating'].mean().reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=era_avg['decade'].astype(str) + 's',
            y=era_avg['elo_rating'],
            text=era_avg['elo_rating'].round(0),
            textposition='auto',
            hovertemplate='Era: %{x}<br>Average ELO: %{y:.0f}',
        ))

        fig.update_layout(
            title='Average ELO Rating by Era',
            xaxis_title='Era',
            yaxis_title='Average ELO Rating',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)'
            )
        )

        return fig

    def create_confidence_chart(self, driver):
        """Create a visualization of the driver's confidence interval."""
        fig = go.Figure()
        
        # Add main ELO rating point
        fig.add_trace(go.Scatter(
            x=[driver.elo_rating],
            y=[0],
            mode='markers',
            marker=dict(
                size=20,
                color='blue',
                symbol='diamond'
            ),
            name='Current Rating',
            hovertemplate='ELO Rating: %{x:.0f}'
        ))
        
        # Add confidence interval
        fig.add_trace(go.Scatter(
            x=[driver.lower_bound, driver.upper_bound],
            y=[0, 0],
            mode='lines',
            line=dict(
                color='rgba(0,0,255,0.3)',
                width=10
            ),
            name='95% Confidence Interval',
            hovertemplate='%{x:.0f}'
        ))
        
        # Update layout
        fig.update_layout(
            title='Rating Confidence Interval',
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                title='ELO Rating',
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                zeroline=False
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            height=200,
            margin=dict(t=30, l=50, r=50, b=30)
        )
        
        return fig