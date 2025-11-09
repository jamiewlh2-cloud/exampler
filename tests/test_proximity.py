import unittest
from src.help_stations import HelpStation

class TestHelpStationProximity(unittest.TestCase):
    def setUp(self):
        self.help_station = HelpStation()
        self.help_station.add_station("Station A", (10, 10))
        self.help_station.add_station("Station B", (20, 20))

    def test_proximity_to_nearby_station(self):
        distance = self.help_station.calculate_distance((12, 12), "Station A")
        self.assertLessEqual(distance, 3, "Should be close to Station A")

    def test_proximity_to_far_station(self):
        distance = self.help_station.calculate_distance((5, 5), "Station B")
        self.assertGreater(distance, 15, "Should be far from Station B")

    def test_non_existent_station(self):
        with self.assertRaises(ValueError):
            self.help_station.calculate_distance((0, 0), "Station C")

if __name__ == '__main__':
    unittest.main()