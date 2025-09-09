#!/usr/bin/env python3
"""
Debug script to isolate infrastructure initialization issues.
"""

import os
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


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


def main():
    """Debug infrastructure initialization."""
    print("🔍 Debugging infrastructure initialization...")

    # Load environment
    backend_dir = Path(__file__).parent
    env_files = [backend_dir / ".env.local", backend_dir / ".env.test", backend_dir / ".env", backend_dir.parent / ".env"]

    for env_file in env_files:
        load_env_file(env_file)

    # Check environment variables
    print(f"DATABASE_URL: {'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}")
    print(f"OPENAI_API_KEY: {'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")

    if os.environ.get("DATABASE_URL"):
        db_url = os.environ["DATABASE_URL"]
        # Mask password for security
        if "@" in db_url:
            parts = db_url.split("@")
            if "://" in parts[0]:
                protocol_user = parts[0].split("://")
                if ":" in protocol_user[1]:
                    user_pass = protocol_user[1].split(":")
                    masked_url = f"{protocol_user[0]}://{user_pass[0]}:***@{parts[1]}"
                    print(f"DATABASE_URL: {masked_url}")
                else:
                    print(f"DATABASE_URL: {db_url}")
            else:
                print(f"DATABASE_URL: {db_url}")
        else:
            print(f"DATABASE_URL: {db_url}")

    # Test infrastructure initialization step by step
    try:
        print("\n🏗️ Testing infrastructure initialization...")

        print("1. Importing infrastructure provider...")
        from modules.infrastructure.public import infrastructure_provider

        print("✅ Import successful")

        print("2. Creating infrastructure provider...")
        infra = infrastructure_provider()
        print("✅ Provider created")

        print("3. Calling initialize()...")
        infra.initialize()
        print("✅ Initialize completed")

        print("4. Validating environment...")
        status = infra.validate_environment()
        if status.is_valid:
            print("✅ Environment validation passed")
        else:
            print("❌ Environment validation failed:")
            for error in status.errors:
                print(f"  - {error}")

        print("5. Testing database session...")
        db_session = infra.get_database_session()
        print(f"✅ Database session created: {db_session.connection_id}")

        print("6. Closing database session...")
        infra.close_database_session(db_session)
        print("✅ Database session closed")

        print("7. Shutting down infrastructure...")
        infra.shutdown()
        print("✅ Infrastructure shutdown complete")

        print("\n🎉 All infrastructure tests passed!")

    except Exception as e:
        print(f"\n❌ Infrastructure test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
