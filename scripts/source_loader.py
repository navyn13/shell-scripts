"""
Load master data source as rows (list of lists of strings).
Supports .csv and .xlsx so you can pass either file path.
"""
import csv
from pathlib import Path


def load_source_rows(path):
    """
    Load a CSV or Excel file and return rows as list[list[str]].
    path: Path or str to .csv or .xlsx file.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".xlsx":
        return _load_xlsx(path)
    return _load_csv(path)


def _load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return list(reader)


def _load_xlsx(path):
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise ImportError(
            "Reading Excel (.xlsx) requires openpyxl. Install with: pip install openpyxl"
        ) from None

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append([_cell_str(c) for c in row])
    wb.close()

    # Pad rows to same length (Excel can have short rows) so column indices work
    if rows:
        max_len = max(len(r) for r in rows)
        for r in rows:
            while len(r) < max_len:
                r.append("")
    return rows


def _cell_str(cell):
    if cell is None:
        return ""
    return str(cell).strip() if isinstance(cell, str) else str(cell)
