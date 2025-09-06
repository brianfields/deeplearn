#!/usr/bin/env python3
"""
Integration Test Runner

Runs all integration tests across backend modules with proper environment setup.
Integration tests use real external APIs and may incur costs.

Usage:
    python scripts/run_integration.py                    # Run all integration tests
    python scripts/run_integration.py --module llm_services  # Run tests for specific module
    python scripts/run_integration.py --help            # Show help

Examples:
    python scripts/run_integration.py
    python scripts/run_integration.py --module llm_services
    python scripts/run_integration.py --cost-check      # Check environment without running tests
    python scripts/run_integration.py --verbose
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def load_env_file(env_path: Path) -> None:
    """Load environment variables from .env file"""
    if not env_path.exists():
        return

    print(f"📄 Loading environment from: {env_path}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Only set if not already in environment
                if key not in os.environ:
                    os.environ[key] = value


def setup_environment():
    """Setup environment by loading .env files"""
    backend_dir = Path(__file__).parent.parent

    # Load .env files in order of precedence (most specific first)
    env_files = [
        backend_dir / ".env.test.local",  # Local test overrides (gitignored)
        backend_dir / ".env.test",  # Test environment
        backend_dir / ".env.local",  # Local overrides (gitignored)
        backend_dir / ".env",  # Default environment
        backend_dir / ".." / ".env",  # Root environment
    ]

    loaded_any = False
    for env_file in env_files:
        if env_file.exists():
            load_env_file(env_file)
            loaded_any = True

    if not loaded_any:
        print("ℹ️  No .env files found. Using system environment variables only.")

    return loaded_any


def check_environment() -> list[str]:
    """Check if environment is properly configured for integration tests"""
    issues = []

    # Check for API keys based on available modules
    backend_dir = Path(__file__).parent.parent
    modules_dir = backend_dir / "modules"

    # Check LLM services requirements
    llm_services_dir = modules_dir / "llm_services"
    if llm_services_dir.exists():
        if not os.getenv("OPENAI_API_KEY"):
            issues.append("OPENAI_API_KEY environment variable not set (required for LLM services)")

    # Add checks for other modules as they're created
    # if (modules_dir / "database").exists():
    #     if not os.getenv("DATABASE_URL"):
    #         issues.append("DATABASE_URL not set (required for database integration tests)")

    return issues


def find_integration_test_files(module_name: str = None) -> list[str]:
    """Find integration test files to run"""
    backend_dir = Path(__file__).parent.parent

    if module_name:
        # Test specific module
        module_path = backend_dir / "modules" / module_name / "tests"
        if not module_path.exists():
            print(f"❌ Module '{module_name}' not found at {module_path}")
            return []

        # Find integration test files
        test_files = []
        for test_file in module_path.glob("test_*integration*.py"):
            test_files.append(str(test_file.relative_to(backend_dir)))

        if not test_files:
            print(f"⚠️  No integration test files found in module '{module_name}'")

        return test_files
    else:
        # Test all modules
        test_files = []
        modules_dir = backend_dir / "modules"

        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir() and (module_dir / "tests").exists():
                    tests_dir = module_dir / "tests"
                    for test_file in tests_dir.glob("test_*integration*.py"):
                        test_files.append(str(test_file.relative_to(backend_dir)))

        # Also check root tests directory
        root_tests = backend_dir / "tests"
        if root_tests.exists():
            for test_file in root_tests.glob("test_*integration*.py"):
                test_files.append(str(test_file.relative_to(backend_dir)))

        return test_files


def run_integration_tests(module_name: str = None, verbose: bool = False) -> int:
    """Run integration tests"""
    print("🌐 Running integration tests (real APIs, may incur costs)...")

    if module_name:
        print(f"📦 Module: {module_name}")
    else:
        print("📦 All modules")

    # Check environment
    issues = check_environment()
    if issues:
        print("❌ Environment issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n💡 Tip: Create a .env file with required API keys")
        return 1

    # Find test files
    test_files = find_integration_test_files(module_name)

    if not test_files:
        print("❌ No integration test files found!")
        return 1

    print(f"📋 Found {len(test_files)} integration test file(s)")
    if verbose:
        for test_file in test_files:
            print(f"  - {test_file}")

    # Set environment variables for integration tests
    env = os.environ.copy()

    # Build pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        *test_files,
        "-v" if verbose else "-q",
        "--tb=short",
    ]

    print(f"🚀 Running: {' '.join(cmd)}")

    # Run tests
    result = subprocess.run(cmd, check=False, cwd=Path(__file__).parent.parent, env=env)

    if result.returncode == 0:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed!")

    return result.returncode


def cost_check() -> int:
    """Check environment and estimate costs without running tests"""
    print("💰 Integration Test Cost Check")
    print("=" * 40)

    # Check environment
    issues = check_environment()
    if issues:
        print("❌ Environment issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ Environment looks good!")

    # Find test files
    test_files = find_integration_test_files()
    print(f"📋 Found {len(test_files)} integration test file(s)")

    # Estimate costs (rough)
    estimated_requests = len(test_files) * 5  # Rough estimate
    estimated_tokens = estimated_requests * 100  # Very rough
    estimated_cost = estimated_tokens * 0.000002  # GPT-3.5-turbo pricing

    print("📊 Rough estimates:")
    print(f"  - Test files: {len(test_files)}")
    print(f"  - Estimated API requests: ~{estimated_requests}")
    print(f"  - Estimated tokens: ~{estimated_tokens}")
    print(f"  - Estimated cost: ~${estimated_cost:.4f}")

    print("\n💡 To run integration tests:")
    print("   python scripts/run_integration.py")

    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run integration tests across backend modules", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Usage:")[1] if "Usage:" in __doc__ else "")

    parser.add_argument("--module", "-m", help="Run tests for specific module only (e.g., llm_services, infrastructure)")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--cost-check", "-c", action="store_true", help="Check environment and estimate costs without running tests")

    parser.add_argument("--list", "-l", action="store_true", help="List available modules and exit")

    args = parser.parse_args()

    # Setup environment
    setup_environment()

    # Handle special commands
    if args.cost_check:
        return cost_check()

    if args.list:
        backend_dir = Path(__file__).parent.parent
        modules_dir = backend_dir / "modules"

        print("📦 Available modules with integration tests:")
        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir() and (module_dir / "tests").exists():
                    tests_dir = module_dir / "tests"
                    integration_files = list(tests_dir.glob("test_*integration*.py"))
                    if integration_files:
                        print(f"  - {module_dir.name} ({len(integration_files)} test file(s))")
        else:
            print("  No modules found")
        return 0

    # Run tests
    return run_integration_tests(args.module, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
