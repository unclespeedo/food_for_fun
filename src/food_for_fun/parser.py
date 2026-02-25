"""Parse Food for Fun Excel order reports."""

from collections import defaultdict
from pathlib import Path

import pandas as pd

from food_for_fun.models import HomeroomOrders, ParseResult

# Column indices in the Excel report
_STUDENT_NAME_COL = 3
_GRADE_COL = 8
_HOMEROOM_COL = 11
_OPTIONS_COL = 43

# Sentinel values that indicate header rows
_HEADER_SENTINELS = {"Student Name", "Homeroom"}


def read_excel(path: Path) -> pd.DataFrame:
    """Read an Excel file, trying xlrd then openpyxl.

    Args:
        path: Path to the Excel file.

    Returns:
        DataFrame with no header row.

    Raises:
        ValueError: If neither engine can read the file.
    """
    try:
        return pd.read_excel(
            path, engine="xlrd", header=None
        )
    except Exception as xlrd_err:
        try:
            return pd.read_excel(
                path, engine="openpyxl", header=None
            )
        except Exception as e:
            raise ValueError(
                f"Failed to read Excel file: {e}"
            ) from xlrd_err


def _is_header_row(
    student_name: object,
    homeroom: object,
) -> bool:
    """Check if a row is a header rather than data."""
    if pd.isna(student_name) or pd.isna(homeroom):
        return True
    return (
        str(student_name) in _HEADER_SENTINELS
        or str(homeroom) in _HEADER_SENTINELS
    )


def parse_orders(df: pd.DataFrame) -> ParseResult:
    """Parse Excel data into structured orders.

    The Excel layout has student info on one row and
    their ordered options on the next row.

    Args:
        df: Raw DataFrame from the Excel file.

    Returns:
        Parsed homeroom orders and all unique options.
    """
    homerooms: dict[str, dict[str, list[str]]] = (
        defaultdict(dict)
    )
    all_options: set[str] = set()

    row = 0
    while row < len(df):
        student_name = df.iloc[row, _STUDENT_NAME_COL]
        homeroom = df.iloc[row, _HOMEROOM_COL]

        if _is_header_row(student_name, homeroom):
            row += 1
            continue

        items: list[str] = []
        if row + 1 < len(df):
            options = df.iloc[row + 1, _OPTIONS_COL]
            if pd.notna(options):
                items = [
                    item.strip()
                    for item in str(options).split(",")
                ]
                all_options.update(items)

        key = str(homeroom).strip()
        homerooms[key][str(student_name)] = items
        row += 1

    result_homerooms = {
        name: HomeroomOrders(
            name=name, student_orders=students
        )
        for name, students in homerooms.items()
    }

    return ParseResult(
        homerooms=result_homerooms,
        all_options=sorted(all_options),
    )
