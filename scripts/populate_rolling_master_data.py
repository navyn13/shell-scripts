#!/usr/bin/env python3
"""
Script to populate Rolling Inspection master_data from CSV.
Output: CSV format.

Usage:
    python3 populate_rolling_master_data.py <csv_file> [output.csv] <model_id>

Column map (0-indexed):
    [1]  Section       (e.g. S1)
    [2]  LS            (e.g. S1-L1)
    [68] Roundness Upper (+3)   ← was 74 (WRONG — was Travel Speed Lower "23")
    [69] Roundness Lower (0)    ← was 75 (WRONG — was Outside Current Upper "221")
"""

import csv
import re
import sys
from pathlib import Path

from source_loader import load_source_rows

# CONFIGURATION
FORM_TEMPLATE_ID = "6c12d436-d583-45cb-bdcc-d511716ee70b"

FIELD_MAPPING = {
    "roundness_top":    "46cf5a34-cf38-4c7d-8116-c93df2d57607",  # Roundness(0-3mm) Top Side
    "roundness_bottom": "a704e351-aea7-4715-a195-8a2760e66ad2",  # Roundness(0-3mm) Bottom Side
}

# ── Correct column indices (0-based) ──────────────────────────────────────────
SECTION_COL         = 2   # Section e.g. S1
LS_COL              = 3   # LS e.g. S1-L1
ROUNDNESS_UPPER_COL = 69  # Roundness Upper     ← was 74 (WRONG — was "23" Travel Speed)
ROUNDNESS_LOWER_COL = 70  # Roundness Lower     ← was 75 (WRONG — was "221" Outside Current)

MIN_COLS = ROUNDNESS_LOWER_COL + 1  # = 70
# ──────────────────────────────────────────────────────────────────────────────

def extract_roundness_value(val):
    """Extract roundness number from strings like '+3', '0', '-3'. Max 3."""
    if not val:
        return 3  # Default to 3 for 0-3mm range
    val_str = str(val).strip()
    match = re.search(r"([+-]?\d+)", val_str)
    if match:
        num = int(match.group(1))
        return min(abs(num), 3)
    return 3  # Default

def parse_csv_data(csv_path):
    rows = load_source_rows(csv_path)
    data_rows = []

    for row in rows[4:]:
        if len(row) < MIN_COLS:
            continue

        section    = row[LS_COL].strip()  # Use LS column for model_id
        shell_code = row[LS_COL].strip()

        if not shell_code:
            continue

        r_upper_raw = row[ROUNDNESS_UPPER_COL] if len(row) > ROUNDNESS_UPPER_COL else ""
        r_lower_raw = row[ROUNDNESS_LOWER_COL] if len(row) > ROUNDNESS_LOWER_COL else ""

        roundness_top = extract_roundness_value(r_upper_raw)

        # Bottom side: if value is 0, default to 3
        roundness_bottom = extract_roundness_value(r_lower_raw) if r_lower_raw else 3
        if roundness_bottom == 0:
            roundness_bottom = 3

        data_rows.append((section, shell_code, {
            "roundness_top":    roundness_top,
            "roundness_bottom": roundness_bottom,
        }))

    return data_rows

def generate_records(parsed_data):
    records = []
    for model_id, shell_code, data in parsed_data:
        for key, value in data.items():
            if value is None:
                continue
            field_id = FIELD_MAPPING.get(key)
            if not field_id:
                continue
            records.append({
                "form_template_id": FORM_TEMPLATE_ID,
                "form_field_id":    field_id,
                "model_id":         model_id,
                "code":             shell_code,
                "value":            str(value),
                "is_image":         "false"
            })
    return records

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 populate_rolling_master_data.py <csv_file> [output.csv] <model_id>")
        print("   model_id is required.")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        sys.exit(f"Error: {csv_path} not found")

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