"""
Main application file that re-exports the Flask app from the app package.
This file exists for compatibility with various WSGI servers and deployment platforms.
"""

import os
# Simply import the app from the app package
from app import app

# For direct execution
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)), debug=True) 