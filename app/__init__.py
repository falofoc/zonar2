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
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Ensure instance directory exists
instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../instance"))
os.makedirs(instance_path, exist_ok=True)
print(f"Database directory: {instance_path}")

# For Render deployment, use /tmp directory if we're in production
is_production = os.environ.get('RENDER', False)
if is_production:
    db_path = '/tmp/amazon_tracker.db'
    print(f"Using production database path: {db_path}")
else:
    db_path = os.path.join(instance_path, "amazon_tracker.db")
    print(f"Using local database path: {db_path}")

# Security settings - Relaxed for development
app.config.update(
    SECRET_KEY='dev-key-please-change-in-production',  # Fixed secret key for development
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,  # Enable HTTPOnly for security
    SESSION_COOKIE_SAMESITE='Lax',   # Use Lax for better security while still allowing cross-site
    PERMANENT_SESSION_LIFETIME=1800,
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_ENABLED=False,
    DEBUG=True
)

# Print database URI for debugging
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

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
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = None  # Disable session protection for development

# Import all other components AFTER the app is created
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translations import translations

# This defines the translate function that's used in templates
def translate(key):
    try:
        # First try to get from user's preferred language
        if hasattr(g, 'lang') and g.lang:
            lang = g.lang
        else:
            # Fall back to cookie or default
            lang = request.cookies.get('language', 'ar')  # Default to Arabic
            
        # Get translation from the dictionary    
        if key in translations and lang in translations:
            return translations[lang].get(key, translations['en'].get(key, key))
        return key
    except Exception as e:
        print(f"Translation error for key {key}: {e}")
        return key

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
try:
    from . import models, routes
except ImportError:
    # Handle case when relative import fails
    import app.models
    import app.routes

def init_db():
    """Initialize the database and create all tables"""
    print("Initializing database...")
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

# Initialize database if it doesn't exist
with app.app_context():
    try:
        db.create_all()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        traceback.print_exc()

@login_manager.user_loader
def load_user(id):
    from app.models import User
    return User.query.get(int(id)) 