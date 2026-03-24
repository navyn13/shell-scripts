#!/usr/bin/env python3
"""
Script to populate Weld Inspection (Outside/Inside/Required) master_data.
Output: CSV format.

Usage:
    python3 populate_welding_master_data.py <csv_file> [output.csv] <model_id>

Full weld column map (0-indexed):
    [1]  Section       (e.g. S1)
    [2]  LS            (e.g. S1-L1)
    --- Tack & Root Weld ---
    [70] WPS No / Current
    [71] Current Upper             ← script named this tr_curr_l (WRONG label, right col)
    [72] Current Lower             ← script named this tr_curr_u (WRONG label, right col)
    [73] Voltage Upper
    [74] Voltage Lower
    [75] Travel Speed Upper
    [76] Travel Speed Lower
    --- Outside Weld (SAW) ---
    [77] Current Upper             ← script used col 83 (WRONG — was Inside Current)
    [78] Current Lower             ← script used col 84 (WRONG)
    [79] Voltage Upper             ← script used col 85 (WRONG)
    [80] Voltage Lower             ← script used col 86 (WRONG)
    [81] Travel Speed Upper        ← script used col 87 (WRONG)
    [82] Travel Speed Lower        ← script used col 88 (WRONG)
    --- Inside Weld ---
    [83] Current Upper             ← script used col 89 (WRONG — was LS VT "OK/NOK")
    [84] Current Lower             ← script used col 90 (WRONG — was LS UT "OK/NOK")
    [85] Voltage Upper             ← script used col 91 (OUT OF RANGE)
    [86] Voltage Lower             ← script used col 92 (OUT OF RANGE)
    [87] Travel Speed Upper        ← script used col 93 (OUT OF RANGE)
    [88] Travel Speed Lower        ← script used col 94 (OUT OF RANGE)
    --- NDT ---
    [89] LS VT  (OK/NOK)
    [90] LS UT  (OK/NOK)
"""

import csv
import sys
from pathlib import Path

from source_loader import load_source_rows

# CONFIGURATION
FORM_TEMPLATE_ID = "741b50ea-a02d-412d-8d68-f4acc1efab8d"

FIELD_MAPPING = {
    # OUTSIDE WELD (SAW) -> Passes 1, 2, 3
    "saw_current": [
        "8d347b10-5cc2-48e5-8451-6897a1d6ae48",  # Outside Pass 1 - Amp DC
        "ef4aeb7b-bebc-4e8a-a0b5-aeac0da7087e",  # Outside Pass 2 - Amp DC
        "2ae83bc7-b233-4fae-acca-ce3eaaf1df7f",  # Outside Pass 3 - Amp DC
    ],
    "saw_voltage": [
        "3c4c680c-adbf-4750-9e6d-3bfb7f6ff1d5",  # Outside Pass 1 - Volt DC
        "7203c306-25df-4ba8-abdc-999b4b33f74d",  # Outside Pass 2 - Volt DC
        "713ad899-b146-4313-9bc6-81df45a4944e",  # Outside Pass 3 - Volt DC
    ],
    "saw_speed": [
        "3ae695c2-8383-4d36-847b-bddcc73fe62e",  # Outside Pass 1 - Speed
        "c52cec4f-9219-4a4c-b43e-001699cd1be4",  # Outside Pass 2 - Speed
        "b0ea0c6f-cc7f-46b8-8cce-accd50812fd4",  # Outside Pass 3 - Speed
    ],
    # INSIDE WELD -> Passes 1, 2, 3
    "inside_current": [
        "22fc5b9b-39e6-43a3-a734-091c774cb118",  # Inside Pass 1 - Amp DC
        "cb96c40a-b5b0-4f0c-b103-af3e798f9912",  # Inside Pass 2 - Amp DC
        "ac69f909-0bd0-40c6-85b8-f5b095db3844",  # Inside Pass 3 - Amp DC
    ],
    "inside_voltage": [
        "40b8c038-ef00-48dd-9a8f-e3885317531e",  # Inside Pass 1 - Volt DC
        "7e1657c7-dd59-4d68-94fb-9f3e0c826f8b",  # Inside Pass 2 - Volt DC
        "bcec6a77-cbed-4c6f-bb54-0cc4746ea74d",  # Inside Pass 3 - Volt DC
    ],
    "inside_speed": [
        "bfbed603-7e93-4276-b64c-bea8166eb6c0",  # Inside Pass 1 - Speed
        "7eddcb7a-4fd4-441f-9e04-44472dfe583a",  # Inside Pass 2 - Speed
        "31a6a6cc-076a-4a02-aa32-6d9130b30fae",  # Inside Pass 3 - Speed
    ],
    # TACK & ROOT WELD -> R0 & R1
    "tack_root_current": [
        "ac0e2893-5b79-428d-9858-ca94c37f07d3",  # Required R0 - Amp DC
        "636e8626-d966-4bda-ac09-79882b17b0d9",  # Required R1 - Amp DC
    ],
    "tack_root_voltage": [
        "f68095cb-fdc3-4ead-be5a-c7e073a037d2",  # Required R0 - Volt DC
        "106c004a-5ff4-4bf4-9d58-d8309b867537",  # Required R1 - Volt DC
    ],
    "tack_root_speed": [
        "a6c4867d-e76b-4fda-b22b-affb07c7c9d0",  # Required R0 - Speed
        "119c1bb0-5091-49fd-b7a7-46a56b79197a",  # Required R1 - Speed
    ],
}

# ── Correct column indices (0-based) ──────────────────────────────────────────
SECTION_COL = 2   # Section e.g. S1
LS_COL      = 3   # LS e.g. S1-L1

# Tack & Root Weld  (cols 71-77)
TR_CURR_UPPER  = 72   # Current Upper
TR_CURR_LOWER  = 73   # Current Lower
TR_VOLT_UPPER  = 74   # Voltage Upper
TR_VOLT_LOWER  = 75   # Voltage Lower
TR_SPEED_UPPER = 76   # Travel Speed Upper
TR_SPEED_LOWER = 77   # Travel Speed Lower

# Outside Weld / SAW
SAW_CURR_UPPER  = 78
SAW_CURR_LOWER  = 79
SAW_VOLT_UPPER  = 80
SAW_VOLT_LOWER  = 81
SAW_SPEED_UPPER = 82
SAW_SPEED_LOWER = 83

# Inside Weld
IN_CURR_UPPER  = 84
IN_CURR_LOWER  = 85
IN_VOLT_UPPER  = 86
IN_VOLT_LOWER  = 87
IN_SPEED_UPPER = 88
IN_SPEED_LOWER = 89

MIN_COLS = IN_SPEED_LOWER + 1  # = 90
# ──────────────────────────────────────────────────────────────────────────────

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

        def get_val(idx):
            return row[idx].strip() if len(row) > idx else ""

        def fmt(upper, lower):
            u, l = get_val(upper), get_val(lower)
            return f"{u}-{l}" if u and l else ""

        row_data = {
            "tack_root_current": fmt(TR_CURR_UPPER,  TR_CURR_LOWER),
            "tack_root_voltage": fmt(TR_VOLT_UPPER,  TR_VOLT_LOWER),
            "tack_root_speed":   fmt(TR_SPEED_UPPER, TR_SPEED_LOWER),
            "saw_current":       fmt(SAW_CURR_UPPER,  SAW_CURR_LOWER),
            "saw_voltage":       fmt(SAW_VOLT_UPPER,  SAW_VOLT_LOWER),
            "saw_speed":         fmt(SAW_SPEED_UPPER, SAW_SPEED_LOWER),
            "inside_current":    fmt(IN_CURR_UPPER,   IN_CURR_LOWER),
            "inside_voltage":    fmt(IN_VOLT_UPPER,   IN_VOLT_LOWER),
            "inside_speed":      fmt(IN_SPEED_UPPER,  IN_SPEED_LOWER),
        }

        data_rows.append((section, shell_code, row_data))

    return data_rows

def generate_records(parsed_data):
    records = []
    for model_id, shell_code, data in parsed_data:
        for key, value in data.items():
            if not value:
                continue
            field_ids = FIELD_MAPPING.get(key)
            if not field_ids:
                continue
            for field_id in field_ids:
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
        print("Usage: python3 populate_welding_master_data.py <csv_file> [output.csv] <model_id>")
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