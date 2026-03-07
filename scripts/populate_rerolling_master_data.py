#!/usr/bin/env python3
"""
Script to populate Re-Rolling Inspection master_data from CSV.
Output: CSV format.

Usage:
    python3 populate_rerolling_master_data.py <csv_file> [output.csv] <model_id>
"""

import csv
import re
import sys
from pathlib import Path

from source_loader import load_source_rows

# CONFIGURATION
FORM_TEMPLATE_ID = "1e05080b-c680-47ab-b438-c5e81a3efc7e"

# Mapping: Internal Key -> Form Field ID
FIELD_MAPPING = {
    "roundness_top": "62f7c8b0-5651-4d13-bde6-2ccfc0618349",      # Roundness (0-3mm) Top Side
    "roundness_bottom": "05ed134c-9ee3-44ea-b5c2-4ab235e7193c",   # Roundness (0-3mm) Bottom Side
    "circumference_top": "43f0a676-67f1-4a91-ace2-c9f2927e6f62",  # Circumference (± 6 mm) Top
    "circumference_bottom": "06c8efaf-7d23-4b40-9a56-e860973d20c5" # Circumference (± 6 mm) Bottom
}

def format_roundness(val):
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    # As per requirement: if value exists (e.g. "+3"), return "0-3"
    return "0-3"

def clean_number(val):
    if not val:
        return None
    val = str(val).strip()
    if not val:
        return None
    try:
        return float(val)
    except:
        return None

def parse_csv_data(csv_path):
    rows = load_source_rows(csv_path)

    # Column Indices
    MODEL_ID_COL = 2  # Section (e.g. S1); col0 empty in this CSV layout
    LS_COL = 3       # LS / shell code (e.g. S1-L1)
    BOTTOM_CF_COL = 68
    TOP_CF_COL = 71
    ROUNDNESS_UPPER_COL = 74
    ROUNDNESS_LOWER_COL = 75

    data_rows = []

    for row in rows[4:]:
        if len(row) < 76: continue

        model_id = row[MODEL_ID_COL].strip()
        shell_code = row[LS_COL].strip()

        if not model_id or not shell_code: continue

        # Helper to safely get col
        def get_val(idx): return row[idx] if len(row) > idx else ""

        row_data = {
            "roundness_top": format_roundness(get_val(ROUNDNESS_UPPER_COL)),
            "roundness_bottom": format_roundness(get_val(ROUNDNESS_LOWER_COL)),
            "circumference_top": clean_number(get_val(TOP_CF_COL)),
            "circumference_bottom": clean_number(get_val(BOTTOM_CF_COL))
        }

        data_rows.append((model_id, shell_code, row_data))

    return data_rows

def generate_records(parsed_data):
    records = []
    for model_id, shell_code, data in parsed_data:
        for key, value in data.items():
            if value is None: continue

            field_id = FIELD_MAPPING.get(key)
            if not field_id: continue

            records.append({
                "form_template_id": FORM_TEMPLATE_ID,
                "form_field_id": field_id,
                "model_id": model_id,
                "code": shell_code,
                "value": str(value),
                "is_image": "false"
            })
    return records

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 populate_rerolling_master_data.py <csv_file> [output.csv] <model_id>")
        print("   model_id is required.")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists(): sys.exit(f"Error: {csv_path} not found")

    cli_model_id = sys.argv[-1].strip()
    if not cli_model_id:
        print("Error: model_id is required.")
        sys.exit(1)

    print(f"Parsing {csv_path.name}...")
    parsed_data = parse_csv_data(csv_path)
    parsed_data = [(cli_model_id, sc, d) for _, sc, d in parsed_data]
    records = generate_records(parsed_data)
    print(f"Generated {len(records)} records.")

    headers = ["form_template_id", "form_field_id", "model_id", "code", "value", "is_image"]
    
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