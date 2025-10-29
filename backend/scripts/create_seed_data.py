#!/usr/bin/env python3
"""
Seed Data Creation Script

This script now uses the JSON-based seed data system.
All unit data is stored in JSON files in the seed_data/ directory.

Usage:
    python scripts/create_seed_data.py --verbose
    python scripts/create_seed_data.py --unit-file seed_data/units/my-unit.json
"""

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> None:
    """Main function - delegates to the JSON-based seed data script."""

    # Parse arguments
    parser = argparse.ArgumentParser(description="Create seed data for development and testing")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress logs")
    parser.add_argument("--output", help="Save a JSON summary of created entities (unused, kept for compatibility)")
    parser.add_argument("--unit-file", help="Process a specific unit JSON file")

    args = parser.parse_args()

    # Build command for the JSON-based script
    json_script = Path(__file__).parent / "create_seed_data_from_json.py"

    cmd = [sys.executable, str(json_script)]

    if args.verbose:
        cmd.append("--verbose")

    if args.unit_file:
        cmd.extend(["--unit-file", args.unit_file])

    # Run the JSON-based script
    result = subprocess.run(cmd, check=False)  # noqa: S603
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
