#!/usr/bin/env python3
"""
Final comprehensive test after all fixes
"""

import sys

def test_all_imports():
    """Test all critical imports"""
    print("🔍 Testing all imports...")
    
    try:
        from simple_storage import SimpleStorage, create_learning_path_from_syllabus, ProgressStatus
        from basic_progress_tracker import BasicProgressTracker
        from learning_service import create_learning_service
        from learning_cli import LearningCLI
        from llm_interface import LLMConfig, LLMProviderType
        from prompt_engineering import PromptFactory
        from data_structures import QuizQuestion, QuizType
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_progress_tracker_full():
    """Test full progress tracker functionality"""
    print("\n🔍 Testing progress tracker...")
    
    try:
        from simple_storage import SimpleStorage, create_learning_path_from_syllabus, ProgressStatus
        from basic_progress_tracker import BasicProgressTracker
        
        # Create storage and tracker
        storage = SimpleStorage()
        tracker = BasicProgressTracker(storage)
        
        # Create test syllabus
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
        
        # Create learning path
        learning_path = create_learning_path_from_syllabus(test_syllabus)
        storage.save_learning_path(learning_path)
        
        topic_id = learning_path.topics[0].id
        
        # Test lesson session
        print("  - Testing lesson session...")
        session = tracker.start_lesson(learning_path.id, topic_id)
        assert session.session_type == 'lesson'
        
        tracker.complete_lesson(session)
        
        # Test progress status
        print("  - Testing progress status...")
        status = tracker.get_topic_status(learning_path.id, topic_id)
        assert status['lesson_completed'] == True
        assert 'status' in status
        assert isinstance(status['status'], str)
        
        # Test overall status
        print("  - Testing overall status...")
        overall_status = tracker.get_learning_path_status(learning_path.id)
        assert 'topic_statuses' in overall_status
        
        # Test recommendation
        print("  - Testing recommendations...")
        recommendation = tracker.get_next_recommended_action(learning_path.id)
        assert 'action' in recommendation
        
        # Clean up
        storage.delete_learning_path(learning_path.id)
        
        print("✅ Progress tracker test passed")
        return True
        
    except Exception as e:
        print(f"❌ Progress tracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_creation():
    """Test CLI creation"""
    print("\n🔍 Testing CLI creation...")
    
    try:
        from learning_cli import LearningCLI
        
        cli = LearningCLI()
        assert cli.storage is not None
        assert cli.progress_tracker is not None
        
        print("✅ CLI creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ CLI creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enum_consistency():
    """Test that enums are consistent"""
    print("\n🔍 Testing enum consistency...")
    
    try:
        from simple_storage import ProgressStatus as SimpleProgressStatus
        from data_structures import ProgressStatus as DataProgressStatus
        
        # They should be the same
        assert SimpleProgressStatus.NOT_STARTED == DataProgressStatus.NOT_STARTED
        assert SimpleProgressStatus.MASTERED == DataProgressStatus.MASTERED
        
        print("✅ Enum consistency test passed")
        return True
        
    except Exception as e:
        print(f"❌ Enum consistency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Final Comprehensive Test Suite")
    print("=" * 50)
    
    tests = [
        ("All Imports", test_all_imports),
        ("Progress Tracker", test_progress_tracker_full),
        ("CLI Creation", test_cli_creation),
        ("Enum Consistency", test_enum_consistency),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"📊 Final Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The app is fully functional!")
        print("\nTo run the app:")
        print("1. Get OpenAI API key from https://platform.openai.com/api-keys")
        print("2. Run: python main.py")
        print("3. Configure API key in settings")
        print("4. Start learning!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())