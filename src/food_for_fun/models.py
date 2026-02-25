"""Data models for Food for Fun orders."""

from dataclasses import dataclass, field


@dataclass
class HomeroomOrders:
    """Orders for a single homeroom/division.

    Attributes:
        name: Homeroom identifier.
        student_orders: Map of student name to their
            ordered items.
    """

    name: str
    student_orders: dict[str, list[str]] = field(
        default_factory=dict,
    )

    @property
    def student_count(self) -> int:
        """Number of students in this homeroom."""
        return len(self.student_orders)

    @property
    def total_items(self) -> int:
        """Total items ordered across all students."""
        return sum(
            len(items)
            for items in self.student_orders.values()
        )

    @property
    def unique_items(self) -> list[str]:
        """Sorted list of unique menu items ordered."""
        items: set[str] = set()
        for order in self.student_orders.values():
            items.update(order)
        return sorted(items)


@dataclass
class ParseResult:
    """Result of parsing the Excel file.

    Attributes:
        homerooms: Parsed homeroom orders.
        all_options: All unique menu options found.
    """

    homerooms: dict[str, HomeroomOrders]
    all_options: list[str]


@dataclass
class PdfConfig:
    """Configuration for PDF generation.

    Attributes:
        groupings: Optional menu item groupings.
        max_class_size: Max class size for blank columns.
            Zero means no blanks.
        blank_columns: Extra blank columns to add to
            every division.
    """

    groupings: list[list[str]] | None = None
    max_class_size: int = 0
    blank_columns: int = 0
