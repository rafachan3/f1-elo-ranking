"""
Visualization utilities for creating Plotly charts.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np


class DriverVisualizationUtils:
    """Utility class for creating driver-related visualizations."""

    def create_top_drivers_chart(self, df):
        """Create bar chart of top drivers by ELO rating."""
        top_drivers = df.nlargest(10, 'elo_rating')
        fig = px.bar(
            top_drivers,
            x='driver',
            y=top_drivers['elo_rating'].round(0),
            labels={'elo_rating': 'ELO Rating', 'driver': 'Driver'},
            text=top_drivers['elo_rating'].round(0)
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title=None,
            yaxis_title='ELO Rating',
            hovermode=False
        )
        return fig

    def create_era_trends_chart(self, df):
        """Create line chart showing ELO trends by era."""
        df = df.copy()
        df['era'] = (df['first_year'] // 10) * 10
        era_group = df.groupby('era').agg({'elo_rating': ['mean', 'max']}).reset_index()
        era_group.columns = ['Era', 'Average ELO', 'Top ELO']

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=era_group['Era'], 
            y=era_group['Average ELO'].round(0), 
            mode='lines+markers',
            name='Average ELO', 
            hovertemplate='Era: %{x}<br>Average ELO: %{y:,.0f}'
        ))
        fig.add_trace(go.Scatter(
            x=era_group['Era'], 
            y=era_group['Top ELO'].round(0), 
            mode='lines+markers',
            name='Top ELO', 
            hovertemplate='Era: %{x}<br>Top ELO: %{y:,.0f}'
        ))
        fig.update_layout(
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
        return fig

    def create_reliability_distribution_chart(self, df):
        """Create pie chart showing distribution of reliability grades."""
        reliability_group = df.groupby('reliability_grade').agg({
            'elo_rating': 'mean', 
            'driver': 'count'
        }).reset_index()
        reliability_group.columns = ['Reliability Grade', 'Average ELO', 'Driver Count']

        grade_order = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F']
        grade_colors = {
            'A+': '#198754', 'A': '#28a745', 'B+': '#0d6efd', 'B': '#3d8bfd',
            'C+': '#fd7e14', 'C': '#ffc107', 'D+': '#dc3545', 'D': '#e35d6a',
            'F': '#343a40'
        }

        reliability_group['Reliability Grade'] = pd.Categorical(
            reliability_group['Reliability Grade'],
            categories=grade_order,
            ordered=True
        )
        reliability_group = reliability_group.sort_values('Reliability Grade')

        fig = px.pie(
            reliability_group,
            values='Driver Count',
            names='Reliability Grade',
            labels={'Driver Count': 'Driver Count', 'Reliability Grade': 'Reliability Grade'},
            category_orders={'Reliability Grade': grade_order},
            color='Reliability Grade',
            color_discrete_map=grade_colors
        )
        fig.update_traces(hovertemplate='Grade: %{label}<br>Count: %{value:,.0f}')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title=None
        )
        return fig

    def create_career_longevity_chart(self, df):
        """Create scatter plot showing career longevity vs ELO rating."""
        career_span_data = df.groupby('career_span').agg({
            'elo_rating': 'mean',
            'driver': 'count'
        }).reset_index()

        career_span_data.columns = ['career_span', 'avg_elo', 'driver_count']
        career_span_data['avg_elo'] = career_span_data['avg_elo'].round(0)

        n_points = len(career_span_data)
        colors = [f'hsl({h},70%,50%)' for h in np.linspace(0, 300, n_points)]

        min_size, max_size = 10, 50
        min_count = career_span_data['driver_count'].min()
        max_count = career_span_data['driver_count'].max()

        def scale_size(count):
            if max_count == min_count:
                return (min_size + max_size) / 2
            scaled = (count - min_count) / (max_count - min_count)
            return min_size + (max_size - min_size) * scaled

        career_span_data['point_size'] = career_span_data['driver_count'].apply(scale_size)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
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

        fig.update_layout(
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
        return fig
 
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
            team_data = team_data.copy()
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
                    avg_elo_diff = round(float(elo_differences.mean()), 1)
                    
                    comparisons.append({
                        'teammate': teammate_races['driverRef'].iloc[0],
                        'races': len(common_races),
                        'win_percentage': win_percentage,
                        'elo_diff': avg_elo_diff if abs(avg_elo_diff) > 0.05 else 0.0
                    })

        return sorted(comparisons, key=lambda x: x['races'], reverse=True)[:5]

    def create_era_performance_chart(self, driver_data):
        """Create a bar chart showing average ELO rating by era (decade)."""
        driver_data = driver_data.copy()
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

    def create_comparison_chart(self, comparison_data):
        """Create a line chart comparing multiple drivers' ELO progression."""
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
        
        return fig
