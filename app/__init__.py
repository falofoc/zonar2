import os
import json
import traceback
from datetime import datetime, timedelta
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

# Generate a more secure secret key
import secrets
secret_key = os.environ.get('SECRET_KEY', None)
if not secret_key:
    secret_key = secrets.token_hex(32)  # 32 bytes = 256 bits

# Security settings with improved session handling
app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_SECURE=is_production,  # Use secure cookies in production
    SESSION_COOKIE_HTTPONLY=True,  # Enable HTTPOnly for security
    SESSION_COOKIE_SAMESITE='Lax',   # Use Lax for better security while still allowing cross-site
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),  # Longer session lifetime
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_ENABLED=False,
    DEBUG=not is_production
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
login_manager.session_protection = "strong"  # Enable strong session protection

# Import all other components AFTER the app is created
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translations import translations

# This defines the translate function that's used in templates
def translate(key):
    try:
        # Debug the language being used
        current_lang = ""
        if hasattr(g, 'lang') and g.lang:
            current_lang = g.lang
        else:
            current_lang = request.cookies.get('language', 'ar')
        
        print(f"DEBUG: Translating key '{key}' for language '{current_lang}'")
        
        # Ensure language value is actually valid
        if current_lang not in ['ar', 'en']:
            print(f"DEBUG: Invalid language '{current_lang}', defaulting to Arabic")
            current_lang = 'ar'
            
        # Get translation from the dictionary
        if key in translations:
            if current_lang in translations and key in translations[current_lang]:
                translated = translations[current_lang].get(key)
                print(f"DEBUG: Found translation: '{translated}'")
                return translated
            elif 'en' in translations and key in translations['en']:
                # Fall back to English if translation not found in requested language
                fallback = translations['en'].get(key)
                print(f"DEBUG: No translation in {current_lang}, using English fallback: '{fallback}'")
                return fallback
            else:
                print(f"DEBUG: No translation found for key '{key}' in any language")
                return key
        else:
            # If key not found in translations, return the key itself
            print(f"DEBUG: Translation key '{key}' not found in translations dictionary")
            return key
    except Exception as e:
        print(f"DEBUG: Translation error for key '{key}': {e}")
        traceback.print_exc()
        return key

@app.context_processor
def utility_processor():
    return dict(translate=translate)

@app.before_request
def before_request():
    """Set up language and theme preference before each request"""
    try:
        # Make session permanent by default
        session.permanent = True
        
        # Print debug info before language detection
        print(f"DEBUG SESSION DATA: {session}")
        if current_user.is_authenticated:
            print(f"DEBUG USER DATA: id={current_user.id}, language={current_user.language}")
        
        # Determine language preference with this priority:
        # 1. Session (most immediate)
        # 2. Authenticated user's stored preference
        # 3. Cookie
        # 4. Default (Arabic)
        if 'language' in session:
            preferred_lang = session['language']
            print(f"DEBUG: Language from session: {preferred_lang}")
        elif current_user.is_authenticated and hasattr(current_user, 'language') and current_user.language:
            preferred_lang = current_user.language
            print(f"DEBUG: Language from user profile: {preferred_lang}")
        else:
            preferred_lang = request.cookies.get('language')
            print(f"DEBUG: Language from cookie: {preferred_lang}")
            
        # Validate language value
        if preferred_lang not in ['ar', 'en']:
            preferred_lang = 'ar'  # Default to Arabic if invalid
            print(f"DEBUG: Using default Arabic language")
        
        # Set the language in Flask's g object for this request
        g.lang = preferred_lang
        print(f"DEBUG: Final language set to {g.lang} for this request")
        
        # Set theme
        if current_user.is_authenticated and hasattr(current_user, 'theme'):
            g.theme = current_user.theme
        else:
            g.theme = request.cookies.get('theme', 'light')
            
        # Add language info to template context
        g.is_arabic = (g.lang == 'ar')
        g.is_english = (g.lang == 'en')
        print(f"DEBUG: is_arabic={g.is_arabic}, is_english={g.is_english}")
    except Exception as e:
        print(f"DEBUG: Error in before_request: {e}")
        traceback.print_exc()
        # Safe fallback
        g.lang = 'ar'
        g.theme = 'light'
        g.is_arabic = True
        g.is_english = False

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