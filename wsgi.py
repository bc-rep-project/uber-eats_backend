import os
import sys
from pathlib import Path

# Get the absolute path of the current file's directory
current_dir = Path(__file__).resolve().parent

# Add the src directory to Python path
src_path = current_dir / 'src'
sys.path.append(str(src_path))

from src.app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 