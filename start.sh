#!/bin/bash

# Run database migrations if needed
python -m flask db upgrade || echo "Migration failed, but continuing..."

# Initialize the database if needed
python -m flask init-db

# Start the application
gunicorn app:app 