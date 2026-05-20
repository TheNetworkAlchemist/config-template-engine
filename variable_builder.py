#!/usr/bin/env python3

"""
Generate a CSV template from variables found in a Jinja2 template.

Features:
- Accepts a .j2, .jinja2, .jinja, or .tmpl template file as a CLI argument
- Auto-detects the first matching template in the current directory if none supplied
- Interactive prompt fallback if no template is found automatically
- Basic validation and error handling
- Automatically creates output directory if needed

Resolution order (mirrors jinja2_template_generator.py):
  1. CLI argument
  2. Auto-detect first .j2 / .jinja2 / .jinja / .tmpl in the current directory
  3. Interactive prompt

Example:
    python variable_builder.py ./templates/example.j2
"""

# Standard library imports
import argparse
import csv
import glob
import os
import re
import sys

# Template extensions to scan for, in priority order
TEMPLATE_EXTENSIONS = ("*.j2", "*.jinja2", "*.jinja", "*.tmpl")


def find_template_in_dir(directory: str):
    """
    Scan *directory* for a template file, checking each extension
    in TEMPLATE_EXTENSIONS order. Returns the first match or None.
    """
    for pattern in TEMPLATE_EXTENSIONS:
        matches = glob.glob(os.path.join(directory, pattern))
        if matches:
            return matches[0]
    return None


def get_template_path():
    """
    Resolve the template file using a three-step priority:
      1. CLI argument
      2. Auto-detect first .j2 / .jinja2 / .jinja / .tmpl in the current directory
      3. Interactive prompt
    """

    parser = argparse.ArgumentParser(
        description="Generate a CSV template from a Jinja2 template file."
    )

    parser.add_argument(
        "template",
        nargs="?",
        help="Path to a .j2, .jinja2, .jinja, or .tmpl template file"
    )

    args = parser.parse_args()

    # 1. CLI argument
    if args.template:
        return args.template

    # 2. Auto-detect in current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    found = find_template_in_dir(script_dir)

    if found:
        print(f"\n[INFO] Auto-detected template file: {found}")
                                                
                                                         
         
        return found

    # 3. Interactive prompt
    print("\n[INFO] No template file found automatically.")
    while True:
        template_path = input(
            "Enter path to Jinja2 template (.j2/.jinja2/.jinja/.tmpl): "
        ).strip()

        if not template_path:
            print("ERROR: Path cannot be empty. Please try again.")
            continue

        template_path = os.path.expanduser(template_path)

        if os.path.isfile(template_path):
            return template_path

        print(f"ERROR: File not found: {template_path}. Please try again.")


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

    valid_extensions = (".j2", ".jinja2", ".jinja", ".tmpl")

    if not template_path.endswith(valid_extensions):
        print("ERROR: Template file must end in .j2, .jinja2, .jinja, or .tmpl")
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