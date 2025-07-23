#!/usr/bin/env python3
"""
Start the Conversational Learning API Server

This script starts the FastAPI web server for the conversational learning app.
"""

import os
from pathlib import Path
import sys

# Add src directory to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Set environment variables if needed
os.environ["PYTHONPATH"] = f"{src_path}:{os.getenv('PYTHONPATH', '')}"


def main():
    """Start the server"""
    try:
        import uvicorn

        print("🚀 Starting Conversational Learning API Server")
        print("📡 Server will be available at: http://localhost:8000")
        print("📋 API docs will be available at: http://localhost:8000/docs")
        print("💡 Make sure your .env file is configured with your OpenAI API key")
        print()

        # Store the project root directory (where .env file is located)
        project_root = Path(__file__).parent.parent
        backend_dir = Path(__file__).parent
        src_dir = backend_dir / "src"

        # Set environment variables to help find .env file
        os.environ["PROJECT_ROOT"] = str(project_root)

        # Change to src directory for proper imports
        os.chdir(src_dir)

        # Start the server
        uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

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
