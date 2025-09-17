#!/usr/bin/env python3
"""
Unit Test Runner

Runs all unit tests across backend modules with proper environment setup.
Unit tests are fast, use mocks, and don't require external API keys.

Usage:
    python scripts/run_unit.py                    # Run all unit tests
    python scripts/run_unit.py --module llm_services  # Run tests for specific module
    python scripts/run_unit.py --help            # Show help

Examples:
    python scripts/run_unit.py
    python scripts/run_unit.py --module llm_services
    python scripts/run_unit.py --module infrastructure
    python scripts/run_unit.py --verbose
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def ensure_venv_activated() -> bool:
    """Ensure the deeplearn virtual environment is activated"""
    # Check if we're already in a virtual environment
    virtual_env = os.getenv("VIRTUAL_ENV")
    if virtual_env:
        venv_name = Path(virtual_env).name
        if venv_name in {"deeplearn", "venv"}:
            print("✅ Virtual environment 'deeplearn' is already activated")
            return True
        else:
            print(f"⚠️  Different virtual environment is active: {venv_name}")
            print("   Deactivate it first, then run this script again")
            return False

    print("🔄 Virtual environment not activated. Activating 'deeplearn'...")
    try:
        # Source the activate script directly and re-run the script
        activate_script = Path.home() / ".virtualenvs" / "deeplearn" / "bin" / "activate"
        if not activate_script.exists():
            print(f"❌ Activate script not found at {activate_script}")
            print("💡 Make sure the 'deeplearn' virtual environment exists")
            return False

        # Re-run the script with the venv activated
        cmd = f"source {activate_script} && python scripts/run_unit.py {' '.join(sys.argv[1:])}"
        result = subprocess.run(["bash", "-c", cmd], cwd=Path(__file__).parent.parent, check=True, capture_output=True, text=True)
        # If we reach here, the subprocess completed successfully
        # Exit with the same return code
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to activate virtual environment: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        print("💡 Make sure the 'deeplearn' virtual environment exists")
        return False


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


def find_test_files(module_name: str | None = None) -> list[str]:
    """Find unit test files to run"""
    backend_dir = Path(__file__).parent.parent

    if module_name:
        # Test specific module
        module_path = backend_dir / "modules" / module_name
        if not module_path.exists():
            print(f"❌ Module '{module_name}' not found at {module_path}")
            return []

        # Find unit test files (exclude integration tests)
        test_files = []
        for test_file in module_path.glob("test_*.py"):
            test_files.append(str(test_file.relative_to(backend_dir)))

        if not test_files:
            print(f"⚠️  No unit test files found in module '{module_name}'")

        return test_files
    else:
        # Test all modules
        test_files = []
        modules_dir = backend_dir / "modules"

        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir():
                    tests_dir = module_dir
                    for test_file in tests_dir.glob("test_*.py"):
                        if "integration" not in test_file.name:
                            test_files.append(str(test_file.relative_to(backend_dir)))

        return test_files


def run_unit_tests(module_name: str | None = None, verbose: bool = False) -> int:
    """Run unit tests"""
    print("🧪 Running unit tests (fast, mocked, no API costs)...")

    if module_name:
        print(f"📦 Module: {module_name}")
    else:
        print("📦 All modules")

    # Find test files
    test_files = find_test_files(module_name)

    if not test_files:
        print("❌ No unit test files found!")
        return 1

    print(f"📋 Found {len(test_files)} unit test file(s)")
    if verbose:
        for test_file in test_files:
            print(f"  - {test_file}")

    # Build pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        *test_files,
        "-v" if verbose else "-q",
        "-m",
        "not integration",  # Exclude integration tests
        "--tb=short",
    ]

    print(f"🚀 Running: {' '.join(cmd)}")

    # Run tests
    result = subprocess.run(cmd, check=False, cwd=Path(__file__).parent.parent)

    if result.returncode == 0:
        print("✅ All unit tests passed!")
    else:
        print("❌ Some unit tests failed!")

    return result.returncode


def main() -> int:
    """Main entry point"""
    # Ensure virtual environment is activated
    if not ensure_venv_activated():
        return 1

    doc_epilog = __doc__.split("Usage:")[1] if __doc__ and "Usage:" in __doc__ else ""
    parser = argparse.ArgumentParser(description="Run unit tests across backend modules", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=doc_epilog)

    parser.add_argument("--module", "-m", help="Run tests for specific module only (e.g., llm_services, infrastructure)")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--list", "-l", action="store_true", help="List available modules and exit")

    args = parser.parse_args()

    # Setup environment
    setup_environment()

    # List modules if requested
    if args.list:
        backend_dir = Path(__file__).parent.parent
        modules_dir = backend_dir / "modules"

        print("📦 Available modules:")
        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir() and (module_dir / "tests").exists():
                    print(f"  - {module_dir.name}")
        else:
            print("  No modules found")
        return 0

    # Run tests
    return run_unit_tests(args.module, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
