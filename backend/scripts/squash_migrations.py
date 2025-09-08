#!/usr/bin/env python3
"""
Migration Squash Script

This script helps consolidate multiple Alembic migrations into a single clean initial migration.
Useful for development environments when you want to clean up migration history before deployment.

⚠️  WARNING: This is DESTRUCTIVE and should only be used in development!
⚠️  This will permanently delete all existing migration files and history.

What this script does:
1. Removes all existing migration files from alembic/versions/
2. Drops ALL database tables by recreating the public schema (DESTRUCTIVE)
3. Drops the alembic_version table to reset migration state
4. Creates a fresh initial migration with all current models
5. Optionally applies the new migration

Requirements:
- Must be run from the backend directory
- Database must be accessible via DATABASE_URL or DATABASE_PASSWORD environment variable
- Virtual environment should be activated
"""

import glob
import os
from pathlib import Path
import subprocess
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Look for .env file in backend directory (parent of scripts)
    base_dir = Path(__file__).parent.parent.parent
    env_file = base_dir / ".env"

    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")

except ImportError:
    print("⚠️  python-dotenv not available, skipping .env file loading")
    print("   Install with: pip install python-dotenv")


def run_command(cmd: str, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command and handle errors."""
    print(f"🔧 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=True)
        if capture_output and result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if capture_output and e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        if check:
            sys.exit(1)
        # Return a mock CompletedProcess for type consistency
        return subprocess.CompletedProcess(args=cmd, returncode=e.returncode, stdout=e.stdout, stderr=e.stderr)


def check_prerequisites() -> bool:
    """Check if we're in the right directory and have the right tools."""
    print("🔍 Checking prerequisites...")

    # Check if we're in backend directory
    if not os.path.exists("alembic"):
        print("❌ Not in backend directory (no alembic folder found)")
        return False

    if not os.path.exists("alembic/versions"):
        print("❌ No alembic/versions directory found")
        return False

    # Check if database configuration is available (DATABASE_URL or DATABASE_PASSWORD)
    database_url = os.environ.get("DATABASE_URL")
    database_password = os.environ.get("DATABASE_PASSWORD")

    if not database_url and not database_password:
        print("❌ Database configuration not found")
        print("   Set either DATABASE_URL or DATABASE_PASSWORD environment variable")
        print("   Example:")
        print("     export DATABASE_PASSWORD='your-db-password'")
        print("     # or")
        print("     export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'")
        return False

    # Check if alembic is available
    try:
        run_command("alembic --help", capture_output=True)
    except:
        print("❌ Alembic not available (is virtual environment activated?)")
        return False

    # Check if psql is available
    try:
        run_command("psql --version", capture_output=True)
    except:
        print("❌ psql not available (needed for database operations)")
        return False

    print("✅ All prerequisites met")
    return True


def get_migration_files() -> list[str]:
    """Get list of existing migration files."""
    pattern = "alembic/versions/*.py"
    files = glob.glob(pattern)
    # Filter out __pycache__ and other non-migration files
    migration_files = [f for f in files if not f.endswith("__init__.py")]
    return migration_files


def confirm_action(message: str) -> bool:
    """Get user confirmation for destructive actions."""
    response = input(f"⚠️  {message} (y/N): ").lower().strip()
    return response == "y" or response == "yes"


def remove_migration_files() -> None:
    """Remove all existing migration files."""
    print("\n🗑️  Removing existing migration files...")

    migration_files = get_migration_files()
    if not migration_files:
        print("   No migration files found to remove")
        return

    print(f"   Found {len(migration_files)} migration files:")
    for file in migration_files:
        print(f"     - {file}")

    if not confirm_action("Delete all these migration files?"):
        print("❌ Aborted by user")
        sys.exit(0)

    for file in migration_files:
        os.remove(file)
        print(f"   ✅ Removed {file}")


def reset_alembic_version() -> None:
    """Drop the alembic_version table to reset migration state."""
    print("\n🔄 Resetting alembic version table...")

    # Get database URL using same logic as other scripts
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        password = os.environ.get("DATABASE_PASSWORD", "")
        if password:
            database_url = f"postgresql://digital_innie_user:{password}@localhost:5432/digital_innie_db"
        else:
            database_url = "postgresql://postgres:@localhost:5432/digital_innie_db"

    # Convert asyncpg URLs back to regular postgresql for psql
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    cmd = f'psql "{database_url}" -c "DROP TABLE IF EXISTS alembic_version;"'
    result = run_command(cmd, check=False, capture_output=True)

    if result.returncode == 0:
        print("   ✅ Alembic version table reset")
    else:
        print("   ⚠️  Warning: Could not reset alembic version table (may not exist)")


def drop_and_recreate_database() -> str | None:
    """Drop and recreate the entire database (alternative to schema recreation)."""
    print("\n🗑️  Dropping and recreating entire database...")

    # Get database URL using same logic as other scripts
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        password = os.environ.get("DATABASE_PASSWORD", "")
        if password:
            database_url = f"postgresql://digital_innie_user:{password}@localhost:5432/digital_innie_db"
        else:
            database_url = "postgresql://postgres:@localhost:5432/digital_innie_db"

    # Convert asyncpg URLs back to regular postgresql for psql
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # Extract database name and create postgres connection URL
    db_name = database_url.split("/")[-1]
    postgres_url = database_url.rsplit("/", 1)[0] + "/postgres"

    # Drop database (if exists)
    drop_cmd = f'psql "{postgres_url}" -c "DROP DATABASE IF EXISTS {db_name};"'
    drop_result = run_command(drop_cmd, check=False, capture_output=True)

    if drop_result.returncode == 0:
        print(f"   ✅ Database '{db_name}' dropped")
    else:
        print(f"   ⚠️  Could not drop database '{db_name}' - it may not exist")

    # Create database
    create_cmd = f'psql "{postgres_url}" -c "CREATE DATABASE {db_name};"'
    create_result = run_command(create_cmd, check=False, capture_output=True)

    if create_result.returncode == 0:
        print(f"   ✅ Database '{db_name}' created")
    else:
        print(f"   ❌ Failed to create database '{db_name}'")
        print(f"   Error output: {create_result.stderr}")

        # Check if it's a permission error
        if "permission denied" in create_result.stderr.lower():
            print("\n💡 Permission Error Solutions:")
            print("   1. Run as a superuser (postgres):")
            print(f'      sudo -u postgres psql -c "CREATE DATABASE {db_name};"')
            print("   2. Grant CREATEDB privilege to your user:")
            print('      sudo -u postgres psql -c "ALTER USER your_username CREATEDB;"')
            print("   3. Use schema recreation instead (option 1) - doesn't require database creation")
            print("   4. Manually create the database and re-run this script")

            if confirm_action("Try schema recreation method instead?"):
                print("\n🔄 Switching to schema recreation method...")
                return "fallback_to_schema"

        sys.exit(1)

    return None  # Success case


def drop_all_tables() -> None:
    """Drop all tables individually (safer than schema recreation).

    This ensures autogenerate creates only CREATE operations and avoids
    attempting to DROP tables with dependency constraints during upgrade.
    Also works when user doesn't own the schema but owns the tables.
    """
    print("\n🧹 Dropping all tables individually...")

    # Get database URL using same logic as other scripts
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        password = os.environ.get("DATABASE_PASSWORD", "")
        if password:
            database_url = f"postgresql://digital_innie_user:{password}@localhost:5432/digital_innie_db"
        else:
            database_url = "postgresql://postgres:@localhost:5432/digital_innie_db"

    # Convert asyncpg URLs back to regular postgresql for psql
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # First, try to connect to the database to see if it exists
    test_cmd = f'psql "{database_url}" -c "SELECT 1;" 2>/dev/null'
    test_result = run_command(test_cmd, check=False, capture_output=True)

    if test_result.returncode != 0:
        print("   ⚠️  Database doesn't exist or is inaccessible. Attempting to create it...")
        # Extract database name from URL for creation
        db_name = database_url.split("/")[-1]
        # Connect to postgres database to create the target database
        postgres_url = database_url.rsplit("/", 1)[0] + "/postgres"
        create_cmd = f'psql "{postgres_url}" -c "CREATE DATABASE {db_name};" 2>/dev/null'
        create_result = run_command(create_cmd, check=False, capture_output=True)

        if create_result.returncode == 0:
            print(f"   ✅ Database '{db_name}' created")
        else:
            print(f"   ⚠️  Database '{db_name}' may already exist or creation failed - continuing...")

    # Try schema recreation first (fastest method)
    schema_cmd = f'psql "{database_url}" -v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS public CASCADE;" -c "CREATE SCHEMA public;" -c "GRANT ALL ON SCHEMA public TO public;"'
    schema_result = run_command(schema_cmd, check=False, capture_output=True)

    if schema_result.returncode == 0:
        print("   ✅ Database schema reset (public schema recreated)")
        return
    else:
        print("   ⚠️  Schema recreation failed (likely permission issue). Trying individual table drops...")
        print(f"   Schema error: {schema_result.stderr}")

    # Fallback: Drop tables individually
    # First, get list of all tables
    list_tables_cmd = f"psql \"{database_url}\" -t -c \"SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version';\""
    list_result = run_command(list_tables_cmd, check=False, capture_output=True)

    if list_result.returncode != 0:
        print("   ❌ Failed to list tables")
        sys.exit(1)

    tables = [table.strip() for table in list_result.stdout.split("\n") if table.strip()]

    if not tables:
        print("   ✅ No tables to drop")
        return

    print(f"   Found {len(tables)} tables to drop: {', '.join(tables)}")

    # Drop tables with CASCADE to handle foreign key constraints
    for table in tables:
        drop_cmd = f'psql "{database_url}" -c "DROP TABLE IF EXISTS {table} CASCADE;"'
        drop_result = run_command(drop_cmd, check=False, capture_output=True)

        if drop_result.returncode == 0:
            print(f"   ✅ Dropped table: {table}")
        else:
            print(f"   ⚠️  Failed to drop table {table}: {drop_result.stderr}")

    print("   ✅ Individual table drops completed")


def create_fresh_migration(migration_name: str) -> str:
    """Create a new initial migration with all current models."""
    print(f"\n🆕 Creating fresh migration: {migration_name}...")

    cmd = f'alembic revision --autogenerate -m "{migration_name}"'
    result = run_command(cmd, capture_output=True)

    if result.returncode == 0:
        print("   ✅ Fresh migration created successfully")
        # Extract migration ID from output if possible
        output_lines = result.stdout.split("\n")
        for line in output_lines:
            if "Generating" in line and ".py" in line:
                # Extract filename from path
                migration_file = line.split("/")[-1].replace(" ...  done", "")
                return migration_file
        return "unknown"
    else:
        print("   ❌ Failed to create migration")
        sys.exit(1)


def apply_migration() -> None:
    """Apply the new migration to the database."""
    print("\n🚀 Applying fresh migration...")

    cmd = "alembic upgrade head"
    result = run_command(cmd, capture_output=True)

    if result.returncode == 0:
        print("   ✅ Migration applied successfully")
    else:
        print("   ❌ Failed to apply migration")
        sys.exit(1)


def verify_migration_state() -> None:
    """Verify the final migration state."""
    print("\n✅ Verifying migration state...")

    cmd = "alembic current"
    result = run_command(cmd, capture_output=True)

    if result.returncode == 0:
        print("   ✅ Migration state verified")
    else:
        print("   ⚠️  Warning: Could not verify migration state")


def main() -> None:
    """Main script execution."""
    print("🔄 Alembic Migration Squash Script")
    print("=" * 50)

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Show current migration files
    migration_files = get_migration_files()
    if migration_files:
        print(f"\n📋 Current migration files ({len(migration_files)}):")
        for file in migration_files:
            print(f"   - {os.path.basename(file)}")
    else:
        print("\n📋 No existing migration files found")
        if not confirm_action("Continue anyway to create initial migration?"):
            sys.exit(0)

    # Final confirmation
    print("\n⚠️  THIS OPERATION IS DESTRUCTIVE!")
    print("This will:")
    print("   1. Delete ALL existing migration files")
    print("   2. Reset the database (either schema recreation or full database drop/recreate)")
    print("   3. Reset the alembic version table (if using schema recreation)")
    print("   4. Create a single fresh migration with current schema")
    print("   5. Optionally apply the new migration")

    if not confirm_action("Are you absolutely sure you want to continue?"):
        print("❌ Operation cancelled")
        sys.exit(0)

    # Ask about database reset method
    print("\n🔧 Choose database reset method:")
    print("   1. Schema recreation (DROP SCHEMA public CASCADE; CREATE SCHEMA public) - Recommended")
    print("   2. Full database drop/recreate (DROP DATABASE; CREATE DATABASE) - More thorough")

    reset_choice = input("Enter choice (1 or 2, default: 1): ").strip()
    use_full_db_drop = reset_choice == "2"

    # Get migration name
    migration_name = input("\n📝 Enter name for the new migration (default: 'initial_schema'): ").strip()
    if not migration_name:
        migration_name = "initial_schema"

    try:
        # Step 1: Remove existing migration files
        remove_migration_files()

        # Step 2: Reset database using chosen method
        if use_full_db_drop:
            result = drop_and_recreate_database()
            if result == "fallback_to_schema":
                # Fall back to schema recreation if database creation failed
                drop_all_tables()
                reset_alembic_version()
            # No need to reset alembic_version table since entire DB was recreated (if successful)
        else:
            drop_all_tables()
            # Step 3: Reset alembic version table (safe even if just dropped)
            reset_alembic_version()

        # Step 4: Create fresh migration
        new_migration = create_fresh_migration(migration_name)

        # Step 5: Ask if user wants to apply migration
        if confirm_action("Apply the new migration now?"):
            apply_migration()
            verify_migration_state()
        else:
            print("⏳ Migration created but not applied. Run 'alembic upgrade head' when ready.")

        print("\n🎉 Migration squash completed successfully!")
        print(f"   📄 New migration: {new_migration}")
        print("   🔧 You can now commit this clean migration history")

    except KeyboardInterrupt:
        print("\n❌ Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
