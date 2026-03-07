#!/usr/bin/env python3
"""
Script to populate Plate Cutting Inspection master_data from CSV.
Output: CSV format.

Usage:
    python3 populate_cutting_master_data.py <csv_file> [output.csv] <model_id>
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
            f.write(json.dumps({"sessionId":"c585cf","location":"populate_cutting_master_data.py","message":msg,"data":data,"timestamp":int(time.time()*1000),"hypothesisId":hid}) + "\n")
    except Exception: pass
# #endregion

# CONFIGURATION
FORM_TEMPLATE_ID = "e9fc96f6-ae81-4d86-b1e3-a490a391aa67"

CSV_KEY_TO_FIELD_ID = {
    # R1 row
    "length_r1_e": "55bc00f4-a957-4424-a889-3fe3f36c45a0",
    "length_r1_f": "dd9de564-46cb-426b-b998-e9690e97cbac",
    "width_r1_j": "5394143d-0bba-4e75-a514-b0d53a19ea29",
    "diagonal_r1_m1": "e1149430-be3e-44d0-9f1e-e9ba11290c00",
    "diagonal_r1_m2": "f64cb558-8a12-49b2-a8ec-8bd1989c8317",
    # R2 row
    "length_r2_e": "f559beda-5c3e-4434-9cfd-e66fefc9805a",
    "length_r2_f": "d8888075-557a-4e32-bac4-1012b22aa5e8",
    "width_r2_j": "09735608-fe51-4078-a422-85e9013411db",
    # R3 row
    "width_r3_j": "e635b0cf-ab03-4d8b-b3fa-def40be1cbe7",
}

def clean_number(val):
    if not val: return None
    val = str(val).strip()
    try: return float(val)
    except: return None

def parse_csv_data(csv_path):
    rows = load_source_rows(csv_path)

    data_rows = []
    
    # Column indices (Section=model_id, LS=shell_code; col0 empty in this CSV layout)
    MODEL_ID_COL = 2  # Section (e.g. S1)
    LS_COL = 3        # LS / shell code (e.g. S1-L1)
    
    # Plate Cutting Inspection columns
    COL_E = 17  # Bottom Length
    COL_F = 18  # Top Length
    COL_J = 20  # Width Left
    COL_M = 22  # Diagonal

    slice_rows = rows[4:]
    # #region agent log
    if slice_rows:
        r0 = slice_rows[0]
        _log("first row cols", {"col0": r0[MODEL_ID_COL][:20] if len(r0) > 0 else None, "col2": r0[2][:20] if len(r0) > 2 else None, "col3": r0[3][:20] if len(r0) > 3 else None, "col4": r0[4][:20] if len(r0) > 4 else None, "row_len": len(r0), "total_slice_rows": len(slice_rows)}, "H1_H2_H3")
    # #endregion
    for row in slice_rows:
        if len(row) <= COL_M: continue

        model_id = row[MODEL_ID_COL].strip()
        shell_code = row[LS_COL].strip()

        if not model_id or not shell_code: continue

        # Helper to safely get col
        def get_val(idx): return row[idx] if len(row) > idx else None

        # Extract cutting inspection data
        cutting_data = {
            # R1 row
            "length_r1_e": clean_number(get_val(COL_E)),
            "length_r1_f": clean_number(get_val(COL_F)),
            "width_r1_j": clean_number(get_val(COL_J)),
            "diagonal_r1_m1": clean_number(get_val(COL_M)),
            "diagonal_r1_m2": clean_number(get_val(COL_M)),
            # R2 row (reusing columns as per logic)
            "length_r2_e": clean_number(get_val(COL_E)),
            "length_r2_f": clean_number(get_val(COL_F)),
            "width_r2_j": clean_number(get_val(COL_J)),
            # R3 row
            "width_r3_j": clean_number(get_val(COL_J)),
        }

        data_rows.append((model_id, shell_code, cutting_data))

    # #region agent log
    _log("after parse", {"data_rows_count": len(data_rows), "slice_rows_count": len(slice_rows)}, "H1_H3")
    # #endregion
    return data_rows

def generate_records(csv_data):
    records = []
    for model_id, shell_code, cutting_data in csv_data:
        for csv_key, value in cutting_data.items():
            if value is None: continue

            form_field_id = CSV_KEY_TO_FIELD_ID.get(csv_key)
            if not form_field_id: continue

            records.append({
                "form_template_id": FORM_TEMPLATE_ID,
                "form_field_id": form_field_id,
                "model_id": model_id,
                "code": shell_code,
                "value": str(value),
                "is_image": "false"
            })
    return records

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 populate_cutting_master_data.py <csv_file> [output.csv] <model_id>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists(): sys.exit(f"Error: {csv_path} not found")

    if len(sys.argv) < 3 or not sys.argv[-1].strip():
        print("Error: model_id is required.")
        sys.exit(1)
    cli_model_id = sys.argv[-1].strip()

    print(f"Parsing {csv_path.name}...")
    csv_data = parse_csv_data(csv_path)
    csv_data = [(cli_model_id, sc, d) for _, sc, d in csv_data]
    records = generate_records(csv_data)
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