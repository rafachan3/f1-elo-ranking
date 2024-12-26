class Driver:
    def __init__(self, driver_id, base_elo=1500):
        self.driver_id = driver_id
        self.rating = base_elo
        self.race_count = 0
        self.rating_history = []
        self.first_year = None
        self.last_year = None