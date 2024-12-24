import pandas as pd
from itertools import combinations
import numpy as np

# Constants
BASE_ELO = 1500
K_FACTOR = 32  # Sensitivity of Elo updates

# Helper Functions
def calculate_expected_score(rating_a, rating_b):
    """Calculate expected score between two ratings."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_elo(rating, expected, actual):
    """Update Elo rating based on expected and actual results."""
    return rating + K_FACTOR * (actual - expected)

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
print(f"Ratings initialized for {len(ratings)} drivers.")

# Create status mapping
status_mapping = dict(zip(status['statusId'], status['status']))

# Sort races by year and round to ensure proper chronological order
races_sorted = races.sort_values(by=["year", "round"])

# Process races in chronological order
race_results = results[['raceId', 'driverId', 'constructorId', 'positionOrder', 'statusId']]
for race_id in races_sorted["raceId"]:
    race_data = race_results[race_results['raceId'] == race_id]

    # Group by constructor to find teammates
    for constructor_id, group in race_data.groupby('constructorId'):
        if len(group) < 2:
            continue  # Skip if less than two drivers for the constructor

        # Pairwise comparisons among teammates
        for row_a, row_b in combinations(group.itertuples(index=False), 2):
            driver_a, driver_b = row_a.driverId, row_b.driverId
            rating_a, rating_b = ratings[driver_a], ratings[driver_b]

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
            ratings[driver_a] = update_elo(rating_a, expected_a, actual_score_a)
            ratings[driver_b] = update_elo(rating_b, expected_b, actual_score_b)

# Combine driver names
drivers['fullName'] = drivers['forename'] + ' ' + drivers['surname']
driver_names = dict(zip(drivers['driverId'], drivers['fullName']))

# Sort drivers by Elo rating
final_ratings = [(driver_names[driver_id], rating) for driver_id, rating in ratings.items()]
final_ratings.sort(key=lambda x: x[1], reverse=True)

# Save rankings to CSV
rankings_df = pd.DataFrame(final_ratings, columns=['Driver', 'Elo Rating'])
rankings_df.to_csv('./f1_driver_elo_rankings.csv', index=False)

print("Elo rankings have been calculated and saved to 'f1_driver_elo_rankings.csv'.")