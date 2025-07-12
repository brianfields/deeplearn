#!/usr/bin/env python3
"""
Test the conversational learning system
"""

import asyncio
import tempfile
import os
from pathlib import Path

def test_conversational_imports():
    """Test that all conversational imports work"""
    print("🔍 Testing conversational imports...")
    
    try:
        from conversational_learning import ConversationalLearningEngine, ConversationSession
        from conversational_cli import ConversationalCLI
        
        print("✅ Conversational imports successful")
        return True
    except Exception as e:
        print(f"❌ Conversational imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_session():
    """Test conversation session creation"""
    print("\n🔍 Testing conversation session...")
    
    try:
        from conversational_learning import ConversationSession, ConversationProgress
        from datetime import datetime
        
        session = ConversationSession(
            topic_id="test_topic",
            topic_title="Test Topic",
            learning_objectives=["Learn A", "Learn B"]
        )
        
        assert session.topic_id == "test_topic"
        assert session.topic_title == "Test Topic"
        assert len(session.learning_objectives) == 2
        assert session.progress is not None
        
        print("✅ Conversation session test passed")
        return True
        
    except Exception as e:
        print(f"❌ Conversation session test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_integration():
    """Test storage integration with conversational system"""
    print("\n🔍 Testing storage integration...")
    
    try:
        from simple_storage import SimpleStorage
        from conversational_learning import ConversationalLearningEngine
        
        # Create temporary storage
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = SimpleStorage(temp_dir)
            
            # Test session saving/loading
            session_data = {
                "topic_id": "test_topic",
                "topic_title": "Test Topic",
                "learning_objectives": ["Learn A"],
                "state": "starting",
                "progress": {
                    "concepts_covered": [],
                    "concepts_mastered": [],
                    "current_concept": None,
                    "understanding_level": 0.0,
                    "engagement_score": 0.0,
                    "time_spent": 0,
                    "message_count": 0,
                    "last_assessment": None
                },
                "messages": [],
                "started_at": "2024-01-01T10:00:00",
                "last_updated": "2024-01-01T10:00:00"
            }
            
            storage.save_current_session(session_data)
            loaded_session = storage.load_current_session()
            
            assert loaded_session["topic_id"] == "test_topic"
            assert loaded_session["topic_title"] == "Test Topic"
            
            print("✅ Storage integration test passed")
            return True
            
    except Exception as e:
        print(f"❌ Storage integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_initialization():
    """Test CLI initialization"""
    print("\n🔍 Testing CLI initialization...")
    
    try:
        # Set minimal environment
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        from conversational_cli import ConversationalCLI
        
        cli = ConversationalCLI()
        assert cli.storage is not None
        assert cli.config is not None
        
        print("✅ CLI initialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ CLI initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        os.environ.pop('OPENAI_API_KEY', None)

def test_config_loading():
    """Test configuration loading"""
    print("\n🔍 Testing configuration loading...")
    
    try:
        from config import config_manager
        
        config = config_manager.config
        assert config is not None
        assert hasattr(config, 'openai_model')
        assert hasattr(config, 'user_level')
        
        print("✅ Configuration loading test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Conversational Learning System Tests")
    print("=" * 50)
    
    tests = [
        test_conversational_imports,
        test_conversation_session,
        test_storage_integration,
        test_cli_initialization,
        test_config_loading,
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
        print("🎉 All tests passed! Conversational learning system is ready!")
        print("\nTo start learning:")
        print("1. Set up your .env file with OPENAI_API_KEY")
        print("2. Run: python learn.py")
        print("3. Start a conversation with your AI tutor!")
    else:
        print(f"⚠️  {failed} test(s) failed.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)