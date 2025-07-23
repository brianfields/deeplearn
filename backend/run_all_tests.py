#!/usr/bin/env python3
"""
Test Runner for Clean Two-Layer Architecture

This script runs all backend tests for our clean two-layer architecture.
Designed for both local development and CI/CD environments.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return the result."""
    print(f"\n🔄 {description}")
    if len(cmd) > 3:  # Only show command if verbose or complex
        print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        if result.stdout.strip():
            # Only show stdout if it contains useful info (not just dots)
            stdout_lines = result.stdout.strip().split("\n")
            useful_lines = [line for line in stdout_lines if line.strip() and not line.strip().startswith(".")]
            if useful_lines:
                print("\n".join(useful_lines))
    else:
        print(f"❌ {description} - FAILED")
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout)

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run backend tests for two-layer architecture")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", type=str, help="Run specific test file (optional)")

    args = parser.parse_args()

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    print("🧪 Backend Test Runner - Two-Layer Architecture")
    print("=" * 60)
    print(f"Working directory: {backend_dir}")
    print()

    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]

    if args.verbose:
        base_cmd.append("-v")
    else:
        base_cmd.append("-q")  # Quiet mode when not verbose

    # Test files in logical execution order
    test_files = [
        ("Service Layer", "tests/test_services.py"),
        ("Content Creation API", "tests/test_api_content_creation.py"),
        ("Learning API", "tests/test_api_learning.py"),
        ("Integration Workflows", "tests/test_integration.py"),
    ]

    test_results = []

    if args.file:
        # Run specific test file
        test_file = f"tests/{args.file}" if not args.file.startswith("tests/") else args.file
        if not test_file.endswith(".py"):
            test_file += ".py"

        if not Path(test_file).exists():
            print(f"❌ Error: Test file {test_file} not found")
            return 1

        cmd = [*base_cmd, test_file]
        success = run_command(cmd, f"Running {test_file}")
        test_results.append((test_file, success))

    else:
        # Run all tests in order
        print("Running all tests in logical order...")

        for description, test_file in test_files:
            if Path(test_file).exists():
                cmd = [*base_cmd, test_file]
                success = run_command(cmd, description)
                test_results.append((test_file, success))
            else:
                print(f"⚠️  Warning: {test_file} not found, skipping")

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)

    for test_file, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        # Show just filename for cleaner output
        filename = Path(test_file).name
        print(f"{status} - {filename}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Two-layer architecture is working correctly.")
        return 0
    else:
        print(f"\n💥 {total - passed} tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
