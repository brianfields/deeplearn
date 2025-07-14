#!/usr/bin/env python3
"""
Create Simple Topic

Ultra-simple script to test LLM generation and PostgreSQL storage.
"""

import argparse
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Test minimal imports
    from config.config import get_llm_config
    from data_structures import BiteSizedTopic, BiteSizedComponent
    from database_service import get_database_service
    import json
    import openai
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def create_simple_content(topic_title: str, user_level: str = "beginner"):
    """Create simple content using basic OpenAI calls"""
    print(f"🎯 Creating simple content for: {topic_title} (level: {user_level})")

    try:
        # Get OpenAI config
        llm_config = get_llm_config()
        openai.api_key = llm_config.api_key
        openai.api_type = "openai"  # Set API type explicitly

        # Create simple didactic snippet using direct OpenAI call
        print("📝 Generating didactic snippet...")
        snippet_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an educational content creator. Create a clear, concise explanation suitable for {user_level} learners."},
                {"role": "user", "content": f"Write a 200-word educational snippet explaining '{topic_title}'. Include:\n1. A clear definition\n2. Key concepts\n3. Why it's important\n\nFormat as JSON with 'title' and 'content' fields."}
            ],
            temperature=0.7,
            max_tokens=500
        )

        snippet_content = snippet_response.choices[0].message.content
        try:
            snippet_data = json.loads(snippet_content)
        except:
            snippet_data = {"title": f"Introduction to {topic_title}", "content": snippet_content}

        # Create simple glossary
        print("📚 Generating glossary...")
        glossary_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are creating a glossary for {user_level} learners."},
                {"role": "user", "content": f"Create a glossary of 3-5 key terms related to '{topic_title}'. Format as JSON array with objects containing 'term' and 'definition' fields."}
            ],
            temperature=0.7,
            max_tokens=400
        )

        glossary_content = glossary_response.choices[0].message.content
        try:
            glossary_data = json.loads(glossary_content)
        except:
            glossary_data = [{"term": topic_title, "definition": "The main concept being studied"}]

        # Store in PostgreSQL
        print("💾 Storing in PostgreSQL...")
        db_service = get_database_service()

        topic_id = str(uuid.uuid4())

        with db_service.get_session() as session:
            # Create main topic
            topic_record = BiteSizedTopic(
                id=topic_id,
                title=topic_title,
                core_concept=topic_title,
                user_level=user_level,
                learning_objectives=[f"Understand {topic_title}"],
                key_concepts=[topic_title],
                key_aspects=[topic_title],
                target_insights=[f"Key insights about {topic_title}"],
                common_misconceptions=[],
                previous_topics=[],
                creation_strategy="simple",
                creation_metadata={"created_by": "create_simple_topic.py"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(topic_record)

            # Create didactic snippet component
            snippet_component = BiteSizedComponent(
                id=str(uuid.uuid4()),
                topic_id=topic_id,
                component_type="didactic_snippet",
                content=json.dumps(snippet_data),
                component_metadata={"title": snippet_data.get("title", topic_title)},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(snippet_component)

            # Create glossary component
            glossary_component = BiteSizedComponent(
                id=str(uuid.uuid4()),
                topic_id=topic_id,
                component_type="glossary",
                content=json.dumps(glossary_data),
                component_metadata={"term_count": len(glossary_data)},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(glossary_component)

            session.commit()

        print(f"✅ Success! Topic ID: {topic_id}")
        print(f"   • Snippet: {snippet_data.get('title', 'Created')}")
        print(f"   • Glossary: {len(glossary_data)} terms")
        print()
        print("🔍 Check with: python quick_inspect.py --all")

        return topic_id

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Topic to create")
    parser.add_argument("--level", default="beginner", choices=["beginner", "intermediate", "advanced"])
    args = parser.parse_args()

    result = create_simple_content(args.topic, args.level)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()