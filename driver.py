import numpy as np

class Driver:
    def __init__(self, driver_id, base_elo=1500):
        self.driver_id = driver_id
        self.rating = base_elo
        self.race_count = 0
        self.rating_history = []
        self.first_year = None
        self.last_year = None
    
    def update_rating(self, new_rating):
        """Update driver's rating and rating history"""
        self.rating_history.append(new_rating)
        self.rating = new_rating
        
    def update_years(self, race_year):
        """Update driver's first and last year"""
        if not self.first_year:
            self.first_year = race_year
        self.last_year = race_year
        
    def increment_race_count(self):
        """Increment the number of races for this driver"""
        self.race_count += 1
        
    def get_rating_volatility(self):
        """Calculate rating volatility"""
        return np.std(self.rating_history) if len(self.rating_history) > 1 else 0
        
    def get_career_span(self):
        """Calculate career span in years"""
        if self.first_year and self.last_year:
            return self.last_year - self.first_year
        return 0

    def get_confidence_interval(self, confidence_calculator):
        """Calculate confidence interval using provided calculator"""
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
        Pre-1980 Era has lower thresholds due to fewer races per season and shorter careers.
        Modern Era (1980-Present) has higher thresholds reflecting longer seasons and careers.
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
        """Convert driver data to statistics dictionary"""
        lower_bound, upper_bound = self.get_confidence_interval(confidence_calculator)
        driver_info = drivers_df[drivers_df['driverId'] == self.driver_id].iloc[0]
        
        return {
            'Driver': f"{driver_info['forename']} {driver_info['surname']}",
            'f1_driver_id': self.driver_id,  # Changed from driver_id
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
            'Flag Level': self.get_flag_level()  # Add flag level to stats dict
        }
