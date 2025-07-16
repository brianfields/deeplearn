#!/usr/bin/env python3
"""
Simple test runner for the simplified backend system.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_tests():
    """Run the comprehensive backend tests."""
    print("🚀 Running comprehensive backend tests...")
    print("=" * 60)

    # Get the test file path
    test_file = Path(__file__).parent / "test_simplified_backend.py"

    if not test_file.exists():
        print("❌ Test file not found!")
        return False

    # Run the tests
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(test_file),
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=Path(__file__).parent.parent)

        if result.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print(f"\n❌ Tests failed with exit code: {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test_class(test_class):
    """Run tests for a specific test class."""
    print(f"🚀 Running tests for {test_class}...")

    test_file = Path(__file__).parent / "test_simplified_backend.py"

    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            f"{test_file}::{test_class}",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=Path(__file__).parent.parent)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test class
        test_class = sys.argv[1]
        success = run_specific_test_class(test_class)
    else:
        # Run all tests
        success = run_tests()

    exit(0 if success else 1)