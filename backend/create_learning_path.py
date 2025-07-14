#!/usr/bin/env python3
"""
Create Learning Path CLI with Comprehensive Reporting

A command-line tool to create learning paths with bite-sized content
and generate exhaustive reports of everything created.

Usage:
    python create_learning_path.py "Topic Name" [options]

Examples:
    python create_learning_path.py "Introduction to Machine Learning"
    python create_learning_path.py "Python for Data Science" --level advanced --report
    python create_learning_path.py "Web Development Basics" --refinements "Focus on practical projects" --detailed
"""

import argparse
import json
import requests
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

def find_storage_path():
    """Find the correct storage path"""
    possible_paths = [
        Path("backend/src/.learning_data"),
        Path("src/.learning_data"),
        Path("backend/.learning_data"),
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
        Path("backend/bite_sized_topics.db"),
        Path("backend/src/bite_sized_topics.db"),
        Path("bite_sized_topics.db"),
        Path("src/bite_sized_topics.db"),
        Path("../bite_sized_topics.db"),
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)
    return None

def get_detailed_content_info(path_id: str) -> Dict[str, Any]:
    """Get detailed information about the bite-sized content"""
    storage_path = find_storage_path()
    db_path = find_db_path()

    if not storage_path or not db_path:
        return {}

    try:
        # Load learning path
        with open(storage_path / "learning_paths.json") as f:
            paths = json.load(f)

        if path_id not in paths:
            return {}

        path_data = paths[path_id]

        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        detailed_info = {
            "path_info": path_data,
            "topics_detail": [],
            "content_statistics": {
                "total_topics": len(path_data.get("topics", [])),
                "topics_with_content": 0,
                "total_components": 0,
                "component_breakdown": {},
                "total_items": 0
            }
        }

        for topic in path_data.get("topics", []):
            topic_detail = {
                "topic_info": topic,
                "bite_sized_content": None,
                "components": []
            }

            if topic.get("has_bite_sized_content") and topic.get("bite_sized_topic_id"):
                detailed_info["content_statistics"]["topics_with_content"] += 1
                bite_sized_id = topic["bite_sized_topic_id"]

                # Get topic details
                cursor.execute("SELECT * FROM topics WHERE id = ?", (bite_sized_id,))
                topic_row = cursor.fetchone()

                if topic_row:
                    topic_detail["bite_sized_content"] = {
                        "id": topic_row["id"],
                        "title": topic_row["title"],
                        "core_concept": topic_row["core_concept"],
                        "user_level": topic_row["user_level"],
                        "creation_strategy": topic_row["creation_strategy"],
                        "created_at": topic_row["created_at"]
                    }

                    # Get components
                    cursor.execute("""
                        SELECT component_type, created_at, content
                        FROM components
                        WHERE topic_id = ?
                        ORDER BY component_type, created_at
                    """, (bite_sized_id,))

                    components = cursor.fetchall()
                    component_stats = {}

                    for comp in components:
                        comp_type = comp["component_type"]
                        content = json.loads(comp["content"])

                        # Count items in this component
                        item_count = 1  # Default for single items like didactic_snippet
                        if isinstance(content, dict):
                            item_count = len(content)
                        elif isinstance(content, list):
                            item_count = len(content)

                        component_detail = {
                            "type": comp_type,
                            "created_at": comp["created_at"],
                            "item_count": item_count,
                            "content_summary": {}
                        }

                        # Add content summary based on type
                        if comp_type == "didactic_snippet":
                            component_detail["content_summary"] = {
                                "title": content.get("title", "N/A"),
                                "snippet_length": len(content.get("snippet", "")),
                                "snippet_preview": content.get("snippet", "")[:100] + "..." if len(content.get("snippet", "")) > 100 else content.get("snippet", "")
                            }
                        elif comp_type == "glossary":
                            component_detail["content_summary"] = {
                                "terms_count": len(content),
                                "terms": list(content.keys())
                            }
                        elif comp_type in ["short_answer_question", "multiple_choice_question"]:
                            component_detail["content_summary"] = {
                                "questions_count": len(content),
                                "sample_questions": [q.get("question", q.get("stem", "")) for q in content[:3]] if isinstance(content, list) else []
                            }
                        elif comp_type == "socratic_dialogue":
                            component_detail["content_summary"] = {
                                "dialogues_count": len(content),
                                "sample_concepts": [d.get("concept", "") for d in content[:3]] if isinstance(content, list) else []
                            }
                        elif comp_type == "post_topic_quiz":
                            component_detail["content_summary"] = {
                                "quiz_items_count": len(content),
                                "question_types": list(set([q.get("type", "unknown") for q in content])) if isinstance(content, list) else []
                            }

                        topic_detail["components"].append(component_detail)

                        # Update statistics
                        if comp_type not in component_stats:
                            component_stats[comp_type] = 0
                        component_stats[comp_type] += 1

                        detailed_info["content_statistics"]["total_components"] += 1
                        detailed_info["content_statistics"]["total_items"] += item_count

                    # Add component breakdown for this topic
                    topic_detail["component_statistics"] = component_stats

                    # Update global component breakdown
                    for comp_type, count in component_stats.items():
                        if comp_type not in detailed_info["content_statistics"]["component_breakdown"]:
                            detailed_info["content_statistics"]["component_breakdown"][comp_type] = 0
                        detailed_info["content_statistics"]["component_breakdown"][comp_type] += count

            detailed_info["topics_detail"].append(topic_detail)

        conn.close()
        return detailed_info

    except Exception as e:
        print(f"⚠️  Error gathering detailed info: {e}")
        return {}

def print_comprehensive_report(result: dict, detailed_info: dict, show_detailed: bool = False):
    """Print a comprehensive report of the created learning path"""

    print(f"\n{'='*80}")
    print(f"📊 COMPREHENSIVE LEARNING PATH REPORT")
    print(f"{'='*80}")

    # Basic Information
    print(f"\n🎯 BASIC INFORMATION:")
    print(f"📚 Topic: {result['topic_name']}")
    print(f"🆔 Path ID: {result['id']}")
    print(f"📝 Description: {result['description']}")
    print(f"📊 Total Topics: {len(result['topics'])}")
    print(f"⏱️  Estimated Duration: {result.get('estimated_total_hours', 'N/A')} hours")
    print(f"📅 Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Bite-sized Content Overview
    if 'bite_sized_content_info' in result:
        content_info = result['bite_sized_content_info']
        print(f"\n🎯 BITE-SIZED CONTENT OVERVIEW:")
        print(f"✅ Generated Topics: {content_info['total_generated']}")
        print(f"🔧 Strategy Used: {content_info['creation_strategy'].upper()}")
        print(f"👤 User Level: {content_info['user_level']}")

    # Detailed Statistics
    if detailed_info and "content_statistics" in detailed_info:
        stats = detailed_info["content_statistics"]
        print(f"\n📈 CONTENT STATISTICS:")
        print(f"📚 Topics with Bite-sized Content: {stats['topics_with_content']}/{stats['total_topics']}")
        print(f"🔧 Total Components Generated: {stats['total_components']}")
        print(f"📋 Total Content Items: {stats['total_items']}")

        if stats["component_breakdown"]:
            print(f"\n🛠️  COMPONENT BREAKDOWN:")
            for comp_type, count in stats["component_breakdown"].items():
                print(f"   • {comp_type.replace('_', ' ').title()}: {count} components")

    # Topic-by-Topic Report
    print(f"\n📖 TOPIC-BY-TOPIC BREAKDOWN:")
    for i, topic_data in enumerate(result['topics'], 1):
        status = "✅" if topic_data.get('has_bite_sized_content') else "❌"
        print(f"\n{i}. {status} {topic_data['title']}")
        print(f"   📖 {topic_data['description']}")
        print(f"   🎯 Learning Objectives: {len(topic_data.get('learning_objectives', []))}")
        print(f"   ⏱️  Duration: {topic_data.get('estimated_duration', 'N/A')} minutes")
        print(f"   📊 Difficulty: {topic_data.get('difficulty_level', 'N/A')}")

        if topic_data.get('has_bite_sized_content'):
            print(f"   🆔 Bite-sized ID: {topic_data.get('bite_sized_topic_id', 'N/A')}")

            # Find detailed info for this topic
            if detailed_info and "topics_detail" in detailed_info:
                topic_detail = next((t for t in detailed_info["topics_detail"] if t["topic_info"]["id"] == topic_data["id"]), None)
                if topic_detail and "component_statistics" in topic_detail:
                    comp_stats = topic_detail["component_statistics"]
                    print(f"   🔧 Components: {sum(comp_stats.values())} total")
                    for comp_type, count in comp_stats.items():
                        print(f"      • {comp_type.replace('_', ' ').title()}: {count}")

    # Detailed Component Analysis (if requested)
    if show_detailed and detailed_info and "topics_detail" in detailed_info:
        print(f"\n{'='*80}")
        print(f"🔍 DETAILED COMPONENT ANALYSIS")
        print(f"{'='*80}")

        for topic_detail in detailed_info["topics_detail"]:
            if topic_detail.get("bite_sized_content") and topic_detail.get("components"):
                print(f"\n📚 TOPIC: {topic_detail['bite_sized_content']['title']}")
                print(f"🆔 ID: {topic_detail['bite_sized_content']['id']}")
                print(f"🎯 Core Concept: {topic_detail['bite_sized_content']['core_concept']}")
                print(f"👤 User Level: {topic_detail['bite_sized_content']['user_level']}")
                print(f"🔧 Strategy: {topic_detail['bite_sized_content']['creation_strategy']}")
                print(f"📅 Created: {topic_detail['bite_sized_content']['created_at']}")

                print(f"\n   📋 COMPONENTS ({len(topic_detail['components'])}):")

                component_groups = {}
                for comp in topic_detail["components"]:
                    comp_type = comp["type"]
                    if comp_type not in component_groups:
                        component_groups[comp_type] = []
                    component_groups[comp_type].append(comp)

                for comp_type, comps in component_groups.items():
                    print(f"\n   🔧 {comp_type.replace('_', ' ').upper()} ({len(comps)} components):")

                    total_items = sum(comp["item_count"] for comp in comps)
                    print(f"      📊 Total Items: {total_items}")

                    # Show content summaries
                    for i, comp in enumerate(comps, 1):
                        summary = comp["content_summary"]
                        print(f"      {i}. Items: {comp['item_count']}")

                        if comp_type == "didactic_snippet":
                            print(f"         Title: {summary.get('title', 'N/A')}")
                            print(f"         Length: {summary.get('snippet_length', 0)} characters")
                            if summary.get('snippet_preview'):
                                print(f"         Preview: {summary['snippet_preview']}")

                        elif comp_type == "glossary":
                            print(f"         Terms: {summary.get('terms_count', 0)}")
                            if summary.get('terms'):
                                print(f"         Examples: {', '.join(summary['terms'][:3])}")

                        elif comp_type in ["short_answer_question", "multiple_choice_question"]:
                            print(f"         Questions: {summary.get('questions_count', 0)}")
                            if summary.get('sample_questions'):
                                for j, q in enumerate(summary['sample_questions'][:2], 1):
                                    print(f"         Q{j}: {q[:60]}...")

                        elif comp_type == "socratic_dialogue":
                            print(f"         Dialogues: {summary.get('dialogues_count', 0)}")
                            if summary.get('sample_concepts'):
                                print(f"         Concepts: {', '.join(summary['sample_concepts'])}")

                        elif comp_type == "post_topic_quiz":
                            print(f"         Quiz Items: {summary.get('quiz_items_count', 0)}")
                            if summary.get('question_types'):
                                print(f"         Types: {', '.join(summary['question_types'])}")

    # Usage Information
    print(f"\n{'='*80}")
    print(f"🌐 ACCESS INFORMATION")
    print(f"{'='*80}")
    print(f"🌐 Frontend URL: http://localhost:3000/courses/{result['id']}")
    print(f"🔍 Inspect Topics: ./inspect topics-for-path {result['id']}")
    print(f"📊 System Status: ./check-strategy")
    print(f"🛠️  Backend API: http://localhost:8000/api/learning-paths/{result['id']}")

def save_report_to_file(result: dict, detailed_info: dict, filename: Optional[str] = None):
    """Save the comprehensive report to a file"""

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in result['topic_name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')[:30]
        filename = f"learning_path_report_{safe_name}_{timestamp}.json"

    report_data = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "path_id": result['id'],
            "topic_name": result['topic_name']
        },
        "learning_path": result,
        "detailed_content_analysis": detailed_info,
        "summary_statistics": {
            "total_topics": len(result['topics']),
            "topics_with_content": detailed_info.get("content_statistics", {}).get("topics_with_content", 0),
            "total_components": detailed_info.get("content_statistics", {}).get("total_components", 0),
            "total_items": detailed_info.get("content_statistics", {}).get("total_items", 0),
            "component_breakdown": detailed_info.get("content_statistics", {}).get("component_breakdown", {})
        }
    }

    try:
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n💾 REPORT SAVED:")
        print(f"📄 File: {filename}")
        print(f"📊 Size: {Path(filename).stat().st_size} bytes")
        return filename

    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        return None

def create_learning_path(
    topic: str,
    user_level: str = "beginner",
    user_refinements: Optional[List[str]] = None,
    custom_instructions: Optional[str] = None,
    server_url: str = "http://localhost:8000",
    show_detailed: bool = False,
    save_report: bool = False,
    report_filename: Optional[str] = None
) -> dict:
    """
    Create a learning path via the API with comprehensive reporting
    """

    # Prepare the request payload
    payload = {
        "topic": topic,
        "user_level": user_level
    }

    if user_refinements:
        payload["user_refinements"] = user_refinements

    if custom_instructions:
        payload["custom_instructions"] = custom_instructions

    try:
        print(f"🚀 Creating learning path for: {topic}")
        print(f"📊 User level: {user_level}")
        if user_refinements:
            print(f"🎯 Refinements: {', '.join(user_refinements)}")
        if custom_instructions:
            print(f"💡 Instructions: {custom_instructions}")

        print(f"\n⏳ Generating content... (this may take 5-10 minutes for rich content)")

        # Make the API request
        response = requests.post(
            f"{server_url}/api/learning-paths",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=600  # 10 minute timeout for rich content generation
        )

        response.raise_for_status()
        result = response.json()

        print(f"✅ Learning path created successfully!")

        # Get detailed content information
        print(f"🔍 Analyzing generated content...")
        detailed_info = get_detailed_content_info(result['id'])

        # Print comprehensive report
        print_comprehensive_report(result, detailed_info, show_detailed)

        # Save report to file if requested
        if save_report:
            saved_file = save_report_to_file(result, detailed_info, report_filename)
            if saved_file:
                print(f"📄 Full report available in: {saved_file}")

        return result

    except requests.exceptions.Timeout:
        print("⏰ Request timed out. Content generation is still running in background.")
        print("🔍 Check status with: ./inspect all")
        return {}

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is the backend running?")
        print("💡 Start server with: cd backend && python start_server.py")
        return {}

    except requests.exceptions.HTTPError as e:
        print(f"❌ API error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Details: {e.response.text}")
        return {}

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {}

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Create learning paths with comprehensive reporting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Introduction to Machine Learning"
  %(prog)s "Python for Data Science" --level advanced --detailed
  %(prog)s "Web Development" --refinements "Focus on React" --report
  %(prog)s "Data Structures" --level intermediate --detailed --report --filename "ds_report.json"
        """
    )

    parser.add_argument(
        "topic",
        help="The main topic for the learning path"
    )

    parser.add_argument(
        "--level",
        choices=["beginner", "intermediate", "advanced"],
        default="beginner",
        help="User skill level (default: beginner)"
    )

    parser.add_argument(
        "--refinements",
        nargs="*",
        help="Refinement suggestions for the content"
    )

    parser.add_argument(
        "--instructions",
        help="Custom instructions for content generation"
    )

    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="API server URL (default: http://localhost:8000)"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed component analysis in the report"
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="Save comprehensive report to JSON file"
    )

    parser.add_argument(
        "--filename",
        help="Custom filename for the report (only used with --report)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON (in addition to the report)"
    )

    args = parser.parse_args()

    # Create the learning path
    result = create_learning_path(
        topic=args.topic,
        user_level=args.level,
        user_refinements=args.refinements,
        custom_instructions=args.instructions,
        server_url=args.server,
        show_detailed=args.detailed,
        save_report=args.report,
        report_filename=args.filename
    )

    # Output result as JSON if requested
    if args.json and result:
        print(f"\n📋 RAW JSON OUTPUT:")
        print(json.dumps(result, indent=2))

    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())