#!/usr/bin/env python3
"""
Script to populate tolerance master_data from Excel/CSV.
Output: CSV format.

Usage:
    python3 tolerance_fetcher.py <source_file> [output.csv] <model_id>

Reads LS codes and tolerance lower/upper columns from Excel.
Combines each pair as "lower , upper" (e.g. "-0 , +50").

Column map (0-indexed):
    [3]  LS  (e.g. S1-L1)
    [8]  Length tolerance lower
    [9]  Length tolerance upper
    [10] Width tolerance lower
    [11] Width tolerance upper
    [12] Thickness tolerance lower
    [13] Thickness tolerance upper
"""

import csv
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from source_loader import load_source_rows

# CONFIGURATION
FORM_TEMPLATE_ID = "31220105-c309-4331-b365-6f0e6c39e05b"

FIELD_MAPPING = {
    "L": "635a8717-b81e-484f-9e23-209c530e99f0",
    "W": "9110d919-c597-4bf0-9007-73c633b5f1c3",
    "T": "f1f0ef78-a4f1-4fb6-913c-3e197e45f457",
}

TOLERANCE_COLUMNS = {
    "L": (8, 9),
    "W": (10, 11),
    "T": (12, 13),
}

LS_COL = 3
MIN_COLS = 14
DATA_START_ROW = 5  # First row of actual data (0-indexed)


def format_tolerance(val):
    """Preserve tolerance strings as shown in Excel (e.g. -0, +50)."""
    if val is None:
        return ""
    return str(val).strip()


def combine_tolerance(lower, upper):
    """Combine lower/upper tolerance values into a single string."""
    lower = format_tolerance(lower)
    upper = format_tolerance(upper)

    if lower and upper:
        return f"{lower} , {upper}"
    if lower:
        return lower
    if upper:
        return upper
    return ""


def parse_source_data(source_path):
    """Parse rows and extract (ls_code, {L, W, T}) tolerance tuples."""
    rows = load_source_rows(source_path)
    parsed = []

    for row in rows[DATA_START_ROW:]:
        if len(row) < MIN_COLS:
            continue

        ls_code = str(row[LS_COL]).strip()
        if not ls_code:
            continue

        values = {}
        for field_name, (lower_col, upper_col) in TOLERANCE_COLUMNS.items():
            lower = row[lower_col] if len(row) > lower_col else ""
            upper = row[upper_col] if len(row) > upper_col else ""
            values[field_name] = combine_tolerance(lower, upper)

        parsed.append((ls_code, values))

    return parsed


def generate_records(parsed_data, model_id):
    """Convert parsed data into output records."""
    now = datetime.now(timezone.utc).isoformat()
    records = []
    for ls_code, values in parsed_data:
        for field_name, value in values.items():
            if value == "":
                continue
            field_id = FIELD_MAPPING.get(field_name)
            if not field_id:
                continue
            records.append({
                "id":               str(uuid.uuid4()),
                "form_template_id": FORM_TEMPLATE_ID,
                "form_field_id":    field_id,
                "model_id":         model_id,
                "code":             ls_code,
                "value":            value,
                "created_at":       now,
                "updated_at":       now,
                "is_image":         "false",
            })
    return records


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 tolerance_fetcher.py <source_file> [output.csv] <model_id>")
        print("   model_id is required.")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    if not source_path.exists():
        sys.exit(f"Error: {source_path} not found")

    cli_model_id = sys.argv[-1].strip()
    if not cli_model_id:
        print("Error: model_id is required.")
        sys.exit(1)

    print(f"Parsing {source_path.name}...")
    parsed_data = parse_source_data(source_path)
    records = generate_records(parsed_data, cli_model_id)
    print(f"Generated {len(records)} records.")

    headers = ["id", "form_template_id", "form_field_id", "model_id", "value", "created_at", "updated_at", "code", "is_image"]

    output_file = sys.stdout
    if len(sys.argv) > 3:
        output_file = open(sys.argv[2], "w", encoding="utf-8", newline="")
        print(f"Saving to {sys.argv[2]}...")

    try:
        writer = csv.DictWriter(output_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)
    finally:
        if output_file is not sys.stdout:
            output_file.close()


if __name__ == "__main__":
    main()
