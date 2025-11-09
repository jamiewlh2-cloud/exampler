# main.py

def main():
    """Interactive entrypoint that uses the Storage, Truck and HelpStation APIs.

    - Government users can add supplies or check inventory.
    - Non-government users can request aid; if near a station they get distance, otherwise a truck is dispatched.
    """
    import json
    from storage import Storage
    from trucks import Truck
    from help_stations import HelpStation
    from typing import List, Dict, Tuple

    print("Welcome to the Aid Dispatch System")

    # Define available supply categories and their units
    SUPPLY_CATEGORIES: Dict[str, str] = {
        'food': 'lbs',
        'medical': None,  # no units, just availability
        'blankets': 'quantity',
        'water': 'lbs'
    }

    def format_supply_name(name: str, quantity: int, unit: str) -> str:
        """Format a supply name with its quantity and unit."""
        if unit is None:
            return name
        return f"{name} ({quantity} {unit})"

    def get_supply_choices() -> List[Tuple[str, str]]:
        """Return list of (name, unit) tuples for supplies."""
        return [(name, unit or '') for name, unit in SUPPLY_CATEGORIES.items()]

    # Use persistent storage so supplies survive program restarts
    storage = Storage('data/storage.json')
    trucks = Truck()
    help_stations = HelpStation()

    # Seed some trucks
    for i in range(1, 6):
        trucks.add_truck(f"Truck {i}")

    # Default help station coordinates for new stations
    default_coords = {
        'North': (51.5074, -0.1278),
        'South': (50.9097, -1.4044),
        'East': (52.6369, 1.2989),
        'West': (51.4816, -3.1791),
        'Central': (52.4862, -1.8904)
    }

    # Authentication flow: ask for gov password; blank or incorrect => non-gov
    GOV_PASSWORD = 'gov'
    pwd = input("Enter gov password (leave blank if non-government): ").strip()

    if pwd == GOV_PASSWORD:
        while True:
            action = input("Enter 'add' to add supplies, 'check' inventory, 'reports' to manage reports, 'stations' to manage aid centres, or 'exit': ").strip().lower()
            if action == 'stations':
                while True:
                    print("\nAid Centre Management")
                    print("1. Add new aid centre")
                    print("2. List aid centres")
                    print("3. Back to main menu")
                    
                    choice = input("Enter choice (1-3): ").strip()
                    if choice == '1':
                        name = input("Enter aid centre name (e.g., Edinburgh Centre): ").strip()
                        location = input("Enter location (North/South/East/West/Central): ").strip().capitalize()
                        
                        if location in default_coords:
                            coords = default_coords[location]
                            help_stations.add_station(name, coords)
                            print(f"Added aid centre: {name} ({location})")
                        else:
                            print("Invalid location. Please choose from North/South/East/West/Central.")
                    
                    elif choice == '2':
                        if help_stations.stations:
                            print("\nRegistered Aid Centres:")
                            for station_name, coords in help_stations.stations.items():
                                # Find location based on coordinates
                                location = "Unknown"
                                for loc, coord in default_coords.items():
                                    if coord == coords:
                                        location = loc
                                        break
                                print(f" - {station_name} ({location})")
                        else:
                            print("No aid centres registered.")
                    
                    elif choice == '3':
                        break
                    else:
                        print("Invalid choice. Please try again.")
                continue
                
            elif action == 'add':
                # Show available categories
                print("\nAvailable supply categories:")
                for i, (name, unit) in enumerate(get_supply_choices(), 1):
                    print(f"{i}. {name}" + (f" (measured in {unit})" if unit else ""))
                
                try:
                    choice = int(input("\nEnter category number (1-4): ").strip())
                    if not (1 <= choice <= 4):
                        raise ValueError("Invalid choice")
                    supply = list(SUPPLY_CATEGORIES.keys())[choice - 1].lower()
                except (ValueError, IndexError):
                    print("Invalid choice. Please enter a number between 1 and 4.")
                    continue

                if supply == 'medical':
                    # Medical supplies are tracked as available/unavailable (1/0)
                    storage.add_supplies(supply, 1)
                    print(f"Added medical supplies to storage.")
                    continue

                try:
                    unit = SUPPLY_CATEGORIES[supply]
                    quantity = int(input(f"Enter quantity ({unit}): ").strip())
                    if quantity <= 0:
                        raise ValueError("Quantity must be positive")
                except ValueError:
                    print("Invalid quantity. Please enter a number.")
                    continue

                storage.add_supplies(supply, quantity)
                print(f"Added {format_supply_name(supply, quantity, unit)} to storage.")
            elif action == 'reports':
                while True:
                    print("\nDisaster Reports Management")
                    print("1. View reports")
                    print("2. Delete report")
                    print("3. Back to main menu")
                    
                    choice = input("Enter choice (1-3): ").strip()
                    if choice == '1':
                        reports = storage.get_reports()
                        if not reports:
                            print("No reports available.")
                        else:
                            print("\nSaved disaster reports:")
                            for i, r in enumerate(reports, start=1):
                                print(f"{i}. {r.get('timestamp')} - {r.get('name')} - {r.get('disaster_type')}: {r.get('details')}")
                    
                    elif choice == '2':
                        reports = storage.get_reports()
                        if not reports:
                            print("No reports available to delete.")
                            continue
                            
                        print("\nCurrent reports:")
                        for i, r in enumerate(reports, start=1):
                            print(f"{i}. {r.get('timestamp')} - {r.get('name')} - {r.get('disaster_type')}")
                        
                        try:
                            index = int(input("\nEnter report number to delete (0 to cancel): ").strip())
                            if index == 0:
                                continue
                            if storage.delete_report(index):
                                print("Report deleted successfully.")
                            else:
                                print("Invalid report number.")
                        except ValueError:
                            print("Invalid input. Please enter a number.")
                    
                    elif choice == '3':
                        break
                    else:
                        print("Invalid choice. Please try again.")
                continue
            elif action == 'check':
                supplies = storage.get_supplies()
                if not supplies:
                    print("No supplies in storage.")
                else:
                    print("\nCurrent supplies in storage:")
                    for supply, quantity in supplies.items():
                        # Convert to lowercase for comparison
                        supply_lower = supply.lower()
                        # Find matching category if any
                        category = next((cat for cat in SUPPLY_CATEGORIES.keys() if cat.lower() == supply_lower), None)
                        
                        if supply_lower == 'medical':
                            status = "Available" if quantity > 0 else "Not available"
                            print(f"Medical supplies: {status}")
                        elif category:
                            unit = SUPPLY_CATEGORIES[category]
                            print(f"{format_supply_name(category, quantity, unit)}")
                        else:
                            # Handle legacy or unknown supplies
                            print(f"{supply}: {quantity}")
            elif action == 'exit':
                break
            else:
                print("Invalid action. Please try again.")

    else:
        # Non-government flow: require the requester to confirm 'non' and state their name
        confirm = input("Enter 'non' to continue as non-government (or anything else to exit): ").strip().lower()
        if confirm != 'non':
            print("Exiting.")
            return

        user_name = input("Enter your name: ").strip()
        if not user_name:
            user_name = "Requester"

        # persist requester name so it's available after program restarts
        storage.add_requester(user_name)

        # Prompt to file a disaster report
        report_choice = input("Would you like to file a disaster report? (y/n): ").strip().lower()
        if report_choice == 'y':
            disaster_type = input("Type of natural disaster (e.g., flood, earthquake): ").strip()
            details = input("Please provide brief details about the situation: ").strip()
            storage.add_report(user_name, disaster_type, details)
            print("Thank you — your report has been saved and will be visible to government users.")

        # For non-government users: do not ask for latitude/longitude.
        # Always attempt to dispatch a truck when supplies are available.
        while True:
            action = input("Enter 'request' to request aid, 'exit' to quit, or 'stations' to list stations: ").strip().lower()
            if action == 'request':
                # Show available supplies
                print("\nAvailable supplies:")
                supplies = storage.get_supplies()
                available_supplies = []
                
                for supply, quantity in supplies.items():
                    supply_lower = supply.lower()
                    category = next((cat for cat in SUPPLY_CATEGORIES.keys() if cat.lower() == supply_lower), None)
                    
                    if category:
                        unit = SUPPLY_CATEGORIES[category]
                        if supply_lower == 'medical' and quantity > 0:
                            print(f"{len(available_supplies) + 1}. Medical supplies (Available)")
                            available_supplies.append(('medical', None))
                        elif quantity > 0:
                            print(f"{len(available_supplies) + 1}. {category} ({quantity} {unit} available)")
                            available_supplies.append((category, unit))
                
                if not available_supplies:
                    print("Sorry, no supplies are currently available.")
                    continue
                
                try:
                    choice = int(input("\nEnter supply number (or 0 to cancel): ").strip())
                    if choice == 0:
                        continue
                    if not (1 <= choice <= len(available_supplies)):
                        print("Invalid choice.")
                        continue
                        
                    supply, unit = available_supplies[choice - 1]
                    max_available = storage.check_inventory(supply)
                    
                    # Handle quantity request
                    if supply == 'medical':
                        quantity = 1
                    else:
                        print(f"\nAvailable {supply}: {max_available} {unit}")
                        try:
                            quantity = int(input(f"Enter amount needed (1-{max_available}): ").strip())
                            if quantity <= 0 or quantity > max_available:
                                print(f"Invalid amount. Please enter a number between 1 and {max_available}.")
                                continue
                        except ValueError:
                            print("Invalid input. Please enter a number.")
                            continue
                    
                    # Find available truck
                    available_truck = None
                    for name, available in trucks.trucks.items():
                        if available:
                            available_truck = name
                            break

                    if available_truck:
                        trucks.dispatch_truck(available_truck)
                        try:
                            # Double check the current inventory before removing
                            current_quantity = storage.check_inventory(supply)
                            if quantity > current_quantity:
                                print(f"Sorry, only {current_quantity} {unit} of {supply} available now.")
                                continue
                                
                            storage.remove_supplies(supply, quantity)
                            if supply == 'medical':
                                print(f"{available_truck} has been dispatched with medical supplies to {user_name}'s location.")
                            else:
                                print(f"{available_truck} has been dispatched with {quantity} {unit} of {supply} to {user_name}'s location.")
                        except ValueError as e:
                            print(f"Error: {str(e)}")
                            continue
                    else:
                        print("No trucks available to dispatch at the moment.")
                    
                    # Ask if they want to request more
                    more = input("\nWould you like to request more supplies? (y/n): ").strip().lower()
                    if more != 'y':
                        action = 'exit'  # This will break the main loop
                        
                except ValueError:
                    print("Invalid input. Please try again.")

            elif action == 'stations':
                if help_stations.stations:
                    print("Known help stations (latitude, longitude):")
                    for sid, loc in help_stations.stations.items():
                        # loc is a (lat, lon) tuple
                        lat, lon = loc
                        print(f" - {sid}: latitude={lat}, longitude={lon}")
                else:
                    print("No help stations registered.")

            elif action == 'exit':
                break
            else:
                print("Invalid action. Please try again.")
    

if __name__ == "__main__":
    main()