"""
Driver entity for ELO rating tracking.
"""
import numpy as np


class Driver:
    """
    Represents an F1 driver with ELO rating history.
    
    Attributes:
        driver_id: Unique identifier for the driver
        rating: Current ELO rating
        race_count: Number of races completed
        rating_history: List of historical ratings
        first_year: First year of racing
        last_year: Last year of racing
    """
    
    def __init__(self, driver_id, base_elo=1500):
        self.driver_id = driver_id
        self.rating = base_elo
        self.race_count = 0
        self.rating_history = []  # List of (year, race_id, rating) tuples
        self.first_year = None
        self.last_year = None
        self._current_race_year = None
        self._current_race_id = None
    
    def set_current_race(self, year, race_id):
        """Set the current race context for rating updates."""
        self._current_race_year = year
        self._current_race_id = race_id
    
    def update_rating(self, new_rating):
        """Update driver's rating and rating history with year/race context."""
        self.rating = new_rating
        self.rating_history.append((
            self._current_race_year,
            self._current_race_id,
            new_rating
        ))
        
    def update_years(self, race_year):
        """Update driver's first and last year."""
        if not self.first_year:
            self.first_year = race_year
        self.last_year = race_year
        
    def increment_race_count(self):
        """Increment the number of races for this driver."""
        self.race_count += 1
        
    def get_rating_volatility(self):
        """Calculate rating volatility (standard deviation of ratings)."""
        if len(self.rating_history) <= 1:
            return 0
        # Extract just the ratings from (year, race_id, rating) tuples
        ratings = [entry[2] for entry in self.rating_history]
        return np.std(ratings)
        
    def get_career_span(self):
        """Calculate career span in years."""
        if self.first_year and self.last_year:
            return self.last_year - self.first_year
        return 0

    def get_yearly_elo_progression(self, base_elo=1500):
        """
        Get end-of-year ELO ratings for each year of the driver's career.
        
        Returns:
            list: List of (year, elo_rating) tuples
        """
        if not self.rating_history or self.first_year is None:
            return []
        
        # Group ratings by year and get the last rating for each year
        year_ratings = {}
        for year, race_id, rating in self.rating_history:
            if year is not None:
                year_ratings[year] = rating  # Last rating in year wins
        
        # Fill in any missing years with interpolated/carried-over values
        if not year_ratings:
            return [(self.first_year, base_elo)]
        
        result = []
        last_rating = base_elo
        for year in range(self.first_year, self.last_year + 1):
            if year in year_ratings:
                last_rating = year_ratings[year]
            result.append((year, last_rating))
        
        return result

    def get_race_elo_progression(self):
        """
        Get ELO rating after each race (deduplicated by race_id).
        
        Returns:
            list: List of (year, race_id, elo_rating) tuples, one per race
        """
        if not self.rating_history:
            return []
        
        # Get the last rating update for each race
        race_ratings = {}
        for year, race_id, rating in self.rating_history:
            if race_id is not None:
                race_ratings[(year, race_id)] = rating
        
        # Sort by year and race_id
        result = [(year, race_id, rating) 
                  for (year, race_id), rating in sorted(race_ratings.items())]
        return result

    def get_confidence_interval(self, confidence_calculator):
        """Calculate confidence interval using provided calculator."""
        rating_volatility = self.get_rating_volatility()
        year_span = self.get_career_span()
        return confidence_calculator.calculate_confidence_interval(
            self.rating, 
            self.race_count, 
            rating_volatility, 
            year_span
        )

    def get_flag_level(self):
        """
        Determine driver classification based on race count and era.
        
        Pre-1980 Era has lower thresholds due to fewer races per season 
        and shorter careers. Modern Era (1980-Present) has higher thresholds 
        reflecting longer seasons and careers.
        """
        # If first_year is None, default to modern era classification
        if not self.first_year or self.first_year >= 1980:
            # Modern Era (1980-Present)
            if self.race_count < 25:
                return 'Rookie'
            elif self.race_count < 75:
                return 'Intermediate'
            elif self.race_count < 150:
                return 'Experienced'
            elif self.race_count < 250:
                return 'Veteran'
            else:
                return 'Legend'
        else:
            # Pre-1980 Era
            if self.race_count < 10:
                return 'Rookie'
            elif self.race_count < 25:
                return 'Intermediate'
            elif self.race_count < 40:
                return 'Experienced'
            elif self.race_count < 50:
                return 'Veteran'
            else:
                return 'Legend'

    def to_stats_dict(self, calculator, confidence_calculator, drivers_df, confidence_score, confidence_grade):
        """Convert driver data to statistics dictionary."""
        lower_bound, upper_bound = self.get_confidence_interval(confidence_calculator)
        driver_info = drivers_df[drivers_df['driverId'] == self.driver_id].iloc[0]
        
        return {
            'Driver': f"{driver_info['forename']} {driver_info['surname']}",
            'f1_driver_id': self.driver_id,
            'Elo Rating': self.rating,
            'Lower Bound': round(lower_bound, 1),
            'Upper Bound': round(upper_bound, 1),
            'Confidence Score': confidence_score,
            'Reliability Grade': confidence_grade,
            'Race Count': self.race_count,
            'Rating Volatility': round(self.get_rating_volatility(), 1),
            'First Year': self.first_year,
            'Last Year': self.last_year,
            'Career Span': self.get_career_span(),
            'Flag Level': self.get_flag_level()
        }
