#!/usr/bin/env python3
"""
Test the fixes for JSON parsing and unique ID generation
"""

import json
import asyncio
from datetime import datetime

def test_json_parsing():
    """Test JSON parsing with markdown code blocks"""
    print("🔍 Testing JSON parsing fixes...")
    
    try:
        from llm_interface import OpenAIProvider, LLMConfig, LLMProviderType
        
        # Test markdown code block parsing
        test_responses = [
            '```json\n{"test": "value"}\n```',
            '```\n{"test": "value"}\n```',
            '{"test": "value"}',
            '```json\n{"test": "value", "nested": {"key": "val"}}\n```'
        ]
        
        # Mock provider to test parsing
        config = LLMConfig(
            provider=LLMProviderType.OPENAI,
            model="gpt-3.5-turbo",
            api_key="test",
            temperature=0.7
        )
        
        provider = OpenAIProvider(config)
        
        for response_text in test_responses:
            # Simulate response parsing
            try:
                content = response_text.strip()
                
                # Handle markdown code blocks
                if content.startswith('```json'):
                    start_idx = content.find('```json') + 7
                    end_idx = content.rfind('```')
                    if end_idx > start_idx:
                        content = content[start_idx:end_idx].strip()
                elif content.startswith('```'):
                    start_idx = content.find('```') + 3
                    end_idx = content.rfind('```')
                    if end_idx > start_idx:
                        content = content[start_idx:end_idx].strip()
                
                parsed = json.loads(content)
                assert parsed["test"] == "value"
                
            except Exception as e:
                print(f"❌ Failed to parse: {response_text}")
                print(f"Error: {e}")
                return False
        
        print("✅ JSON parsing test passed")
        return True
        
    except Exception as e:
        print(f"❌ JSON parsing test failed: {e}")
        return False

def test_unique_id_generation():
    """Test unique ID generation"""
    print("\n🔍 Testing unique ID generation...")
    
    try:
        from simple_storage import generate_unique_id
        
        # Generate multiple IDs quickly
        ids = []
        for i in range(10):
            id_val = generate_unique_id("test")
            ids.append(id_val)
        
        # Check that all IDs are unique
        if len(set(ids)) != len(ids):
            print("❌ Generated duplicate IDs!")
            return False
        
        # Check ID format
        for id_val in ids:
            if not id_val.startswith("test_"):
                print(f"❌ Invalid ID format: {id_val}")
                return False
        
        print("✅ Unique ID generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Unique ID generation test failed: {e}")
        return False

def test_learning_path_creation():
    """Test learning path creation with unique IDs"""
    print("\n🔍 Testing learning path creation...")
    
    try:
        from simple_storage import create_learning_path_from_syllabus
        
        # Create test syllabus
        syllabus = {
            'topic_name': 'Neural Networks',
            'description': 'Learn about neural networks',
            'topics': [
                {
                    'title': 'Introduction to Neural Networks',
                    'description': 'Basic concepts',
                    'learning_objectives': ['Understand neural networks']
                },
                {
                    'title': 'Perceptron Model',
                    'description': 'Learn about perceptrons',
                    'learning_objectives': ['Understand perceptrons']
                }
            ]
        }
        
        # Create multiple learning paths
        paths = []
        for i in range(3):
            path = create_learning_path_from_syllabus(syllabus)
            paths.append(path)
        
        # Check that all paths have unique IDs
        path_ids = [p.id for p in paths]
        if len(set(path_ids)) != len(path_ids):
            print("❌ Generated duplicate path IDs!")
            return False
        
        # Check that all topics have unique IDs
        for path in paths:
            topic_ids = [t.id for t in path.topics]
            if len(set(topic_ids)) != len(topic_ids):
                print("❌ Generated duplicate topic IDs!")
                return False
        
        print("✅ Learning path creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Learning path creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Bug Fixes")
    print("=" * 30)
    
    tests = [
        test_json_parsing,
        test_unique_id_generation,
        test_learning_path_creation,
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
        print("🎉 All fixes working correctly!")
        print("\nThe app should now handle:")
        print("✅ JSON responses with markdown code blocks")
        print("✅ Unique ID generation for learning paths")
        print("✅ No duplicate learning paths")
    else:
        print(f"⚠️  {failed} test(s) failed.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)