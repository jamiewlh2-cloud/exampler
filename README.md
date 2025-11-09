# Aid Dispatch Project

This project is designed to facilitate the management and dispatch of aid supplies from government entities to non-government organizations or individuals in need. It includes a storage system for necessary supplies, a truck dispatch system, and a mechanism for non-government users to request aid based on their proximity to help stations.

## Project Structure

```
aid-dispatch-project
├── src
│   ├── main.py          # Entry point of the application
│   ├── gov.py           # Government user functionalities
│   ├── non_gov.py       # Non-government user functionalities
│   ├── storage.py       # Storage management for supplies
│   ├── trucks.py        # Truck dispatch management
│   ├── help_stations.py  # Management of help stations
│   └── utils.py         # Utility functions for calculations
├── data
│   └── stations.json    # JSON file containing help station data
├── tests
│   ├── test_storage.py   # Unit tests for the Storage class
│   ├── test_dispatch.py   # Unit tests for the Truck class
│   └── test_proximity.py  # Unit tests for the HelpStation class
├── requirements.txt      # Project dependencies
├── README.md             # Project documentation
└── .gitignore            # Files to ignore in version control
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd aid-dispatch-project
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/main.py
   ```

## Usage

- Government users can input necessary supplies and manage the inventory.
- Non-government users can request aid and receive information about the nearest help stations.

## Examples

- Government input: Add supplies to the storage.
- Non-government request: Request aid and receive truck dispatch or distance to the nearest help station.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.