#!/usr/bin/env python3
"""
Main entry point for the Conversational Learning App

This script provides a ChatGPT-like learning experience with Socratic dialogue.
"""

import sys
import os
import asyncio
from pathlib import Path

# Import configuration
from config import config_manager, setup_logging, validate_config, print_config_summary

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing_deps = []
    
    try:
        import openai
    except ImportError:
        missing_deps.append("openai")
    
    try:
        import tiktoken
    except ImportError:
        missing_deps.append("tiktoken")
    
    try:
        import pydantic
    except ImportError:
        missing_deps.append("pydantic")
    
    try:
        import rich
    except ImportError:
        missing_deps.append("rich")
    
    try:
        import dotenv
    except ImportError:
        missing_deps.append("python-dotenv")
    
    return missing_deps

def print_banner():
    """Print application banner"""
    print("="*60)
    print("💬 Conversational Learning App")
    print("ChatGPT-like AI Tutor with Socratic Dialogue")
    print("="*60)
    print()

def print_quick_setup():
    """Print quick setup instructions"""
    print("📋 Quick Setup:")
    print("1. Copy .env.example to .env")
    print("2. Add your OpenAI API key to .env:")
    print("   OPENAI_API_KEY=your-api-key-here")
    print("3. Run: python learn.py")
    print()

async def main():
    """Main entry point"""
    print_banner()
    
    # Check dependencies
    missing_deps = check_dependencies()
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print()
        print("Please install missing dependencies:")
        print("pip install " + " ".join(missing_deps))
        print()
        print("Or install all dependencies:")
        print("pip install -r requirements.txt")
        return 1
    
    # Setup logging
    setup_logging()
    
    # Load and validate configuration
    config = config_manager.config
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found!")
        print_quick_setup()
        
        if not config.openai_api_key:
            print("❌ No API key configured. Please create a .env file with your OpenAI API key.")
            return 1
    
    # Validate configuration
    try:
        if not validate_config():
            print("❌ Configuration validation failed.")
            print("Please check your .env file settings.")
            return 1
    except Exception as e:
        print(f"⚠️  Configuration issue: {e}")
        if not config.openai_api_key:
            print("Please ensure your OpenAI API key is configured.")
            return 1
    
    # Show configuration summary if debug mode
    if config.debug:
        print_config_summary()
    
    # Create data directory
    data_dir = Path(config.data_directory)
    if not data_dir.exists():
        print(f"📁 Creating data directory: {config.data_directory}")
        data_dir.mkdir(exist_ok=True)
    
    # Start the conversational learning app
    try:
        print("🚀 Starting Conversational Learning App...")
        print("💡 Tip: You can continue conversations anytime, and progress is automatically saved!")
        print()
        
        from conversational_cli import ConversationalCLI
        cli = ConversationalCLI()
        await cli.run()
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Your progress has been saved.")
        return 0
    except Exception as e:
        print(f"❌ Error running application: {e}")
        print()
        print("Troubleshooting tips:")
        print("1. Check your OpenAI API key in .env file")
        print("2. Verify your internet connection")
        print("3. Try: pip install -r requirements.txt")
        print("4. Set DEBUG=true in .env for more details")
        
        if config.debug:
            import traceback
            traceback.print_exc()
        
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))