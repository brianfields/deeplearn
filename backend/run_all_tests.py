#!/usr/bin/env python3
"""
Comprehensive Test Runner for Backend

This script provides an easy way to run all tests locally with different configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import os

def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ {description} - FAILED")
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout)
    
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Run backend tests')
    parser.add_argument('--quick', action='store_true', help='Run only quick tests')
    parser.add_argument('--mcq', action='store_true', help='Run only MCQ-related tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--file', type=str, help='Run specific test file')
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🧪 Backend Test Runner")
    print("=" * 50)
    print(f"Working directory: {backend_dir}")
    print()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.parallel:
        base_cmd.extend(["-n", "auto"])
    
    if args.coverage:
        base_cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # Determine which tests to run
    test_results = []
    
    if args.file:
        # Run specific test file
        test_file = f"tests/{args.file}" if not args.file.startswith("tests/") else args.file
        if not test_file.endswith(".py"):
            test_file += ".py"
        
        cmd = base_cmd + [test_file]
        success = run_command(cmd, f"Running {test_file}")
        test_results.append((test_file, success))
    
    elif args.quick:
        # Run quick tests only
        quick_tests = [
            "tests/test_data_structures.py",
            "tests/test_very_simple.py"
        ]
        
        for test_file in quick_tests:
            cmd = base_cmd + [test_file]
            success = run_command(cmd, f"Quick test: {test_file}")
            test_results.append((test_file, success))
    
    elif args.mcq:
        # Run MCQ-related tests only
        mcq_tests = [
            "tests/test_mcq_prompts.py",
            "tests/test_mcq_service.py",
            "tests/test_orchestrator_mcq.py",
            "tests/test_mcq_script.py"
        ]
        
        for test_file in mcq_tests:
            cmd = base_cmd + [test_file]
            success = run_command(cmd, f"MCQ test: {test_file}")
            test_results.append((test_file, success))
    
    elif args.integration:
        # Run integration tests only
        integration_tests = [
            "tests/test_bite_sized_integration.py",
            "tests/test_system.py"
        ]
        
        for test_file in integration_tests:
            cmd = base_cmd + [test_file]
            success = run_command(cmd, f"Integration test: {test_file}")
            test_results.append((test_file, success))
    
    else:
        # Run all tests in logical groups
        test_groups = [
            ("Core Data Structures", ["tests/test_data_structures.py"]),
            ("MCQ System", [
                "tests/test_mcq_prompts.py",
                "tests/test_mcq_service.py",
                "tests/test_orchestrator_mcq.py",
                "tests/test_mcq_script.py"
            ]),
            ("Backend Services", [
                "tests/test_very_simple.py",
                "tests/test_conversational.py"
            ]),
            ("Integration Tests", [
                "tests/test_bite_sized_integration.py",
                "tests/test_system.py"
            ])
        ]
        
        for group_name, test_files in test_groups:
            print(f"\n🏷️  {group_name}")
            print("=" * 50)
            
            for test_file in test_files:
                if Path(test_file).exists():
                    cmd = base_cmd + [test_file]
                    success = run_command(cmd, f"{group_name}: {test_file}")
                    test_results.append((test_file, success))
                else:
                    print(f"⚠️  Warning: {test_file} not found, skipping")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_file, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_file}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The backend is working correctly.")
        return 0
    else:
        print(f"\n💥 {total - passed} tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())