"""Tests for PDF generation logic."""

from food_for_fun.models import (
    HomeroomOrders,
    PdfConfig,
)
from food_for_fun.pdf import _build_table_data, _order_items


class TestOrderItems:
    """Tests for _order_items helper."""

    def test_no_groupings(self) -> None:
        """Without groupings, keep original order."""
        items = ["Milk", "Pizza", "Salad"]

        ordered, boundaries = _order_items(items, None)

        assert ordered == items
        assert len(boundaries) == 3

    def test_with_groupings(self) -> None:
        """Apply groupings to reorder items."""
        items = ["Milk", "Pizza", "Salad"]
        groupings = [
            ["Pizza", "Salad"],
            ["Milk"],
        ]

        ordered, boundaries = _order_items(
            items, groupings
        )

        assert ordered == ["Pizza", "Salad", "Milk"]
        assert boundaries == [(1, 2), (3, 3)]

    def test_groupings_skip_missing(self) -> None:
        """Skip items not in unique_items."""
        items = ["Milk", "Pizza"]
        groupings = [["Pizza", "Juice"], ["Milk"]]

        ordered, _ = _order_items(items, groupings)

        assert ordered == ["Pizza", "Milk"]

    def test_groupings_dedup_across_groups(self) -> None:
        """Duplicates across groups are included once."""
        items = ["Milk", "Pizza", "Salad"]
        groupings = [
            ["Pizza", "Milk"],
            ["Milk", "Salad"],
        ]

        ordered, boundaries = _order_items(
            items, groupings
        )

        assert ordered == ["Pizza", "Milk", "Salad"]
        assert boundaries == [(1, 2), (3, 3)]


class TestBuildTableData:
    """Tests for _build_table_data."""

    def test_empty_homeroom_returns_none(self) -> None:
        """Return None when no items ordered."""
        hr = HomeroomOrders(
            name="Empty",
            student_orders={"Alice": []},
        )

        result = _build_table_data(hr, PdfConfig())

        assert result is None

    def test_basic_table_structure(self) -> None:
        """Verify table has header + data rows."""
        hr = HomeroomOrders(
            name="Room A",
            student_orders={
                "Alice": ["Pizza"],
                "Bob": ["Pizza", "Milk"],
            },
        )

        result = _build_table_data(hr, PdfConfig())
        assert result is not None
        rows, widths, _ = result

        # 1 header + 2 items (Milk, Pizza)
        assert len(rows) == 3
        # 2 students + Options + Total
        assert len(rows[0]) == 4
        assert len(widths) == 4

    def test_max_class_size_adds_blanks(self) -> None:
        """Add blank columns for max class size."""
        hr = HomeroomOrders(
            name="Room A",
            student_orders={"Alice": ["Pizza"]},
        )
        config = PdfConfig(max_class_size=3)

        result = _build_table_data(hr, config)
        assert result is not None
        rows, _, _ = result

        # 3 students (2 blank + 1) + Options + Total
        assert len(rows[0]) == 5
        # Blank columns have empty header
        assert rows[0][0] == ""
        assert rows[0][1] == ""
