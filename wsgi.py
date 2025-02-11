import os
import sys
from pathlib import Path

# Get the absolute path of the current file's directory
current_dir = Path(__file__).resolve().parent

# Add the src directory to Python path
src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))

# Add all subdirectories in src to Python path
for item in src_path.iterdir():
    if item.is_dir() and not item.name.startswith('__'):
        sys.path.insert(0, str(item))

from app import app

if __name__ == '__main__':
    app.run() 