class NonGov:
    def __init__(self, location):
        self.location = location

    def request_aid(self, storage, help_stations):
        if not help_stations.is_nearby(self.location):
            return self.dispatch_truck(storage)
        else:
            distance = help_stations.get_distance(self.location)
            return f"You are {distance} km away from the nearest help station."

    def dispatch_truck(self, storage):
        if storage.check_availability():
            storage.decrease_supply()
            return "A truck has been dispatched to your location."
        else:
            return "No supplies available for dispatch."