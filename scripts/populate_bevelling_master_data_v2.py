#!/usr/bin/env python3
"""
Bevelling master data v2 — maps form fields to the Bay-4 Master Data Excel layout.

Source: Envision 3x_140HH 353MT (CleanMax 353MT Model) Bay-4 Master Data.xlsx
        (and other files using the same header structure)

Usage:
    python3 populate_bevelling_master_data_v2.py <xlsx_or_csv> [output.csv] <model_id>

Column map (0-indexed) from Excel row 4/5 headers:
    [2]  Section
    [3]  LS (shell code)

    --- Plate Bevelling (A & C Side) ---
    [28] Top Bevel Degree (C)
    [29] Top Bevel Degree (A)
    [32] Bevel Distance (A&C) — Top
    [33] Bevel Distance (A&C) — Bottom
    [34] Bottom Bevel Degree (A)
    [35] Bottom Bevel Degree (C)
    [42] Root face (A&C)

    --- Plate Bevelling Left Side (B Side) ---
    [45] Top/Bottom Bevel Degree (B)
    [48] Bevel Distance (B) — Top
    [49] Bevel Distance (B) — Bottom
    [52] Root Face (B)

    --- Plate Bevelling Right Side (D Side) ---
    [55] Top/Bottom Bevel Degree (D)
    [58] Bevel Distance (D) — Top
    [59] Bevel Distance (D) — Bottom
    [62] Root Face (D)

Data rows start at row index 6 (after 6 header rows).
"""

import csv
import sys
from pathlib import Path

from source_loader import load_source_rows

FORM_TEMPLATE_ID = "564b7379-a7b8-4391-99f8-bd9b8c213d8d"

CSV_KEY_TO_FIELD_ID = {
    "side_a_top_bevel_degree":    "4a6c3dbe-9164-4560-9a51-b2ab52faca39",
    "side_a_top_bevel_distance":  "06ee05fc-c500-4e04-8a9f-20dc1520161d",
    "side_a_bot_bevel_degree":    "c12ad342-cc2d-4499-b984-94a9c3cf9700",
    "side_a_bot_bevel_distance":  "e5e46315-0341-4a26-92a6-539c6756796b",
    "side_a_root_face":           "280912a0-d088-4305-b981-3eab9bd1c0f7",
    "side_b_top_bevel_degree":    "79e305f5-4ee2-4fff-8cb2-d422eed1be5a",
    "side_b_top_bevel_distance":  "4cd0cd7e-bdf0-416f-a49a-924f9d4f526f",
    "side_b_bot_bevel_degree":    "d1e771b4-4669-493b-b353-f39f3fa6e4e2",
    "side_b_bot_bevel_distance":  "2a103359-ff4e-4051-a829-25e6b8027fbc",
    "side_b_root_face":           "eea2a3a6-3e98-4b2f-8765-58e073af7945",
    "side_c_top_bevel_degree":    "c8a0400f-f581-46fb-ab10-83e495d815ac",
    "side_c_top_bevel_distance":  "5fbd1e85-bf89-4931-ae4e-d9f4e427e11a",
    "side_c_bot_bevel_degree":    "4c728c4a-799d-40b0-b729-d155be58f8d9",
    "side_c_bot_bevel_distance":  "4b82d209-f62d-4680-a555-5c01c0116641",
    "side_c_root_face":           "496fdb55-28eb-481e-92de-e12ae193ee26",
    "side_d_top_bevel_degree":    "531d271f-e359-4963-bee4-6d646bb06919",
    "side_d_top_bevel_distance":  "6fe4f846-2156-4b98-82cb-9c55886b6a18",
    "side_d_bot_bevel_degree":    "e71a8af6-4286-42d7-a2ab-175cb893cdfe",
    "side_d_bot_bevel_distance":  "8e140569-e29f-4007-bee9-31e17976efa3",
    "side_d_root_face":           "f2d59e71-04f3-454d-8720-af6bc3089d29",
}

LS_COL = 3
DATA_START_ROW = 6

# Plate Bevelling (A & C Side)
C_TOP_ANGLE_COL = 28
A_TOP_ANGLE_COL = 29
AC_DIST_TOP_COL = 32
AC_DIST_BOT_COL = 33
A_BOT_ANGLE_COL = 34
C_BOT_ANGLE_COL = 35
AC_ROOT_FACE_COL = 42

# Plate Bevelling Left Side (B Side)
B_ANGLE_COL = 45
B_DIST_TOP_COL = 48
B_DIST_BOT_COL = 49
B_ROOT_FACE_COL = 52

# Plate Bevelling Right Side (D Side)
D_ANGLE_COL = 55
D_DIST_TOP_COL = 58
D_DIST_BOT_COL = 59
D_ROOT_FACE_COL = 62

MIN_COLS = D_ROOT_FACE_COL + 1


def _fmt(value):
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def clean_angle(val):
    if not val:
        return None
    val = str(val).strip().replace("°", "")
    try:
        return _fmt(float(val))
    except ValueError:
        return None


def clean_number(val):
    if not val:
        return None
    val = str(val).strip()
    try:
        return _fmt(float(val))
    except ValueError:
        return None


def parse_source_data(source_path):
    rows = load_source_rows(source_path)
    data_rows = []

    for row in rows[DATA_START_ROW:]:
        if len(row) < MIN_COLS:
            continue

        shell_code = row[LS_COL].strip()
        if not shell_code:
            continue

        def col(idx):
            return row[idx] if len(row) > idx else None

        bevelling_data = {
            # Side A — its own angle columns, shared A&C distance/root face columns
            "side_a_top_bevel_degree":   clean_angle(col(A_TOP_ANGLE_COL)),
            "side_a_top_bevel_distance": clean_number(col(AC_DIST_TOP_COL)),
            "side_a_bot_bevel_degree":   clean_angle(col(A_BOT_ANGLE_COL)),
            "side_a_bot_bevel_distance": clean_number(col(AC_DIST_BOT_COL)),
            "side_a_root_face":          clean_number(col(AC_ROOT_FACE_COL)),

            # Side B — left / B side
            "side_b_top_bevel_degree":   clean_angle(col(B_ANGLE_COL)),
            "side_b_top_bevel_distance": clean_number(col(B_DIST_TOP_COL)),
            "side_b_bot_bevel_degree":   clean_angle(col(B_ANGLE_COL)),
            "side_b_bot_bevel_distance": clean_number(col(B_DIST_BOT_COL)),
            "side_b_root_face":          clean_number(col(B_ROOT_FACE_COL)),

            # Side C — its own angle columns, shared A&C distance/root face columns
            "side_c_top_bevel_degree":   clean_angle(col(C_TOP_ANGLE_COL)),
            "side_c_top_bevel_distance": clean_number(col(AC_DIST_TOP_COL)),
            "side_c_bot_bevel_degree":   clean_angle(col(C_BOT_ANGLE_COL)),
            "side_c_bot_bevel_distance": clean_number(col(AC_DIST_BOT_COL)),
            "side_c_root_face":          clean_number(col(AC_ROOT_FACE_COL)),

            # Side D — right / D side
            "side_d_top_bevel_degree":   clean_angle(col(D_ANGLE_COL)),
            "side_d_top_bevel_distance": clean_number(col(D_DIST_TOP_COL)),
            "side_d_bot_bevel_degree":   clean_angle(col(D_ANGLE_COL)),
            "side_d_bot_bevel_distance": clean_number(col(D_DIST_BOT_COL)),
            "side_d_root_face":          clean_number(col(D_ROOT_FACE_COL)),
        }

        data_rows.append((shell_code, bevelling_data))

    return data_rows


def generate_master_data(parsed_rows, model_id):
    records = []
    for shell_code, bevelling_data in parsed_rows:
        for csv_key, value in bevelling_data.items():
            if value is None:
                continue
            field_id = CSV_KEY_TO_FIELD_ID.get(csv_key)
            if not field_id:
                continue
            records.append({
                "form_template_id": FORM_TEMPLATE_ID,
                "form_field_id":    field_id,
                "model_id":         model_id,
                "code":             shell_code,
                "value":            str(value),
                "is_image":         "false",
            })
    return records


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 populate_bevelling_master_data_v2.py <xlsx_or_csv> [output.csv] <model_id>")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    if not source_path.exists():
        print(f"Error: source file not found at {source_path}")
        sys.exit(1)

    cli_model_id = sys.argv[-1].strip()
    if not cli_model_id:
        print("Error: model_id is required.")
        sys.exit(1)

    print(f"Parsing {source_path.name} (bevelling v2)...")
    parsed_rows = parse_source_data(source_path)
    if not parsed_rows:
        print("Warning: No bevelling data found.")
        sys.exit(1)

    records = generate_master_data(parsed_rows, cli_model_id)
    print(f"Found {len(parsed_rows)} shell rows, generated {len(records)} master_data records")

    headers = ["form_template_id", "form_field_id", "model_id", "code", "value", "is_image"]
    output_path = sys.stdout
    if len(sys.argv) > 3:
        out = Path(sys.argv[2])
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"Saving to {out}...")
        output_path = open(out, "w", encoding="utf-8", newline="")

    try:
        writer = csv.DictWriter(output_path, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)
        if output_path is not sys.stdout:
            print("Done.")
    finally:
        if output_path is not sys.stdout:
            output_path.close()


if __name__ == "__main__":
    main()
