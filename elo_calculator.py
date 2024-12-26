import numpy as np
from scipy.stats import norm

class EloCalculator:
    def __init__(self):
        self.BASE_ELO = 1500
        self.MAX_K_FACTOR = 32
        self.MIN_K_FACTOR = 16
        self.RACES_THRESHOLD = 50
        self.MIN_RACES_FOR_ESTABLISHED = 20
        self.CONFIDENCE_LEVEL = 0.95

    def calculate_k_factor(self, driver_races, race_year):
        experience_factor = max(self.MIN_K_FACTOR, 
                              self.MAX_K_FACTOR * (1 - min(1, driver_races / self.RACES_THRESHOLD)))
        era_factor = 0.8 if race_year < 1970 else 1.0
        return experience_factor * era_factor

    def calculate_expected_score(self, rating_a, rating_b):
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update_elo(self, rating, expected, actual, k_factor):
        return rating + k_factor * (actual - expected)

    def calculate_confidence_interval(self, rating, n_races, rating_volatility, year_span):
        base_se = 200 / np.sqrt(max(1, n_races))
        volatility_factor = 1 + (rating_volatility / 100)
        history_factor = 1 + (year_span / 50)
        adjusted_se = base_se * volatility_factor * history_factor
        z_score = norm.ppf((1 + self.CONFIDENCE_LEVEL) / 2)
        margin = z_score * adjusted_se
        return rating - margin, rating + margin