import numpy as np
from scipy.stats import norm

class EloCalculator:
    """
    Calculator for Formula 1 driver ELO ratings with configurable parameters.
    """
    
    # Base ELO parameters
    BASE_ELO = 1500
    MIN_RACES_FOR_ESTABLISHED = 20
    
    # Base K-factors
    MAX_K_FACTOR = 40  # Higher than chess due to F1's higher variability
    MIN_K_FACTOR = 20  # Higher than chess to allow for performance evolution
    
    # Experience thresholds
    ROOKIE_RACES = 10      # Initial high-volatility period
    LEARNING_RACES = 25    # Rapid development period
    ESTABLISHED_RACES = 50 # Considered experienced
    
    # Era factors based on data reliability and standardization
    ERA_FACTORS = {
        (1950, 1959): 0.7,  # Limited data, less standardized
        (1960, 1969): 0.8,  # Improving standardization
        (1970, 1979): 0.9,  # Modern record-keeping begins
        (1980, None): 1.0   # Full modern era
    }
    
    # Season length factors
    MIN_SEASON_RACES = 7    # Minimum races in 1950
    MAX_SEASON_RACES = 22   # Maximum races in modern era

    def get_era_factor(self, year):
        """Get the era adjustment factor for a given year."""
        for (start, end), factor in self.ERA_FACTORS.items():
            if end is None and year >= start:
                return factor
            if start <= year <= end:
                return factor
        return 1.0  # Default for any year not explicitly covered

    def calculate_k_factor(self, driver_races, race_year, season_races=None):
        """
        Calculate the K-factor for a driver based on experience and era.
        
        Args:
            driver_races: Number of races completed by driver
            race_year: Year of the race
            season_races: Number of races in the season (optional)
            
        Returns:
            float: The calculated K-factor for the given conditions
        """
        # 1. Calculate base K-factor using experience curve
        if driver_races <= self.ROOKIE_RACES:
            # Rookie phase - maximum K-factor
            experience_factor = 1.0
        elif driver_races <= self.LEARNING_RACES:
            # Learning phase - rapid decay
            progress = (driver_races - self.ROOKIE_RACES) / (self.LEARNING_RACES - self.ROOKIE_RACES)
            experience_factor = 1.0 - (progress * 0.6)  # Decay to 0.4 during learning phase
        else:
            # Experience phase - gradual decay
            progress = min(1.0, (driver_races - self.LEARNING_RACES) / 
                         (self.ESTABLISHED_RACES - self.LEARNING_RACES))
            experience_factor = 0.4 - (progress * 0.2)  # Decay from 0.4 to 0.2
            
        base_k = self.MAX_K_FACTOR * experience_factor
        base_k = max(self.MIN_K_FACTOR, base_k)
        
        # 2. Apply era factor
        era_factor = self.get_era_factor(race_year)
        
        # 3. Apply season length normalization if available
        season_factor = 1.0
        if season_races:
            season_factor = ((self.MAX_SEASON_RACES - season_races) / 
                           (self.MAX_SEASON_RACES - self.MIN_SEASON_RACES) * 0.2 + 0.8)
            
        return base_k * era_factor * season_factor

    def calculate_expected_score(self, rating_a, rating_b):
        """
        Calculate expected score for driver A against driver B.
        
        Args:
            rating_a: ELO rating of driver A
            rating_b: ELO rating of driver B
            
        Returns:
            float: Expected score for driver A (between 0 and 1)
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update_elo(self, rating, expected, actual, k_factor):
        """
        Update ELO rating based on expected and actual scores.
        
        Args:
            rating: Current ELO rating
            expected: Expected score from calculate_expected_score()
            actual: Actual score (1 for win, 0 for loss)
            k_factor: K-factor from calculate_k_factor()
            
        Returns:
            float: The new ELO rating
        """
        return rating + k_factor * (actual - expected)

