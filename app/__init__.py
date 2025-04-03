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
from flask_mail import Mail

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

# Generate a more secure secret key
import secrets
secret_key = os.environ.get('SECRET_KEY', None)
if not secret_key:
    secret_key = secrets.token_hex(32)  # 32 bytes = 256 bits

# Configure Flask-Mail settings
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't', 'yes', 'y']
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't', 'yes', 'y']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', None)
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', None)
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', None)

# Security settings with improved session handling
app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_SECURE=is_production,  # Use secure cookies in production
    SESSION_COOKIE_HTTPONLY=True,  # Enable HTTPOnly for security
    SESSION_COOKIE_SAMESITE='Lax',   # Use Lax for better security while still allowing cross-site
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),  # Longer session lifetime
    DEBUG=not is_production
)

# Initialize Flask-Mail
mail = Mail(app)

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

# Initialize login manager with relaxed settings
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = "strong"  # Enable strong session protection

# Initialize Supabase client
from .supabase_client import get_supabase_client
supabase = get_supabase_client()

# Import all other components AFTER the app is created
import sys
import os
# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Now import translations should work
from translations import translations

# This defines the translate function that's used in templates
def translate(key):
    """Translate a key to the current language with better error handling"""
    try:
        # FORCE simple approach - directly access g if possible
        current_lang = getattr(g, 'lang', None)
        
        # If g.lang is not set, try to get from request
        if not current_lang:
            current_lang = request.cookies.get('language')
            
        # Still nothing? Default to Arabic
        if not current_lang or current_lang not in ['ar', 'en']:
            current_lang = 'ar'
            
        print(f"TRANSLATING '{key}' FOR LANGUAGE '{current_lang}'")
        
        # Get translation directly with fallbacks
        if key in translations[current_lang]:
            result = translations[current_lang][key]
            print(f"FOUND TRANSLATION: {result}")
            return result
        elif key in translations['en']:
            result = translations['en'][key]
            print(f"FALLBACK TO EN: {result}")
            return result
        else:
            print(f"NO TRANSLATION FOR: {key}")
            return key
    except Exception as e:
        print(f"TRANSLATION ERROR: {e}")
        if key in translations['ar']:
            return translations['ar'][key]
        return key

@app.context_processor
def utility_processor():
    """Add helper functions to template context"""
    return dict(translate=translate)

@app.before_request
def before_request():
    """Set language preference before each request"""
    # ALWAYS force Arabic if none specified
    if 'language' not in session and 'language' not in request.cookies:
        print("FORCING ARABIC BY DEFAULT - NO LANGUAGE SPECIFIED")
        g.lang = 'ar'
        session['language'] = 'ar'
    else:
        # Get language from session or cookies
        lang = session.get('language') or request.cookies.get('language')
        if lang not in ['ar', 'en']:
            print(f"INVALID LANGUAGE '{lang}' - FORCING ARABIC")
            lang = 'ar'
            session['language'] = 'ar'
        g.lang = lang
        
    print(f"LANGUAGE SET TO: {g.lang}")
    
    # Set theme
    if current_user.is_authenticated and hasattr(current_user, 'theme'):
        g.theme = current_user.theme
    else:
        g.theme = request.cookies.get('theme', 'light')
        
    # Arabic language flags for templates
    g.is_arabic = (g.lang == 'ar')
    g.is_english = (g.lang == 'en')
    print(f"CURRENT STATE: AR={g.is_arabic}, EN={g.is_english}")

# Import Supabase models
from .supabase_models import SupabaseUser, SupabaseProduct, SupabaseNotification

@login_manager.user_loader
def load_user(id):
    return SupabaseUser.get_by_id(int(id))

# Initialize Supabase tables if they don't exist
def init_supabase_tables():
    """
    Create Supabase tables if they don't exist
    """
    try:
        # Check if tables exist by attempting to select from them
        # If they don't exist, this will raise an exception
        supabase.table('users').select('id').limit(1).execute()
        supabase.table('products').select('id').limit(1).execute()
        supabase.table('notifications').select('id').limit(1).execute()
        print("Supabase tables already exist")
    except Exception as e:
        print(f"Error checking tables: {e}")
        print("Creating Supabase tables...")
        
        try:
            # Create users table
            supabase.table('users').insert({
                'id': 0,  # This is a dummy record that will be deleted
                'username': 'dummy',
                'email': 'dummy@example.com',
                'password_hash': 'dummy',
                'language': 'ar',
                'theme': 'light',
                'created_at': datetime.utcnow().isoformat(),
                'email_verified': False,
                'is_admin': False
            }).execute()
            
            # Create products table
            supabase.table('products').insert({
                'id': 0,  # This is a dummy record that will be deleted
                'url': 'https://example.com',
                'name': 'Dummy Product',
                'current_price': 0.0,
                'user_id': 0,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            # Create notifications table
            supabase.table('notifications').insert({
                'id': 0,  # This is a dummy record that will be deleted
                'message': 'Dummy notification',
                'read': False,
                'created_at': datetime.utcnow().isoformat(),
                'user_id': 0
            }).execute()
            
            # Delete dummy records
            supabase.table('users').delete().eq('id', 0).execute()
            supabase.table('products').delete().eq('id', 0).execute()
            supabase.table('notifications').delete().eq('id', 0).execute()
            
            print("Supabase tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")
            traceback.print_exc()

# Initialize Supabase tables
init_supabase_tables()

# Now import the routes
try:
    from . import routes
except ImportError:
    # Handle case when relative import fails
    import app.routes 