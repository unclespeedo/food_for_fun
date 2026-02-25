"""Generate PDF reports from parsed order data."""

from pathlib import Path

from reportlab.graphics.shapes import (
    Drawing,
    Group,
    String,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from food_for_fun.models import (
    HomeroomOrders,
    PdfConfig,
)

_PAGE_WIDTH = 10 * inch
_OPTIONS_COL_WIDTH = 2.5 * inch
_TOTAL_COL_WIDTH = 0.6 * inch


def _rotated_text(text: str) -> Drawing:
    """Create 270-degree rotated text for headers.

    Args:
        text: The text to render vertically.

    Returns:
        A Drawing containing the rotated text.
    """
    text_width = len(text) * 4.5
    d = Drawing(10, text_width + 4)

    g = Group()
    s = String(0, 0, text)
    s.fontSize = 7
    s.fontName = "Helvetica"
    s.textAnchor = "start"

    g.add(s)
    g.rotate(270)
    g.shift(2, text_width + 4)

    d.add(g)
    return d


def _order_items(
    unique_items: list[str],
    groupings: list[list[str]] | None,
) -> tuple[list[str], list[tuple[int, int]]]:
    """Determine item order and group boundaries.

    Args:
        unique_items: All unique items for this homeroom.
        groupings: Optional user-defined groupings.

    Returns:
        Tuple of (ordered items, group boundaries).
        Boundaries are (start_row, end_row) in 1-based
        table coordinates.
    """
    if not groupings:
        items = unique_items
        boundaries = [
            (i + 1, i + 1) for i in range(len(items))
        ]
        return items, boundaries

    ordered: list[str] = []
    boundaries: list[tuple[int, int]] = []
    current_row = 1

    for group in groupings:
        group_start = current_row
        for item in group:
            if item in unique_items:
                ordered.append(item)
                current_row += 1
        if current_row > group_start:
            boundaries.append(
                (group_start, current_row - 1)
            )

    return ordered, boundaries


def _build_table_data(
    homeroom: HomeroomOrders,
    config: PdfConfig,
) -> (
    tuple[list[list[object]], list[float],
          list[tuple[int, int]]]
    | None
):
    """Build table data for a single homeroom.

    Args:
        homeroom: The homeroom order data.
        config: PDF generation configuration.

    Returns:
        Tuple of (table_data, col_widths,
        group_boundaries), or None if no items.
    """
    unique_items = homeroom.unique_items
    if not unique_items:
        return None

    students = sorted(homeroom.student_orders.keys())

    # Prepend blank columns for additional students
    if (
        config.max_class_size > 0
        and len(students) < config.max_class_size
    ):
        blanks = config.max_class_size - len(students)
        students = [""] * blanks + students

    if config.blank_columns > 0:
        students = (
            [""] * config.blank_columns + students
        )

    # Header row: student names + Options + Total
    header: list[object] = [
        _rotated_text(s) if s else ""
        for s in students
    ]
    header.extend(["Options", "Total"])

    ordered_items, group_boundaries = _order_items(
        unique_items, config.groupings
    )

    # Data rows
    rows: list[list[object]] = [header]
    for item in ordered_items:
        row: list[object] = []
        row_total = 0
        for student in students:
            if not student:
                row.append("")
            else:
                count = homeroom.student_orders[
                    student
                ].count(item)
                row.append(str(count) if count else "")
                row_total += count
        row.extend([item, str(row_total)])
        rows.append(row)

    # Column widths
    available = (
        _PAGE_WIDTH
        - _OPTIONS_COL_WIDTH
        - _TOTAL_COL_WIDTH
    )
    num = len(students)
    student_w = available / num if num else 0.5 * inch

    widths = (
        [student_w] * num
        + [_OPTIONS_COL_WIDTH, _TOTAL_COL_WIDTH]
    )

    return rows, widths, group_boundaries


def _table_style(
    group_boundaries: list[tuple[int, int]],
) -> TableStyle:
    """Build the table style with optional group lines.

    Args:
        group_boundaries: Row boundaries for groups.

    Returns:
        Configured TableStyle.
    """
    commands: list[tuple[object, ...]] = [
        ("ALIGN", (0, 0), (-3, -1), "CENTER"),
        ("ALIGN", (-2, 0), (-2, -1), "LEFT"),
        ("ALIGN", (-1, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (-2, 0), (-2, -1),
         "Helvetica-Bold"),
        ("FONTNAME", (-1, 0), (-1, -1),
         "Helvetica-Bold"),
        ("FONTSIZE", (-2, 0), (-2, 0), 10),
        ("FONTSIZE", (-1, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("TOPPADDING", (0, 0), (-1, 0), 25),
        ("TOPPADDING", (-2, 0), (-1, 0), 6),
        ("VALIGN", (0, 0), (-3, 0), "TOP"),
        ("FONTNAME", (0, 1), (-3, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
        (
            "ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.white, colors.lightgrey],
        ),
        (
            "BACKGROUND", (-1, 1), (-1, -1),
            colors.lightgoldenrodyellow,
        ),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
    ]

    if len(group_boundaries) > 1:
        for i in range(len(group_boundaries) - 1):
            end_row = group_boundaries[i][1]
            commands.append((
                "LINEBELOW",
                (0, end_row),
                (-1, end_row),
                1.5,
                colors.black,
            ))

    return TableStyle(commands)


def generate_pdf(
    homerooms: dict[str, HomeroomOrders],
    output_path: Path,
    config: PdfConfig | None = None,
) -> int:
    """Generate a multi-page PDF with one page per homeroom.

    Args:
        homerooms: Map of homeroom name to orders.
        output_path: Where to write the PDF.
        config: Optional PDF configuration.

    Returns:
        Number of pages created.
    """
    if config is None:
        config = PdfConfig()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(letter),
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.5 * inch,
    )

    elements: list[object] = []
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]

    sorted_rooms = sorted(homerooms.items())
    pages = 0

    for _name, homeroom in sorted_rooms:
        result = _build_table_data(homeroom, config)
        if result is None:
            continue

        table_data, col_widths, boundaries = result

        if pages > 0:
            elements.append(PageBreak())

        title = f"Division: {homeroom.name}"
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.3 * inch))

        table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1,
        )
        table.setStyle(_table_style(boundaries))
        elements.append(table)

        elements.append(Spacer(1, 0.2 * inch))
        if config.max_class_size > 0:
            summary = (
                f"Students: {homeroom.student_count}"
                f"/{config.max_class_size}"
                f" | Total Items Ordered:"
                f" {homeroom.total_items}"
            )
        else:
            summary = (
                f"Students: {homeroom.student_count}"
                f" | Total Items Ordered:"
                f" {homeroom.total_items}"
            )
        elements.append(
            Paragraph(summary, styles["Normal"])
        )
        pages += 1

    if pages > 0:
        doc.build(elements)

    return pages
