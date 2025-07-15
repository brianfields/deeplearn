#!/usr/bin/env python3
"""
SQLite Migration Script for Bite-Sized Topics Component Schema

This script migrates the SQLite database schema for bite-sized topics components:
1. Adds a 'title' field to each component
2. Consolidates 'metadata' field into the 'content' field
3. Updates the table schema to match the new structure

Usage:
    python migrate_sqlite_component_schema.py [db_path]
"""

import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import uuid
from datetime import datetime

def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"

    # Copy the database file
    with open(db_path, 'rb') as src:
        with open(backup_path, 'wb') as dst:
            dst.write(src.read())

    print(f"Database backed up to: {backup_path}")
    return backup_path

def migrate_components_table(db_path: str):
    """Migrate the components table to new schema"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Check if migration is needed
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(components)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'title' in columns:
            print("Migration already completed - title column exists")
            return

        print("Starting migration...")

        # Create new components table with updated schema
        cursor.execute("""
            CREATE TABLE components_new (
                id TEXT PRIMARY KEY,
                topic_id TEXT NOT NULL,
                component_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE
            )
        """)

        # Migrate data from old table to new table
        cursor.execute("SELECT * FROM components")
        rows = cursor.fetchall()

        migrated_count = 0
        for row in rows:
            # Parse existing content and metadata
            content = json.loads(row['content']) if row['content'] else {}
            metadata = json.loads(row['metadata']) if row['metadata'] else {}

            # Generate title based on component type and content
            title = generate_title(row['component_type'], content, metadata)

            # Consolidate metadata into content
            consolidated_content = {**content, **metadata}

            # Insert into new table
            cursor.execute("""
                INSERT INTO components_new
                (id, topic_id, component_type, title, content, created_at, updated_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['id'],
                row['topic_id'],
                row['component_type'],
                title,
                json.dumps(consolidated_content),
                row['created_at'],
                row['updated_at'],
                row['version']
            ))
            migrated_count += 1

        # Drop old table and rename new table
        cursor.execute("DROP TABLE components")
        cursor.execute("ALTER TABLE components_new RENAME TO components")

        # Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_topic_id ON components (topic_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_type ON components (component_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_topic_type ON components (topic_id, component_type)")

        conn.commit()
        print(f"Migration completed successfully! Migrated {migrated_count} components")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

def generate_title(component_type: str, content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """Generate a title for a component based on its type and content"""
    if component_type == 'didactic_snippet':
        return content.get('title', 'Didactic Snippet')
    elif component_type == 'glossary':
        concept = content.get('concept', metadata.get('concept', 'Term'))
        return f"Glossary: {concept}"
    elif component_type == 'socratic_dialogue':
        return content.get('title', 'Socratic Dialogue')
    elif component_type == 'short_answer_question':
        return content.get('title', 'Short Answer Question')
    elif component_type == 'multiple_choice_question':
        return content.get('title', 'Multiple Choice Question')
    elif component_type == 'post_topic_quiz':
        return content.get('title', 'Post-Topic Quiz Item')
    else:
        return 'Component'

def main():
    """Main migration function"""
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "bite_sized_topics.db"

    if not Path(db_path).exists():
        print(f"Database file not found: {db_path}")
        sys.exit(1)

    print(f"Migrating database: {db_path}")

    # Create backup
    backup_path = backup_database(db_path)

    try:
        # Perform migration
        migrate_components_table(db_path)
        print("Migration completed successfully!")
        print(f"Backup available at: {backup_path}")

    except Exception as e:
        print(f"Migration failed: {e}")
        print(f"Database backup is available at: {backup_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()