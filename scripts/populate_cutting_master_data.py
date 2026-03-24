#!/usr/bin/env python3
"""
Script to populate Plate Cutting Inspection master_data from CSV.
Output: CSV format.

Usage:
    python3 populate_cutting_master_data.py <csv_file> [output.csv] <model_id>

Column mapping (0-indexed, based on actual Excel layout):
    col[0]  = Sr.No
    col[1]  = Section
    col[2]  = LS (shell code)
    col[3]  = Material Grade
    col[4]  = Thickness (T)
    col[5]  = Width (W)
    col[6]  = Length (L)
    col[7]  = Length Tol Lower
    col[8]  = Length Tol Upper
    col[9]  = Width Tol Lower
    col[10] = Width Tol Upper
    col[11] = Thickness Tol Lower
    col[12] = Thickness Tol Upper
    --- Plate Cutting Inspection ---
    col[13] = Bottom Length      (E)
    col[14] = Top Length         (F)
    col[15] = Width Left         (G)
    col[16] = Width Right        (J)
    col[17] = Thickness
    col[18] = Diagonal           (M1 - first diagonal measurement)
    col[19] = Length Tol Lower   (EN10029 Class-B)
    col[20] = Length Tol Upper
    col[21] = Width Tol Lower
    col[22] = Width Tol Upper
    col[23] = Thickness Tol Lower
    col[24] = Thickness Tol Upper
    col[25] = Diagonal Tol Lower
    col[26] = Diagonal Tol Upper (M2 - second diagonal measurement)
"""

import csv
import json
import sys
import time
from pathlib import Path

from source_loader import load_source_rows

# #region agent log
DEBUG_LOG = Path(__file__).resolve().parent / ".cursor" / "debug-c585cf.log"
def _log(msg, data, hid):
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "c585cf",
                "location": "populate_cutting_master_data.py",
                "message": msg,
                "data": data,
                "timestamp": int(time.time() * 1000),
                "hypothesisId": hid
            }) + "\n")
    except Exception:
        pass
# #endregion

# CONFIGURATION
FORM_TEMPLATE_ID = "e9fc96f6-ae81-4d86-b1e3-a490a391aa67"

CSV_KEY_TO_FIELD_ID = {
    # R1 row — Plate Cutting Inspection actual measurements
    "length_r1_e": "55bc00f4-a957-4424-a889-3fe3f36c45a0",   # Bottom Length
    "length_r1_f": "dd9de564-46cb-426b-b998-e9690e97cbac",   # Top Length
    "width_r1_j":  "5394143d-0bba-4e75-a514-b0d53a19ea29",   # Width Right
    "diagonal_r1_m1": "e1149430-be3e-44d0-9f1e-e9ba11290c00", # Diagonal 1
    "diagonal_r1_m2": "f64cb558-8a12-49b2-a8ec-8bd1989c8317", # Diagonal 2
    # R2 row
    "length_r2_e": "f559beda-5c3e-4434-9cfd-e66fefc9805a",
    "length_r2_f": "d8888075-557a-4e32-bac4-1012b22aa5e8",
    "width_r2_j":  "09735608-fe51-4078-a422-85e9013411db",
    # R3 row
    "width_r3_j":  "e635b0cf-ab03-4d8b-b3fa-def40be1cbe7",
}

# ── Correct column indices (0-based) ──────────────────────────────────────────
SR_NO_COL       = 0
SECTION_COL     = 2
LS_COL          = 3   # Shell code  e.g. S1-L1
GRADE_COL       = 4

# Plate Cutting Inspection
COL_E           = 14  # Bottom Length       ← was 17 (WRONG)
COL_F           = 15  # Top Length          ← was 18 (WRONG)
COL_G           = 16  # Width Left          ← NEW (was missing)
COL_J           = 17  # Width Right         ← was 20 (WRONG)
COL_THICKNESS   = 18  # Thickness
COL_M1          = 19  # Diagonal 1          ← was 22 (WRONG — that col is "+3")
COL_M2          = 26  # Diagonal 2 (second diagonal value at end of EN10029 block)
# ──────────────────────────────────────────────────────────────────────────────

def clean_number(val):
    if not val:
        return None
    val = str(val).strip()
    try:
        return float(val)
    except ValueError:
        return None

def parse_csv_data(csv_path):
    rows = load_source_rows(csv_path)
    data_rows = []

    # Skip header rows (first 4 rows are headers/labels)
    slice_rows = rows[4:]

    # Debug: log first row
    if slice_rows:
        r0 = slice_rows[0]
        _log("first data row", {
            "LS":        r0[LS_COL]      if len(r0) > LS_COL      else None,
            "col_E(13)": r0[COL_E]       if len(r0) > COL_E       else None,
            "col_F(14)": r0[COL_F]       if len(r0) > COL_F       else None,
            "col_G(15)": r0[COL_G]       if len(r0) > COL_G       else None,
            "col_J(16)": r0[COL_J]       if len(r0) > COL_J       else None,
            "col_T(17)": r0[COL_THICKNESS] if len(r0) > COL_THICKNESS else None,
            "col_M1(18)":r0[COL_M1]      if len(r0) > COL_M1      else None,
            "col_M2(26)":r0[COL_M2]      if len(r0) > COL_M2      else None,
            "row_len":   len(r0),
            "total_slice_rows": len(slice_rows),
        }, "H1_H2_H3")

    for row in slice_rows:
        # Need at least up to col 26 (M2)
        if len(row) <= COL_M2:
            continue

        section    = row[LS_COL].strip()  # Use LS column for model_id
        shell_code = row[LS_COL].strip()

        if not shell_code:
            continue

        def get_val(idx):
            return row[idx] if len(row) > idx else None

        cutting_data = {
            # R1 — actual measured values from Plate Cutting Inspection
            "length_r1_e":    clean_number(get_val(COL_E)),    # Bottom Length
            "length_r1_f":    clean_number(get_val(COL_F)),    # Top Length
            "width_r1_j":     clean_number(get_val(COL_J)),    # Width Right
            "diagonal_r1_m1": clean_number(get_val(COL_M1)),   # Diagonal 1
            "diagonal_r1_m2": clean_number(get_val(COL_M2)),   # Diagonal 2

            # R2 — reuse same measurement columns (same physical measurements, different form rows)
            "length_r2_e":    clean_number(get_val(COL_E)),
            "length_r2_f":    clean_number(get_val(COL_F)),
            "width_r2_j":     clean_number(get_val(COL_J)),

            # R3
            "width_r3_j":     clean_number(get_val(COL_J)),
        }

        data_rows.append((section, shell_code, cutting_data))

    _log("after parse", {
        "data_rows_count": len(data_rows),
        "slice_rows_count": len(slice_rows)
    }, "H1_H3")

    return data_rows

def generate_records(csv_data):
    records = []
    for model_id, shell_code, cutting_data in csv_data:
        for csv_key, value in cutting_data.items():
            if value is None:
                continue

            form_field_id = CSV_KEY_TO_FIELD_ID.get(csv_key)
            if not form_field_id:
                continue

            records.append({
                "form_template_id": FORM_TEMPLATE_ID,
                "form_field_id":    form_field_id,
                "model_id":         model_id,
                "code":             shell_code,
                "value":            str(value),
                "is_image":         "false"
            })
    return records

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 populate_cutting_master_data.py <csv_file> [output.csv] <model_id>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        sys.exit(f"Error: {csv_path} not found")

    if len(sys.argv) < 3 or not sys.argv[-1].strip():
        print("Error: model_id is required.")
        sys.exit(1)
    cli_model_id = sys.argv[-1].strip()

    print(f"Parsing {csv_path.name}...")
    csv_data = parse_csv_data(csv_path)

    # Override section/model_id with CLI-provided value
    csv_data = [(cli_model_id, sc, d) for _, sc, d in csv_data]

    records = generate_records(csv_data)
    print(f"Generated {len(records)} records.")

    headers = ["form_template_id", "form_field_id", "model_id", "code", "value", "is_image"]

    output_file = sys.stdout
    if len(sys.argv) > 3:
        output_path = sys.argv[2]
        output_file = open(output_path, "w", encoding="utf-8", newline="")
        print(f"Saving to {output_path}...")

    try:
        writer = csv.DictWriter(output_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)
    finally:
        if output_file is not sys.stdout:
            output_file.close()

if __name__ == "__main__":
    main()