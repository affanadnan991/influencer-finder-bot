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
    """Saves matched profiles to numbered CSV files."""

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def save_results(self, profiles: list[dict]) -> str:
        """Save profiles to a new numbered CSV file. Returns the file path."""
        if not profiles:
            return ""

        csv_number = _get_next_csv_number()
        filepath = os.path.join(OUTPUT_DIR, f"{csv_number}.csv")

        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for profile in profiles:
                row = {}
                for col in CSV_COLUMNS:
                    row[col] = profile.get(col, "")
                writer.writerow(row)

        print(f"\n  CSV saved: {filepath} ({len(profiles)} profiles)")
        return filepath
