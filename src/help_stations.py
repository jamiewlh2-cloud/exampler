class HelpStation:
    def __init__(self):
        self.stations = {}

    def add_station(self, station_id, location):
        self.stations[station_id] = location

    def get_station(self, station_id):
        return self.stations.get(station_id)

    def calculate_distance(self, user_location, station_id):
        """Calculate Euclidean distance from user_location to a station by id.

        Raises ValueError if the station_id does not exist.
        """
        location = self.get_station(station_id)
        if location is None:
            raise ValueError(f"Station '{station_id}' does not exist")
        # location is a tuple (x, y)
        return ((user_location[0] - location[0]) ** 2 + (user_location[1] - location[1]) ** 2) ** 0.5

    def find_nearest_station(self, user_location):
        nearest_station = None
        min_distance = float('inf')

        for station_id, location in self.stations.items():
            distance = self.calculate_distance(user_location, location)
            if distance < min_distance:
                min_distance = distance
                nearest_station = station_id

        if nearest_station is None:
            return None, None
        return nearest_station, min_distance