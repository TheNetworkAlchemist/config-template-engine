#!/usr/bin/env python3

"""
Generate a CSV template from variables found in a Jinja2 template.

Features:
- Accepts a .j2 or .jinja2 template file as a command-line argument
- Interactive prompt if no argument is supplied
- Basic validation and error handling
- Automatically creates output directory if needed

Example:
    python variable_builder.py ./templates/example.j2
"""

# Standard library imports
import argparse
import csv
import os
import re
import sys


def get_template_path():
    """
    Retrieve template path from CLI arguments,
    fallback to template.j2 in current directory,
    or interactive prompt.
    """

    parser = argparse.ArgumentParser(
        description="Generate a CSV template from a Jinja2 template file."
    )

    parser.add_argument(
        "template",
        nargs="?",
        help="Path to a .j2 or .jinja2 template file"
    )

    args = parser.parse_args()

    # If CLI argument supplied, use it
    if args.template:
        return args.template

    # Attempt automatic default template
    default_template = "template.j2"

    if os.path.isfile(default_template):
        print(
            f"\nNo template argument supplied. "
            f"Using default template: {default_template}"
        )
        return default_template

    # Fall back to interactive prompt
    print("\nNo template file provided.")
    template_path = input(
        "Enter path to Jinja2 template (.j2/.jinja2): "
    ).strip()

    return template_path


def validate_template(template_path):
    """
    Validate template path and extension.
    """

    if not template_path:
        print("ERROR: No template path provided.")
        sys.exit(1)

    if not os.path.isfile(template_path):
        print(f"ERROR: File does not exist: {template_path}")
        sys.exit(1)

    valid_extensions = (".j2", ".jinja2")

    if not template_path.endswith(valid_extensions):
        print("ERROR: Template file must end in .j2 or .jinja2")
        sys.exit(1)


def extract_variables(template_path):
    """
    Extract unique variables from Jinja2 template.
    """

    preconfig_vars = []

    try:
        with open(template_path, "r", encoding="utf-8") as jinja_file:
            data = jinja_file.readlines()

    except Exception as exc:
        print(f"ERROR: Unable to read template file: {exc}")
        sys.exit(1)

    for line in data:
        result = re.search(r"\['(.*?)'\]|\{\{\s*(.*?)\s*\}\}", line)

        if result:
            variable = result.group(1) or result.group(2)

            if variable not in preconfig_vars:
                preconfig_vars.append(variable)

    return preconfig_vars


def write_csv(headers):
    """
    Write extracted variables to CSV file.
    """

    output_directory = "output_configs"
    csv_filename = "variables.csv"

    try:
        os.makedirs(output_directory, exist_ok=True)

        output_path = os.path.join(output_directory, csv_filename)

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

        print(f"\nSuccessfully created CSV template: {output_path}")

    except Exception as exc:
        print(f"ERROR: Unable to write CSV file: {exc}")
        sys.exit(1)


def main():
    """
    Main program execution.
    """

    template_path = get_template_path()

    validate_template(template_path)

    print(f"\nProcessing template: {template_path}")

    variables = extract_variables(template_path)

    if not variables:
        print("WARNING: No variables were found in the template.")
    else:
        print(f"Found {len(variables)} variable(s).")

    write_csv(variables)


if __name__ == "__main__":
    main()