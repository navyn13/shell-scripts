#!/usr/bin/env python3
"""
Script to populate Re-Rolling Inspection master_data from CSV.
Output: CSV format.

Usage:
    python3 populate_rerolling_master_data.py <csv_file> [output.csv] <model_id>

Full Shell Rolling column map (0-indexed):
    [1]  Section       (e.g. S1)
    [2]  LS            (e.g. S1-L1)
    [62] Bottom CF                  ← was 68 (WRONG — was Roundness Upper "+3")
    [63] Bottom CF Upper (+6)
    [64] Bottom CF Lower (-6)
    [65] Top CF                     ← was 71 (WRONG — was Top CF Lower "-6")
    [66] Top CF Upper (+6)
    [67] Top CF Lower (-6)
    [68] Roundness Upper (+3)       ← was 74 (WRONG — was Travel Speed Lower "23")
    [69] Roundness Lower (0)        ← was 75 (WRONG — was Outside Current Upper "221")
"""

import csv
import sys
from pathlib import Path

from source_loader import load_source_rows

# CONFIGURATION
FORM_TEMPLATE_ID = "1e05080b-c680-47ab-b438-c5e81a3efc7e"

FIELD_MAPPING = {
    "roundness_top":        "62f7c8b0-5651-4d13-bde6-2ccfc0618349",  # Roundness (0-3mm) Top Side
    "roundness_bottom":     "05ed134c-9ee3-44ea-b5c2-4ab235e7193c",  # Roundness (0-3mm) Bottom Side
    "circumference_top":    "43f0a676-67f1-4a91-ace2-c9f2927e6f62",  # Circumference (± 6 mm) Top
    "circumference_bottom": "06c8efaf-7d23-4b40-9a56-e860973d20c5",  # Circumference (± 6 mm) Bottom
}

# ── Correct column indices (0-based) ──────────────────────────────────────────
SECTION_COL          = 2   # Section e.g. S1
LS_COL               = 3   # LS e.g. S1-L1

BOTTOM_CF_COL        = 63  # Bottom CF           ← was 68 (WRONG — was Roundness "+3")
TOP_CF_COL           = 66  # Top CF              ← was 71 (WRONG — was "-6" tolerance)
ROUNDNESS_UPPER_COL  = 69  # Roundness Upper     ← was 74 (WRONG — was Travel Speed "23")
ROUNDNESS_LOWER_COL  = 70  # Roundness Lower     ← was 75 (WRONG — was Outside Current "221")

MIN_COLS = ROUNDNESS_LOWER_COL + 1  # = 70
# ──────────────────────────────────────────────────────────────────────────────

def format_roundness(val):
    """If a roundness value exists, return the display string '0-3'."""
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    return "0-3"

def clean_number(val):
    if not val:
        return None
    val = str(val).strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None

def parse_csv_data(csv_path):
    rows = load_source_rows(csv_path)
    data_rows = []

    # Skip first 4 header rows
    for row in rows[4:]:
        if len(row) < MIN_COLS:
            continue

        section    = row[LS_COL].strip()  # Use LS column for model_id
        shell_code = row[LS_COL].strip()

        if not shell_code:
            continue

        def get_val(idx):
            return row[idx] if len(row) > idx else ""

        row_data = {
            "roundness_top":        format_roundness(get_val(ROUNDNESS_UPPER_COL)),
            "roundness_bottom":     format_roundness(get_val(ROUNDNESS_LOWER_COL)),
            "circumference_top":    clean_number(get_val(TOP_CF_COL)),
            "circumference_bottom": clean_number(get_val(BOTTOM_CF_COL)),
        }

        data_rows.append((section, shell_code, row_data))

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
        print("Usage: python3 populate_rerolling_master_data.py <csv_file> [output.csv] <model_id>")
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