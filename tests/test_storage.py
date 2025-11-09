import unittest
from src.storage import Storage

class TestStorage(unittest.TestCase):
    def setUp(self):
        self.storage = Storage()

    def test_add_supplies(self):
        self.storage.add_supplies('water', 100)
        self.assertEqual(self.storage.check_inventory('water'), 100)

    def test_check_inventory_empty(self):
        self.assertEqual(self.storage.check_inventory('food'), 0)

    def test_add_multiple_supplies(self):
        self.storage.add_supplies('food', 50)
        self.storage.add_supplies('food', 30)
        self.assertEqual(self.storage.check_inventory('food'), 80)

    def test_remove_supplies(self):
        self.storage.add_supplies('medicines', 20)
        self.storage.remove_supplies('medicines', 10)
        self.assertEqual(self.storage.check_inventory('medicines'), 10)

    def test_remove_supplies_exceeding(self):
        self.storage.add_supplies('bandages', 15)
        with self.assertRaises(ValueError):
            self.storage.remove_supplies('bandages', 20)

if __name__ == '__main__':
    unittest.main()