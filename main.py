import pandas as pd
from itertools import combinations
import numpy as np

# Constants
BASE_ELO = 1500
MAX_K_FACTOR = 32 # Maximum K-factor for new drivers
MIN_K_FACTOR = 16 # Minimum K-factor for experienced drivers
RACES_THRESHOLD = 50  # Number of races after which K-factor starts decreasing

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

def process_special_races(race_data, races_df, race_id):
    """
    Special handling for various race scenarios
    Returns modified race data with adjusted driver participations
    """
    race_info = races_df[races_df['raceId'] == race_id].iloc[0]
    race_year = race_info['year']
    race_name = race_info['name']
    
    # Create weight column
    race_data = race_data.copy()
    race_data['weight'] = 1.0
    
    # Indianapolis 500 handling
    if race_name == 'Indianapolis 500':
        race_data = handle_shared_drives(race_data)
    
    # Pre-qualifying era (1989-1992)
    elif 1989 <= race_year <= 1992:
        # Only consider drivers who made the actual race
        race_data = race_data[race_data['grid'] > 0]
    
    # Shared drives era (pre-1970)
    elif race_year < 1970:
        race_data = handle_shared_drives(race_data)
    
    # Special shortened races
    elif (race_year == 1976 and race_name == 'Japanese Grand Prix') or \
         (race_year == 1991 and race_name == 'Australian Grand Prix') or \
         (race_year == 2009 and race_name == 'Malaysian Grand Prix') or \
         (race_year == 2021 and race_name == 'Belgian Grand Prix'):
        race_data['weight'] = 0.5
    
    return race_data

def handle_shared_drives(race_data):
    """
    Handle races where multiple drivers shared the same car
    """
    return race_data.groupby('grid').agg({
        'driverId': 'first',  # Take primary driver
        'constructorId': 'first',
        'positionOrder': 'min',  # Best position achieved
        'statusId': 'last',  # Final status
        'weight': 'first'  # Maintain weight
    }).reset_index()

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

    # Initialize ratings dictionary
    ratings = {driver_id: BASE_ELO for driver_id in drivers['driverId']}

    # Initialize driver race counts for K-factor calculation
    driver_race_counts = {}

    # Create status mapping
    status_mapping = dict(zip(status['statusId'], status['status']))

    # Sort races by year and round to ensure proper chronological order
    races_sorted = races.sort_values(by=["year", "round"])

    # Process races in chronological order
    race_results = results[['raceId', 'driverId', 'constructorId', 'positionOrder', 'statusId', 'grid']]

    for race_id in races_sorted["raceId"]:
        race_year = races_sorted[races_sorted['raceId'] == race_id]['year'].iloc[0]
        race_data = race_results[race_results['raceId'] == race_id]

        # Apply special race handling
        race_data = process_special_races(race_data, races_sorted, race_id)

        # Group by constructor to find teammates
        for constructor_id, group in race_data.groupby('constructorId'):
            if len(group) < 2:
                continue  # Skip if less than two drivers for the constructor

            # Update race counts for K-factor calculation
            for driver_id in group['driverId']:
                driver_race_counts[driver_id] = driver_race_counts.get(driver_id, 0) + 1

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

                # Update ratings
                ratings[driver_a] = update_elo(rating_a, expected_a, actual_score_a, k_factor_a)
                ratings[driver_b] = update_elo(rating_b, expected_b, actual_score_b, k_factor_b)

                # Get race weight and update ratings
                race_weight = getattr(row_a, 'weight', 1.0)
                weighted_k_a = k_factor_a * race_weight
                weighted_k_b = k_factor_b * race_weight
                
                ratings[driver_a] = update_elo(rating_a, expected_a, actual_score_a, weighted_k_a)
                ratings[driver_b] = update_elo(rating_b, expected_b, actual_score_b, weighted_k_b)
                
    # Combine driver names
    drivers['fullName'] = drivers['forename'] + ' ' + drivers['surname']
    driver_names = dict(zip(drivers['driverId'], drivers['fullName']))

    # Sort drivers by Elo rating
    final_ratings = [(driver_names[driver_id], rating, driver_race_counts.get(driver_id, 0)) 
                     for driver_id, rating in ratings.items()]
    final_ratings.sort(key=lambda x: x[1], reverse=True)

    # Save rankings to CSV
    rankings_df = pd.DataFrame(final_ratings, 
                             columns=['Driver', 'Elo Rating', 'Race Count'])
    rankings_df.to_csv('./f1_driver_elo_rankings_improved.csv', index=False)

    print("Elo rankings have been calculated and saved to 'f1_driver_elo_rankings.csv'.")

if __name__ == "__main__":
    main()
