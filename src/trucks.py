class Truck:
    def __init__(self):
        # Maintain a dict of truck_name -> availability (True means available)
        self.trucks = {}

    def add_truck(self, truck_name):
        # Add a new truck as available
        self.trucks[truck_name] = True

    def dispatch_truck(self, truck_name):
        # Dispatch a specific truck if it exists and is available
        if truck_name not in self.trucks:
            return False
        if not self.trucks[truck_name]:
            return False
        self.trucks[truck_name] = False
        return True

    def return_truck(self, truck_name):
        # Mark a truck as available again; if it doesn't exist, add it as available
        self.trucks[truck_name] = True

    def is_truck_available(self, truck_name):
        return self.trucks.get(truck_name, False)