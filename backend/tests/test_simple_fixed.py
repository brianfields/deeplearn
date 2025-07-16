#!/usr/bin/env python3
"""
Simple focused tests for the simplified backend system.

This test file focuses on basic functionality without complex mocking.
"""

import pytest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that we can import all the main modules."""
    try:
        # Test core imports
        from data_structures import BiteSizedTopic, BiteSizedComponent
        from modules.lesson_planning.bite_sized_topics.storage import ComponentType
        from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService

        # Test API imports
        from api.server import app
        from api import routes

        print("✅ All imports successful")
        assert True

    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_data_structures():
    """Test that our data structures work correctly."""
    from modules.lesson_planning.bite_sized_topics.storage import ComponentType

    # Test enum values
    assert ComponentType.DIDACTIC_SNIPPET.value == "didactic_snippet"
    assert ComponentType.GLOSSARY.value == "glossary"
    assert ComponentType.MULTIPLE_CHOICE_QUESTION.value == "multiple_choice_question"

    print("✅ Data structures work correctly")

def test_service_initialization():
    """Test that we can initialize the BiteSizedTopicService."""
    from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService
    from unittest.mock import Mock

    # Create mock dependencies
    mock_config = Mock()
    mock_llm_client = Mock()

    # Should not raise an exception
    service = BiteSizedTopicService(mock_config, mock_llm_client)
    assert service is not None
    assert hasattr(service, 'prompts')

    print("✅ Service initialization successful")

def test_service_content_validation():
    """Test the content validation functionality."""
    import asyncio
    from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService
    from unittest.mock import Mock

    # Create service
    mock_config = Mock()
    mock_llm_client = Mock()
    service = BiteSizedTopicService(mock_config, mock_llm_client)

    async def run_validation_test():
        # Test with good content
        good_content = """
        # Test Lesson

        This is a comprehensive lesson with:
        - **Key concepts** explained clearly
        - Interactive elements like questions?
        - Proper formatting and structure

        Think about how this applies to real-world scenarios.
        """

        result = await service.validate_content(good_content)
        assert result["valid"] is True
        assert len(result["issues"]) == 0

        # Test with bad content (too short)
        bad_content = "Short"
        result = await service.validate_content(bad_content)
        assert result["valid"] is False
        assert "Content too short" in result["issues"]

        print("✅ Content validation working correctly")

    # Run the async test
    asyncio.run(run_validation_test())

def test_json_parsing():
    """Test the JSON parsing functionality."""
    from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService
    from unittest.mock import Mock

    # Create service
    mock_config = Mock()
    mock_llm_client = Mock()
    service = BiteSizedTopicService(mock_config, mock_llm_client)

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

    # Test fallback parsing
    non_json_content = "Title: Fallback Title\nSnippet: Fallback content"
    result = service._parse_didactic_snippet(non_json_content)
    assert result["title"] == "Fallback Title"
    assert result["snippet"] == "Fallback content"

    print("✅ JSON parsing working correctly")

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health endpoint using httpx."""
    from httpx import AsyncClient
    from api.server import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert data["status"] == "healthy"

        print("✅ Health endpoint working correctly")

def test_prompt_registry():
    """Test that all expected prompts are registered."""
    from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService
    from unittest.mock import Mock

    # Create service
    mock_config = Mock()
    mock_llm_client = Mock()
    service = BiteSizedTopicService(mock_config, mock_llm_client)

    # Check that all expected prompts are present
    expected_prompts = [
        'lesson_content',
        'didactic_snippet',
        'glossary',
        'socratic_dialogue',
        'short_answer_questions',
        'multiple_choice_questions',
        'post_topic_quiz'
    ]

    for prompt_name in expected_prompts:
        assert prompt_name in service.prompts, f"Missing prompt: {prompt_name}"
        assert service.prompts[prompt_name] is not None

    print("✅ All expected prompts are registered")

if __name__ == "__main__":
    # Run the tests manually for debugging
    print("Running simple backend tests...")
    print("=" * 50)

    try:
        test_imports()
        test_data_structures()
        test_service_initialization()
        test_service_content_validation()
        test_json_parsing()
        test_prompt_registry()

        # Run async test manually
        import asyncio
        asyncio.run(test_health_endpoint())

        print("\n🎉 All simple tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()