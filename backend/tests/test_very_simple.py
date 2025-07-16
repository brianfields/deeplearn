#!/usr/bin/env python3
"""
Very simple tests for core functionality.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_imports():
    """Test that we can import the basic modules."""
    print("Testing basic imports...")

    try:
        # Test core data structures
        from data_structures import BiteSizedTopic, BiteSizedComponent
        print("✅ Data structures imported successfully")

        # Test component types
        from modules.lesson_planning.bite_sized_topics.storage import ComponentType
        print("✅ ComponentType imported successfully")

        # Test service
        from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService
        print("✅ BiteSizedTopicService imported successfully")

        # Test API
        from api.server import app
        print("✅ FastAPI app imported successfully")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_component_types():
    """Test that ComponentType enum works correctly."""
    print("Testing ComponentType enum...")

    try:
        from modules.lesson_planning.bite_sized_topics.storage import ComponentType

        # Test that we can access enum values
        assert ComponentType.DIDACTIC_SNIPPET.value == "didactic_snippet"
        assert ComponentType.GLOSSARY.value == "glossary"
        assert ComponentType.MULTIPLE_CHOICE_QUESTION.value == "multiple_choice_question"

        print("✅ ComponentType enum working correctly")
        return True

    except Exception as e:
        print(f"❌ ComponentType test failed: {e}")
        return False

def test_service_json_parsing():
    """Test JSON parsing methods directly without service initialization."""
    print("Testing JSON parsing methods...")

    try:
        # Import the service class but don't instantiate it
        from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService

        # Create a dummy instance just to access the parsing method
        # We'll bypass the __init__ by setting the attributes directly
        service = object.__new__(BiteSizedTopicService)

        # Test didactic snippet parsing
        json_content = '''```json
        {
            "title": "Test Title",
            "snippet": "Test snippet content",
            "type": "didactic_snippet",
            "difficulty": 2
        }
        ```'''

        result = service._parse_didactic_snippet(json_content)
        assert result["title"] == "Test Title"
        assert result["snippet"] == "Test snippet content"
        assert result["type"] == "didactic_snippet"
        assert result["difficulty"] == 2

        print("✅ JSON parsing working correctly")
        return True

    except Exception as e:
        print(f"❌ JSON parsing test failed: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint manually without async."""
    print("Testing health endpoint...")

    try:
        from api.server import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert data["status"] == "healthy"

        print("✅ Health endpoint working correctly")
        return True

    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_database_structures():
    """Test that database table definitions work."""
    print("Testing database structures...")

    try:
        from data_structures import BiteSizedTopic, BiteSizedComponent

        # Test that we can access table metadata
        assert BiteSizedTopic.__tablename__ == "bite_sized_topics"
        assert BiteSizedComponent.__tablename__ == "bite_sized_components"

        # Test that required columns exist
        topic_columns = [col.name for col in BiteSizedTopic.__table__.columns]
        assert "id" in topic_columns
        assert "title" in topic_columns
        assert "core_concept" in topic_columns

        component_columns = [col.name for col in BiteSizedComponent.__table__.columns]
        assert "id" in component_columns
        assert "topic_id" in component_columns
        assert "component_type" in component_columns

        print("✅ Database structures working correctly")
        return True

    except Exception as e:
        print(f"❌ Database structures test failed: {e}")
        return False

def run_all_tests():
    """Run all simple tests."""
    print("🚀 Running very simple backend tests...")
    print("=" * 60)

    tests = [
        test_basic_imports,
        test_component_types,
        test_service_json_parsing,
        test_health_endpoint,
        test_database_structures
    ]

    passed = 0
    failed = 0

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
            failed += 1

    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed}/{passed + failed}")

    if failed == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n💥 {failed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)