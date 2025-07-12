#!/usr/bin/env python3
"""
Simple test to reproduce the exact error
"""

def test_progress_tracker():
    """Test progress tracker"""
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

if __name__ == "__main__":
    test_progress_tracker()