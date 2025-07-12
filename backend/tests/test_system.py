#!/usr/bin/env python3
"""
System Test for Proactive Learning App

This script tests the core functionality to ensure everything is working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Test data storage
def test_storage():
    """Test data storage functionality"""
    print("Testing data storage...")
    
    try:
        from simple_storage import SimpleStorage, create_learning_path_from_syllabus
        
        # Create storage
        storage = SimpleStorage()
        
        # Create test syllabus
        test_syllabus = {
            'topic_name': 'Test Topic',
            'description': 'Test description',
            'topics': [
                {
                    'title': 'Test Topic 1',
                    'description': 'Test description 1',
                    'learning_objectives': ['Objective 1', 'Objective 2']
                }
            ]
        }
        
        # Create learning path
        learning_path = create_learning_path_from_syllabus(test_syllabus)
        storage.save_learning_path(learning_path)
        
        # Load learning path
        loaded_path = storage.load_learning_path(learning_path.id)
        assert loaded_path is not None
        assert loaded_path.topic_name == 'Test Topic'
        
        # Clean up
        storage.delete_learning_path(learning_path.id)
        
        print("✅ Storage test passed")
        return True
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

def test_progress_tracker():
    """Test progress tracking functionality"""
    print("Testing progress tracker...")
    
    try:
        from simple_storage import SimpleStorage, create_learning_path_from_syllabus
        from basic_progress_tracker import BasicProgressTracker
        
        # Create storage and tracker
        storage = SimpleStorage()
        tracker = BasicProgressTracker(storage)
        
        # Create test learning path
        test_syllabus = {
            'topic_name': 'Test Topic',
            'description': 'Test description',
            'topics': [
                {
                    'title': 'Test Topic 1',
                    'description': 'Test description 1',
                    'learning_objectives': ['Objective 1']
                }
            ]
        }
        
        learning_path = create_learning_path_from_syllabus(test_syllabus)
        storage.save_learning_path(learning_path)
        
        # Test lesson session
        topic_id = learning_path.topics[0].id
        session = tracker.start_lesson(learning_path.id, topic_id)
        assert session.session_type == 'lesson'
        
        tracker.complete_lesson(session)
        
        # Test progress status
        status = tracker.get_topic_status(learning_path.id, topic_id)
        assert status['lesson_completed'] == True
        
        # Clean up
        storage.delete_learning_path(learning_path.id)
        
        print("✅ Progress tracker test passed")
        return True
        
    except Exception as e:
        print(f"❌ Progress tracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm_service():
    """Test LLM service functionality"""
    print("Testing LLM service...")
    
    try:
        from learning_service import create_learning_service
        
        # Check if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  LLM service test skipped - No API key found")
            print("   Set OPENAI_API_KEY environment variable to test")
            return True
        
        # Create service
        service = create_learning_service(api_key=api_key)
        
        # Test syllabus generation
        syllabus = await service.generate_syllabus(
            topic="Basic Math",
            user_level="beginner"
        )
        
        assert 'topics' in syllabus
        assert len(syllabus['topics']) > 0
        
        print("✅ LLM service test passed")
        return True
        
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("Testing dependencies...")
    
    required_modules = [
        'openai',
        'tiktoken',
        'pydantic',
        'sqlalchemy'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing modules: {', '.join(missing_modules)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available")
    return True

def test_cli_imports():
    """Test CLI imports"""
    print("Testing CLI imports...")
    
    try:
        from learning_cli import LearningCLI
        
        # Test CLI creation
        cli = LearningCLI()
        assert cli.storage is not None
        assert cli.progress_tracker is not None
        
        print("✅ CLI imports test passed")
        return True
        
    except Exception as e:
        print(f"❌ CLI imports test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🧪 Running Proactive Learning App System Tests")
    print("="*50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Storage", test_storage),
        ("Progress Tracker", test_progress_tracker),
        ("CLI Imports", test_cli_imports),
        ("LLM Service", test_llm_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        if result:
            passed += 1
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your system is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return False

def main():
    """Main test runner"""
    result = asyncio.run(run_all_tests())
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())