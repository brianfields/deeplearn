#!/usr/bin/env python3
"""
Integration Test Runner

Runs all integration tests across backend modules with proper environment setup.
Integration tests use real external APIs and may incur costs.

Usage:
    python scripts/run_integration.py                        # Run all integration tests
    python scripts/run_integration.py --module llm_services  # Run tests for specific module
    python scripts/run_integration.py --no-cache             # Disable LLM cache for tests
    python scripts/run_integration.py --model gpt-5-mini     # Override LLM model for tests
    python scripts/run_integration.py --help                 # Show help

Examples:
    python scripts/run_integration.py
    python scripts/run_integration.py --module llm_services
    python scripts/run_integration.py --cost-check           # Check environment without running tests
    python scripts/run_integration.py --model gpt-5-mini     # Run with GPT-5 Mini
    python scripts/run_integration.py --verbose
"""

import argparse
import logging
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
        cmd = f"source {activate_script} && python scripts/run_integration.py {' '.join(sys.argv[1:])}"
        result = subprocess.run(["bash", "-c", cmd], cwd=Path(__file__).parent.parent, check=True, capture_output=True, text=True)  # noqa: S603,S607
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
    with env_path.open() as f:
        for line_content in f:
            stripped_line = line_content.strip()
            if stripped_line and not stripped_line.startswith("#") and "=" in stripped_line:
                key, value = stripped_line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Only set if not already in environment
                if key not in os.environ:
                    os.environ[key] = value


def setup_detailed_logging() -> None:
    """Set up detailed logging for verbose mode."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])

    # Set specific loggers to DEBUG for detailed flow tracking
    logging.getLogger("modules.llm_services.providers.openai").setLevel(logging.DEBUG)
    logging.getLogger("modules.flow_engine.flows.base").setLevel(logging.DEBUG)
    logging.getLogger("modules.flow_engine.steps.base").setLevel(logging.DEBUG)
    logging.getLogger("modules.content_creator.flows").setLevel(logging.INFO)
    logging.getLogger("modules.content_creator.service").setLevel(logging.INFO)


def setup_environment() -> None:
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


def check_environment() -> list[str]:
    """Check if environment is properly configured for integration tests"""
    issues = []

    # Check for API keys based on available modules
    backend_dir = Path(__file__).parent.parent
    modules_dir = backend_dir / "modules"

    # Check LLM services requirements
    llm_services_dir = modules_dir / "llm_services"
    if llm_services_dir.exists() and not os.getenv("OPENAI_API_KEY"):
        issues.append("OPENAI_API_KEY environment variable not set (required for LLM services)")

    # Add checks for other modules as they're created

    return issues


def find_integration_test_files(module_name: str | None = None) -> list[str]:
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


def run_integration_tests(module_name: str | None = None, verbose: bool = False) -> int:
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

    # Setup detailed logging if verbose mode is enabled
    if verbose:
        print("📝 Setting up detailed logging for verbose mode...")
        # Set environment variable to enable detailed logging in subprocess
        env["INTEGRATION_TEST_VERBOSE_LOGGING"] = "true"

    # Allow disabling LLM cache via env flag from CLI
    if os.getenv("RUN_INTEGRATION_NO_CACHE", "false").lower() == "true":
        print("🚫 Disabling LLM cache for this run (LLM_CACHE_ENABLED=false)")
        env["LLM_CACHE_ENABLED"] = "false"

    # Build pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        *test_files,
        "-v" if verbose else "-q",
        "--tb=short",
    ]

    # Add flags for verbose mode to show print statements and logging
    if verbose:
        cmd.extend(["-s", "--log-cli-level=DEBUG", "--log-cli-format=%(asctime)s - %(name)s - %(levelname)s - %(message)s"])

    print(f"🚀 Running: {' '.join(cmd)}")

    # Run tests
    result = subprocess.run(cmd, check=False, cwd=Path(__file__).parent.parent, env=env)  # noqa: S603

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


def main() -> int:
    """Main entry point"""
    # Ensure virtual environment is activated
    if not ensure_venv_activated():
        return 1

    doc_epilog = __doc__.split("Usage:")[1] if __doc__ and "Usage:" in __doc__ else ""
    parser = argparse.ArgumentParser(description="Run integration tests across backend modules", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=doc_epilog)

    parser.add_argument("--module", "-m", help="Run tests for specific module only (e.g., llm_services, infrastructure)")
    parser.add_argument("--model", help="Override LLM model for tests (default: gpt-5-mini)", default="gpt-5-mini")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM cache during tests (sets LLM_CACHE_ENABLED=false)")

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

    # Pass no-cache flag via env to runner
    if args.no_cache:
        os.environ["RUN_INTEGRATION_NO_CACHE"] = "true"

    # Pass model override to subprocess via env
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model

    # Run tests
    return run_integration_tests(args.module, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
