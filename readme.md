# Master Data Scripts

Scripts to generate form master data (bevelling, cutting, rolling, rerolling, welding) from Excel or CSV files.

## Folder layout

```
project/
  scripts/            ← all Python scripts (run_all.py, populate_*.py, source_loader.py)
  source/             ← put your Excel/CSV files here (can be multiple)
  <OutputFolder1>/    ← created per source file (5 CSVs + combined_master_data.csv)
  <OutputFolder2>/
  ...
```

## Prerequisites

- Python 3
- For **Excel (.xlsx)** support: `pip3 install openpyxl` (or `pip3 install -r requirements.txt`)

## How to run

**Run from the project root** (the folder that contains `scripts/` and `source/`).

### Run all scripts (batch)

1. Put your **source Excel/CSV files** in the **`source/`** folder.

2. Run (no arguments). The script will **ask for model_id in the terminal for each source file**:

```bash
python3 scripts/run_all.py
```

You will see prompts like:
```
Enter model_id for 'Envision 3x_140HH 353MT Bay-4 Master Data.xlsx': model-353
Enter model_id for 'Envision 3x_140HH 338MT Bay-4 Master Data.xlsx': model-338
```

For **each file** in `source/`, the script creates a folder at project root with the same name (no extension) and writes inside it:
- 5 master CSVs (master_bevelling.csv, master_cutting.csv, etc.)
- **combined_master_data.csv** (all 5 merged)

---

### Run single script

From project root. **model_id is required** (last argument).

```bash
python3 scripts/populate_bevelling_master_data.py source/MyFile.xlsx output_folder/master_bevelling.csv MODEL_ID
python3 scripts/populate_cutting_master_data.py source/MyFile.xlsx output_folder/master_cutting.csv MODEL_ID
python3 scripts/populate_rolling_master_data.py source/MyFile.xlsx output_folder/master_rolling.csv MODEL_ID
python3 scripts/populate_rerolling_master_data.py source/MyFile.xlsx output_folder/master_rerolling.csv MODEL_ID
python3 scripts/populate_welding_master_data.py source/MyFile.xlsx output_folder/master_welding.csv MODEL_ID
```

## Output files (per source file)

| Script | Output file |
|--------|-------------|
| populate_bevelling_master_data.py | master_bevelling.csv |
| populate_rerolling_master_data.py | master_rerolling.csv |
| populate_rolling_master_data.py | master_rolling.csv |
| populate_cutting_master_data.py | master_cutting.csv |
| populate_welding_master_data.py | master_welding.csv |

**run_all.py** also creates **combined_master_data.csv** in each output folder.
