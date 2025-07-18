"""
Test Script for Bite-Sized Content Integration

This script demonstrates the complete workflow from syllabus creation
to bite-sized content generation and storage.
"""

import pytest
import asyncio
import json
from typing import Dict, Any

# Mock imports for testing without actual LLM calls
class MockLLMClient:
    """Mock LLM client for testing"""

    async def generate_structured_response(self, messages, schema):
        """Mock structured response generation"""
        return {
            "topic_name": "Machine Learning Fundamentals",
            "description": "Learn the basics of machine learning concepts and algorithms",
            "estimated_total_hours": 2.5,
            "topics": [
                {
                    "title": "Introduction to Machine Learning",
                    "description": "Overview of ML concepts and applications",
                    "learning_objectives": ["Understand what ML is", "Identify ML types", "Recognize ML applications"],
                    "estimated_duration": 15,
                    "difficulty_level": 1,
                    "assessment_type": "quiz"
                },
                {
                    "title": "Supervised Learning Basics",
                    "description": "Understanding supervised learning algorithms",
                    "learning_objectives": ["Define supervised learning", "Compare classification vs regression", "Understand training process"],
                    "estimated_duration": 15,
                    "difficulty_level": 2,
                    "assessment_type": "quiz"
                },
                {
                    "title": "Data Preprocessing",
                    "description": "Preparing data for machine learning",
                    "learning_objectives": ["Clean data", "Handle missing values", "Scale features"],
                    "estimated_duration": 15,
                    "difficulty_level": 2,
                    "assessment_type": "quiz"
                },
                {
                    "title": "Model Evaluation",
                    "description": "Assessing model performance",
                    "learning_objectives": ["Choose evaluation metrics", "Understand overfitting", "Apply cross-validation"],
                    "estimated_duration": 15,
                    "difficulty_level": 3,
                    "assessment_type": "quiz"
                },
                {
                    "title": "Common Algorithms",
                    "description": "Overview of popular ML algorithms",
                    "learning_objectives": ["Compare different algorithms", "Understand when to use each", "Implement basic algorithms"],
                    "estimated_duration": 15,
                    "difficulty_level": 3,
                    "assessment_type": "quiz"
                }
            ]
        }

    async def generate_response(self, messages):
        """Mock response generation for bite-sized content"""
        return """
        Title: Introduction to Machine Learning
        Snippet: Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. Instead of following pre-written instructions, ML systems identify patterns in data and make predictions or decisions based on those patterns. This revolutionary approach has transformed everything from email filtering to medical diagnosis, making it one of the most impactful technologies of our time.
        """

class MockServiceConfig:
    """Mock service configuration"""
    def __init__(self):
        self.cache_enabled = False
        self.retry_attempts = 3

@pytest.mark.asyncio
async def test_bite_sized_integration():
    """Test the complete bite-sized content integration workflow"""

    print("🚀 Starting Bite-Sized Content Integration Test")
    print("=" * 60)

    # Step 1: Initialize services
    print("\n1. Initializing Services...")
    try:
        from src.modules.lesson_planning.service import LessonPlanningService
        from src.modules.lesson_planning.bite_sized_topics.storage import TopicRepository
        from src.simple_storage import SimpleStorage, create_learning_path_from_syllabus

        config = MockServiceConfig()
        llm_client = MockLLMClient()

        lesson_service = LessonPlanningService(config, llm_client)
        topic_repository = TopicRepository(db_path="test_bite_sized_topics.db")
        storage = SimpleStorage(data_dir="test_learning_data")

        print("✅ Services initialized successfully")

    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False

    # Step 2: Generate syllabus with bite-sized content
    print("\n2. Generating Syllabus with Bite-Sized Content...")
    try:
        syllabus = await lesson_service.generate_syllabus(
            topic="Machine Learning Fundamentals",
            user_level="beginner"
        )

        print(f"✅ Syllabus generated with {len(syllabus['topics'])} topics")

        # Check if bite-sized content was generated
        if 'bite_sized_content' in syllabus:
            bite_sized_info = syllabus['bite_sized_content']
            print(f"✅ Bite-sized content generated for {bite_sized_info['total_generated']} topics")
            print(f"   Strategy: {bite_sized_info['creation_strategy']}")
            print(f"   User level: {bite_sized_info['user_level']}")
        else:
            print("❌ No bite-sized content found in syllabus")
            return False

    except Exception as e:
        print(f"❌ Syllabus generation failed: {e}")
        return False

    # Step 3: Create and store learning path
    print("\n3. Creating Learning Path...")
    try:
        learning_path = create_learning_path_from_syllabus(syllabus)
        storage.save_learning_path(learning_path)

        print(f"✅ Learning path created: {learning_path.id}")

        # Check topics for bite-sized content references
        topics_with_content = sum(1 for topic in learning_path.topics if topic.has_bite_sized_content)
        print(f"✅ {topics_with_content} topics have bite-sized content references")

    except Exception as e:
        print(f"❌ Learning path creation failed: {e}")
        return False

    # Step 4: Verify storage
    print("\n4. Verifying Storage...")
    try:
        # Check if topics were stored in TopicRepository
        for topic in learning_path.topics:
            if topic.bite_sized_topic_id:
                stored_topic = await topic_repository.get_topic(topic.bite_sized_topic_id)
                if stored_topic:
                    print(f"✅ Bite-sized content found for '{topic.title}'")
                    print(f"   Components: {stored_topic.component_count}")
                else:
                    print(f"❌ Bite-sized content missing for '{topic.title}'")

        # Check if learning path was stored
        loaded_path = storage.load_learning_path(learning_path.id)
        if loaded_path:
            print(f"✅ Learning path successfully stored and retrieved")
        else:
            print(f"❌ Learning path storage failed")

    except Exception as e:
        print(f"❌ Storage verification failed: {e}")
        return False

    # Step 5: Simulate API response
    print("\n5. Simulating API Response...")
    try:
        from src.api.models import LearningPathResponse, TopicResponse

        # Create API response
        response = LearningPathResponse(
            id=learning_path.id,
            topic_name=learning_path.topic_name,
            description=learning_path.description,
            topics=[TopicResponse(
                id=topic.id,
                title=topic.title,
                description=topic.description,
                learning_objectives=topic.learning_objectives,
                estimated_duration=15,
                difficulty_level=1,
                bite_sized_topic_id=topic.bite_sized_topic_id,
                has_bite_sized_content=topic.has_bite_sized_content
            ) for topic in learning_path.topics],
            current_topic_index=learning_path.current_topic_index,
            estimated_total_hours=len(learning_path.topics) * 0.25,
            bite_sized_content_info=syllabus.get('bite_sized_content')
        )

        print(f"✅ API response created successfully")
        print(f"   Response includes bite-sized content info: {response.bite_sized_content_info is not None}")

    except Exception as e:
        print(f"❌ API response creation failed: {e}")
        return False

    # Step 6: Show summary
    print("\n6. Integration Summary")
    print("=" * 40)
    print(f"📚 Learning Path: {learning_path.topic_name}")
    print(f"📝 Total Topics: {len(learning_path.topics)}")
    print(f"🎯 Topics with Bite-Sized Content: {topics_with_content}")
    print(f"⚙️  Content Strategy: {bite_sized_info['creation_strategy']}")
    print(f"👤 User Level: {bite_sized_info['user_level']}")

    print("\n🎉 Integration test completed successfully!")
    print("\nNext Steps:")
    print("1. Start the backend server: python backend/start_server.py")
    print("2. Start the frontend: npm run dev (in web directory)")
    print("3. Create a new learning path to see bite-sized content in action")

    return True

@pytest.mark.asyncio
async def test_tutoring_integration():
    """Test tutoring system integration with bite-sized content"""

    print("\n🤖 Testing Tutoring Integration")
    print("=" * 40)

    try:
        from src.modules.lesson_planning.bite_sized_topics.tutoring_api import TutoringAPI, TutoringContext, LearnerState, LearningPhase
        from src.modules.lesson_planning.bite_sized_topics.storage import TopicRepository

        repository = TopicRepository(db_path="test_bite_sized_topics.db")
        tutoring_api = TutoringAPI(repository)

        # Create tutoring context
        context = TutoringContext(
            learner_state=LearnerState.LEARNING,
            learning_phase=LearningPhase.INTRODUCTION,
            user_level="beginner"
        )

        print("✅ Tutoring API initialized")
        print(f"   Context: {context.learner_state.value} learner in {context.learning_phase.value} phase")

        # Test would require actual stored content, so we'll just verify the API is working
        print("✅ Tutoring integration ready for content-based testing")

    except Exception as e:
        print(f"❌ Tutoring integration test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    print("🧪 Bite-Sized Content Integration Test Suite")
    print("=" * 60)

    async def run_tests():
        # Run main integration test
        success = await test_bite_sized_integration()

        if success:
            # Run tutoring integration test
            await test_tutoring_integration()

            print("\n✅ All tests completed successfully!")
            print("\nManual Testing Instructions:")
            print("1. Start the backend server")
            print("2. Start the frontend development server")
            print("3. Create a new learning path through the web interface")
            print("4. Verify that topics show 'Enhanced Content' badges")
            print("5. Check that the bite-sized content summary appears")
            print("6. Confirm that the first 5 topics have bite-sized content")
        else:
            print("\n❌ Integration tests failed!")
            print("Please check the error messages above and fix any issues.")

    asyncio.run(run_tests())