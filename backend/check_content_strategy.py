#!/usr/bin/env python3
"""
Check Content Strategy Status

This script shows the current status of bite-sized content generation
and explains what's been updated.
"""

import json
import sqlite3
from pathlib import Path

def find_storage_path():
    """Find the correct storage path"""
    possible_paths = [
        Path("src/.learning_data"),
        Path("../src/.learning_data"),
        Path(".learning_data"),
        Path("../.learning_data"),
    ]

    for path in possible_paths:
        if path.exists() and (path / "learning_paths.json").exists():
            return path
    return None

def find_db_path():
    """Find the correct database path"""
    possible_paths = [
        Path("bite_sized_topics.db"),
        Path("../bite_sized_topics.db"),
        Path("src/bite_sized_topics.db"),
        Path("../src/bite_sized_topics.db"),
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)
    return None

def main():
    """Check the current status"""
    print("🔍 Bite-Sized Content Strategy Status")
    print("=" * 50)

    storage_path = find_storage_path()
    db_path = find_db_path()

    if not storage_path:
        print("❌ No learning paths found")
        return

    if not db_path:
        print("❌ No bite-sized content database found")
        return

    # Load learning paths
    with open(storage_path / "learning_paths.json") as f:
        paths = json.load(f)

    # Check database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM topics")
    topic_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM components")
    component_count = cursor.fetchone()[0]
    conn.close()

    print(f"📚 Learning Paths: {len(paths)}")
    print(f"🎯 Bite-sized Topics: {topic_count}")
    print(f"🔧 Components: {component_count}")

    # Analyze paths
    complete_paths = 0
    partial_paths = 0
    no_content_paths = 0

    for path_id, path_data in paths.items():
        topics_with_content = sum(1 for topic in path_data.get("topics", []) if topic.get("has_bite_sized_content", False))
        total_topics = len(path_data.get("topics", []))

        if topics_with_content == 0:
            no_content_paths += 1
        elif topics_with_content >= min(5, total_topics):
            complete_paths += 1
        else:
            partial_paths += 1

    print(f"\n📊 Status Breakdown:")
    print(f"✅ Complete (5+ topics): {complete_paths}")
    print(f"🔄 Partial (1-4 topics): {partial_paths}")
    print(f"❌ No content: {no_content_paths}")

    print(f"\n🎉 UPDATES COMPLETED:")
    print(f"✅ Strategy changed from CORE_ONLY to COMPLETE")
    print(f"✅ New learning paths will generate 6 component types:")
    print(f"   - Didactic snippet (core content)")
    print(f"   - Glossary (concept definitions)")
    print(f"   - Socratic dialogues (interactive conversations)")
    print(f"   - Short answer questions (open-ended)")
    print(f"   - Multiple choice questions (assessments)")
    print(f"   - Post-topic quiz (comprehensive)")

    print(f"\n💡 NEXT STEPS:")
    print(f"1. Create a new learning path to test the enhanced content")
    print(f"2. Use ./inspect topics-for-path <path_id> to see topics")
    print(f"3. Use ./inspect topic <topic_uuid> to see rich content")
    print(f"4. Enhanced content will take longer to generate (6 components vs 2)")

if __name__ == "__main__":
    main()