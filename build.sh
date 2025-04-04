#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

# Make the setup_db.py script executable
chmod +x setup_db.py

# This script is used by Render to build the application.
echo "Setting up database..."
python setup_db.py || echo "Database setup failed, will try again at startup"

# Create a simple startup script that initializes the database
cat > start.sh << 'EOL'
#!/usr/bin/env bash
set -o errexit

echo "Starting application..."
echo "Initializing database..."
python -m flask init-db || echo "Database initialization failed, will continue with limited functionality"

echo "Starting gunicorn server..."
gunicorn app:app
EOL

chmod +x start.sh

echo "Build complete!" 