"""Tests for data models."""

from food_for_fun.models import (
    HomeroomOrders,
    PdfConfig,
)


class TestHomeroomOrders:
    """Tests for HomeroomOrders dataclass."""

    def test_student_count(self) -> None:
        """Count students in a homeroom."""
        hr = HomeroomOrders(
            name="Room 101",
            student_orders={
                "Alice": ["Pizza"],
                "Bob": ["Salad", "Milk"],
            },
        )
        assert hr.student_count == 2

    def test_total_items(self) -> None:
        """Sum all ordered items."""
        hr = HomeroomOrders(
            name="Room 101",
            student_orders={
                "Alice": ["Pizza"],
                "Bob": ["Salad", "Milk"],
            },
        )
        assert hr.total_items == 3

    def test_unique_items_sorted(self) -> None:
        """Return sorted unique items."""
        hr = HomeroomOrders(
            name="Room 101",
            student_orders={
                "Alice": ["Pizza", "Milk"],
                "Bob": ["Salad", "Milk"],
            },
        )
        assert hr.unique_items == [
            "Milk", "Pizza", "Salad",
        ]

    def test_empty_homeroom(self) -> None:
        """Handle homeroom with no students."""
        hr = HomeroomOrders(name="Empty")
        assert hr.student_count == 0
        assert hr.total_items == 0
        assert hr.unique_items == []


class TestPdfConfig:
    """Tests for PdfConfig defaults."""

    def test_defaults(self) -> None:
        """Verify default config values."""
        config = PdfConfig()
        assert config.groupings is None
        assert config.max_class_size == 0
