#!/usr/bin/env python3
"""
Migration script to move data from SQLite to PostgreSQL.

This script migrates:
1. Learning paths from JSON files to PostgreSQL
2. Bite-sized topics from SQLite to PostgreSQL
3. Components from SQLite to PostgreSQL

Usage:
    python migrate_to_postgres.py [--dry-run] [--backup]
"""

import os
import sys
import json
import sqlite3
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database_service import init_database_service, DatabaseService
from data_structures import SimpleLearningPath, BiteSizedTopic, BiteSizedComponent
from config.config import config_manager


def find_sqlite_db() -> Optional[Path]:
    """Find the SQLite database file"""
    possible_paths = [
        Path("bite_sized_topics.db"),
        Path("../bite_sized_topics.db"),
        Path("src/bite_sized_topics.db"),
        Path("../src/bite_sized_topics.db"),
    ]

    for path in possible_paths:
        if path.exists():
            return path
    return None


def find_learning_data_dir() -> Optional[Path]:
    """Find the learning data directory"""
    possible_paths = [
        Path(".learning_data"),
        Path("../.learning_data"),
        Path("src/.learning_data"),
        Path("../src/.learning_data"),
    ]

    for path in possible_paths:
        if path.exists():
            return path
    return None


def backup_existing_data(backup_dir: Path):
    """Create backup of existing data"""
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Backup SQLite database
    sqlite_db = find_sqlite_db()
    if sqlite_db and sqlite_db.exists():
        backup_sqlite = backup_dir / f"bite_sized_topics_{timestamp}.db"
        shutil.copy2(sqlite_db, backup_sqlite)
        print(f"✅ Backed up SQLite database to {backup_sqlite}")

    # Backup learning data directory
    learning_data = find_learning_data_dir()
    if learning_data and learning_data.exists():
        backup_learning = backup_dir / f"learning_data_{timestamp}"
        shutil.copytree(learning_data, backup_learning)
        print(f"✅ Backed up learning data to {backup_learning}")


def migrate_learning_paths(db_service: DatabaseService, dry_run: bool = False) -> int:
    """Migrate learning paths from JSON files to PostgreSQL"""
    learning_data_dir = find_learning_data_dir()
    if not learning_data_dir:
        print("❌ No learning data directory found")
        return 0

    learning_paths_file = learning_data_dir / "learning_paths.json"
    if not learning_paths_file.exists():
        print("❌ No learning_paths.json file found")
        return 0

    print(f"📖 Reading learning paths from {learning_paths_file}")

    try:
        with open(learning_paths_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for path_id, path_data in data.items():
            learning_path = SimpleLearningPath(
                id=path_data['id'],
                topic_name=path_data['topic_name'],
                description=path_data.get('description', ''),
                topics=path_data.get('topics', []),
                current_topic_index=path_data.get('current_topic_index', 0),
                estimated_total_hours=path_data.get('estimated_total_hours', 0.0),
                created_at=datetime.fromisoformat(path_data['created_at']) if 'created_at' in path_data else datetime.utcnow(),
                updated_at=datetime.fromisoformat(path_data['updated_at']) if 'updated_at' in path_data else datetime.utcnow()
            )

            if not dry_run:
                db_service.save_learning_path(learning_path)

            print(f"  ✅ Migrated learning path: {learning_path.topic_name}")
            count += 1

        return count

    except Exception as e:
        print(f"❌ Error migrating learning paths: {e}")
        return 0


def migrate_bite_sized_topics(db_service: DatabaseService, dry_run: bool = False) -> tuple[int, int]:
    """Migrate bite-sized topics from SQLite to PostgreSQL"""
    sqlite_db = find_sqlite_db()
    if not sqlite_db:
        print("❌ No SQLite database found")
        return 0, 0

    print(f"📖 Reading bite-sized topics from {sqlite_db}")

    try:
        conn = sqlite3.connect(str(sqlite_db))
        conn.row_factory = sqlite3.Row

        # Get all topics
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topics ORDER BY created_at")
        topics = cursor.fetchall()

        topic_count = 0
        component_count = 0

        for topic_row in topics:
            if not dry_run:
                # Create BiteSizedTopic
                topic = BiteSizedTopic(
                    id=topic_row['id'],
                    title=topic_row['title'],
                    core_concept=topic_row['core_concept'],
                    user_level=topic_row['user_level'],
                    learning_objectives=json.loads(topic_row['learning_objectives']),
                    key_concepts=json.loads(topic_row['key_concepts']),
                    key_aspects=json.loads(topic_row['key_aspects']),
                    target_insights=json.loads(topic_row['target_insights']),
                    common_misconceptions=json.loads(topic_row['common_misconceptions']),
                    previous_topics=json.loads(topic_row['previous_topics']),
                    creation_strategy=topic_row['creation_strategy'],
                    creation_metadata=json.loads(topic_row['creation_metadata']),
                    created_at=datetime.fromisoformat(topic_row['created_at']),
                    updated_at=datetime.fromisoformat(topic_row['updated_at']),
                    version=topic_row['version']
                )

                # Save topic using database service session
                with db_service.get_session() as session:
                    session.add(topic)
                    session.commit()

            print(f"  ✅ Migrated topic: {topic_row['title']}")
            topic_count += 1

            # Get components for this topic
            cursor.execute("SELECT * FROM components WHERE topic_id = ?", (topic_row['id'],))
            components = cursor.fetchall()

            for component_row in components:
                if not dry_run:
                    component = BiteSizedComponent(
                        id=component_row['id'],
                        topic_id=component_row['topic_id'],
                        component_type=component_row['component_type'],
                        content=component_row['content'],
                        metadata=json.loads(component_row['metadata']),
                        created_at=datetime.fromisoformat(component_row['created_at']),
                        updated_at=datetime.fromisoformat(component_row['updated_at']),
                        version=component_row['version']
                    )

                    # Save component using database service session
                    with db_service.get_session() as session:
                        session.add(component)
                        session.commit()

                component_count += 1

        conn.close()
        return topic_count, component_count

    except Exception as e:
        print(f"❌ Error migrating bite-sized topics: {e}")
        return 0, 0


def verify_migration(db_service: DatabaseService):
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")

    # Check learning paths
    learning_paths = db_service.get_all_learning_paths()
    print(f"✅ Found {len(learning_paths)} learning paths in PostgreSQL")

    # Check bite-sized topics
    with db_service.get_session() as session:
        from sqlalchemy import select, func

        topic_count = session.execute(select(func.count(BiteSizedTopic.id))).scalar()
        component_count = session.execute(select(func.count(BiteSizedComponent.id))).scalar()

        print(f"✅ Found {topic_count} bite-sized topics in PostgreSQL")
        print(f"✅ Found {component_count} components in PostgreSQL")


def main():
    parser = argparse.ArgumentParser(description="Migrate from SQLite to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without actually migrating")
    parser.add_argument("--backup", action="store_true", help="Create backup before migration")
    parser.add_argument("--backup-dir", default="./migration_backup", help="Directory for backups")

    args = parser.parse_args()

    print("🚀 Starting migration from SQLite to PostgreSQL")

    # Create backup if requested
    if args.backup:
        print(f"\n📦 Creating backup in {args.backup_dir}")
        backup_existing_data(Path(args.backup_dir))

    # Initialize database service
    try:
        print("\n🔧 Initializing PostgreSQL connection...")
        db_service = init_database_service()
        print("✅ Connected to PostgreSQL successfully")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("Please ensure PostgreSQL is running and DATABASE_URL is set correctly")
        return 1

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No data will be modified")

    # Migrate learning paths
    print("\n📚 Migrating learning paths...")
    path_count = migrate_learning_paths(db_service, args.dry_run)
    print(f"✅ Migrated {path_count} learning paths")

    # Migrate bite-sized topics
    print("\n🎓 Migrating bite-sized topics...")
    topic_count, component_count = migrate_bite_sized_topics(db_service, args.dry_run)
    print(f"✅ Migrated {topic_count} topics and {component_count} components")

    if not args.dry_run:
        # Verify migration
        verify_migration(db_service)

        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update your CLI scripts to use PostgreSQL")
        print("2. Update the server to use DatabaseService")
        print("3. Test the application with the new database")
        print("4. Archive or remove old SQLite files")
    else:
        print("\n📋 Dry run completed - use without --dry-run to perform actual migration")

    return 0


if __name__ == "__main__":
    sys.exit(main())