import pandas as pd
from itertools import combinations
from driver import Driver
from elo_calculator import EloCalculator
from confidence_calculator import ConfidenceCalculator

class F1DataProcessor:
    def __init__(self):
        self.elo_calculator = EloCalculator()
        self.confidence_calculator = ConfidenceCalculator()
        self.drivers_dict = {}
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
        
        # Initialize driver objects
        for driver_id in self.drivers['driverId']:
            self.drivers_dict[driver_id] = Driver(driver_id, self.elo_calculator.BASE_ELO)
            
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
                    driver = self.drivers_dict[driver_id]
                    driver.increment_race_count()
                    driver.update_years(race_year)

                for row_a, row_b in combinations(group.itertuples(index=False), 2):
                    self._process_driver_pair(row_a, row_b, race_year)

    def _process_driver_pair(self, row_a, row_b, race_year):
        driver_a = self.drivers_dict[row_a.driverId]
        driver_b = self.drivers_dict[row_b.driverId]

        k_factor_a = self.elo_calculator.calculate_k_factor(driver_a.race_count, race_year)
        k_factor_b = self.elo_calculator.calculate_k_factor(driver_b.race_count, race_year)

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

        expected_a = self.elo_calculator.calculate_expected_score(driver_a.rating, driver_b.rating)
        expected_b = 1 - expected_a

        race_weight = getattr(row_a, 'weight', 1.0)
        weighted_k_a = k_factor_a * race_weight
        weighted_k_b = k_factor_b * race_weight

        new_rating_a = self.elo_calculator.update_elo(driver_a.rating, expected_a, actual_score_a, weighted_k_a)
        new_rating_b = self.elo_calculator.update_elo(driver_b.rating, expected_b, actual_score_b, weighted_k_b)

        driver_a.update_rating(new_rating_a)
        driver_b.update_rating(new_rating_b)

    def calculate_rankings(self):
        final_stats = []
        confidence_widths = []

        # Calculate confidence widths first
        for driver in self.drivers_dict.values():
            if driver.race_count == 0:
                continue

            lower_bound, upper_bound = driver.get_confidence_interval(self.confidence_calculator)
            confidence_widths.append(upper_bound - lower_bound)
            
        min_width = min(confidence_widths)
        max_width = max(confidence_widths)

        # Generate final statistics
        for driver in self.drivers_dict.values():
            if driver.race_count == 0:
                continue

            lower_bound, upper_bound = driver.get_confidence_interval(self.confidence_calculator)
            width = upper_bound - lower_bound
            confidence_score = self.confidence_calculator.calculate_confidence_score(width, max_width, min_width)
            confidence_grade = self.confidence_calculator.get_confidence_grade(confidence_score)

            final_stats.append(
                driver.to_stats_dict(
                    self.elo_calculator,
                    self.confidence_calculator,
                    self.drivers,
                    confidence_score,
                    confidence_grade
                )
            )

        rankings_df = pd.DataFrame(final_stats)
        return rankings_df.sort_values('Elo Rating', ascending=False)
