"""Tests for Excel parsing logic."""

import numpy as np
import pandas as pd

from food_for_fun.parser import parse_orders


def _make_df(
    rows: list[list[object]],
    num_cols: int = 44,
) -> pd.DataFrame:
    """Build a DataFrame matching the Excel layout.

    Args:
        rows: List of sparse row data as
            (col_index, value) pairs won't work here,
            so we use full rows padded to num_cols.
        num_cols: Total columns to pad to.

    Returns:
        DataFrame matching expected Excel structure.
    """
    padded = []
    for row in rows:
        full = [np.nan] * num_cols
        for i, val in enumerate(row):
            if i < num_cols and val is not None:
                full[i] = val
        padded.append(full)
    return pd.DataFrame(padded)


def _student_row(
    name: str,
    homeroom: str,
    grade: str = "5",
) -> list[object]:
    """Create a student info row.

    Args:
        name: Student name (col 3).
        homeroom: Homeroom name (col 11).
        grade: Grade level (col 8).

    Returns:
        Sparse row list.
    """
    row: list[object] = [None] * 44
    row[3] = name
    row[8] = grade
    row[11] = homeroom
    return row


def _options_row(options: str) -> list[object]:
    """Create an options row.

    Args:
        options: Comma-separated option string (col 43).

    Returns:
        Sparse row list.
    """
    row: list[object] = [None] * 44
    row[43] = options
    return row


class TestParseOrders:
    """Tests for parse_orders function."""

    def test_single_student(self) -> None:
        """Parse a single student with options."""
        df = _make_df([
            _student_row("Alice", "Room A"),
            _options_row("Pizza, Milk"),
        ])

        result = parse_orders(df)

        assert "Room A" in result.homerooms
        hr = result.homerooms["Room A"]
        assert hr.student_orders["Alice"] == [
            "Pizza", "Milk",
        ]
        assert result.all_options == ["Milk", "Pizza"]

    def test_multiple_students_same_homeroom(
        self,
    ) -> None:
        """Group students by homeroom."""
        df = _make_df([
            _student_row("Alice", "Room A"),
            _options_row("Pizza"),
            _student_row("Bob", "Room A"),
            _options_row("Salad"),
        ])

        result = parse_orders(df)

        assert len(result.homerooms) == 1
        hr = result.homerooms["Room A"]
        assert hr.student_count == 2

    def test_multiple_homerooms(self) -> None:
        """Separate students into different homerooms."""
        df = _make_df([
            _student_row("Alice", "Room A"),
            _options_row("Pizza"),
            _student_row("Bob", "Room B"),
            _options_row("Salad"),
        ])

        result = parse_orders(df)

        assert len(result.homerooms) == 2
        assert "Room A" in result.homerooms
        assert "Room B" in result.homerooms

    def test_skips_header_rows(self) -> None:
        """Skip rows with header sentinel values."""
        df = _make_df([
            _student_row("Student Name", "Homeroom"),
            _options_row(""),
            _student_row("Alice", "Room A"),
            _options_row("Pizza"),
        ])

        result = parse_orders(df)

        assert len(result.homerooms) == 1
        hr = result.homerooms["Room A"]
        assert "Student Name" not in hr.student_orders

    def test_student_without_options(self) -> None:
        """Handle student with no options row."""
        df = _make_df([
            _student_row("Alice", "Room A"),
        ])

        result = parse_orders(df)

        hr = result.homerooms["Room A"]
        assert hr.student_orders["Alice"] == []

    def test_all_options_collected(self) -> None:
        """Collect all unique options across students."""
        df = _make_df([
            _student_row("Alice", "Room A"),
            _options_row("Pizza, Milk"),
            _student_row("Bob", "Room A"),
            _options_row("Salad, Milk"),
        ])

        result = parse_orders(df)

        assert result.all_options == [
            "Milk", "Pizza", "Salad",
        ]

    def test_empty_dataframe(self) -> None:
        """Handle empty input."""
        df = _make_df([])

        result = parse_orders(df)

        assert len(result.homerooms) == 0
        assert result.all_options == []
