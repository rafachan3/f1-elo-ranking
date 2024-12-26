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

    def get_confidence_interval(self, calculator):
        """Calculate confidence interval using provided calculator"""
        rating_volatility = self.get_rating_volatility()
        year_span = self.get_career_span()
        return calculator.calculate_confidence_interval(
            self.rating, 
            self.race_count, 
            rating_volatility, 
            year_span
        )

    def to_stats_dict(self, calculator, drivers_df, confidence_score, confidence_grade):
        """Convert driver data to statistics dictionary"""
        lower_bound, upper_bound = self.get_confidence_interval(calculator)
        driver_info = drivers_df[drivers_df['driverId'] == self.driver_id].iloc[0]
        
        return {
            'Driver': f"{driver_info['forename']} {driver_info['surname']}",
            'Elo Rating': self.rating,
            'Lower Bound': round(lower_bound, 1),
            'Upper Bound': round(upper_bound, 1),
            'Confidence Score': confidence_score,
            'Reliability Grade': confidence_grade,
            'Race Count': self.race_count,
            'Rating Volatility': round(self.get_rating_volatility(), 1),
            'Is Established': self.race_count >= calculator.MIN_RACES_FOR_ESTABLISHED,
            'First Year': self.first_year,
            'Last Year': self.last_year,
            'Career Span': self.get_career_span()
        }
