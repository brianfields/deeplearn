#!/usr/bin/env python3
"""
Database Reset Script

This script provides an easy way to completely wipe and recreate
both PostgreSQL and SQLite databases for the deeplearn project.
"""

from pathlib import Path
import subprocess


def reset_postgresql():
    """Reset PostgreSQL database using Alembic"""
    print("🗑️  Resetting PostgreSQL database...")

    try:
        # Test database connection by trying to run alembic current
        print("   Testing database connection...")
        result = subprocess.run(["alembic", "current"], capture_output=True, text=True, check=False)

        if result.returncode != 0:
            print("⚠️  PostgreSQL connection failed - database may not be configured")
            print("   Make sure DATABASE_URL or DATABASE_PASSWORD is set")
            print(f"   Error: {result.stderr}")
            return False

        # Downgrade to base (removes all tables)
        print("   Downgrading database...")
        result = subprocess.run(["alembic", "downgrade", "base"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"   Error downgrading: {result.stderr}")
            return False

        # Upgrade to head (recreates all tables)
        print("   Upgrading database...")
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"   Error upgrading: {result.stderr}")
            return False

        print("✅ PostgreSQL database reset successfully")
        return True

    except Exception as e:
        print(f"❌ Error resetting PostgreSQL: {e}")
        return False


def reset_sqlite():
    """Reset SQLite databases"""
    print("🗑️  Resetting SQLite databases...")

    # Common SQLite database file patterns
    sqlite_patterns = ["*.db", "bite_sized_topics.db", "test_*.db", "example_*.db"]

    removed_files = []

    # Search in current directory and subdirectories
    for pattern in sqlite_patterns:
        for db_file in Path().glob(pattern):
            if db_file.is_file():
                try:
                    db_file.unlink()
                    removed_files.append(str(db_file))
                    print(f"   Removed: {db_file}")
                except Exception as e:
                    print(f"   Error removing {db_file}: {e}")

        # Also check subdirectories
        for db_file in Path().glob(f"**/{pattern}"):
            if db_file.is_file():
                try:
                    db_file.unlink()
                    removed_files.append(str(db_file))
                    print(f"   Removed: {db_file}")
                except Exception as e:
                    print(f"   Error removing {db_file}: {e}")

    if removed_files:
        print(f"✅ Removed {len(removed_files)} SQLite database files")
    else:
        print("✅ No SQLite database files to remove")

    return True


def main():
    """Main reset function"""
    print("🚀 Database Reset Script")
    print("=" * 40)

    # Check if user wants to proceed
    response = input("⚠️  This will PERMANENTLY delete all data. Continue? (y/N): ")
    if response.lower() not in ["y", "yes"]:
        print("❌ Reset cancelled")
        return

    print()

    # Reset databases
    postgresql_success = reset_postgresql()
    sqlite_success = reset_sqlite()

    print()
    print("📋 Reset Summary:")
    print(f"   PostgreSQL: {'✅ Success' if postgresql_success else '❌ Failed'}")
    print(f"   SQLite: {'✅ Success' if sqlite_success else '❌ Failed'}")

    if postgresql_success and sqlite_success:
        print("\n🎉 Database reset completed successfully!")
        print("\nNext steps:")
        print("   1. Run your scripts to create new test data")
        print("   2. Or start with a clean database")
        print("\nTest commands:")
        print('   python create_single_topic.py "Test topic"')
        print("   python inspect_bite_sized_content.py")
    else:
        print("\n⚠️  Some operations failed. Check the errors above.")


if __name__ == "__main__":
    main()
