"""
Configuration for pytest and imports
"""
import os
import sys
from pathlib import Path

# Get the absolute path of the current file's directory (src)
current_dir = Path(__file__).resolve().parent

# Add the src directory to Python path if not already there
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir)) 