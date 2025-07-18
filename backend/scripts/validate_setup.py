#!/usr/bin/env python3
"""
Validation script to check MCQ creation setup
"""

import sys
import os
from pathlib import Path
import json

def validate_setup():
    """Validate that all required files and components are present"""
    
    print("🔍 Validating MCQ Creation Setup...")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if current_dir.name != "backend":
        print("❌ Please run this script from the backend directory")
        return False
    
    # Check required files
    required_files = [
        "scripts/create_mcqs.py",
        "pytorch_tensor_material.txt",
        "src/modules/lesson_planning/bite_sized_topics/mcq_service.py",
        "src/core/llm_client.py",
        "src/core/prompt_base.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files present")
    
    # Check Python imports
    try:
        sys.path.insert(0, str(Path("src")))
        from modules.lesson_planning.bite_sized_topics.mcq_service import MCQService
        from core.llm_client import create_llm_client
        from core.prompt_base import PromptContext
        print("✅ Python imports working correctly")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Check PyTorch material
    material_file = Path("pytorch_tensor_material.txt")
    with open(material_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if len(content) < 1000:
        print("❌ PyTorch material file seems too short")
        return False
    
    print(f"✅ PyTorch material loaded: {len(content)} characters")
    
    # Check script permissions
    script_file = Path("scripts/create_mcqs.py")
    if not os.access(script_file, os.R_OK):
        print("❌ Script file is not readable")
        return False
    
    print("✅ Script file is accessible")
    
    # Test script help
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "scripts/create_mcqs.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Script help command works")
        else:
            print("❌ Script help command failed")
            return False
    except Exception as e:
        print(f"❌ Error testing script: {e}")
        return False
    
    print("\n🎉 Setup validation successful!")
    print("\n📋 Ready to create MCQs!")
    print("\n🚀 Try this command:")
    print("   python scripts/create_mcqs.py --topic 'PyTorch Tensor Usage' --file pytorch_tensor_material.txt --output pytorch_mcqs.json --domain 'Machine Learning' --level intermediate --verbose")
    print("\n💡 Don't forget to set your OpenAI API key:")
    print("   export OPENAI_API_KEY='your-api-key-here'")
    
    return True

if __name__ == "__main__":
    success = validate_setup()
    sys.exit(0 if success else 1)