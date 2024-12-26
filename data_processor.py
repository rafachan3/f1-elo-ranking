import pandas as pd
from itertools import combinations
import numpy as np
from driver import Driver
from elo_calculator import EloCalculator

class F1DataProcessor:
    def __init__(self):
        self.calculator = EloCalculator()
        self.ratings = {}
        self.driver_race_counts = {}
        self.rating_histories = {}
        self.driver_first_year = {}
        self.driver_last_year = {}
        self.status_mapping = {}
        
    def load_data(self, data_path='./data'):
        self.circuits = pd.read_csv(f'{data_path}/circuits.csv')
        self.constructors = pd.read_csv(f'{data_path}/constructors.csv')
        self.drivers = pd.read_csv(f'{data_path}/drivers.csv')
        self.qualifying = pd.read_csv(f'{data_path}/qualifying.csv')
        self.races = pd.read_csv(f'{data_path}/races.csv')
        self.results = pd.read_csv(f'{data_path}/results.csv')
        self.sprint_results = pd.read_csv(f'{data_path}/sprint_results.csv')
        self.status = pd.read_csv(f'{data_path}/status.csv')

        self.races = self.races[self.races['name'] != 'Indianapolis 500']
        self.ratings = {driver_id: self.calculator.BASE_ELO for driver_id in self.drivers['driverId']}
        self.rating_histories = {driver_id: [] for driver_id in self.drivers['driverId']}
        self.status_mapping = dict(zip(self.status['statusId'], self.status['status']))

    def process_races(self):
        races_sorted = self.races.sort_values(by=["year", "round"])
        race_results = self.results[['raceId', 'driverId', 'constructorId', 'positionOrder', 'statusId', 'grid']]

        for race_id in races_sorted["raceId"]:
            race_year = races_sorted[races_sorted['raceId'] == race_id]['year'].iloc[0]
            
            if race_id not in self.races['raceId'].values:
                continue

            race_data = race_results[race_results['raceId'] == race_id].copy()
            race_data['weight'] = 1.0

            # Special handling for shortened races
            if ((race_year == 1976 and races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0] == 'Japanese Grand Prix') or
                (race_year == 1991 and races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0] == 'Australian Grand Prix') or
                (race_year == 2009 and races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0] == 'Malaysian Grand Prix') or
                (race_year == 2021 and races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0] == 'Belgian Grand Prix')):
                race_data['weight'] = 0.5

            for constructor_id, group in race_data.groupby('constructorId'):
                if len(group) < 2:
                    continue

                for driver_id in group['driverId']:
                    self.driver_race_counts[driver_id] = self.driver_race_counts.get(driver_id, 0) + 1
                    if driver_id not in self.driver_first_year:
                        self.driver_first_year[driver_id] = race_year
                    self.driver_last_year[driver_id] = race_year

                for row_a, row_b in combinations(group.itertuples(index=False), 2):
                    self._process_driver_pair(row_a, row_b, race_year)

    def _process_driver_pair(self, row_a, row_b, race_year):
        driver_a, driver_b = row_a.driverId, row_b.driverId
        rating_a, rating_b = self.ratings[driver_a], self.ratings[driver_b]

        k_factor_a = self.calculator.calculate_k_factor(self.driver_race_counts[driver_a], race_year)
        k_factor_b = self.calculator.calculate_k_factor(self.driver_race_counts[driver_b], race_year)

        status_a = self.status_mapping[row_a.statusId]
        status_b = self.status_mapping[row_b.statusId]

        penalized_status = {3, 4, 20}
        is_penalized_a = row_a.statusId in penalized_status
        is_penalized_b = row_b.statusId in penalized_status

        if is_penalized_a and 'Finished' in status_b:
            actual_score_a, actual_score_b = 0, 1
        elif is_penalized_b and 'Finished' in status_a:
            actual_score_a, actual_score_b = 1, 0
        elif is_penalized_a and is_penalized_b:
            return
        else:
            actual_score_a = 1 if row_a.positionOrder < row_b.positionOrder else 0
            actual_score_b = 1 - actual_score_a

        expected_a = self.calculator.calculate_expected_score(rating_a, rating_b)
        expected_b = 1 - expected_a

        race_weight = getattr(row_a, 'weight', 1.0)
        weighted_k_a = k_factor_a * race_weight
        weighted_k_b = k_factor_b * race_weight

        new_rating_a = self.calculator.update_elo(rating_a, expected_a, actual_score_a, weighted_k_a)
        new_rating_b = self.calculator.update_elo(rating_b, expected_b, actual_score_b, weighted_k_b)

        self.rating_histories[driver_a].append(new_rating_a)
        self.rating_histories[driver_b].append(new_rating_b)

        self.ratings[driver_a] = new_rating_a
        self.ratings[driver_b] = new_rating_b

    def calculate_rankings(self):
        final_stats = []
        confidence_widths = []

        for driver_id, rating in self.ratings.items():
            n_races = self.driver_race_counts.get(driver_id, 0)
            if n_races == 0:
                continue

            rating_history = self.rating_histories[driver_id]
            rating_volatility = np.std(rating_history) if len(rating_history) > 1 else 0
            year_span = (self.driver_last_year.get(driver_id, 2024) - 
                        self.driver_first_year.get(driver_id, 2024))

            lower_bound, upper_bound = self.calculator.calculate_confidence_interval(
                rating, n_races, rating_volatility, year_span)
            confidence_widths.append(upper_bound - lower_bound)

        min_width = min(confidence_widths)
        max_width = max(confidence_widths)
        width_range = max_width - min_width

        def calculate_confidence_score(width):
            normalized_width = (max_width - width) / width_range
            return round(normalized_width * 100)

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

        for driver_id, rating in self.ratings.items():
            n_races = self.driver_race_counts.get(driver_id, 0)
            if n_races == 0:
                continue

            rating_history = self.rating_histories[driver_id]
            rating_volatility = np.std(rating_history) if len(rating_history) > 1 else 0
            year_span = (self.driver_last_year.get(driver_id, 2024) - 
                        self.driver_first_year.get(driver_id, 2024))

            lower_bound, upper_bound = self.calculator.calculate_confidence_interval(
                rating, n_races, rating_volatility, year_span)

            width = upper_bound - lower_bound
            confidence_score = calculate_confidence_score(width)
            confidence_grade = get_confidence_grade(confidence_score)

            final_stats.append({
                'Driver': f"{self.drivers[self.drivers['driverId'] == driver_id]['forename'].iloc[0]} "
                         f"{self.drivers[self.drivers['driverId'] == driver_id]['surname'].iloc[0]}",
                'Elo Rating': rating,
                'Lower Bound': round(lower_bound, 1),
                'Upper Bound': round(upper_bound, 1),
                'Confidence Score': confidence_score,
                'Reliability Grade': confidence_grade,
                'Race Count': n_races,
                'Rating Volatility': round(rating_volatility, 1),
                'Is Established': n_races >= self.calculator.MIN_RACES_FOR_ESTABLISHED,
                'First Year': self.driver_first_year.get(driver_id),
                'Last Year': self.driver_last_year.get(driver_id),
                'Career Span': year_span
            })

        rankings_df = pd.DataFrame(final_stats)
        return rankings_df.sort_values('Elo Rating', ascending=False)
    