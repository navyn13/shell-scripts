#!/usr/bin/env python3
"""
Script to generate master_data records for bevelling fields from CSV file.
Output: CSV format.

Usage:
    python3 populate_bevelling_master_data.py <csv_file> [output.csv] <model_id>

Full column map (0-indexed) from Excel:
    [0]  Sr.No
    [1]  Section  (e.g. S1)
    [2]  LS       (e.g. S1-L1)
    [3]  Material Grade
    [4]  Thickness (T)
    [5]  Width (W)
    [6]  Length (L)
    [7]  Length Tol Lower
    [8]  Length Tol Upper
    [9]  Width Tol Lower
    [10] Width Tol Upper
    [11] Thickness Tol Lower
    [12] Thickness Tol Upper
    --- Plate Cutting Inspection ---
    [13] Bottom Length (E)
    [14] Top Length (F)
    [15] Width Left (G)
    [16] Width Right (J)
    [17] Thickness
    [18] Diagonal (M1)
    [19] Length Tol Lower (EN10029)
    [20] Length Tol Upper (EN10029)
    [21] Width Tol Lower (EN10029)
    [22] Width Tol Upper (EN10029)
    [23] Thickness Tol Lower (EN10029)
    [24] Thickness Tol Upper (EN10029)
    [25] Diagonal Tol Lower
    [26] Diagonal Tol Upper (M2)
    --- Plate Bevelling - LEFT SIDE ---
    [27] Bevel Left TOP Angle (A)
    [28] Bevel Left TOP Angle +2°
    [29] Bevel Left TOP Angle -2°
    [30] Bevel Left TOP DI
    [31] Bevel Left TOP DE
    [32] Bevel Left BOT Angle (A)
    [33] Bevel Left BOT Angle +2°
    [34] Bevel Left BOT Angle -2°
    [35] Bevel Left BOT DI
    [36] Bevel Left BOT DE
    [37] Root Face Tol +1
    [38] Root Face Tol -1
    [39] Root Face LEFT (R)          ← actual measurement
    [40] Root Face +1
    [41] Root Face -1
    --- Plate Bevelling - RIGHT SIDE TOP ---
    [42] Bevel Right TOP Angle (A)
    [43] Bevel Right TOP Angle +2
    [44] Bevel Right TOP Angle -2
    [45] Bevel Right TOP DI
    [46] Bevel Right TOP DE
    [47] Root Face Tol +1
    [48] Root Face Tol -1
    [49] Root Face RIGHT TOP (R)     ← actual measurement
    [50] Root Face +1
    [51] Root Face -1
    --- Plate Bevelling - RIGHT SIDE BOTTOM ---
    [52] Bevel Right BOT Angle (A)
    [53] Bevel Right BOT Angle +2
    [54] Bevel Right BOT Angle -2
    [55] Bevel Right BOT DI
    [56] Bevel Right BOT DE
    [57] Root Face Tol +1
    [58] Root Face Tol -1
    [59] Root Face RIGHT BOT (R)     ← actual measurement
    [60] Root Face +1
    [61] Root Face -1
    --- Shell Rolling ---
    [62] Bottom CF
    ...
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
                "location": "populate_bevelling_master_data.py",
                "message": msg,
                "data": data,
                "timestamp": int(time.time() * 1000),
                "hypothesisId": hid
            }) + "\n")
    except Exception:
        pass
# #endregion

# CONFIGURATION
FORM_TEMPLATE_ID = "564b7379-a7b8-4391-99f8-bd9b8c213d8d"

CSV_KEY_TO_FIELD_ID = {
    # Side A — Bevel Left Top
    "side_a_top_bevel_degree":    "4a6c3dbe-9164-4560-9a51-b2ab52faca39",
    "side_a_top_bevel_distance":  "06ee05fc-c500-4e04-8a9f-20dc1520161d",
    # Side A — Bevel Left Bottom
    "side_a_bot_bevel_degree":    "c12ad342-cc2d-4499-b984-94a9c3cf9700",
    "side_a_bot_bevel_distance":  "e5e46315-0341-4a26-92a6-539c6756796b",
    # Side A — Root Face (Left Side)
    "side_a_root_face":           "280912a0-d088-4305-b981-3eab9bd1c0f7",
    # Side B — Bevel Right Top
    "side_b_top_bevel_degree":    "79e305f5-4ee2-4fff-8cb2-d422eed1be5a",
    "side_b_top_bevel_distance":  "4cd0cd7e-bdf0-416f-a49a-924f9d4f526f",
    # Side B — Bevel Right Bottom
    "side_b_bot_bevel_degree":    "d1e771b4-4669-493b-b353-f39f3fa6e4e2",
    "side_b_bot_bevel_distance":  "2a103359-ff4e-4051-a829-25e6b8027fbc",
    # Side B — Root Face (Right Top Side)
    "side_b_root_face":           "eea2a3a6-3e98-4b2f-8765-58e073af7945",
    # Side C (mapped to Right Bot if needed — adjust UUIDs as required)
    "side_c_top_bevel_degree":    "c8a0400f-f581-46fb-ab10-83e495d815ac",
    "side_c_top_bevel_distance":  "5fbd1e85-bf89-4931-ae4e-d9f4e427e11a",
    "side_c_bot_bevel_degree":    "4c728c4a-799d-40b0-b729-d155be58f8d9",
    "side_c_bot_bevel_distance":  "4b82d209-f62d-4680-a555-5c01c0116641",
    "side_c_root_face":           "496fdb55-28eb-481e-92de-e12ae193ee26",
    # Side D
    "side_d_top_bevel_degree":    "531d271f-e359-4963-bee4-6d646bb06919",
    "side_d_top_bevel_distance":  "6fe4f846-2156-4b98-82cb-9c55886b6a18",
    "side_d_bot_bevel_degree":    "e71a8af6-4286-42d7-a2ab-175cb893cdfe",
    "side_d_bot_bevel_distance":  "8e140569-e29f-4007-bee9-31e17976efa3",
    "side_d_root_face":           "f2d59e71-04f3-454d-8720-af6bc3089d29",
}

# ── Correct column indices (0-based) ──────────────────────────────────────────
SECTION_COL = 2   # Section e.g. S1
LS_COL      = 3   # Shell code e.g. S1-L1

# Plate Bevelling - LEFT SIDE
LEFT_TOP_ANGLE_COL = 28   # Bevel Left Top Angle (A)   ← was 33 (WRONG — was +2° tolerance)
LEFT_TOP_DI_COL    = 31   # Bevel Left Top DI           ← was 36 (WRONG — was Left Bot DE)
LEFT_TOP_DE_COL    = 32   # Bevel Left Top DE           ← was 37 (WRONG — was root face +1)
LEFT_BOT_ANGLE_COL = 33   # Bevel Left Bot Angle (A)   ← was 38 (WRONG — was root face -1)
LEFT_BOT_DI_COL    = 36   # Bevel Left Bot DI           ← was 41 (WRONG — was root face -1)
LEFT_BOT_DE_COL    = 37   # Bevel Left Bot DE           ← was 42 (WRONG — was Right Top Angle)
LEFT_ROOT_COL      = 40   # Root Face LEFT (R)          ← was 45 (WRONG — was Right Top DI)

# Plate Bevelling - RIGHT SIDE TOP
RIGHT_TOP_ANGLE_COL = 43  # Bevel Right Top Angle (A)  ← was 48 (WRONG — was root face -1)
RIGHT_TOP_DI_COL    = 46  # Bevel Right Top DI          ← was 51 (WRONG — was root face -1)
RIGHT_TOP_DE_COL    = 47  # Bevel Right Top DE          ← was 52 (WRONG — was Right Bot Angle)
RIGHT_TOP_ROOT_COL  = 50  # Root Face RIGHT TOP (R)     ← was 55 (WRONG — was Right Bot DI)

# Plate Bevelling - RIGHT SIDE BOTTOM
RIGHT_BOT_ANGLE_COL = 53  # Bevel Right Bot Angle (A)  ← was 58 (WRONG — was root face -1)
RIGHT_BOT_DI_COL    = 56  # Bevel Right Bot DI          ← was 61 (WRONG — was root face -1)
RIGHT_BOT_DE_COL    = 57  # Bevel Right Bot DE          ← was 62 (WRONG — was Bottom CF)
RIGHT_BOT_ROOT_COL  = 60  # Root Face RIGHT BOT (R)     ← was 65 (WRONG — was Top CF)

# Minimum columns needed to process a row
MIN_COLS = RIGHT_BOT_ROOT_COL + 1  # = 60
# ──────────────────────────────────────────────────────────────────────────────

def clean_angle(val):
    if not val:
        return None
    val = str(val).strip().replace("°", "")
    try:
        return float(val)
    except ValueError:
        return None

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
            "Section(1)":         r0[SECTION_COL]       if len(r0) > SECTION_COL       else None,
            "LS(2)":              r0[LS_COL]             if len(r0) > LS_COL             else None,
            "LeftTopAngle(27)":   r0[LEFT_TOP_ANGLE_COL] if len(r0) > LEFT_TOP_ANGLE_COL else None,
            "LeftTopDI(30)":      r0[LEFT_TOP_DI_COL]    if len(r0) > LEFT_TOP_DI_COL    else None,
            "LeftTopDE(31)":      r0[LEFT_TOP_DE_COL]    if len(r0) > LEFT_TOP_DE_COL    else None,
            "LeftBotAngle(32)":   r0[LEFT_BOT_ANGLE_COL] if len(r0) > LEFT_BOT_ANGLE_COL else None,
            "LeftBotDI(35)":      r0[LEFT_BOT_DI_COL]    if len(r0) > LEFT_BOT_DI_COL    else None,
            "LeftBotDE(36)":      r0[LEFT_BOT_DE_COL]    if len(r0) > LEFT_BOT_DE_COL    else None,
            "LeftRoot(39)":       r0[LEFT_ROOT_COL]       if len(r0) > LEFT_ROOT_COL       else None,
            "RightTopAngle(42)":  r0[RIGHT_TOP_ANGLE_COL] if len(r0) > RIGHT_TOP_ANGLE_COL else None,
            "RightTopDI(45)":     r0[RIGHT_TOP_DI_COL]    if len(r0) > RIGHT_TOP_DI_COL    else None,
            "RightTopDE(46)":     r0[RIGHT_TOP_DE_COL]    if len(r0) > RIGHT_TOP_DE_COL    else None,
            "RightTopRoot(49)":   r0[RIGHT_TOP_ROOT_COL]  if len(r0) > RIGHT_TOP_ROOT_COL  else None,
            "RightBotAngle(52)":  r0[RIGHT_BOT_ANGLE_COL] if len(r0) > RIGHT_BOT_ANGLE_COL else None,
            "RightBotDI(55)":     r0[RIGHT_BOT_DI_COL]    if len(r0) > RIGHT_BOT_DI_COL    else None,
            "RightBotDE(56)":     r0[RIGHT_BOT_DE_COL]    if len(r0) > RIGHT_BOT_DE_COL    else None,
            "RightBotRoot(59)":   r0[RIGHT_BOT_ROOT_COL]  if len(r0) > RIGHT_BOT_ROOT_COL  else None,
            "row_len":            len(r0),
            "total_slice_rows":   len(slice_rows),
        }, "H1_H2_H5")

    for row in slice_rows:
        if len(row) < MIN_COLS:
            continue

        section    = row[LS_COL].strip()  # Use LS column for model_id
        shell_code = row[LS_COL].strip()

        if not shell_code:
            continue

        def get_col(idx):
            return row[idx] if len(row) > idx else None

        bevelling_data = {
            # Side A — Left Side (Top bevel + Bottom bevel + Root Face)
            "side_a_top_bevel_degree":   clean_angle(get_col(LEFT_TOP_ANGLE_COL)),
            "side_a_top_bevel_distance": clean_number(get_col(LEFT_TOP_DE_COL)),    # DE = external depth
            "side_a_bot_bevel_degree":   clean_angle(get_col(LEFT_BOT_ANGLE_COL)),
            "side_a_bot_bevel_distance": clean_number(get_col(LEFT_BOT_DI_COL)),    # DI = internal depth
            "side_a_root_face":          clean_number(get_col(LEFT_ROOT_COL)),

            # Side B — Right Side Top (Top bevel + Bottom bevel + Root Face)
            "side_b_top_bevel_degree":   clean_angle(get_col(RIGHT_TOP_ANGLE_COL)),
            "side_b_top_bevel_distance": clean_number(get_col(RIGHT_TOP_DE_COL)),
            "side_b_bot_bevel_degree":   clean_angle(get_col(RIGHT_TOP_ANGLE_COL)), # same angle, top side
            "side_b_bot_bevel_distance": clean_number(get_col(RIGHT_TOP_DI_COL)),
            "side_b_root_face":          clean_number(get_col(RIGHT_TOP_ROOT_COL)),

            # Side C — Right Side Bottom (Top bevel + Bottom bevel + Root Face)
            "side_c_top_bevel_degree":   clean_angle(get_col(RIGHT_BOT_ANGLE_COL)),
            "side_c_top_bevel_distance": clean_number(get_col(RIGHT_BOT_DE_COL)),
            "side_c_bot_bevel_degree":   clean_angle(get_col(RIGHT_BOT_ANGLE_COL)), # same angle, bot side
            "side_c_bot_bevel_distance": clean_number(get_col(RIGHT_BOT_DI_COL)),
            "side_c_root_face":          clean_number(get_col(RIGHT_BOT_ROOT_COL)),

            # Side D — Left Top bevel distance (DI side)
            "side_d_top_bevel_degree":   clean_angle(get_col(LEFT_TOP_ANGLE_COL)),
            "side_d_top_bevel_distance": clean_number(get_col(LEFT_TOP_DI_COL)),
            "side_d_bot_bevel_degree":   clean_angle(get_col(LEFT_BOT_ANGLE_COL)),
            "side_d_bot_bevel_distance": clean_number(get_col(LEFT_BOT_DE_COL)),
            "side_d_root_face":          clean_number(get_col(LEFT_ROOT_COL)),
        }

        data_rows.append((section, shell_code, bevelling_data))

    _log("after parse", {
        "data_rows_count": len(data_rows),
        "slice_rows_count": len(slice_rows)
    }, "H4")

    return data_rows

def generate_master_data(csv_data):
    master_data_records = []

    for model_id, shell_code, bevelling_data in csv_data:
        for csv_key, value in bevelling_data.items():
            if value is None:
                continue

            form_field_id = CSV_KEY_TO_FIELD_ID.get(csv_key)
            if not form_field_id:
                continue

            master_data_records.append({
                "form_template_id": FORM_TEMPLATE_ID,
                "form_field_id":    form_field_id,
                "model_id":         model_id,
                "code":             shell_code,
                "value":            str(value),
                "is_image":         "false"
            })

    return master_data_records

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 populate_bevelling_master_data.py <csv_file> [output.csv] <model_id>")
        sys.exit(1)

    # Legacy support: skip form_fields.json if passed as first arg
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

    if len(sys.argv) <= arg_idx + 2 or not sys.argv[arg_idx + 2].strip():
        print("Error: model_id is required.")
        print("Usage: python3 populate_bevelling_master_data.py <csv_file> [output.csv] <model_id>")
        sys.exit(1)
    cli_model_id = sys.argv[arg_idx + 2].strip()

    print(f"Parsing {csv_path.name}...")
    csv_data = parse_csv_data(csv_path)

    if not csv_data:
        print("Warning: No data found in CSV")
        sys.exit(1)

    # Override model_id with CLI value
    csv_data = [(cli_model_id, sc, d) for _, sc, d in csv_data]

    print(f"Found {len(csv_data)} rows in CSV")
    master_data_records = generate_master_data(csv_data)
    print(f"Generated {len(master_data_records)} master_data records")

    headers = ["form_template_id", "form_field_id", "model_id", "code", "value", "is_image"]

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
        writer = csv.DictWriter(sys.stdout, fieldnames=headers)
        writer.writeheader()
        writer.writerows(master_data_records)

if __name__ == "__main__":
    main()