"""
Example of how to run tests with real LLM APIs.

This file demonstrates the patterns for testing with real LLMs.
It's not run by default to avoid costs and API key requirements.

To run this test:
1. Set your OpenAI API key: export OPENAI_API_KEY="sk-..."
2. Enable real LLM testing: export TEST_WITH_REAL_LLM="true"
3. Run: pytest modules/llm_services/tests/example_real_llm_test.py -v

WARNING: This test will make real API calls and may incur small costs (~$0.001-0.01)
"""

import os

import pytest

from modules.llm_services.domain.entities.prompt import (
    PromptContext,
    UserLevel,
)
from modules.llm_services.module_api import create_llm_service

# Skip this entire file unless explicitly enabled
pytestmark = pytest.mark.skipif(not (os.getenv("TEST_WITH_REAL_LLM", "false").lower() == "true" and os.getenv("OPENAI_API_KEY")), reason="Real LLM testing not enabled. Set TEST_WITH_REAL_LLM=true and OPENAI_API_KEY to run.")


@pytest.fixture
def real_llm_service():
    """Create a real LLM service for testing"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    return create_llm_service(
        api_key=api_key,
        model="gpt-3.5-turbo",  # Use cheaper model
        provider="openai",
        cache_enabled=True,
    )


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.asyncio
async def test_real_simple_generation(real_llm_service):
    """
    Test simple content generation with real LLM.

    This is a minimal test that demonstrates real LLM interaction.
    Expected cost: ~$0.001
    """
    # Use a very simple, predictable input
    result = await real_llm_service.generate_content(prompt_name="extract_material", source_material="Python is a programming language.")

    # Basic assertions that should work with any reasonable LLM response
    assert isinstance(result, str)
    assert len(result) > 10  # Should generate meaningful content
    assert len(result) < 1000  # Shouldn't be excessively long

    # Check that it mentions relevant concepts (flexible matching)
    result_lower = result.lower()
    relevant_terms = ["python", "programming", "language", "code"]
    assert any(term in result_lower for term in relevant_terms), f"Expected response to mention programming concepts, got: {result[:100]}..."

    print(f"✅ Generated {len(result)} characters: {result[:100]}...")


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.asyncio
async def test_real_context_influence(real_llm_service):
    """
    Test that context actually influences LLM responses.

    This test demonstrates how to verify that context parameters
    are being used by the LLM.
    Expected cost: ~$0.002-0.005
    """
    source_material = "Machine learning uses algorithms to find patterns in data."

    # Test with beginner context
    beginner_context = PromptContext(user_level=UserLevel.BEGINNER, time_constraint=5, custom_instructions="Use simple language and avoid jargon")

    beginner_result = await real_llm_service.generate_content(prompt_name="extract_material", context=beginner_context, source_material=source_material)

    # Test with advanced context
    advanced_context = PromptContext(user_level=UserLevel.ADVANCED, time_constraint=15, custom_instructions="Include technical details and mathematical concepts")

    advanced_result = await real_llm_service.generate_content(prompt_name="extract_material", context=advanced_context, source_material=source_material)

    # Both should be valid responses
    assert isinstance(beginner_result, str)
    assert isinstance(advanced_result, str)
    assert len(beginner_result) > 10
    assert len(advanced_result) > 10

    # Results should be different (though this is probabilistic)
    assert beginner_result != advanced_result, "Expected different responses for different contexts"

    print(f"✅ Beginner response ({len(beginner_result)} chars): {beginner_result[:100]}...")
    print(f"✅ Advanced response ({len(advanced_result)} chars): {advanced_result[:100]}...")

    # Optional: Check for complexity differences (heuristic)
    # Advanced might be longer or use more technical terms
    # (These are probabilistic, so don't make them strict assertions)
    if len(advanced_result) > len(beginner_result) * 1.2:
        print("📊 Advanced response is notably longer")

    technical_terms = ["algorithm", "model", "optimization", "neural", "statistical"]
    advanced_technical_count = sum(1 for term in technical_terms if term in advanced_result.lower())
    beginner_technical_count = sum(1 for term in technical_terms if term in beginner_result.lower())

    if advanced_technical_count > beginner_technical_count:
        print("📊 Advanced response uses more technical terms")


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.asyncio
async def test_real_structured_generation(real_llm_service):
    """
    Test structured content generation with real LLM.

    This demonstrates testing JSON schema compliance with real LLMs.
    Expected cost: ~$0.002-0.01
    """
    schema = {
        "type": "object",
        "properties": {"summary": {"type": "string"}, "key_concepts": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 5}, "difficulty_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]}},
        "required": ["summary", "key_concepts", "difficulty_level"],
    }

    result = await real_llm_service.generate_structured_content(prompt_name="extract_material", response_schema=schema, source_material="Quantum computing uses quantum bits (qubits) to perform calculations.")

    # Validate structure
    assert isinstance(result, dict)
    assert "summary" in result
    assert "key_concepts" in result
    assert "difficulty_level" in result

    # Validate types
    assert isinstance(result["summary"], str)
    assert isinstance(result["key_concepts"], list)
    assert isinstance(result["difficulty_level"], str)

    # Validate content
    assert len(result["summary"]) > 10
    assert 2 <= len(result["key_concepts"]) <= 5
    assert result["difficulty_level"] in ["beginner", "intermediate", "advanced"]

    # All key concepts should be strings
    assert all(isinstance(concept, str) for concept in result["key_concepts"])

    print(f"✅ Structured result: {result}")


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.asyncio
async def test_real_error_handling(real_llm_service):
    """
    Test error handling with real LLM service.

    This demonstrates how to test error conditions with real APIs.
    Expected cost: ~$0.001 (may not make API call if error is caught early)
    """
    # Test with missing required variable
    with pytest.raises(Exception) as exc_info:
        await real_llm_service.generate_content(
            prompt_name="extract_material",
            # Missing required 'source_material' variable
        )

    # Should get a meaningful error message
    error_message = str(exc_info.value)
    assert "source_material" in error_message or "required" in error_message.lower()

    print(f"✅ Proper error handling: {error_message}")


@pytest.mark.integration
@pytest.mark.llm
def test_real_service_configuration(real_llm_service):
    """
    Test that the real service is configured correctly.

    This test doesn't make API calls, so it's free.
    """
    stats = real_llm_service.get_stats()

    # Verify configuration
    assert stats["service"] == "llm_services"
    config = stats["config"]
    assert config["provider"] == "openai"
    assert config["model"] == "gpt-3.5-turbo"
    assert 0.0 <= config["temperature"] <= 2.0
    assert config["max_tokens"] > 0

    print(f"✅ Service configured: {config}")


if __name__ == "__main__":
    # Run this file directly with:
    # python -m pytest modules/llm_services/tests/example_real_llm_test.py -v -s

    print("🚨 WARNING: This test makes real API calls and may incur costs!")
    print("Make sure you have:")
    print("1. OPENAI_API_KEY environment variable set")
    print("2. TEST_WITH_REAL_LLM=true environment variable set")
    print("3. Sufficient API credits")
    print()

    pytest.main([__file__, "-v", "-s"])
