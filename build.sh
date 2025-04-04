#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

# This script is used by Render to build the application.
echo "Setting up database..."
python setup_db.py

echo "Build complete!" 