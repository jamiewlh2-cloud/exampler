import json
import os
from typing import Optional, List, Dict
from datetime import datetime


class Storage:
    def __init__(self, persistence_file: Optional[str] = None):
        """Storage with optional JSON persistence.

        If persistence_file is provided (e.g. 'data/storage.json'), the storage will
        load existing supplies/reports from that file (if present) and save after changes.
        If persistence_file is None, storage is in-memory only (used by tests).
        """
        self.supplies: Dict[str, int] = {}
        # Keep a list of reports submitted by non-government users
        # Each report is a dict: {"name": str, "disaster_type": str, "details": str, "timestamp": str}
        self.reports: List[Dict] = []
        # Keep a list of known requester names
        self.requesters: List[str] = []

        self._persistence_file = persistence_file
        if self._persistence_file:
            # Ensure directory exists
            dirpath = os.path.dirname(self._persistence_file)
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)
            self._load()

    def _load(self):
        try:
            if os.path.exists(self._persistence_file):
                with open(self._persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Two possible formats supported for backward compatibility:
                        # 1) flat mapping of item -> int (older format)
                        # 2) structured mapping: {"supplies": {...}, "reports": [...], "requesters": [...]}
                        if 'supplies' in data:
                            self.supplies = {k: int(v) for k, v in data.get('supplies', {}).items()}
                            self.reports = data.get('reports', []) or []
                            self.requesters = data.get('requesters', []) or []
                        else:
                            # assume flat mapping
                            self.supplies = {k: int(v) for k, v in data.items()}
        except Exception:
            # If loading fails, keep defaults but don't raise in app runtime
            self.supplies = {}
            self.reports = []
            self.requesters = []

    def _save(self):
        if not self._persistence_file:
            return
        try:
            payload = {
                'supplies': self.supplies,
                'reports': self.reports,
                'requesters': self.requesters,
            }
            with open(self._persistence_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
        except Exception:
            # On failure to persist, ignore (do not crash the app)
            pass

    def _get_actual_key(self, item: str) -> str:
        """Find the actual key in storage matching the item name case-insensitively."""
        item_lower = item.lower()
        for key in self.supplies.keys():
            if key.lower() == item_lower:
                return key
        return item  # Return original if no match found

    # Supplies API
    def add_supplies(self, item: str, quantity: int):
        actual_key = self._get_actual_key(item)
        if actual_key in self.supplies:
            self.supplies[actual_key] += quantity
        else:
            self.supplies[actual_key] = quantity
        self._save()

    def check_inventory(self, item: str) -> int:
        # Return quantity for a specific item; 0 if not present
        actual_key = self._get_actual_key(item)
        return int(self.supplies.get(actual_key, 0))

    def remove_supplies(self, item: str, quantity: int) -> bool:
        # Remove quantity and raise ValueError if attempting to remove more than available
        actual_key = self._get_actual_key(item)
        if actual_key not in self.supplies:
            raise ValueError(f"Item '{item}' not found in storage")
        if self.supplies[actual_key] < quantity:
            raise ValueError(f"Not enough '{item}' in storage to remove {quantity}")
        self.supplies[actual_key] -= quantity
        if self.supplies[actual_key] == 0:
            del self.supplies[actual_key]
        self._save()
        return True

    # Requester/report API
    def add_requester(self, name: str):
        name = name.strip()
        if not name:
            return
        if name not in self.requesters:
            self.requesters.append(name)
            self._save()

    def add_report(self, name: str, disaster_type: str, details: str):
        report = {
            'name': name,
            'disaster_type': disaster_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        self.reports.append(report)
        # also ensure requester is recorded
        self.add_requester(name)
        self._save()

    def get_reports(self) -> List[Dict]:
        return list(self.reports)

    def delete_report(self, index: int) -> bool:
        """Delete a report by its index (1-based). Returns True if successful."""
        if 1 <= index <= len(self.reports):
            del self.reports[index - 1]
            self._save()
            return True
        return False

    def get_supplies(self) -> Dict[str, int]:
        """Get a copy of the current supplies inventory."""
        return dict(self.supplies)