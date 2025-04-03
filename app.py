"""
Main application file that re-exports the Flask app from the app package.
This file exists for compatibility with various WSGI servers and deployment platforms.
"""

import os
import sys

# Add the current directory to sys.path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Import the app from the app package
    from app import app
except ImportError as e:
    print(f"Error importing app in app.py: {e}")
    print("Python path:", sys.path)
    print("Current directory:", os.getcwd())
    raise

# For direct execution
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)), debug=True) 