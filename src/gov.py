class Gov:
    def __init__(self):
        self.supplies = {}

    def add_supply(self, item, quantity):
        if item in self.supplies:
            self.supplies[item] += quantity
        else:
            self.supplies[item] = quantity

    def check_inventory(self):
        return self.supplies

    def remove_supply(self, item, quantity):
        if item in self.supplies and self.supplies[item] >= quantity:
            self.supplies[item] -= quantity
            if self.supplies[item] == 0:
                del self.supplies[item]
            return True
        return False