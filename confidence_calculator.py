import math

class ConfidenceCalculator:
    def __init__(self):
        self.CONFIDENCE_LEVEL = 0.95
        # Z-score for 95% confidence interval (norm.ppf(0.975) = 1.959963984540054)
        self.Z_SCORE_95 = 1.959964

    def calculate_confidence_interval(self, rating, n_races, rating_volatility, year_span):
        base_se = 200 / math.sqrt(max(1, n_races))
        volatility_factor = 1 + (rating_volatility / 100)
        history_factor = 1 + (year_span / 50)
        adjusted_se = base_se * volatility_factor * history_factor
        margin = self.Z_SCORE_95 * adjusted_se
        return rating - margin, rating + margin

    def calculate_confidence_score(self, width, max_width, min_width):
        width_range = max_width - min_width
        normalized_width = (max_width - width) / width_range
        return round(normalized_width * 100)

    def get_confidence_grade(self, score):
        if score >= 90: return 'A+'
        elif score >= 80: return 'A'
        elif score >= 70: return 'B+'
        elif score >= 60: return 'B'
        elif score >= 50: return 'C+'
        elif score >= 40: return 'C'
        elif score >= 30: return 'D+'
        elif score >= 20: return 'D'
        else: return 'F'