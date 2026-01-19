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
        """Create a clean chart showing ELO progression with team tenure indicated by background bands."""
        if 'elo_rating' not in team_data.columns:
            team_data = team_data.copy()
            team_data['elo_rating'] = team_data.groupby('team').cumcount() + 1500

        # F1 team colors - a curated palette for visual distinction
        team_colors = {
            # Current/Recent Teams
            'Red Bull': '#3671C6',
            'Ferrari': '#E8002D',
            'Mercedes': '#27F4D2',
            'McLaren': '#FF8000',
            'Aston Martin': '#229971',
            'Alpine F1 Team': '#FF87BC',
            'Williams': '#64C4FF',
            'RB F1 Team': '#6692FF',
            'Sauber': '#52E252',
            'Haas F1 Team': '#B6BABD',
            # Historical Teams
            'Lotus': '#FFD700',
            'Brabham': '#2E8B57',
            'Tyrrell': '#00008B',
            'BRM': '#006400',
            'Cooper': '#4169E1',
            'Renault': '#FFE200',
            'Jordan': '#FFD700',
            'BAR': '#FFFFFF',
            'Benetton': '#00D2BE',
            'Ligier': '#0066CC',
            'Minardi': '#000000',
            'Arrows': '#FF6600',
            'March': '#FF4500',
            'Surtees': '#8B0000',
            'Shadow': '#1C1C1C',
            'Prost': '#1E90FF',
            'Sauber': '#006F62',
            'Jaguar': '#0A5C36',
            'Toyota': '#CC0000',
            'Honda': '#FFFFFF',
            'Toro Rosso': '#1E41FF',
            'Racing Point': '#F596C8',
            'Force India': '#FF5F1F',
            'Lotus F1': '#B6860E',
            'Caterham': '#00994C',
            'Marussia': '#6E0000',
            'HRT': '#A49E8C',
            'Virgin': '#C82D2D',
            'Alfa Romeo': '#A50F2D',
            'AlphaTauri': '#2B4562',
        }
        
        # Generate distinct colors for unknown teams using a pleasing palette
        default_palette = [
            '#E63946', '#F4A261', '#2A9D8F', '#264653', '#E9C46A',
            '#8338EC', '#3A86FF', '#06D6A0', '#EF476F', '#FFD166',
            '#118AB2', '#073B4C', '#F72585', '#7209B7', '#560BAD'
        ]
        
        # Sort data by year to create continuous timeline
        team_data = team_data.sort_values('year').copy()
        
        # Create grouped data by year - get average ELO and primary team per year
        team_summary = team_data.groupby(['year', 'team'])['elo_rating'].mean().reset_index()
        team_summary = team_summary.sort_values('year')
        
        # Get the primary team for each year (the one with most races that year)
        year_team_counts = team_data.groupby(['year', 'team']).size().reset_index(name='race_count')
        primary_team_per_year = year_team_counts.loc[year_team_counts.groupby('year')['race_count'].idxmax()]
        primary_team_per_year = primary_team_per_year[['year', 'team']].sort_values('year')
        
        # Get all unique teams in chronological order of first appearance
        teams_in_order = []
        for _, row in primary_team_per_year.iterrows():
            if row['team'] not in teams_in_order:
                teams_in_order.append(row['team'])
        
        # Assign colors to teams
        color_map = {}
        color_idx = 0
        for team in teams_in_order:
            # Try partial matching for team names
            matched = False
            for key, color in team_colors.items():
                if key.lower() in team.lower() or team.lower() in key.lower():
                    color_map[team] = color
                    matched = True
                    break
            if not matched:
                color_map[team] = default_palette[color_idx % len(default_palette)]
                color_idx += 1

        # Calculate y-axis range with padding
        y_min = team_summary['elo_rating'].min()
        y_max = team_summary['elo_rating'].max()
        y_padding = (y_max - y_min) * 0.15 if y_max != y_min else 50
        
        fig = go.Figure()
        
        # Identify team tenure periods (consecutive years with same primary team)
        tenure_periods = []
        current_team = None
        start_year = None
        
        for _, row in primary_team_per_year.iterrows():
            if row['team'] != current_team:
                if current_team is not None:
                    tenure_periods.append({
                        'team': current_team,
                        'start': start_year,
                        'end': prev_year
                    })
                current_team = row['team']
                start_year = row['year']
            prev_year = row['year']
        
        # Add the last tenure period
        if current_team is not None:
            tenure_periods.append({
                'team': current_team,
                'start': start_year,
                'end': prev_year
            })
        
        # Add vertical background bands for each team tenure (non-overlapping)
        for tenure in tenure_periods:
            color = color_map[tenure['team']]
            hex_color = color.lstrip('#')
            if len(hex_color) == 6:
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            else:
                r, g, b = 100, 100, 100
            
            # Add vertical rectangle for this tenure period
            fig.add_vrect(
                x0=tenure['start'] - 0.5,
                x1=tenure['end'] + 0.5,
                fillcolor=f'rgba({r},{g},{b},0.12)',
                layer='below',
                line_width=0,
            )
        
        # Add team-colored line segments connecting to show career flow
        all_years_elo = team_summary.groupby('year')['elo_rating'].mean().reset_index().sort_values('year')
        
        # Add a subtle connecting line showing overall progression
        fig.add_trace(go.Scatter(
            x=all_years_elo['year'],
            y=all_years_elo['elo_rating'],
            mode='lines',
            line=dict(color='rgba(150,150,150,0.4)', width=2),
            name='Career Path',
            hoverinfo='skip',
            showlegend=False
        ))
        
        # Add team-colored line segments with markers
        for team in teams_in_order:
            team_df = team_summary[team_summary['team'] == team].sort_values('year')
            if team_df.empty:
                continue
                
            color = color_map[team]
            
            # Add the main line with markers for this team
            fig.add_trace(go.Scatter(
                x=team_df['year'],
                y=team_df['elo_rating'],
                mode='lines+markers',
                name=team,
                line=dict(color=color, width=3),
                marker=dict(
                    size=10,
                    color=color,
                    line=dict(width=2, color='white'),
                    symbol='circle'
                ),
                hovertemplate=(
                    f'<b>{team}</b><br>' +
                    'Year: %{x}<br>' +
                    'ELO: %{y:.0f}<extra></extra>'
                )
            ))
        
        fig.update_layout(
            title=dict(
                text=f'<b>Career Journey by Team</b><br><sup>{driver_name}</sup>',
                font=dict(size=16),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title='Year',
            yaxis_title='ELO Rating',
            hovermode='closest',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(0,0,0,0.1)',
                borderwidth=1,
                font=dict(size=11)
            ),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.15)',
                dtick=2 if len(team_summary['year'].unique()) > 10 else 1,
                tickangle=0
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.15)',
                range=[y_min - y_padding, y_max + y_padding]
            ),
            margin=dict(t=80, b=60)
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
