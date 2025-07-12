#!/usr/bin/env python3
"""
Quick test to verify the app works after fixes
"""

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    
    try:
        from simple_storage import SimpleStorage
        print("✅ SimpleStorage imported")
        
        from basic_progress_tracker import BasicProgressTracker
        print("✅ BasicProgressTracker imported")
        
        from learning_service import create_learning_service
        print("✅ LearningService imported")
        
        from learning_cli import LearningCLI
        print("✅ LearningCLI imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_storage():
    """Test storage functionality"""
    print("\nTesting storage...")
    
    try:
        from simple_storage import SimpleStorage, create_learning_path_from_syllabus
        
        storage = SimpleStorage()
        
        # Test syllabus
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
        
        # Load it back
        loaded_path = storage.load_learning_path(learning_path.id)
        assert loaded_path.topic_name == 'Test Topic'
        
        # Clean up
        storage.delete_learning_path(learning_path.id)
        
        print("✅ Storage works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

def test_progress_tracker():
    """Test progress tracker"""
    print("\nTesting progress tracker...")
    
    try:
        from simple_storage import SimpleStorage, create_learning_path_from_syllabus
        from basic_progress_tracker import BasicProgressTracker
        
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
        tracker.complete_lesson(session)
        
        # Check status
        status = tracker.get_topic_status(learning_path.id, topic_id)
        assert status['lesson_completed'] == True
        
        # Clean up
        storage.delete_learning_path(learning_path.id)
        
        print("✅ Progress tracker works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Progress tracker test failed: {e}")
        return False

def main():
    """Run quick tests"""
    print("🧪 Quick Test Suite")
    print("=" * 30)
    
    tests = [
        ("Imports", test_imports),
        ("Storage", test_storage),
        ("Progress Tracker", test_progress_tracker),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The app is ready to use!")
        print("\nTo run the app:")
        print("1. Set your OpenAI API key as environment variable:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("2. Run: python main.py")
    else:
        print("⚠️  Some tests failed.")

if __name__ == "__main__":
    main()