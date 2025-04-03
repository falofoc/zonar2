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
from flask_mail import Mail, Message
import firebase_admin
from firebase_admin import credentials, auth

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

# Configure Flask-Mail settings
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't', 'yes', 'y']
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't', 'yes', 'y']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', None)
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', None)
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', None)
app.config['MAIL_DEBUG'] = os.environ.get('MAIL_DEBUG', 'false').lower() == 'true' # Log email sending errors

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

# Initialize Flask-Mail
mail = Mail(app)

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

    # Fetch unread notifications count for authenticated users
    if current_user.is_authenticated:
        try:
            unread_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
        except Exception as e:
            print(f"Error fetching notification count: {e}")
            unread_count = 0 # Default to 0 on error
        g.unread_count = unread_count
    else:
        g.unread_count = 0

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

def create_app():
    load_dotenv() # Load environment variables from .env file

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'a_very_secret_key' # Replace with a strong secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    
    # Mail Configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('true', '1', 't')
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('true', '1', 't')
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_DEBUG'] = os.environ.get('MAIL_DEBUG', 'false').lower() == 'true' # Log email sending errors
    
    # Ensure necessary email variables are set
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        print("WARNING: MAIL_USERNAME or MAIL_PASSWORD environment variables are not set. Email features may not work.")

    # Firebase Admin SDK Initialization
    try:
        # Path to your service account key file (from environment variable)
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if cred_path:
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialized successfully using service account file.")
            else:
                print(f"WARNING: Service account key file not found at path specified in GOOGLE_APPLICATION_CREDENTIALS: {cred_path}")
                print("Firebase Admin SDK will not be initialized.")
        else:
            print("WARNING: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
            print("Firebase Admin SDK will not be initialized.")
    except Exception as e:
        print(f"ERROR initializing Firebase Admin SDK: {e}")
        print(traceback.format_exc())

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    CORS(app) # Enable CORS for all routes
    mail = Mail(app)

    login_manager.login_view = 'login' # Redirect to login page if user is not logged in
    login_manager.login_message = translations['en']['login_required_message'] # Default message
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def before_request():
        g.lang = request.accept_languages.best_match(['en', 'ar']) or 'ar' # Default to Arabic
        if current_user.is_authenticated and hasattr(current_user, 'language') and current_user.language:
            g.lang = current_user.language
            
        # Fetch unread notifications count for authenticated users
        if current_user.is_authenticated:
            try:
                unread_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
            except Exception as e:
                print(f"Error fetching notification count: {e}")
                unread_count = 0 # Default to 0 on error
            g.unread_count = unread_count
        else:
            g.unread_count = 0

    @app.context_processor
    def inject_global_vars():
        return {
            'translate': lambda key: translations.get(g.lang, translations['ar']).get(key, key),
            'current_lang': g.lang,
            'unread_count': getattr(g, 'unread_count', 0), # Provide default value
            'GOOGLE_CLIENT_ID': os.environ.get('GOOGLE_CLIENT_ID') # Make Google Client ID available
        }

    # Register routes
    from . import routes
    app.register_blueprint(routes.bp)

    # Initialize scheduler if not already initialized
    if not scheduler.running:
        print("Initializing scheduler...")
        try:
            scheduler.init_app(app)
            scheduler.start()
            print("Scheduler started successfully.")
        except Exception as e:
            print(f"Error initializing or starting scheduler: {e}")
            print(traceback.format_exc())
    else:
        print("Scheduler is already running.")

    return app

# Initialize extensions globally for use in routes etc.
mail = Mail() 