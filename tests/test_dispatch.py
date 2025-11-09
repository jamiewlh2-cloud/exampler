import unittest
from src.trucks import Truck

class TestTruckDispatch(unittest.TestCase):

    def setUp(self):
        self.truck = Truck()

    def test_dispatch_truck(self):
        self.truck.add_truck("Truck 1")
        self.assertTrue(self.truck.dispatch_truck("Truck 1"))
        self.assertFalse(self.truck.is_truck_available("Truck 1"))

    def test_dispatch_non_existent_truck(self):
        self.assertFalse(self.truck.dispatch_truck("Truck 2"))

    def test_check_truck_availability(self):
        self.truck.add_truck("Truck 3")
        self.truck.dispatch_truck("Truck 3")
        self.assertFalse(self.truck.is_truck_available("Truck 3"))
        self.truck.add_truck("Truck 4")
        self.assertTrue(self.truck.is_truck_available("Truck 4"))

if __name__ == '__main__':
    unittest.main()