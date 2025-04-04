"""
WSGI entry point for the Flask application
"""
import os
from dotenv import load_dotenv

# Load environment variables and print diagnostic information
load_dotenv()
print("Environment variables at startup:")
print(f"SUPABASE_URL present: {bool(os.getenv('SUPABASE_URL'))}")
print(f"SUPABASE_KEY present: {bool(os.getenv('SUPABASE_KEY'))}")
print(f"SUPABASE_SERVICE_KEY present: {bool(os.getenv('SUPABASE_SERVICE_KEY'))}")
print(f"FLASK_APP: {os.getenv('FLASK_APP')}")
print(f"PYTHONPATH: {os.getenv('PYTHONPATH')}")

from app import app

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run() 