#!/usr/bin/env python3
"""
Database Reset Script

Resets the database by dropping all tables and optionally loading seed data.
This script provides a clean slate for development and testing.

⚠️  WARNING: This is DESTRUCTIVE and will delete all data!
⚠️  Only use this in development environments.

Usage:
    python scripts/reset_database.py
    python scripts/reset_database.py --seed
    python scripts/reset_database.py --seed --verbose
    python scripts/reset_database.py --seed --lesson "Neural Networks" --concept "Backpropagation"

Features:
- Drops all database tables (preserves database itself)
- Resets Alembic migration state
- Recreates database schema via Alembic migrations
- Optionally loads seed data using create_seed_data.py
- Comprehensive error handling and rollback
- Confirmation prompts for safety
"""

import argparse
from pathlib import Path
import subprocess
import sys
import traceback

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from sqlalchemy import text

from modules.infrastructure.public import infrastructure_provider
from modules.infrastructure.service import DatabaseConnectionError


def load_environment() -> None:
    """Load environment variables from .env file."""
    if not DOTENV_AVAILABLE:
        return

    # Look for .env file in project root
    backend_dir = Path(__file__).parent.parent
    env_paths = [backend_dir / ".env", backend_dir.parent / ".env"]

    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from {env_path}")
            return

    print("⚠️  No .env file found - using system environment variables only")


def run_command(cmd: str, check: bool = True, capture_output: bool = False, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a shell command with proper error handling."""
    print(f"🔧 Running: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=True, cwd=cwd)  # noqa: S602

        if capture_output and result.stdout:
            print(f"   Output: {result.stdout.strip()}")

        return result

    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        raise


def confirm_action(message: str, force: bool = False) -> bool:
    """Ask for user confirmation unless force is True."""
    if force:
        return True

    response = input(f"{message} (y/N): ").strip().lower()
    return response in ["y", "yes"]


def check_database_connection() -> bool:
    """Check if database connection is available."""
    try:
        infra = infrastructure_provider()
        infra.initialize()

        with infra.get_session_context() as session:
            # Simple query to test connection
            session.execute(text("SELECT 1"))

        print("✅ Database connection verified")
        return True

    except DatabaseConnectionError as e:
        print(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected database error: {e}")
        return False


def drop_all_tables(verbose: bool = False) -> None:
    """Drop all tables in the database."""
    print("🗑️  Dropping all database tables...")

    try:
        infra = infrastructure_provider()
        infra.initialize()

        with infra.get_session_context() as session:
            if verbose:
                print("   Querying existing tables...")

            # Get all table names
            result = session.execute(
                text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename != 'alembic_version'
            """)
            )
            tables = [row[0] for row in result.fetchall()]

            if not tables:
                print("   No tables found to drop")
                return

            if verbose:
                print(f"   Found {len(tables)} tables: {', '.join(tables)}")  # pyright: ignore[reportCallIssue, reportArgumentType]

            # Drop tables with CASCADE to handle foreign key constraints
            for table in tables:
                if verbose:
                    print(f"   Dropping table: {table}")
                session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

            print(f"✅ Dropped {len(tables)} tables")

    except Exception as e:
        print(f"❌ Failed to drop tables: {e}")
        raise


def reset_alembic_version(verbose: bool = False) -> None:
    """Reset the Alembic version table."""
    print("🔄 Resetting Alembic migration state...")

    try:
        infra = infrastructure_provider()
        infra.initialize()

        with infra.get_session_context() as session:
            if verbose:
                print("   Dropping alembic_version table...")

            session.execute(text("DROP TABLE IF EXISTS alembic_version"))
            print("✅ Alembic migration state reset")

    except Exception as e:
        print(f"❌ Failed to reset Alembic state: {e}")
        raise


def run_migrations(verbose: bool = False) -> None:
    """Run Alembic migrations to recreate schema."""
    print("🏗️  Running database migrations...")

    backend_dir = Path(__file__).parent.parent

    try:
        # Run alembic upgrade head (alembic doesn't have --verbose flag)
        cmd = "alembic upgrade head"

        if verbose:
            print(f"   Running: {cmd}")

        result = run_command(cmd, cwd=str(backend_dir), capture_output=True)

        if "Running upgrade" in result.stdout or "Target database is up to date" in result.stdout or "Successfully imported models" in result.stdout:
            print("✅ Database schema created successfully")
            if verbose and result.stdout:
                print(f"   Migration output: {result.stdout.strip()}")
        else:
            print("⚠️  Migration completed but output was unexpected:")
            print(f"   {result.stdout}")

    except subprocess.CalledProcessError:
        print("❌ Migration failed!")
        print("   This might indicate:")
        print("   - Missing migration files")
        print("   - Database connection issues")
        print("   - Schema conflicts")
        raise


def load_seed_data(verbose: bool = False, **seed_kwargs: str) -> None:
    """Load seed data using the create_seed_data.py script."""
    print("🌱 Loading seed data...")

    backend_dir = Path(__file__).parent.parent
    seed_script = backend_dir / "scripts" / "create_seed_data.py"

    if not seed_script.exists():
        raise FileNotFoundError(f"Seed data script not found: {seed_script}")

    # Build command
    cmd_parts = [sys.executable, str(seed_script)]

    if verbose:
        cmd_parts.append("--verbose")

    # Add optional seed data parameters
    if seed_kwargs.get("lesson"):
        cmd_parts.extend(["--lesson", seed_kwargs["lesson"]])
    if seed_kwargs.get("concept"):
        cmd_parts.extend(["--concept", seed_kwargs["concept"]])
    if seed_kwargs.get("level"):
        cmd_parts.extend(["--level", seed_kwargs["level"]])
    if seed_kwargs.get("domain"):
        cmd_parts.extend(["--domain", seed_kwargs["domain"]])

    try:
        result = subprocess.run(cmd_parts, cwd=str(backend_dir), check=True, capture_output=True, text=True)  # noqa: S603

        # Print the output from seed script
        if result.stdout:
            print(result.stdout)

        print("✅ Seed data loaded successfully")

    except subprocess.CalledProcessError as e:
        print("❌ Seed data loading failed!")
        if e.stdout:
            print("stdout:", e.stdout)
        if e.stderr:
            print("stderr:", e.stderr)
        raise


def main() -> None:
    """Main function to reset database and optionally load seed data."""
    parser = argparse.ArgumentParser(
        description="Reset database and optionally load seed data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/reset_database.py                    # Interactive confirmation
  python scripts/reset_database.py --confirm          # Skip confirmation
  python scripts/reset_database.py --confirm --seed --verbose
  python scripts/reset_database.py --seed --lesson "Neural Networks" --concept "Backpropagation"

⚠️  WARNING: This will delete all data in the database!
        """,
    )

    # Optional arguments
    parser.add_argument("--confirm", action="store_true", help="Skip interactive confirmation prompt")
    parser.add_argument("--seed", action="store_true", help="Load seed data after reset")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")

    # Seed data options (passed through to create_seed_data.py)
    parser.add_argument("--lesson", help="Lesson title for seed data")
    parser.add_argument("--concept", help="Core concept for seed data")
    parser.add_argument("--level", choices=["beginner", "intermediate", "advanced"], help="User level for seed data")
    parser.add_argument("--domain", help="Subject domain for seed data")

    args = parser.parse_args()

    # Configure output
    if args.verbose:
        print("🔧 Verbose mode enabled")

    print("🔄 Database Reset Script")
    print("=" * 50)

    # Show warning and ask for confirmation unless --confirm or --force is used
    if not args.confirm and not args.force:
        print("⚠️  WARNING: This will permanently delete all data in the database!")
        print("   - All tables will be dropped")
        print("   - Alembic migration state will be reset")
        print("   - Database schema will be recreated")
        if args.seed:
            print("   - Seed data will be loaded")
        print()

        if not confirm_action("Are you sure you want to continue?"):
            print("❌ Operation cancelled by user")
            sys.exit(0)
    elif args.confirm:
        print("✅ Confirmation skipped via --confirm flag")

    try:
        # Load environment
        load_environment()

        # Check database connection
        if not check_database_connection():
            print("❌ Cannot proceed without database connection")
            sys.exit(1)

        print("\n🚀 Starting database reset...")

        # Step 1: Drop all tables
        drop_all_tables(args.verbose)

        # Step 2: Reset Alembic version
        reset_alembic_version(args.verbose)

        # Step 3: Run migrations to recreate schema
        run_migrations(args.verbose)

        # Step 4: Load seed data if requested
        if args.seed:
            seed_kwargs = {}
            if args.lesson:
                seed_kwargs["lesson"] = args.lesson
            if args.concept:
                seed_kwargs["concept"] = args.concept
            if args.level:
                seed_kwargs["level"] = args.level
            if args.domain:
                seed_kwargs["domain"] = args.domain

            load_seed_data(args.verbose, **seed_kwargs)

        print("\n🎉 Database reset completed successfully!")
        print("   ✅ All tables dropped and recreated")
        print("   ✅ Migration state reset")
        print("   ✅ Schema recreated from migrations")
        if args.seed:
            print("   ✅ Seed data loaded")

        print("\n🔗 Next steps:")
        print("   - Start your application server")
        if args.seed:
            print("   - Check frontend at http://localhost:3000")
        else:
            print("   - Create lessons via API or run seed script")

    except KeyboardInterrupt:
        print("\n❌ Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Reset failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
