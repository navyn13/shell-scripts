#!/usr/bin/env python3
"""
Master Runner Script
--------------------
Scripts live in 'scripts/'; source files in 'source/'. Reads all Excel/CSV from
source/, prompts for model_id for each file in the terminal, then runs all
population scripts and writes 5 master CSVs + combined_master_data.csv.

Usage:
  From project root: python3 scripts/run_all.py
  You will be asked to enter model_id for each source file.
"""

import csv
import sys
import subprocess
from pathlib import Path

SOURCE_FOLDER = "source"


def get_base_dir():
    """Project root = parent of the folder containing this script (scripts/)."""
    return Path(__file__).resolve().parent.parent


def combine_csvs(output_files, final_output_path):
    """Merges multiple CSV files into one, preserving the header."""
    if not output_files:
        return
    headers = ["form_template_id", "form_field_id", "model_id", "code", "value", "is_image"]
    combined_records = []
    for file_path in output_files:
        if not file_path.exists():
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                combined_records.extend(list(reader))
        except Exception as e:
            print(f"   ❌ Error reading {file_path.name}: {e}")
    try:
        with open(final_output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(combined_records)
        print(f"\n🔗 Combined: {final_output_path.name} ({len(combined_records)} total records)")
    except Exception as e:
        print(f"   ❌ Error writing combined file: {e}")


def get_source_files(source_dir):
    """Return all .xlsx and .csv in source_dir, excluding master_* and combined_*."""
    files = []
    for f in source_dir.glob("*.xlsx"):
        files.append(f)
    for f in source_dir.glob("*.csv"):
        if not f.name.startswith("master_") and not f.name.startswith("combined_"):
            files.append(f)
    return sorted(files, key=lambda p: p.name.lower())


def process_one_source(scripts_dir, base_dir, source_path, model_id, jobs):
    """Run all scripts for one source file; return (success_count, total_jobs)."""
    output_dir = base_dir / source_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📄 Source: {source_path.name}")
    print(f"   Model ID: {model_id}")
    print(f"   Output: {output_dir.name}/")
    print("-" * 60)

    success_count = 0
    successful_outputs = []

    for script_name, output_name in jobs:
        script_path = scripts_dir / script_name
        output_path = output_dir / output_name

        if not script_path.exists():
            print(f"⚠️  Skipping {script_name} (File not found)")
            continue

        print(f"🚀 Running {script_name}...")
        try:
            cmd = [sys.executable, str(script_path), str(source_path), str(output_path), model_id]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"   ✅ {output_dir.name}/{output_name}")
            success_count += 1
            successful_outputs.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"   ❌ FAILED: {e.stderr}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print("-" * 60)

    if successful_outputs:
        combine_csvs(successful_outputs, output_dir / "combined_master_data.csv")

    return success_count, len(jobs)


def main():
    scripts_dir = Path(__file__).resolve().parent
    base_dir = get_base_dir()

    source_dir = base_dir / SOURCE_FOLDER
    if not source_dir.is_dir():
        print(f"❌ Error: Folder '{SOURCE_FOLDER}/' not found at project root. Create it and add your Excel/CSV files.")
        sys.exit(1)

    source_files = get_source_files(source_dir)
    if not source_files:
        print(f"❌ Error: No .xlsx or .csv files found in '{SOURCE_FOLDER}/'.")
        sys.exit(1)

    jobs = [
        ("populate_bevelling_master_data.py", "master_bevelling.csv"),
        ("populate_rerolling_master_data.py", "master_rerolling.csv"),
        ("populate_rolling_master_data.py", "master_rolling.csv"),
        ("populate_cutting_master_data.py", "master_cutting.csv"),
        ("populate_welding_master_data.py", "master_welding.csv"),
    ]

    print(f"📂 Project root:       {base_dir}")
    print(f"📁 Scripts:            scripts/")
    print(f"📁 Source:             {SOURCE_FOLDER}/")
    print(f"📋 Found {len(source_files)} file(s) to process")
    print()

    total_ok = 0
    total_jobs = len(jobs) * len(source_files)
    for source_path in source_files:
        while True:
            try:
                model_id = input(f"Enter model_id for '{source_path.name}': ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Cancelled.")
                sys.exit(1)
            if model_id:
                break
            print("   model_id cannot be empty. Try again.")
        ok, n = process_one_source(scripts_dir, base_dir, source_path, model_id, jobs)
        total_ok += ok

    print(f"\n🎉 Done. Processed {len(source_files)} source(s). Outputs in folders named after each file.")
    if total_ok < total_jobs:
        print(f"   ({total_ok}/{total_jobs} script runs succeeded)")


if __name__ == "__main__":
    main()