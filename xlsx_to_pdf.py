#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas>=2.0.0",
#     "openpyxl>=3.1.0",
#     "xlrd>=2.0.1",
#     "reportlab>=4.0.0",
# ]
# ///

"""
Convert Food for Fun Excel report to PDF with one page per division.

Usage:
    ./xlsx_to_pdf.py <input.xls> [output.pdf]

Each page shows a division with:
- Title: "Division: $Division"
- Student names as columns (text rotated 270 degrees, vertical)
- Menu items (Options) as rows
- Quantities under each student
- Total column showing sum per menu item
"""

import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    PageBreak,
    Spacer,
)
from reportlab.graphics.shapes import Drawing, String, Group


def read_excel_file(input_path: Path) -> pd.DataFrame:
    """Read Excel file without headers."""
    try:
        df = pd.read_excel(input_path, engine='xlrd', header=None)
    except Exception as xlrd_error:
        try:
            df = pd.read_excel(input_path, engine='openpyxl', header=None)
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}") from xlrd_error
    return df


def parse_orders(df: pd.DataFrame) -> Dict[str, Dict[str, List[str]]]:
    """
    Parse the Excel data into structured orders by homeroom.

    The Excel structure has student info on one row and their options
    on the next row.

    Returns:
        Dict mapping homeroom -> {student_name: [list of items ordered]}
    """
    homerooms = defaultdict(dict)

    # Column indices based on analysis
    STUDENT_NAME_COL = 3
    GRADE_COL = 8
    HOMEROOM_COL = 11
    OPTIONS_COL = 43

    i = 0
    while i < len(df):
        student_name = df.iloc[i, STUDENT_NAME_COL]
        grade = df.iloc[i, GRADE_COL]
        homeroom = df.iloc[i, HOMEROOM_COL]

        # Skip header rows and rows without valid data
        if (pd.isna(student_name) or pd.isna(homeroom) or
                student_name == 'Student Name' or homeroom == 'Homeroom'):
            i += 1
            continue

        # Check if the next row has options data
        items = []
        if i + 1 < len(df):
            options = df.iloc[i + 1, OPTIONS_COL]
            if pd.notna(options):
                items = [item.strip() for item in str(options).split(',')]

        # Store in homerooms dict (just by homeroom, not grade)
        homeroom_key = str(homeroom).strip()
        homerooms[homeroom_key][str(student_name)] = items

        # Skip ahead - student rows seem to be spaced out
        i += 1

    return homerooms


def create_rotated_text(text: str) -> Drawing:
    """Create a 270-degree rotated text drawing (vertical, top to bottom)."""
    # Calculate drawing size based on text length
    text_width = len(text) * 5  # Width when horizontal

    # Drawing size: width becomes height when rotated
    d = Drawing(12, text_width + 5)

    # Create a group and rotate it
    g = Group()
    s = String(0, 0, text)
    s.fontSize = 8
    s.fontName = 'Helvetica'
    s.textAnchor = 'start'

    g.add(s)
    g.rotate(270)  # Rotate 270 degrees (vertical, top to bottom)
    g.shift(2, text_width + 5)  # Shift to position within drawing

    d.add(g)
    return d


def create_homeroom_table(
    student_orders: Dict[str, List[str]],
    homeroom: str
) -> Tuple[List[List], List[float]]:
    """
    Create table data for a single division.

    Returns:
        (table_data, column_widths)
    """
    # Get all unique menu items across all students
    all_items = []
    for items in student_orders.values():
        all_items.extend(items)

    # Get unique items and sort them
    unique_items = sorted(set(all_items))

    if not unique_items:
        # No items ordered in this division
        return None, None

    # Get sorted student names
    students = sorted(student_orders.keys())

    # Build table data
    # Header row: student names (rotated) + ["Options", "Total"]
    header_row = []
    for student in students:
        header_row.append(create_rotated_text(student))
    header_row.append("Options")
    header_row.append("Total")

    table_data = [header_row]

    # Data rows: one per menu item
    for item in unique_items:
        row = []
        row_total = 0
        for student in students:
            # Count how many times this student ordered this item
            count = student_orders[student].count(item)
            row.append(str(count) if count > 0 else "")
            row_total += count
        row.append(item)
        row.append(str(row_total))
        table_data.append(row)

    # Calculate column widths
    num_students = len(students)
    options_col_width = 2.5 * inch
    total_col_width = 0.6 * inch
    available_width = 10 * inch - options_col_width - total_col_width
    student_col_width = (
        available_width / num_students if num_students > 0 else 0.5 * inch
    )

    col_widths = (
        [student_col_width] * num_students +
        [options_col_width, total_col_width]
    )

    return table_data, col_widths


def create_pdf_from_homerooms(
    homerooms: Dict[str, Dict[str, List[str]]],
    output_path: Path
) -> None:
    """Create multi-page PDF with one page per homeroom."""

    # Create PDF document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.5*inch,
    )

    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']

    # Sort homerooms
    sorted_homerooms = sorted(homerooms.items(), key=lambda x: x[0])

    pages_created = 0
    for idx, (homeroom, student_orders) in enumerate(sorted_homerooms):
        # Create table
        table_data, col_widths = create_homeroom_table(student_orders, homeroom)

        if table_data is None:
            # Skip homerooms with no orders
            continue

        # Add page break before each homeroom except the first
        if pages_created > 0:
            elements.append(PageBreak())

        # Title
        title = f"Division: {homeroom}"
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.3*inch))

        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Style the table
        num_rows = len(table_data)
        num_cols = len(table_data[0])

        table.setStyle(TableStyle([
            # Header row (student names) - no background
            ('ALIGN', (0, 0), (-3, -1), 'CENTER'),  # Students centered
            ('ALIGN', (-2, 0), (-2, -1), 'LEFT'),  # Options left-aligned
            ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),  # Total centered
            ('FONTNAME', (-2, 0), (-2, -1), 'Helvetica-Bold'),  # Options bold
            ('FONTNAME', (-1, 0), (-1, -1), 'Helvetica-Bold'),  # Total bold
            ('FONTSIZE', (-2, 0), (-2, 0), 10),
            ('FONTSIZE', (-1, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 40),  # Rotated text padding
            ('TOPPADDING', (-2, 0), (-1, 0), 8),  # Options/Total padding
            ('VALIGN', (0, 0), (-3, 0), 'TOP'),  # Rotated text alignment

            # Data rows
            ('FONTNAME', (0, 1), (-3, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.lightgrey]),

            # Total column styling
            ('BACKGROUND', (-1, 1), (-1, -1),
             colors.lightgoldenrodyellow),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)

        # Summary info
        num_students = len(student_orders)
        total_items = sum(len(items) for items in student_orders.values())
        elements.append(Spacer(1, 0.2*inch))
        summary = f"Students: {num_students} | Total Items Ordered: {total_items}"
        elements.append(Paragraph(summary, styles['Normal']))

        pages_created += 1

    if pages_created == 0:
        print("Warning: No homerooms with orders found!")
        return

    # Build PDF
    doc.build(elements)

    print(f"PDF created successfully: {output_path}")
    print(f"Total pages: {pages_created}")


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    # Parse arguments
    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.pdf')

    # Read and parse Excel file
    print(f"Reading Excel file: {input_path}")
    try:
        df = read_excel_file(input_path)
        homerooms = parse_orders(df)
        print(f"Found {len(homerooms)} homerooms")

        # Show homeroom summary
        for homeroom, students in sorted(homerooms.items()):
            num_orders = sum(1 for items in students.values() if items)
            total_items = sum(len(items) for items in students.values())
            print(
                f"  Homeroom {homeroom}: {len(students)} students, "
                f"{num_orders} with orders, {total_items} items"
            )
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return 1

    # Create PDF
    print(f"\nCreating PDF: {output_path}")
    try:
        create_pdf_from_homerooms(homerooms, output_path)
    except Exception as e:
        print(f"Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
