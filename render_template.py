#!/usr/bin/env python3
"""
Jinja2 Template Generator
--------------------------
Renders Jinja2 templates using variables from a CSV, XLS, or XLSX file.

Usage:
    python3 jinja2_template_generator.py [variables_file] [template_file]

    - variables_file : Path to a .csv, .xls, or .xlsx file (optional via CLI)
    - template_file  : Path to a Jinja2 template file (optional via CLI)

Behaviour:
    1. Variables file resolution order:
       a. Command-line argument
       b. Auto-detect in the script's directory (first .csv/.xls/.xlsx found)
       c. Interactive prompt

    2. Output:
       - Rendered files are saved to  ./rendered_template_YYYY-MM-DD/
       - If the variables file has a HOSTNAME or hostname column, each row
         is saved as  <hostname>.txt
       - Otherwise files are named  template-01.txt, template-02.txt, …
"""

import os
import sys
import glob
import datetime
import platform
from typing import Optional

# ---------------------------------------------------------------------------
# Dependency check / install helper
# ---------------------------------------------------------------------------

def ensure_packages():
    """Ensure required third-party packages are available, installing if needed."""
    import importlib.util, subprocess

    required = {
        "jinja2": "jinja2",
        "openpyxl": "openpyxl",   # xlsx support for pandas
        "xlrd": "xlrd",            # xls support for pandas
        "pandas": "pandas",
    }

    missing = []
    for module, pip_name in required.items():
        if importlib.util.find_spec(module) is None:
            missing.append(pip_name)

    if missing:
        print(f"[INFO] Installing missing packages: {', '.join(missing)}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )
        print("[INFO] Packages installed successfully.\n")


ensure_packages()

# ---------------------------------------------------------------------------
# Imports (after install)
# ---------------------------------------------------------------------------

import pandas as pd
from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateNotFound

# ---------------------------------------------------------------------------
# Platform-aware input helper
# ---------------------------------------------------------------------------

def prompt_input(message: str) -> str:
    """Cross-platform interactive prompt."""
    try:
        return input(message).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n[ABORTED] No input provided.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

VARIABLE_EXTENSIONS = ("*.csv", "*.xls", "*.xlsx")


def find_variables_file_in_dir(directory: str) -> Optional[str]:
    """Return the first variables file found in *directory*, or None."""
    for pattern in VARIABLE_EXTENSIONS:
        matches = glob.glob(os.path.join(directory, pattern))
        if matches:
            return matches[0]
    return None


def resolve_variables_file(cli_arg: Optional[str], script_dir: str) -> str:
    """Resolve the variables file path using the 3-step fallback strategy."""

    # 1. CLI argument
    if cli_arg:
        path = os.path.abspath(cli_arg)
        if os.path.isfile(path):
            return path
        print(f"[ERROR] Provided variables file not found: {path}")
        sys.exit(1)

    # 2. Auto-detect in script directory
    found = find_variables_file_in_dir(script_dir)
    if found:
        print(f"[INFO] Auto-detected variables file: {found}")
        return os.path.abspath(found)

    # 3. Interactive prompt
    print("[INFO] No variables file found automatically.")
    while True:
        path = prompt_input("Enter the path to your variables file (.csv/.xls/.xlsx): ")
        if not path:
            print("[ERROR] Path cannot be empty.")
            continue
        # Expand ~ on all platforms
        path = os.path.expanduser(path)
        if platform.system() == "Windows":
            path = path.replace("/", "\\")
        if os.path.isfile(path):
            return os.path.abspath(path)
        print(f"[ERROR] File not found: {path}. Please try again.")


def resolve_template_file(cli_arg: Optional[str], script_dir: str) -> str:
    """Resolve the Jinja2 template file path."""

    # 1. CLI argument
    if cli_arg:
        path = os.path.abspath(cli_arg)
        if os.path.isfile(path):
            return path
        print(f"[ERROR] Provided template file not found: {path}")
        sys.exit(1)

    # 2. Auto-detect *.j2 or *.jinja2 or *.tmpl in script directory
    for pattern in ("*.j2", "*.jinja2", "*.tmpl", "*.jinja"):
        matches = glob.glob(os.path.join(script_dir, pattern))
        if matches:
            print(f"[INFO] Auto-detected template file: {matches[0]}")
            return os.path.abspath(matches[0])

    # 3. Interactive prompt
    print("[INFO] No Jinja2 template file found automatically.")
    while True:
        path = prompt_input("Enter the path to your Jinja2 template file: ")
        if not path:
            print("[ERROR] Path cannot be empty.")
            continue
        path = os.path.expanduser(path)
        if platform.system() == "Windows":
            path = path.replace("/", "\\")
        if os.path.isfile(path):
            return os.path.abspath(path)
        print(f"[ERROR] File not found: {path}. Please try again.")


# ---------------------------------------------------------------------------
# Variables loader
# ---------------------------------------------------------------------------

def load_variables(file_path: str) -> pd.DataFrame:
    """Load a CSV, XLS, or XLSX file into a DataFrame."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(file_path, dtype=str)
    elif ext == ".xls":
        df = pd.read_excel(file_path, dtype=str, engine="xlrd")
    elif ext == ".xlsx":
        df = pd.read_excel(file_path, dtype=str, engine="openpyxl")
    else:
        print(f"[ERROR] Unsupported file type: {ext}")
        sys.exit(1)

    # Strip whitespace from column names and string values
    df.columns = [c.strip() for c in df.columns]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

    print(f"[INFO] Loaded {len(df)} row(s) from '{os.path.basename(file_path)}'")
    return df


# ---------------------------------------------------------------------------
# Hostname column detection
# ---------------------------------------------------------------------------

def get_hostname_column(df: pd.DataFrame) -> Optional[str]:
    """Return the name of the hostname column if present, else None."""
    for col in df.columns:
        if col.lower() == "hostname":
            return col
    return None


# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

def create_output_dir(script_dir: str) -> str:
    """Create and return the output directory path."""
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    output_dir = os.path.join(script_dir, "output_configs", f"rendered_template_{date_str}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory: {output_dir}")
    return output_dir


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def render_templates(template_path: str, df: pd.DataFrame, output_dir: str) -> None:
    """Render the Jinja2 template for each row in *df* and write output files."""

    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
    )

    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        print(f"[ERROR] Template not found by Jinja2 loader: {template_path}")
        sys.exit(1)

    hostname_col = get_hostname_column(df)

    if hostname_col:
        print(f"[INFO] Using column '{hostname_col}' for output file names.")
    else:
        print("[INFO] No HOSTNAME column found — using sequential file names.")

    total = len(df)
    pad_width = len(str(total))  # e.g. 3 digits for 100 rows

    for idx, row in df.iterrows():
        variables = row.to_dict()

        try:
            rendered = template.render(**variables)
        except Exception as exc:
            print(f"[WARNING] Row {idx + 1}: Render error — {exc}")
            rendered = f"# RENDER ERROR on row {idx + 1}: {exc}\n"

        # Determine output filename
        if hostname_col and pd.notna(row.get(hostname_col)):
            hostname_val = str(row[hostname_col]).strip()
            # Sanitise: remove characters that are invalid in filenames
            safe_name = "".join(
                c if c.isalnum() or c in "-_." else "_" for c in hostname_val
            )
            out_filename = f"{safe_name}.txt"
        else:
            seq = str(idx + 1).zfill(pad_width)
            out_filename = f"template-{seq}.txt"

        out_path = os.path.join(output_dir, out_filename)

        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(rendered)

        print(f"  [{idx + 1}/{total}] Written: {out_filename}")

    print(f"\n[DONE] {total} file(s) rendered to: {output_dir}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Determine the directory that contains this script (cross-platform)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Parse CLI arguments
    # Usage: script.py [variables_file] [template_file]
    cli_vars    = sys.argv[1] if len(sys.argv) > 1 else None
    cli_tmpl    = sys.argv[2] if len(sys.argv) > 2 else None

    print("=" * 60)
    print(" Jinja2 Template Generator")
    print(f" Platform : {platform.system()} {platform.release()}")
    print(f" Python   : {platform.python_version()}")
    print("=" * 60 + "\n")

    # Resolve file paths
    vars_path  = resolve_variables_file(cli_vars, script_dir)
    tmpl_path  = resolve_template_file(cli_tmpl, script_dir)

    print(f"\n[INFO] Variables file : {vars_path}")
    print(f"[INFO] Template file  : {tmpl_path}\n")

    # Load variables
    df = load_variables(vars_path)

    if df.empty:
        print("[ERROR] The variables file contains no data rows.")
        sys.exit(1)

    # Create output directory
    output_dir = create_output_dir(script_dir)

    # Render
    print()
    render_templates(tmpl_path, df, output_dir)


if __name__ == "__main__":
    main()
