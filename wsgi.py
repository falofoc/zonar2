"""
WSGI entry point for the Flask application
"""
import sys
import os

# Add the current directory to sys.path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from app import app
except ImportError as e:
    print(f"Error importing app in wsgi.py: {e}")
    print("Python path:", sys.path)
    print("Current directory:", os.getcwd())
    raise

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run() 