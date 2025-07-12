#!/usr/bin/env python3
"""
Start the Conversational Learning API Server

This script starts the FastAPI web server for the conversational learning app.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Set environment variables if needed
os.environ['PYTHONPATH'] = f"{src_path}:{os.getenv('PYTHONPATH', '')}"

def main():
    """Start the server"""
    try:
        import uvicorn

        print("🚀 Starting Conversational Learning API Server")
        print("📡 Server will be available at: http://localhost:8000")
        print("📋 API docs will be available at: http://localhost:8000/docs")
        print("💡 Make sure your .env file is configured with your OpenAI API key")
        print()

        # Change to src directory for proper imports
        os.chdir(Path(__file__).parent / "src")

        # Start the server
        uvicorn.run(
            "api.server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install the required dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()