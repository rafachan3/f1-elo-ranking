import pandas as pd
from itertools import combinations
import numpy as np
from scipy.stats import norm


# Constants
BASE_ELO = 1500
MAX_K_FACTOR = 32 # Maximum K-factor for new drivers
MIN_K_FACTOR = 16 # Minimum K-factor for experienced drivers
RACES_THRESHOLD = 50  # Number of races after which K-factor starts decreasing
MIN_RACES_FOR_ESTABLISHED = 20  # Minimum races for "established" rating
CONFIDENCE_LEVEL = 0.95  # For confidence interval calculation

def calculate_k_factor(driver_races, race_year):
    """
    Calculate dynamic K-factor based on driver experience and race era
    """
    # Decrease K-factor as driver gains experience
    experience_factor = max(MIN_K_FACTOR, 
                          MAX_K_FACTOR * (1 - min(1, driver_races / RACES_THRESHOLD)))
    
    # Adjust K-factor for historical races (less reliable data)
    era_factor = 0.8 if race_year < 1970 else 1.0
    
    return experience_factor * era_factor

def calculate_expected_score(rating_a, rating_b):
    """Calculate expected score between two ratings."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_elo(rating, expected, actual, k_factor):
    """Update Elo rating based on expected and actual results."""
    return rating + k_factor * (actual - expected)

def calculate_confidence_interval(rating, n_races, rating_volatility, year_span):
    """
    Calculate confidence interval for a driver's rating
    
    Parameters:
    - rating: Current ELO rating
    - n_races: Number of races participated in
    - rating_volatility: Standard deviation of rating changes
    - year_span: Number of years between first and last race
    
    Returns:
    - lower_bound, upper_bound
    """
    # Base standard error calculation
    base_se = 200 / np.sqrt(max(1, n_races))  # 200 is chosen as a scaling factor
    
    # Adjust for rating volatility
    volatility_factor = 1 + (rating_volatility / 100)  # Normalize volatility impact
    
    # Adjust for historical uncertainty
    history_factor = 1 + (year_span / 50)  # Increase uncertainty for longer careers
    
    # Combined standard error
    adjusted_se = base_se * volatility_factor * history_factor
    
    # Calculate confidence interval
    z_score = norm.ppf((1 + CONFIDENCE_LEVEL) / 2)
    margin = z_score * adjusted_se
    
    return rating - margin, rating + margin

def main():
    # Load datasets
    circuits = pd.read_csv('./data/circuits.csv')
    constructors = pd.read_csv('./data/constructors.csv')
    drivers = pd.read_csv('./data/drivers.csv')
    qualifying = pd.read_csv('./data/qualifying.csv')
    races = pd.read_csv('./data/races.csv')
    results = pd.read_csv('./data/results.csv')
    sprint_results = pd.read_csv('./data/sprint_results.csv')
    status = pd.read_csv('./data/status.csv')

    races = races[races['name'] != 'Indianapolis 500']

    # Initialize ratings dictionary
    ratings = {driver_id: BASE_ELO for driver_id in drivers['driverId']}
    driver_race_counts = {} # Initialize driver race counts for K-factor calculation
    rating_histories = {driver_id: [] for driver_id in drivers['driverId']}
    driver_first_year = {}
    driver_last_year = {}

    # Create status mapping
    status_mapping = dict(zip(status['statusId'], status['status']))

    # Sort races by year and round to ensure proper chronological order
    races_sorted = races.sort_values(by=["year", "round"])

    # Process races in chronological order
    race_results = results[['raceId', 'driverId', 'constructorId', 'positionOrder', 'statusId', 'grid']]

    for race_id in races_sorted["raceId"]:
        race_year = races_sorted[races_sorted['raceId'] == race_id]['year'].iloc[0]
        race_data = race_results[race_results['raceId'] == race_id]

        # Skip if race_id not in filtered races
        if race_id not in races['raceId'].values:
            continue

        # Get race data and initialize weight column
        race_data = race_results[race_results['raceId'] == race_id].copy()
        race_data['weight'] = 1.0

        # Special handling for shortened races
        if ((race_year == 1976 and races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0] == 'Japanese Grand Prix') or
            (race_year == 1991 and races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0] == 'Australian Grand Prix') or
            (race_year == 2009 and races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0] == 'Malaysian Grand Prix') or
            (race_year == 2021 and races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0] == 'Belgian Grand Prix')):
            race_data['weight'] = 0.5
        
        # Group by constructor to find teammates
        for constructor_id, group in race_data.groupby('constructorId'):
            if len(group) < 2:
                continue  # Skip if less than two drivers for the constructor

            # Update race counts for K-factor calculation and year tracking
            for driver_id in group['driverId']:
                driver_race_counts[driver_id] = driver_race_counts.get(driver_id, 0) + 1

                if driver_id not in driver_first_year:
                    driver_first_year[driver_id] = race_year
                driver_last_year[driver_id] = race_year

            # Pairwise comparisons among teammates
            for row_a, row_b in combinations(group.itertuples(index=False), 2):
                driver_a, driver_b = row_a.driverId, row_b.driverId
                rating_a, rating_b = ratings[driver_a], ratings[driver_b]

                # Calculate dynamic K-factors
                k_factor_a = calculate_k_factor(driver_race_counts[driver_a], race_year)
                k_factor_b = calculate_k_factor(driver_race_counts[driver_b], race_year)

                # Check statuses
                status_a = status_mapping[row_a.statusId]
                status_b = status_mapping[row_b.statusId]

                # Determine if drivers are penalized
                penalized_status = {3, 4, 20}  # accident, collision, spun off
                is_penalized_a = row_a.statusId in penalized_status
                is_penalized_b = row_b.statusId in penalized_status

                # Actual scores for penalized drivers
                if is_penalized_a and 'Finished' in status_b:
                    actual_score_a = 0
                    actual_score_b = 1
                elif is_penalized_b and 'Finished' in status_a:
                    actual_score_a = 1
                    actual_score_b = 0
                elif is_penalized_a and is_penalized_b:
                    continue  # Skip if both are penalized (no valid comparison)
                else:
                    # Normal comparison for finished drivers
                    actual_score_a = 1 if row_a.positionOrder < row_b.positionOrder else 0
                    actual_score_b = 1 - actual_score_a

                # Calculate expected scores
                expected_a = calculate_expected_score(rating_a, rating_b)
                expected_b = 1 - expected_a

                # Get race weight and update ratings
                race_weight = getattr(row_a, 'weight', 1.0)
                weighted_k_a = k_factor_a * race_weight
                weighted_k_b = k_factor_b * race_weight

                # Update ratings
                new_rating_a = update_elo(rating_a, expected_a, actual_score_a, weighted_k_a)
                new_rating_b = update_elo(rating_b, expected_b, actual_score_b, weighted_k_b)
                
                # Store ratings history
                rating_histories[driver_a].append(new_rating_a)
                rating_histories[driver_b].append(new_rating_b)
                
                # Update current ratings
                ratings[driver_a] = new_rating_a
                ratings[driver_b] = new_rating_b

    # Calculate final statistics and confidence intervals
    final_stats = []
    confidence_widths = []  # To collect all widths for normalization
    for driver_id, rating in ratings.items():
        n_races = driver_race_counts.get(driver_id, 0)
        
        # Skip drivers with no races
        if n_races == 0:
            continue
        
        # Calculate rating volatility
        rating_history = rating_histories[driver_id]
        rating_volatility = np.std(rating_history) if len(rating_history) > 1 else 0
        
        # Calculate year span
        year_span = (driver_last_year.get(driver_id, 2024) - 
                    driver_first_year.get(driver_id, 2024))
        
        # Calculate confidence interval
        lower_bound, upper_bound = calculate_confidence_interval(
            rating, n_races, rating_volatility, year_span
        )
        confidence_widths.append(upper_bound - lower_bound)

    # Calculate min and max widths for normalization
    min_width = min(confidence_widths)
    max_width = max(confidence_widths)
    width_range = max_width - min_width

    # Function to calculate confidence score (0-100)
    def calculate_confidence_score(width):
        # Invert the scale so narrower intervals get higher scores
        normalized_width = (max_width - width) / width_range
        # Convert to 0-100 scale
        return round(normalized_width * 100)
    
        # Function to convert score to grade
    def get_confidence_grade(score):
        if score >= 90: return 'A+'
        elif score >= 80: return 'A'
        elif score >= 70: return 'B+'
        elif score >= 60: return 'B'
        elif score >= 50: return 'C+'
        elif score >= 40: return 'C'
        elif score >= 30: return 'D+'
        elif score >= 20: return 'D'
        else: return 'F'

    # Second pass to create final statistics
    for driver_id, rating in ratings.items():
        n_races = driver_race_counts.get(driver_id, 0)
        if n_races == 0:
            continue
            
        rating_history = rating_histories[driver_id]
        rating_volatility = np.std(rating_history) if len(rating_history) > 1 else 0
        year_span = (driver_last_year.get(driver_id, 2024) - 
                    driver_first_year.get(driver_id, 2024))
        
        lower_bound, upper_bound = calculate_confidence_interval(
            rating, n_races, rating_volatility, year_span
        )
        
        width = upper_bound - lower_bound
        confidence_score = calculate_confidence_score(width)
        confidence_grade = get_confidence_grade(confidence_score)
        
        final_stats.append({
            'Driver': f"{drivers[drivers['driverId'] == driver_id]['forename'].iloc[0]} "
                     f"{drivers[drivers['driverId'] == driver_id]['surname'].iloc[0]}",
            'Elo Rating': rating,
            'Lower Bound': round(lower_bound, 1),
            'Upper Bound': round(upper_bound, 1),
            'Confidence Score': confidence_score,
            'Reliability Grade': confidence_grade,
            'Race Count': n_races,
            'Rating Volatility': round(rating_volatility, 1),
            'Is Established': n_races >= MIN_RACES_FOR_ESTABLISHED,
            'First Year': driver_first_year.get(driver_id),
            'Last Year': driver_last_year.get(driver_id),
            'Career Span': year_span
        })
    
    # Create DataFrame and sort by rating
    rankings_df = pd.DataFrame(final_stats)
    rankings_df = rankings_df.sort_values('Elo Rating', ascending=False)
    
    # Save rankings
    rankings_df.to_csv('./f1_driver_elo_rankings_improved.csv', index=False)

    
    print("Improved Elo rankings have been calculated and saved.")

if __name__ == "__main__":
    main()
