# Ensure the backend directory is on sys.path so tests can import `modules.*`
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
BACKEND_DIR_STR = str(BACKEND_DIR)
if BACKEND_DIR_STR not in sys.path:
    sys.path.insert(0, BACKEND_DIR_STR)
