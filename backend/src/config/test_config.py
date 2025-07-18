#!/usr/bin/env python3
"""
Test configuration system
"""

import os
import tempfile
from pathlib import Path

def test_env_loading():
    """Test .env file loading"""
    print("🔍 Testing .env file loading...")

    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
OPENAI_API_KEY=test-key-123
OPENAI_MODEL=gpt-4o
USER_LEVEL=advanced
LESSON_DURATION=20
MASTERY_THRESHOLD=0.85
DEBUG=true
""")
        temp_env_file = f.name

    try:
        # Test configuration loading
        from config import ConfigManager

        config_manager = ConfigManager(temp_env_file)
        config = config_manager.config

        # Check if values were loaded correctly
        assert config.openai_api_key == "test-key-123"
        assert config.openai_model == "gpt-4o"
        assert config.user_level == "advanced"
        assert config.lesson_duration == 20
        assert config.mastery_threshold == 0.85
        assert config.debug == True

        print("✅ .env file loading test passed")
        return True

    except Exception as e:
        print(f"❌ .env file loading test failed: {e}")
        return False
    finally:
        # Clean up
        os.unlink(temp_env_file)

def test_llm_config_creation():
    """Test LLM config creation"""
    print("\n🔍 Testing LLM config creation...")

    try:
        # Set test environment variables
        os.environ['OPENAI_API_KEY'] = 'test-key-456'
        os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'
        os.environ['TEMPERATURE'] = '0.8'

        from config import ConfigManager

        config_manager = ConfigManager()
        llm_config = config_manager.get_llm_config()

        # Check LLM config
        assert llm_config.api_key == 'test-key-456'
        assert llm_config.model == 'gpt-3.5-turbo'
        assert llm_config.temperature == 0.8

        print("✅ LLM config creation test passed")
        return True

    except Exception as e:
        print(f"❌ LLM config creation test failed: {e}")
        return False
    finally:
        # Clean up environment variables
        os.environ.pop('OPENAI_API_KEY', None)
        os.environ.pop('OPENAI_MODEL', None)
        os.environ.pop('TEMPERATURE', None)

def test_validation():
    """Test configuration validation"""
    print("\n🔍 Testing configuration validation...")

    try:
        # Set invalid configuration
        os.environ['OPENAI_API_KEY'] = 'test-key'
        os.environ['MASTERY_THRESHOLD'] = '1.5'  # Invalid - should be ≤ 1.0
        os.environ['PASSING_THRESHOLD'] = '0.95'  # Invalid - should be < mastery

        from config import ConfigManager

        config_manager = ConfigManager()

        # Validation should fail
        is_valid = config_manager.validate_config()
        assert not is_valid

        print("✅ Configuration validation test passed")
        return True

    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False
    finally:
        # Clean up
        os.environ.pop('OPENAI_API_KEY', None)
        os.environ.pop('MASTERY_THRESHOLD', None)
        os.environ.pop('PASSING_THRESHOLD', None)

def test_azure_config():
    """Test Azure OpenAI configuration"""
    print("\n🔍 Testing Azure OpenAI configuration...")

    try:
        # Set Azure configuration
        os.environ['AZURE_OPENAI_API_KEY'] = 'azure-key-123'
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
        os.environ['OPENAI_MODEL'] = 'gpt-4o'

        from config import ConfigManager
        from llm_interface import LLMProviderType

        config_manager = ConfigManager()
        llm_config = config_manager.get_llm_config()

        # Check Azure config
        assert llm_config.provider == LLMProviderType.AZURE_OPENAI
        assert llm_config.api_key == 'azure-key-123'
        assert llm_config.base_url == 'https://test.openai.azure.com/'

        print("✅ Azure OpenAI configuration test passed")
        return True

    except Exception as e:
        print(f"❌ Azure OpenAI configuration test failed: {e}")
        return False
    finally:
        # Clean up
        os.environ.pop('AZURE_OPENAI_API_KEY', None)
        os.environ.pop('AZURE_OPENAI_ENDPOINT', None)
        os.environ.pop('OPENAI_MODEL', None)

def test_learning_service_config():
    """Test learning service configuration"""
    print("\n🔍 Testing learning service configuration...")

    try:
        # Set configuration
        os.environ['OPENAI_API_KEY'] = 'test-key'
        os.environ['LESSON_DURATION'] = '25'
        os.environ['MAX_QUIZ_QUESTIONS'] = '8'
        os.environ['CACHE_ENABLED'] = 'false'

        from config import ConfigManager

        config_manager = ConfigManager()
        service_config = config_manager.get_learning_service_config()

        # Check service config
        assert service_config.default_lesson_duration == 25
        assert service_config.max_quiz_questions == 8
        assert service_config.cache_enabled == False

        print("✅ Learning service configuration test passed")
        return True

    except Exception as e:
        print(f"❌ Learning service configuration test failed: {e}")
        return False
    finally:
        # Clean up
        os.environ.pop('OPENAI_API_KEY', None)
        os.environ.pop('LESSON_DURATION', None)
        os.environ.pop('MAX_QUIZ_QUESTIONS', None)
        os.environ.pop('CACHE_ENABLED', None)

def main():
    """Run all configuration tests"""
    print("🧪 Configuration System Tests")
    print("=" * 40)

    tests = [
        test_env_loading,
        test_llm_config_creation,
        test_validation,
        test_azure_config,
        test_learning_service_config,
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All configuration tests passed!")
        print("\nConfiguration system is working correctly!")
    else:
        print(f"⚠️  {failed} test(s) failed.")

    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)