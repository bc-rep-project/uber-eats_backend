import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.append(str(src_path))

from app import app

if __name__ == '__main__':
    app.run() 