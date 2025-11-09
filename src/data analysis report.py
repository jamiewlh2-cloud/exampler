import json
import re
import urllib.parse
import urllib.request
from typing import Optional, Tuple, List, Dict

# Geocoder setup (OpenStreetMap Nominatim). Replace contact@example.com with a real contact per policy.
USER_AGENT = "exampler-geocoder/1.0 (contact@example.com)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode(number: Optional[str], street: str, city: str, country: str) -> Optional[Tuple[float, float, str]]:
    street_part = " ".join(p.strip() for p in (number or "", street or "") if p and p.strip())
    parts = [p for p in (street_part, city, country) if p and p.strip()]
    if not parts:
        return None
    q = ", ".join(parts)
    params = {"format": "json", "q": q, "limit": 1, "addressdetails": 0}
    url = NOMINATIM_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            if not data:
                return None
            first = data[0]
            return float(first["lat"]), float(first["lon"]), first.get("display_name", "")
    except Exception:
        return None


def _extract_location_from_details(details: str) -> Tuple[Optional[str], Optional[float], Optional[float]]:
    if not details:
        return None, None, None
    addr = None
    lat = None
    lon = None
    if "location_resolved:" in details:
        try:
            addr_part = details.split("location_resolved:", 1)[1]
            addr = addr_part.split("|", 1)[0].strip()
            if addr == "":
                addr = None
        except Exception:
            addr = None
    mlat = re.search(r"lat:\s*([-\d\.]+)", details)
    mlon = re.search(r"lon:\s*([-\d\.]+)", details)
    try:
        if mlat:
            lat = float(mlat.group(1))
    except Exception:
        lat = None
    try:
        if mlon:
            lon = float(mlon.group(1))
    except Exception:
        lon = None
    return addr, lat, lon


def _extract_description_from_details(details: str) -> str:
    if not details:
        return ""
    if "location_resolved:" in details:
        return details.split("location_resolved:", 1)[0].rstrip(" |").strip()
    return details.strip()


def main():
    from storage import Storage
    from trucks import Truck
    from help_stations import HelpStation

    print("Welcome to the Aid Dispatch System")

    SUPPLY_CATEGORIES: Dict[str, Optional[str]] = {
        "food": "lbs",
        "medical": None,
        "blankets": "quantity",
        "water": "lbs",
    }

    def format_supply_name(name: str, quantity: int, unit: Optional[str]) -> str:
        if unit is None:
            return f"{name} ({quantity})"
        return f"{name} ({quantity} {unit})"

    def get_supply_choices() -> List[Tuple[str, str]]:
        return [(name, unit or "") for name, unit in SUPPLY_CATEGORIES.items()]

    storage = Storage("data/storage.json")
    trucks = Truck()
    help_stations = HelpStation()

    for i in range(1, 6):
        trucks.add_truck(f"Truck {i}")

    default_coords = {
        "North": (51.5074, -0.1278),
        "South": (50.9097, -1.4044),
        "East": (52.6369, 1.2989),
        "West": (51.4816, -3.1791),
        "Central": (52.4862, -1.8904),
    }

    GOV_PASSWORD = "gov"
    pwd = input("Enter gov password (leave blank if non-government): ").strip()

    if pwd == GOV_PASSWORD:
        while True:
            action = input(
                "Enter 'add' to add supplies, 'check' inventory, 'reports' to manage reports, 'stations' to manage aid centres, or 'exit': "
            ).strip().lower()

            if action == "stations":
                while True:
                    print("\nAid Centre Management")
                    print("1. Add new aid centre")
                    print("2. List aid centres")
                    print("3. Back to main menu")
                    choice = input("Enter choice (1-3): ").strip()
                    if choice == "1":
                        name = input("Enter aid centre name: ").strip()
                        location = input("Enter location (North/South/East/West/Central): ").strip().capitalize()
                        if location in default_coords:
                            coords = default_coords[location]
                            help_stations.add_station(name, coords)
                            print(f"Added aid centre: {name} ({location})")
                        else:
                            print("Invalid location.")
                    elif choice == "2":
                        if help_stations.stations:
                            print("\nRegistered Aid Centres:")
                            for station_name, coords in help_stations.stations.items():
                                print(f" - {station_name}: {coords}")
                        else:
                            print("No aid centres registered.")
                    elif choice == "3":
                        break
                    else:
                        print("Invalid choice.")
                continue

            if action == "add":
                print("\nAvailable supply categories:")
                for i, (name, unit) in enumerate(get_supply_choices(), 1):
                    print(f"{i}. {name}" + (f" (measured in {unit})" if unit else ""))
                try:
                    choice = int(input("\nEnter category number: ").strip())
                    if not (1 <= choice <= len(SUPPLY_CATEGORIES)):
                        raise ValueError
                    supply = list(SUPPLY_CATEGORIES.keys())[choice - 1].lower()
                except Exception:
                    print("Invalid choice.")
                    continue

                if supply == "medical":
                    storage.add_supplies(supply, 1)
                    print("Added medical supplies to storage.")
                    continue

                try:
                    unit = SUPPLY_CATEGORIES[supply]
                    quantity = int(input(f"Enter quantity ({unit}): ").strip())
                    if quantity <= 0:
                        raise ValueError
                except Exception:
                    print("Invalid quantity.")
                    continue

                storage.add_supplies(supply, quantity)
                print(f"Added {format_supply_name(supply, quantity, unit)} to storage.")
                continue

            if action == "reports":
                while True:
                    print("\nDisaster Reports Management")
                    print("1. View reports (full report + address & coordinates)")
                    print("2. Delete report")
                    print("3. Back to main menu")
                    choice = input("Enter choice (1-3): ").strip()
                    if choice == "1":
                        reports = storage.get_reports()
                        if not reports:
                            print("No reports available.")
                        else:
                            print("\nSaved disaster reports:")
                            for i, r in enumerate(reports, start=1):
                                name = r.get("name", "Unknown")
                                dtype = r.get("disaster_type", "Unknown")
                                details_raw = r.get("details", "") or ""
                                description = _extract_description_from_details(details_raw)
                                addr, lat, lon = _extract_location_from_details(details_raw)
                                addr_display = addr or "Address unknown"
                                lat_display = lat if lat is not None else "N/A"
                                lon_display = lon if lon is not None else "N/A"
                                print(f"{i}. Reporter: {name}")
                                print(f"   Type   : {dtype}")
                                print(f"   Details: {description}")
                                print(f"   Address: {addr_display}")
                                print(f"   Lat/Lon: {lat_display} / {lon_display}")
                                print("-" * 60)
                    elif choice == "2":
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
                            print("Invalid input.")
                    elif choice == "3":
                        break
                    else:
                        print("Invalid choice.")
                continue

            if action == "check":
                supplies = storage.get_supplies()
                if not supplies:
                    print("No supplies in storage.")
                else:
                    print("\nCurrent supplies in storage:")
                    for supply, quantity in supplies.items():
                        supply_lower = supply.lower()
                        category = next((cat for cat in SUPPLY_CATEGORIES.keys() if cat.lower() == supply_lower), None)
                        if supply_lower == "medical":
                            status = "Available" if quantity > 0 else "Not available"
                            print(f"Medical supplies: {status}")
                        elif category:
                            unit = SUPPLY_CATEGORIES[category]
                            print(f"{format_supply_name(category, quantity, unit)}")
                        else:
                            print(f"{supply}: {quantity}")
                continue

            if action == "exit":
                break

            print("Invalid action. Please try again.")

    else:
        confirm = input("Enter 'non' to continue as non-government (or anything else to exit): ").strip().lower()
        if confirm != "non":
            print("Exiting.")
            return

        user_name = input("Enter your name: ").strip() or "Requester"
        storage.add_requester(user_name)

        report_choice = input("Would you like to file a disaster report? (y/n): ").strip().lower()
        if report_choice == "y":
            disaster_type = input("Type of natural disaster (e.g., flood, earthquake): ").strip()
            details = input("Please provide brief details about the situation: ").strip()

            print("\nPlease provide the location for this report (leave blank if unknown).")
            number = input("Address (number) : ").strip()
            street = input("Street name      : ").strip()
            city = input("City / Town      : ").strip()
            country = input("Country          : ").strip()

            coords = geocode(number or None, street, city, country)
            if coords is None:
                storage.add_report(user_name, disaster_type, details)
                print("Report saved.")
            else:
                lat, lon, display = coords
                details_with_location = f"{details} | location_resolved: {display} | lat:{lat} lon:{lon}"
                storage.add_report(user_name, disaster_type, details_with_location)
                print("Report saved.")

        while True:
            action = input("Enter 'request' to request aid, 'exit' to quit, or 'stations' to list stations: ").strip().lower()
            if action == "request":
                print("\nAvailable supplies:")
                supplies = storage.get_supplies()
                available_supplies: List[Tuple[str, Optional[str]]] = []
                for supply, quantity in supplies.items():
                    supply_lower = supply.lower()
                    category = next((cat for cat in SUPPLY_CATEGORIES.keys() if cat.lower() == supply_lower), None)
                    if category:
                        unit = SUPPLY_CATEGORIES[category]
                        if supply_lower == "medical" and quantity > 0:
                            print(f"{len(available_supplies) + 1}. Medical supplies (Available)")
                            available_supplies.append(("medical", None))
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
                    if supply == "medical":
                        quantity = 1
                    else:
                        print(f"\nAvailable {supply}: {max_available} {unit}")
                        quantity = int(input(f"Enter amount needed (1-{max_available}): ").strip())
                        if quantity <= 0 or quantity > max_available:
                            print("Invalid amount.")
                            continue
                    available_truck = next((n for n, av in trucks.trucks.items() if av), None)
                    if available_truck:
                        trucks.dispatch_truck(available_truck)
                        current_quantity = storage.check_inventory(supply)
                        if quantity > current_quantity:
                            print(f"Sorry, only {current_quantity} available now.")
                            continue
                        storage.remove_supplies(supply, quantity)
                        if supply == "medical":
                            print(f"{available_truck} dispatched with medical supplies to {user_name}'s location.")
                        else:
                            print(f"{available_truck} dispatched with {quantity} {unit} of {supply} to {user_name}'s location.")
                    else:
                        print("No trucks available to dispatch at the moment.")
                    more = input("\nWould you like to request more supplies? (y/n): ").strip().lower()
                    if more != "y":
                        break
                except Exception:
                    print("Invalid input. Please try again.")
            elif action == "stations":
                if help_stations.stations:
                    print("Known help stations (latitude, longitude):")
                    for sid, loc in help_stations.stations.items():
                        lat, lon = loc
                        print(f" - {sid}: latitude={lat}, longitude={lon}")
                else:
                    print("No help stations registered.")
            elif action == "exit":
                break
            else:
                print("Invalid action. Please try again.")


if __name__ == "__main__":
    main()

import json
import re
import urllib.parse
import urllib.request
from typing import Optional, Tuple, List, Dict

# Geocoder setup (OpenStreetMap Nominatim). Replace contact@example.com with a real contact per policy.
USER_AGENT = "exampler-geocoder/1.0 (contact@example.com)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode(number: Optional[str], street: str, city: str, country: str) -> Optional[Tuple[float, float, str]]:
    street_part = " ".join(p.strip() for p in (number or "", street or "") if p and p.strip())
    parts = [p for p in (street_part, city, country) if p and p.strip()]
    if not parts:
        return None
    q = ", ".join(parts)
    params = {"format": "json", "q": q, "limit": 1, "addressdetails": 0}
    url = NOMINATIM_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            if not data:
                return None
            first = data[0]
            return float(first["lat"]), float(first["lon"]), first.get("display_name", "")
    except Exception:
        return None


def _extract_location_from_details(details: str) -> Tuple[Optional[str], Optional[float], Optional[float]]:
    if not details:
        return None, None, None
    addr = None
    lat = None
    lon = None
    if "location_resolved:" in details:
        try:
            addr_part = details.split("location_resolved:", 1)[1]
            addr = addr_part.split("|", 1)[0].strip()
            if addr == "":
                addr = None
        except Exception:
            addr = None
    mlat = re.search(r"lat:\s*([-\d\.]+)", details)
    mlon = re.search(r"lon:\s*([-\d\.]+)", details)
    try:
        if mlat:
            lat = float(mlat.group(1))
    except Exception:
        lat = None
    try:
        if mlon:
            lon = float(mlon.group(1))
    except Exception:
        lon = None
    return addr, lat, lon


def _extract_description_from_details(details: str) -> str:
    if not details:
        return ""
    if "location_resolved:" in details:
        return details.split("location_resolved:", 1)[0].rstrip(" |").strip()
    return details.strip()


def main():
    from storage import Storage
    from trucks import Truck
    from help_stations import HelpStation

    print("Welcome to the Aid Dispatch System")

    SUPPLY_CATEGORIES: Dict[str, Optional[str]] = {
        "food": "lbs",
        "medical": None,
        "blankets": "quantity",
        "water": "lbs",
    }

    def format_supply_name(name: str, quantity: int, unit: Optional[str]) -> str:
        if unit is None:
            return f"{name} ({quantity})"
        return f"{name} ({quantity} {unit})"

    def get_supply_choices() -> List[Tuple[str, str]]:
        return [(name, unit or "") for name, unit in SUPPLY_CATEGORIES.items()]

    storage = Storage("data/storage.json")
    trucks = Truck()
    help_stations = HelpStation()

    for i in range(1, 6):
        trucks.add_truck(f"Truck {i}")

    default_coords = {
        "North": (51.5074, -0.1278),
        "South": (50.9097, -1.4044),
        "East": (52.6369, 1.2989),
        "West": (51.4816, -3.1791),
        "Central": (52.4862, -1.8904),
    }

    GOV_PASSWORD = "gov"
    pwd = input("Enter gov password (leave blank if non-government): ").strip()

    if pwd == GOV_PASSWORD:
        while True:
            action = input(
                "Enter 'add' to add supplies, 'check' inventory, 'reports' to manage reports, 'stations' to manage aid centres, or 'exit': "
            ).strip().lower()

            if action == "stations":
                while True:
                    print("\nAid Centre Management")
                    print("1. Add new aid centre")
                    print("2. List aid centres")
                    print("3. Back to main menu")
                    choice = input("Enter choice (1-3): ").strip()
                    if choice == "1":
                        name = input("Enter aid centre name: ").strip()
                        location = input("Enter location (North/South/East/West/Central): ").strip().capitalize()
                        if location in default_coords:
                            coords = default_coords[location]
                            help_stations.add_station(name, coords)
                            print(f"Added aid centre: {name} ({location})")
                        else:
                            print("Invalid location.")
                    elif choice == "2":
                        if help_stations.stations:
                            print("\nRegistered Aid Centres:")
                            for station_name, coords in help_stations.stations.items():
                                print(f" - {station_name}: {coords}")
                        else:
                            print("No aid centres registered.")
                    elif choice == "3":
                        break
                    else:
                        print("Invalid choice.")
                continue

            if action == "add":
                print("\nAvailable supply categories:")
                for i, (name, unit) in enumerate(get_supply_choices(), 1):
                    print(f"{i}. {name}" + (f" (measured in {unit})" if unit else ""))
                try:
                    choice = int(input("\nEnter category number: ").strip())
                    if not (1 <= choice <= len(SUPPLY_CATEGORIES)):
                        raise ValueError
                    supply = list(SUPPLY_CATEGORIES.keys())[choice - 1].lower()
                except Exception:
                    print("Invalid choice.")
                    continue

                if supply == "medical":
                    storage.add_supplies(supply, 1)
                    print("Added medical supplies to storage.")
                    continue

                try:
                    unit = SUPPLY_CATEGORIES[supply]
                    quantity = int(input(f"Enter quantity ({unit}): ").strip())
                    if quantity <= 0:
                        raise ValueError
                except Exception:
                    print("Invalid quantity.")
                    continue

                storage.add_supplies(supply, quantity)
                print(f"Added {format_supply_name(supply, quantity, unit)} to storage.")
                continue

            if action == "reports":
                while True:
                    print("\nDisaster Reports Management")
                    print("1. View reports (full report + address & coordinates)")
                    print("2. Delete report")
                    print("3. Back to main menu")
                    choice = input("Enter choice (1-3): ").strip()
                    if choice == "1":
                        reports = storage.get_reports()
                        if not reports:
                            print("No reports available.")
                        else:
                            print("\nSaved disaster reports:")
                            for i, r in enumerate(reports, start=1):
                                name = r.get("name", "Unknown")
                                dtype = r.get("disaster_type", "Unknown")
                                details_raw = r.get("details", "") or ""
                                description = _extract_description_from_details(details_raw)
                                addr, lat, lon = _extract_location_from_details(details_raw)
                                addr_display = addr or "Address unknown"
                                lat_display = lat if lat is not None else "N/A"
                                lon_display = lon if lon is not None else "N/A"
                                print(f"{i}. Reporter: {name}")
                                print(f"   Type   : {dtype}")
                                print(f"   Details: {description}")
                                print(f"   Address: {addr_display}")
                                print(f"   Lat/Lon: {lat_display} / {lon_display}")
                                print("-" * 60)
                    elif choice == "2":
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
                            print("Invalid input.")
                    elif choice == "3":
                        break
                    else:
                        print("Invalid choice.")
                continue

            if action == "check":
                supplies = storage.get_supplies()
                if not supplies:
                    print("No supplies in storage.")
                else:
                    print("\nCurrent supplies in storage:")
                    for supply, quantity in supplies.items():
                        supply_lower = supply.lower()
                        category = next((cat for cat in SUPPLY_CATEGORIES.keys() if cat.lower() == supply_lower), None)
                        if supply_lower == "medical":
                            status = "Available" if quantity > 0 else "Not available"
                            print(f"Medical supplies: {status}")
                        elif category:
                            unit = SUPPLY_CATEGORIES[category]
                            print(f"{format_supply_name(category, quantity, unit)}")
                        else:
                            print(f"{supply}: {quantity}")
                continue

            if action == "exit":
                break

            print("Invalid action. Please try again.")

    else:
        confirm = input("Enter 'non' to continue as non-government (or anything else to exit): ").strip().lower()
        if confirm != "non":
            print("Exiting.")
            return

        user_name = input("Enter your name: ").strip() or "Requester"
        storage.add_requester(user_name)

        report_choice = input("Would you like to file a disaster report? (y/n): ").strip().lower()
        if report_choice == "y":
            disaster_type = input("Type of natural disaster (e.g., flood, earthquake): ").strip()
            details = input("Please provide brief details about the situation: ").strip()

            print("\nPlease provide the location for this report (leave blank if unknown).")
            number = input("Address (number) : ").strip()
            street = input("Street name      : ").strip()
            city = input("City / Town      : ").strip()
            country = input("Country          : ").strip()

            coords = geocode(number or None, street, city, country)
            if coords is None:
                storage.add_report(user_name, disaster_type, details)
                print("Report saved.")
            else:
                lat, lon, display = coords
                details_with_location = f"{details} | location_resolved: {display} | lat:{lat} lon:{lon}"
                storage.add_report(user_name, disaster_type, details_with_location)
                print("Report saved.")

        while True:
            action = input("Enter 'request' to request aid, 'exit' to quit, or 'stations' to list stations: ").strip().lower()
            if action == "request":
                print("\nAvailable supplies:")
                supplies = storage.get_supplies()
                available_supplies: List[Tuple[str, Optional[str]]] = []
                for supply, quantity in supplies.items():
                    supply_lower = supply.lower()
                    category = next((cat for cat in SUPPLY_CATEGORIES.keys() if cat.lower() == supply_lower), None)
                    if category:
                        unit = SUPPLY_CATEGORIES[category]
                        if supply_lower == "medical" and quantity > 0:
                            print(f"{len(available_supplies) + 1}. Medical supplies (Available)")
                            available_supplies.append(("medical", None))
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
                    if supply == "medical":
                        quantity = 1
                    else:
                        print(f"\nAvailable {supply}: {max_available} {unit}")
                        quantity = int(input(f"Enter amount needed (1-{max_available}): ").strip())
                        if quantity <= 0 or quantity > max_available:
                            print("Invalid amount.")
                            continue
                    available_truck = next((n for n, av in trucks.trucks.items() if av), None)
                    if available_truck:
                        trucks.dispatch_truck(available_truck)
                        current_quantity = storage.check_inventory(supply)
                        if quantity > current_quantity:
                            print(f"Sorry, only {current_quantity} available now.")
                            continue
                        storage.remove_supplies(supply, quantity)
                        if supply == "medical":
                            print(f"{available_truck} dispatched with medical supplies to {user_name}'s location.")
                        else:
                            print(f"{available_truck} dispatched with {quantity} {unit} of {supply} to {user_name}'s location.")
                    else:
                        print("No trucks available to dispatch at the moment.")
                    more = input("\nWould you like to request more supplies? (y/n): ").strip().lower()
                    if more != "y":
                        break
                except Exception:
                    print("Invalid input. Please try again.")
            elif action == "stations":
                if help_stations.stations:
                    print("Known help stations (latitude, longitude):")
                    for sid, loc in help_stations.stations.items():
                        lat, lon = loc
                        print(f" - {sid}: latitude={lat}, longitude={lon}")
                else:
                    print("No help stations registered.")
            elif action == "exit":
                break
            else:
                print("Invalid action. Please try again.")


if __name__ == "__main__":
    main()