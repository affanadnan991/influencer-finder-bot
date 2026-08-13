"""Simple CSV storage for discovered profiles. Each run creates a new numbered file."""

import os
import csv
from datetime import datetime

from config import OUTPUT_DIR, CSV_COLUMNS


def _get_next_csv_number() -> int:
    """Find the next available CSV number (1.csv, 2.csv, 3.csv...)."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing = []
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(".csv"):
            name = filename[:-4]  # remove .csv
            try:
                existing.append(int(name))
            except ValueError:
                continue
    if not existing:
        return 1
    return max(existing) + 1


class ProfileStore:
    """Saves matched profiles to a numbered CSV file, one row at a time as they're found."""

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.filepath: str = ""

    def start_new_file(self) -> str:
        """Create a new numbered CSV file with just the header. Returns the file path."""
        csv_number = _get_next_csv_number()
        self.filepath = os.path.join(OUTPUT_DIR, f"{csv_number}.csv")
        with open(self.filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
        return self.filepath

    def append_profile(self, profile: dict) -> None:
        """Append a single matched profile to the CSV file immediately."""
        if not self.filepath:
            self.start_new_file()
        row = {col: profile.get(col, "") for col in CSV_COLUMNS}
        with open(self.filepath, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writerow(row)
