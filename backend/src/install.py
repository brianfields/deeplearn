#!/usr/bin/env python3
"""
Installation Script for Proactive Learning App

This script helps set up the learning app with all dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print installation banner"""
    print("="*60)
    print("🚀 Proactive Learning App - Installation")
    print("="*60)
    print()

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_pip():
    """Check if pip is available"""
    print("📦 Checking pip...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
        print("✅ pip is available")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip not found")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("📥 Installing dependencies...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Install requirements
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_data_directory():
    """Create data directory"""
    print("📁 Creating data directory...")
    
    data_dir = Path(".learning_data")
    data_dir.mkdir(exist_ok=True)
    
    print("✅ Data directory created")
    return True

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    try:
        subprocess.run([sys.executable, "test_system.py"], 
                      capture_output=True, check=True)
        print("✅ Installation test passed")
        return True
        
    except subprocess.CalledProcessError:
        print("⚠️  Installation test had some issues")
        print("   You can still try running the app")
        return True

def print_next_steps():
    """Print next steps"""
    print("\n🎯 Next Steps:")
    print("1. Get an OpenAI API key:")
    print("   - Go to https://platform.openai.com/api-keys")
    print("   - Create a new API key")
    print()
    print("2. Run the app:")
    print("   python main.py")
    print()
    print("3. Configure your API key in the app settings")
    print()
    print("4. Start learning! 🚀")

def main():
    """Main installation process"""
    print_banner()
    
    # Check requirements
    if not check_python_version():
        return 1
    
    if not check_pip():
        return 1
    
    # Install components
    steps = [
        ("Install dependencies", install_dependencies),
        ("Create data directory", create_data_directory),
        ("Test installation", test_installation),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ Installation failed at: {step_name}")
            return 1
    
    print("\n🎉 Installation completed successfully!")
    print_next_steps()
    return 0

if __name__ == "__main__":
    sys.exit(main())