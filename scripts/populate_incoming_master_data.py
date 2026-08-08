#!/usr/bin/env python3
"""
Script to populate Incoming Inspection master_data from Excel/CSV.
Output: CSV format.

Usage:
    python3 populate_incoming_master_data.py <source_file> [output.csv] <model_id>

Reads LS codes and T, W, L columns from Excel.
Maps T, W, L to specific form field IDs.

Column map (0-indexed):
    [3] LS  (e.g. S1-L1)
    [5] T   (Thickness)
    [6] W   (Width)
    [7] L   (Length)
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
    "T": "b6b34ec6-1727-4354-9002-b96107c514ee",
    "W": "d31a6801-10c5-4f55-b15c-d6b5701b8fba",
    "L": "917767d7-4aee-4b58-80de-bafce3b0065d",
}

LS_COL = 3
T_COL  = 5
W_COL  = 6
L_COL  = 7

MIN_COLS = L_COL + 1
DATA_START_ROW = 5  # First row of actual data (0-indexed)


def format_value(val):
    """
    Format a cell value as a clean string.
    Removes trailing '.0' for integer floats (e.g. 48.0 -> 48).
    Keeps exact decimal precision for non-integer floats.
    """
    if val is None or val == "":
        return ""

    s = str(val).strip()
    if not s:
        return ""

    # Try to parse as a number
    try:
        f = float(s)
        # If it's a whole number, format without decimal
        if f.is_integer():
            return str(int(f))
        # Otherwise, keep as-is but strip any trailing zeros from the original string
        return s
    except ValueError:
        return s


def parse_source_data(source_path):
    """Parse rows and extract (ls_code, {T, W, L}) tuples."""
    rows = load_source_rows(source_path)
    parsed = []

    for row in rows[DATA_START_ROW:]:
        if len(row) < MIN_COLS:
            continue

        ls_code = str(row[LS_COL]).strip()
        if not ls_code:
            continue

        values = {
            "T": format_value(row[T_COL]) if len(row) > T_COL else "",
            "W": format_value(row[W_COL]) if len(row) > W_COL else "",
            "L": format_value(row[L_COL]) if len(row) > L_COL else "",
        }
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
        print("Usage: python3 populate_incoming_master_data.py <source_file> [output.csv] <model_id>")
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
