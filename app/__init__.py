import os
import json
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, g, session
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask_cors import CORS  # Add CORS support
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Security settings - Relaxed for development
app.config.update(
    SECRET_KEY='dev-key-please-change-in-production',  # Fixed secret key for development
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,  # Enable HTTPOnly for security
    SESSION_COOKIE_SAMESITE='Lax',   # Use Lax for better security while still allowing cross-site
    PERMANENT_SESSION_LIFETIME=1800,
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), "../instance", "amazon_tracker.db"))}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_ENABLED=False,
    DEBUG=True
)

# Initialize CORS with very permissive settings for development
CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],  # Specify allowed origins
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
         "supports_credentials": True,
         "expose_headers": ["Content-Type", "Authorization"],
         "max_age": 3600
     }},
     supports_credentials=True)

# Initialize database and login manager with relaxed settings
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = None  # Disable session protection for development

# Import all other components AFTER the app is created
from ..translations import translations
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import trackers

# This defines the translate function that's used in templates
def translate(key):
    return translations[g.lang].get(key, translations['en'].get(key, key))

@app.context_processor
def utility_processor():
    return dict(translate=translate)

@app.before_request
def before_request():
    # Set language based on user preference or default to Arabic
    if current_user.is_authenticated:
        g.lang = current_user.language
        g.theme = current_user.theme
    else:
        g.lang = request.cookies.get('language', 'ar')  # Default to Arabic
        g.theme = request.cookies.get('theme', 'light')

# Now import the rest of the app components
from . import models, routes

def init_db():
    """Initialize the database and create all tables"""
    # Ensure instance directory exists
    os.makedirs('../instance', exist_ok=True)
    
    # Create all tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!") 