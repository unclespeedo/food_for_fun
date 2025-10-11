# Food for Fun Excel to PDF Converter

Convert Food for Fun Excel order reports into formatted PDF documents with one page per division/homeroom.

## Features

- **Automatic Excel Parsing**: Supports both `.xls` (xlrd) and `.xlsx` (openpyxl) formats
- **Division-Based Layout**: Creates one page per homeroom/division
- **Rotated Headers**: Student names displayed vertically (270° rotation) for space efficiency
- **Order Summary**: Shows quantities of each menu item ordered per student
- **Totals Column**: Automatically calculates total items ordered per menu option
- **Visual Formatting**: Alternating row colors, highlighted totals, and clean grid layout
- **Summary Statistics**: Displays student count and total items per division

## Requirements

- Python 3.11 or higher
- UV package manager (for script dependencies)

### Dependencies

The script automatically manages these dependencies via UV:
- `pandas>=2.0.0`
- `openpyxl>=3.1.0`
- `xlrd>=2.0.1`
- `reportlab>=4.0.0`

## Installation

1. Install UV if not already installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Make the script executable:
```bash
chmod +x xlsx_to_pdf.py
```

## Usage

### Basic Usage

```bash
./xlsx_to_pdf.py <input.xls> [output.pdf]
```

### Examples

Convert with automatic output filename:
```bash
./xlsx_to_pdf.py ~/Downloads/ItemOrderReport.xls
# Creates: ~/Downloads/ItemOrderReport.pdf
```

Convert with custom output filename:
```bash
./xlsx_to_pdf.py ~/Downloads/ItemOrderReport.xls ~/Documents/orders.pdf
```

## Input File Format

The script expects Excel files with the following structure:
- **Column 3**: Student Name
- **Column 8**: Grade
- **Column 11**: Homeroom/Division
- **Column 43**: Options (comma-separated menu items)

Each student record consists of two rows:
1. Row with student information
2. Row with ordered items (in Options column)

## Output Format

Each PDF page includes:

1. **Division Header**: "Division: [Homeroom Name]"
2. **Order Table**:
   - Column headers: Student names (rotated vertically)
   - Rows: Menu items/options
   - Cells: Quantity ordered (blank if 0)
   - Last column: Total per menu item
3. **Summary Footer**: Student count and total items ordered

### Table Styling

- Alternating white/gray row backgrounds
- Yellow-highlighted totals column
- Bold headers for Options and Total columns
- Grid lines for clear separation

## Output Examples

```
Division: Room 101

[Student1] [Student2] [Student3] Options           Total
    2          1          0       Pizza Slice       3
    1          1          1       Chocolate Milk    3
    0          1          0       Salad             1

Students: 3 | Total Items Ordered: 7
```

## Error Handling

The script handles:
- Missing input files
- Unsupported Excel formats
- Empty or malformed data
- Divisions with no orders (skipped)

## Exit Codes

- `0`: Success
- `1`: Error (invalid input, file not found, or processing failure)

## Technical Details

### PDF Specifications

- **Page Size**: Letter (landscape orientation)
- **Margins**: 0.5" sides, 0.75" top, 0.5" bottom
- **Fonts**: Helvetica and Helvetica-Bold
- **Font Sizes**: 8pt (data), 10pt (headers)

### Column Widths

- **Options Column**: 2.5 inches
- **Total Column**: 0.6 inches
- **Student Columns**: Dynamically calculated based on available space

## Development

### Code Structure

```
xlsx_to_pdf.py
├── read_excel_file()          # Excel file reading with engine fallback
├── parse_orders()             # Parse Excel into homeroom structure
├── create_rotated_text()      # Generate vertical text for headers
├── create_homeroom_table()    # Build table data for one division
├── create_pdf_from_homerooms() # Generate multi-page PDF
└── main()                     # CLI entry point
```

### PEP 8 Compliance

The code follows PEP 8 standards:
- Type hints for all functions
- Docstrings for all public functions
- Line length ≤ 99 characters
- Proper exception handling with chaining
- Module-level imports

## License

Copyright © Food for Fun

## Support

For issues or questions, contact the development team.
