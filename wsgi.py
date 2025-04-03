"""
WSGI entry point for the Flask application
"""
from app import app

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run() 