#!/usr/bin/env python3
"""
Debug test to identify the exact issue
"""

def test_progress_status():
    """Test ProgressStatus enum"""
    print("Testing ProgressStatus enum...")
    
    try:
        from simple_storage import ProgressStatus
        print(f"ProgressStatus imported: {ProgressStatus}")
        print(f"NOT_STARTED value: {ProgressStatus.NOT_STARTED}")
        print(f"Type: {type(ProgressStatus.NOT_STARTED)}")
        return True
    except Exception as e:
        print(f"Error with ProgressStatus: {e}")
        return False

def test_progress_tracker_basic():
    """Test basic progress tracker functionality"""
    print("\nTesting progress tracker basic functionality...")
    
    try:
        from simple_storage import SimpleStorage, create_learning_path_from_syllabus
        from basic_progress_tracker import BasicProgressTracker
        
        # Create storage and tracker
        storage = SimpleStorage()
        tracker = BasicProgressTracker(storage)
        
        print("✅ BasicProgressTracker created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating BasicProgressTracker: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_learning_path_creation():
    """Test learning path creation"""
    print("\nTesting learning path creation...")
    
    try:
        from simple_storage import create_learning_path_from_syllabus
        
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
        print(f"✅ Learning path created: {learning_path.topic_name}")
        print(f"Progress type: {type(list(learning_path.progress.values())[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating learning path: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debug tests"""
    print("🔍 Debug Tests")
    print("=" * 30)
    
    tests = [
        test_progress_status,
        test_progress_tracker_basic,
        test_learning_path_creation,
    ]
    
    for test in tests:
        test()
        print("-" * 30)

if __name__ == "__main__":
    main()