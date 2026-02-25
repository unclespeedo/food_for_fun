"""CLI entry point for Food for Fun converter."""

import sys
from pathlib import Path

from food_for_fun.models import PdfConfig
from food_for_fun.parser import parse_orders, read_excel
from food_for_fun.pdf import generate_pdf


def _prompt_groupings(
    all_options: list[str],
) -> list[list[str]] | None:
    """Prompt user to create menu item groupings.

    Args:
        all_options: All unique menu options.

    Returns:
        List of option groups, or None if skipped.
    """
    print(f"\nFound {len(all_options)} unique menu options:")
    for i, option in enumerate(all_options, 1):
        print(f"  {i:2d}. {option}")

    print(
        "\nWould you like to group any of these "
        "options together? (y/n): ",
        end="",
    )
    if input().strip().lower() not in ("y", "yes"):
        return None

    groupings: list[list[str]] = []
    used: set[str] = set()

    while True:
        available = [
            (i, opt)
            for i, opt in enumerate(all_options, 1)
            if opt not in used
        ]
        if not available:
            print("All options have been grouped!")
            break

        print("\nAvailable options:")
        for i, option in available:
            print(f"  {i:2d}. {option}")

        print(
            "\nEnter the numbers of options to group "
            "together (comma-separated): ",
            end="",
        )
        user_input = input().strip()
        if not user_input:
            break

        try:
            numbers = [
                int(n.strip())
                for n in user_input.split(",")
            ]
        except ValueError:
            print(
                "Invalid input. "
                "Please enter comma-separated numbers."
            )
            continue

        group: list[str] = []
        for num in numbers:
            if not (1 <= num <= len(all_options)):
                print(f"Warning: Invalid number {num}")
                continue
            option = all_options[num - 1]
            if option in used:
                print(
                    f"Warning: '{option}' already grouped"
                )
                continue
            group.append(option)
            used.add(option)

        if group:
            groupings.append(group)
            print(f"Created group: {', '.join(group)}")
        else:
            print("No valid options selected")

        print("\nCreate another group? (y/n): ", end="")
        if input().strip().lower() not in ("y", "yes"):
            break

    ungrouped = [
        opt for opt in all_options if opt not in used
    ]
    if ungrouped:
        groupings.append(ungrouped)
        print(
            "Added remaining options as final group: "
            f"{', '.join(ungrouped)}"
        )

    return groupings


def _prompt_max_class_size() -> int:
    """Prompt user for maximum class size.

    Returns:
        Max class size, or 0 if not specified.
    """
    print(
        "\nWould you like to specify a maximum class "
        "size to add blank spaces? (y/n): ",
        end="",
    )
    if input().strip().lower() not in ("y", "yes"):
        return 0

    while True:
        print("Enter maximum class size: ", end="")
        try:
            size = int(input().strip())
            if size > 0:
                return size
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if len(sys.argv) < 2:
        print(
            "Usage: food-for-fun <input.xls> "
            "[output.pdf]"
        )
        return 1

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    output_path = (
        Path(sys.argv[2])
        if len(sys.argv) >= 3
        else input_path.with_suffix(".pdf")
    )

    print(f"Reading Excel file: {input_path}")
    try:
        df = read_excel(input_path)
        result = parse_orders(df)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return 1

    print(f"Found {len(result.homerooms)} homerooms")
    for name, hr in sorted(result.homerooms.items()):
        orders = sum(
            1
            for items in hr.student_orders.values()
            if items
        )
        print(
            f"  Homeroom {name}: "
            f"{hr.student_count} students, "
            f"{orders} with orders, "
            f"{hr.total_items} items"
        )

    groupings = _prompt_groupings(result.all_options)
    max_class_size = _prompt_max_class_size()

    config = PdfConfig(
        groupings=groupings,
        max_class_size=max_class_size,
    )

    print(f"\nCreating PDF: {output_path}")
    try:
        pages = generate_pdf(
            result.homerooms, output_path, config
        )
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return 1

    if pages == 0:
        print("Warning: No homerooms with orders found!")
    else:
        print(f"PDF created successfully: {output_path}")
        print(f"Total pages: {pages}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
