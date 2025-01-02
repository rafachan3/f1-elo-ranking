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


        # Define absolute non-start status IDs
        self.non_start_status_ids = {
            73,  # Injured
            77,  # 107% Rule
            81,  # Did not qualify
            82,  # Injury
            89,  # Safety concerns before race
            96,  # Excluded before race
            97,  # Did not prequalify
            104  # Fatal accident
        }

        # Define withdrawal status ID
        self.withdrawal_status_ids = {
            54,  # Withdrew
        }

        # Define Indianapolis 500 race IDs
        self.indy_500_race_ids = {748, 757, 768, 778, 786, 794, 800, 809, 818, 826, 835}
        
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

        print("Creating driver objects...")
        # Initialize driver objects
        for _, driver_row in self.drivers.iterrows():
            driver_id = driver_row['driverId']
            self.drivers_dict[driver_id] = Driver(driver_id, self.elo_calculator.BASE_ELO)
            
        self.status_mapping = dict(zip(self.status['statusId'], self.status['status']))

    def get_driver_elo_progression(self, driver_id):
        """Get the ELO rating progression for a specific driver."""
        driver = self.drivers_dict.get(driver_id)
        
        if not driver or driver.first_year is None or driver.last_year is None:
            print(f"Driver {driver_id} not found or missing year data")
            return pd.DataFrame(columns=['year', 'driverId', 'elo_rating'])
        
        # Create progression data
        years = list(range(driver.first_year, driver.last_year + 1))
        num_years = len(years)
        
        # Ensure we have enough ratings
        if len(driver.rating_history) < num_years:
            # If we don't have enough ratings, pad with the base ELO
            ratings = [self.elo_calculator.BASE_ELO] * (num_years - len(driver.rating_history))
            ratings.extend(driver.rating_history)
        else:
            # Take the last N ratings where N is number of years
            ratings = driver.rating_history[-num_years:]
        
        # Verify array lengths
        if len(years) != len(ratings):
            print(f"Warning: Mismatch in array lengths for driver {driver_id}")
            print(f"Years: {len(years)}, Ratings: {len(ratings)}")
            # Adjust ratings array if necessary
            if len(ratings) > len(years):
                ratings = ratings[-len(years):]
            else:
                ratings.extend([ratings[-1]] * (len(years) - len(ratings)))
        
        data = {
            'year': years,
            'driverId': [driver_id] * len(years),
            'elo_rating': ratings
        }
        
        return pd.DataFrame(data)

    def get_all_drivers_elo_progression(self):
        """Get ELO progression for all drivers."""
        all_progressions = []
        
        for driver_id, driver in self.drivers_dict.items():
            if driver.race_count > 0:  # Only include drivers who participated in races
                progression = self.get_driver_elo_progression(driver_id)
                if not progression.empty:
                    all_progressions.append(progression)
        
        if all_progressions:
            return pd.concat(all_progressions, ignore_index=True)
        return pd.DataFrame(columns=['year', 'driverId', 'elo_rating'])

    def process_races(self):
        print("Starting race processing")
        races_sorted = self.races.sort_values(by=["year", "round"])
        race_results = self.results[['raceId', 'driverId', 'constructorId', 'positionOrder', 'statusId', 'grid', 'position', 'laps']]

        # Calculate races per season
        races_per_season = self.races.groupby('year').size()

        for race_id in races_sorted["raceId"]:
            race_year = races_sorted[races_sorted['raceId'] == race_id]['year'].iloc[0]
            race_name = races_sorted[races_sorted['raceId'] == race_id]['name'].iloc[0]
            season_races = races_per_season[race_year]

            # Filter out Indianapolis 500 races using specific raceIds
            if race_id in self.indy_500_race_ids:
                continue

            race_data = race_results[race_results['raceId'] == race_id].copy()
            race_data['weight'] = 1.0

            # Special handling for shortened races
            if ((race_year == 1976 and race_name == 'Japanese Grand Prix') or
                (race_year == 1991 and race_name == 'Australian Grand Prix') or
                (race_year == 2009 and race_name == 'Malaysian Grand Prix') or
                (race_year == 2021 and race_name == 'Belgian Grand Prix')):
                race_data['weight'] = 0.5

            # First filter out definite non-starts
            race_data = race_data[~race_data['statusId'].isin(self.non_start_status_ids)]

            # Handle withdrawals based on era and circumstances
            withdrawal_mask = race_data['statusId'].isin(self.withdrawal_status_ids)
            if withdrawal_mask.any():
                era_adjustments = (
                    # Pre-1970s withdrawals with grid position likely mean race start
                    ((race_year < 1970) & (race_data['grid'] > 0)) |
                    # In modern era, must have completed at least one lap to count
                    ((race_year >= 1970) & (race_data['laps'] > 0))
                )
                race_data = race_data[~withdrawal_mask | era_adjustments]
                
            # Increment race count for ALL drivers in this race
            processed_drivers = set()
            for _, row in race_data.iterrows():
                driver_id = row['driverId']
                if driver_id not in processed_drivers:
                    driver = self.drivers_dict[driver_id]
                    driver.increment_race_count()
                    driver.update_years(race_year)
                    processed_drivers.add(driver_id)

            # Do teammate comparisons only where possible
            for constructor_id, group in race_data.groupby('constructorId'):
                if len(group) < 2:
                    continue  # Only skips teammate comparison, not race counting

                for row_a, row_b in combinations(group.itertuples(index=False), 2):
                    self._process_driver_pair(row_a, row_b, race_year, season_races)

    def _process_driver_pair(self, row_a, row_b, race_year, season_races):
        driver_a = self.drivers_dict[row_a.driverId]
        driver_b = self.drivers_dict[row_b.driverId]

        k_factor_a = self.elo_calculator.calculate_k_factor(
            driver_a.race_count, 
            race_year,
            season_races
        )
        k_factor_b = self.elo_calculator.calculate_k_factor(
            driver_b.race_count, 
            race_year,
            season_races
        )

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
