#!/usr/bin/env python3
"""
Script to generate master_data records for bevelling fields from CSV file.
Output: CSV format.

Usage:
    python3 populate_bevelling_master_data.py <form_fields.json> <csv_file> [output.csv]
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
            f.write(json.dumps({"sessionId":"c585cf","location":"populate_bevelling_master_data.py","message":msg,"data":data,"timestamp":int(time.time()*1000),"hypothesisId":hid}) + "\n")
    except Exception: pass
# #endregion

# FIELD MAPPING CONFIGURATION
FORM_TEMPLATE_ID = "564b7379-a7b8-4391-99f8-bd9b8c213d8d"

CSV_KEY_TO_FIELD_ID = {
    # Side A
    "side_a_top_bevel_degree": "4a6c3dbe-9164-4560-9a51-b2ab52faca39",
    "side_a_top_bevel_distance": "06ee05fc-c500-4e04-8a9f-20dc1520161d",
    "side_a_bot_bevel_degree": "c12ad342-cc2d-4499-b984-94a9c3cf9700",
    "side_a_bot_bevel_distance": "e5e46315-0341-4a26-92a6-539c6756796b",
    "side_a_root_face": "280912a0-d088-4305-b981-3eab9bd1c0f7",
    # Side B
    "side_b_top_bevel_degree": "79e305f5-4ee2-4fff-8cb2-d422eed1be5a",
    "side_b_top_bevel_distance": "4cd0cd7e-bdf0-416f-a49a-924f9d4f526f",
    "side_b_bot_bevel_degree": "d1e771b4-4669-493b-b353-f39f3fa6e4e2",
    "side_b_bot_bevel_distance": "2a103359-ff4e-4051-a829-25e6b8027fbc",
    "side_b_root_face": "eea2a3a6-3e98-4b2f-8765-58e073af7945",
    # Side C
    "side_c_top_bevel_degree": "c8a0400f-f581-46fb-ab10-83e495d815ac",
    "side_c_top_bevel_distance": "5fbd1e85-bf89-4931-ae4e-d9f4e427e11a",
    "side_c_bot_bevel_degree": "4c728c4a-799d-40b0-b729-d155be58f8d9",
    "side_c_bot_bevel_distance": "4b82d209-f62d-4680-a555-5c01c0116641",
    "side_c_root_face": "496fdb55-28eb-481e-92de-e12ae193ee26",
    # Side D
    "side_d_top_bevel_degree": "531d271f-e359-4963-bee4-6d646bb06919",
    "side_d_top_bevel_distance": "6fe4f846-2156-4b98-82cb-9c55886b6a18",
    "side_d_bot_bevel_degree": "e71a8af6-4286-42d7-a2ab-175cb893cdfe",
    "side_d_bot_bevel_distance": "8e140569-e29f-4007-bee9-31e17976efa3",
    "side_d_root_face": "f2d59e71-04f3-454d-8720-af6bc3089d29",
}

def parse_csv_data(csv_path):
    """
    Parse CSV or Excel file and extract bevelling data with MODEL ID and shell_code (LS).
    """
    rows = load_source_rows(csv_path)

    # Column indices (Section=model_id, LS=shell_code; col0 empty in this CSV layout)
    MODEL_ID_COL = 2  # Section (e.g. S1)
    LS_COL = 3        # LS / shell code (e.g. S1-L1)

    # Plate Bevelling Inspection - Top side
    TOP_ANGLE_COL = 33
    TOP_DI_COL = 36
    TOP_DE_COL = 37
    TOP_ROOT_COL = 45

    # Plate Bevelling Inspection - Bottom side
    BOT_ANGLE_COL = 38
    BOT_DI_COL = 41
    BOT_DE_COL = 42

    # Bevelling Plate Left Side
    LEFT_ANGLE_COL = 48
    LEFT_DI_COL = 51
    LEFT_DE_COL = 52
    LEFT_ROOT_COL = 55

    # Bevelling Plate Right Side
    RIGHT_ANGLE_COL = 58
    RIGHT_DI_COL = 61
    RIGHT_DE_COL = 62
    RIGHT_ROOT_COL = 65

    data_rows = []

    def clean_angle(val):
        if not val: return None
        val = str(val).strip().replace("°", "")
        try: return float(val)
        except: return None

    def clean_number(val):
        if not val: return None
        val = str(val).strip()
        try: return float(val)
        except: return None

    slice_rows = rows[4:]
    # #region agent log
    if slice_rows:
        r0 = slice_rows[0]
        _log("first row cols", {"col0": r0[MODEL_ID_COL][:30] if len(r0) > 0 else None, "col2": r0[2][:30] if len(r0) > 2 else None, "col3": r0[3][:30] if len(r0) > 3 else None, "col4": r0[4][:30] if len(r0) > 4 else None, "row_len": len(r0), "total_slice_rows": len(slice_rows)}, "H1_H2_H5")
    # #endregion
    for row_idx, row in enumerate(slice_rows, start=4):
        if len(row) < 66: continue

        model_id = row[MODEL_ID_COL].strip()
        shell_code = row[LS_COL].strip()

        if not model_id or not shell_code: continue

        # Helper to safely get column value
        def get_col(idx): return row[idx] if len(row) > idx else None

        bevelling_data = {
            # Side A (Top)
            "side_a_top_bevel_degree": clean_angle(get_col(TOP_ANGLE_COL)),
            "side_a_top_bevel_distance": clean_number(get_col(TOP_DE_COL)),
            "side_a_bot_bevel_degree": clean_angle(get_col(TOP_ANGLE_COL)),
            "side_a_bot_bevel_distance": clean_number(get_col(TOP_DI_COL)),
            "side_a_root_face": clean_number(get_col(TOP_ROOT_COL)),
            
            # Side B (Bottom)
            "side_b_top_bevel_degree": clean_angle(get_col(BOT_ANGLE_COL)),
            "side_b_top_bevel_distance": clean_number(get_col(BOT_DE_COL)),
            "side_b_bot_bevel_degree": clean_angle(get_col(BOT_ANGLE_COL)),
            "side_b_bot_bevel_distance": clean_number(get_col(BOT_DI_COL)),
            "side_b_root_face": clean_number(get_col(TOP_ROOT_COL)), # Same root face

            # Side C (Left)
            "side_c_top_bevel_degree": clean_angle(get_col(LEFT_ANGLE_COL)),
            "side_c_top_bevel_distance": clean_number(get_col(LEFT_DE_COL)),
            "side_c_bot_bevel_degree": clean_angle(get_col(LEFT_ANGLE_COL)),
            "side_c_bot_bevel_distance": clean_number(get_col(LEFT_DI_COL)),
            "side_c_root_face": clean_number(get_col(LEFT_ROOT_COL)),

            # Side D (Right)
            "side_d_top_bevel_degree": clean_angle(get_col(RIGHT_ANGLE_COL)),
            "side_d_top_bevel_distance": clean_number(get_col(RIGHT_DE_COL)),
            "side_d_bot_bevel_degree": clean_angle(get_col(RIGHT_ANGLE_COL)),
            "side_d_bot_bevel_distance": clean_number(get_col(RIGHT_DI_COL)),
            "side_d_root_face": clean_number(get_col(RIGHT_ROOT_COL)),
        }

        data_rows.append((model_id, shell_code, bevelling_data))

    return data_rows

def generate_master_data(csv_data):
    """
    Generate list of records for CSV output.
    """
    master_data_records = []

    for model_id, shell_code, bevelling_data in csv_data:
        for csv_key, value in bevelling_data.items():
            if value is None: continue

            form_field_id = CSV_KEY_TO_FIELD_ID.get(csv_key)
            if not form_field_id: continue

            record = {
                "form_template_id": FORM_TEMPLATE_ID,
                "form_field_id": form_field_id,
                "model_id": model_id,
                "code": shell_code,
                "value": str(value),
                "is_image": "false"
            }
            master_data_records.append(record)

    return master_data_records

def main():
    # Argument handling: allows running with just the CSV file argument
    if len(sys.argv) < 2:
        print("Usage: python3 populate_bevelling_master_data.py <csv_file> [output.csv] <model_id>")
        print("\nNote: The form_fields.json argument is no longer needed as mappings are hardcoded.")
        sys.exit(1)

    # Handle if user still passes form_fields.json as first arg (legacy support)
    arg_idx = 1
    if sys.argv[1].endswith(".json") and "fields" in sys.argv[1]:
        arg_idx = 2
        if len(sys.argv) < 3:
             print("Error: Please provide the CSV file path.")
             sys.exit(1)

    csv_path = Path(sys.argv[arg_idx])
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)

    # model_id is mandatory
    if len(sys.argv) <= arg_idx + 2 or not sys.argv[arg_idx + 2].strip():
        print("Error: model_id is required.")
        print("Usage: python3 populate_bevelling_master_data.py <csv_file> [output.csv] <model_id>")
        sys.exit(1)
    cli_model_id = sys.argv[arg_idx + 2].strip()

    print(f"Parsing {csv_path.name}...")
    csv_data = parse_csv_data(csv_path)

    # #region agent log
    _log("after parse", {"csv_data_len": len(csv_data)}, "H4")
    # #endregion
    if not csv_data:
        print("Warning: No data found in CSV")
        sys.exit(1)

    csv_data = [(cli_model_id, sc, d) for _, sc, d in csv_data]

    print(f"Found {len(csv_data)} rows in CSV")
    
    master_data_records = generate_master_data(csv_data)
    print(f"Generated {len(master_data_records)} master_data records")

    # CSV Output Setup
    headers = ["form_template_id", "form_field_id", "model_id", "code", "value", "is_image"]
    
    # Determine output stream (file or stdout)
    output_path = None
    if len(sys.argv) > arg_idx + 1:
        output_path = sys.argv[arg_idx + 1]
    
    if output_path:
        print(f"Saving to {output_path}...")
        try:
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(master_data_records)
            print("Done.")
        except IOError as e:
            print(f"Error writing to file: {e}")
    else:
        # Print to stdout
        writer = csv.DictWriter(sys.stdout, fieldnames=headers)
        writer.writeheader()
        writer.writerows(master_data_records)

if __name__ == "__main__":
    main()