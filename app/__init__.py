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
from logging.handlers import RotatingFileHandler
import logging
from translations import TRANSLATIONS as translations_dict

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

    # Verify user session
    if current_user.is_authenticated:
        # Get the stored session token from the session
        session_token = session.get('user_session_token')
        
        # Update user's last_active timestamp
        current_user.last_active = datetime.utcnow()
        db.session.commit()
        
        # Check if the token is valid for this user
        if not session_token or not current_user.verify_session_token(session_token):
            # Session is invalid - user may be logged in elsewhere
            # This won't run for endpoints exempted from login requirements
            if not request.endpoint or request.endpoint not in ['logout', 'login', 'static']:
                # Forcibly logout the user
                logout_user()
                session.pop('user_session_token', None)
                session['flash_message'] = {
                    'message': translate('session_expired_elsewhere'),
                    'category': 'warning'
                }
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # For AJAX requests, return a JSON response
                    return jsonify({
                        'success': False,
                        'message': translate('session_expired_elsewhere'),
                        'redirect': '/login'
                    }), 401
                else:
                    # For regular requests, redirect to login
                    return redirect(url_for('login'))

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

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)

# Import models and routes
from app.models import User, Product

# Create the database tables
with app.app_context():
    db.create_all()

from app import routes 

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Load translations
    with app.app_context():
        # Import translations here to avoid circular import
        from translations import TRANSLATIONS
        try:
            # Import bot translations if available
            from bot_translations import BOT_TRANSLATIONS
            # Merge bot translations with main translations
            for lang in BOT_TRANSLATIONS:
                if lang in TRANSLATIONS:
                    TRANSLATIONS[lang].update(BOT_TRANSLATIONS[lang])
        except ImportError:
            # Bot translations not available
            pass
        
        app.config['TRANSLATIONS'] = TRANSLATIONS
    
    # Import routes
    from app.routes import init_routes
    init_routes(app)
    
    # Register blueprints
    try:
        # Register bot blueprint if available
        from bot_routes import bot_bp
        app.register_blueprint(bot_bp)
    except ImportError:
        # Bot routes not available
        pass
    
    # Set up login manager
    login_manager.login_view = 'login'
    
    # ... (rest of the function) ... 