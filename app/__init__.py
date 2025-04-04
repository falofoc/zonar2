import os
import json
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, g, session
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail

# Load environment variables
load_dotenv()

# Print environment variables for debugging
print("Environment variables at app startup:")
print(f"SUPABASE_URL present: {bool(os.environ.get('SUPABASE_URL'))}")
print(f"SUPABASE_KEY present: {bool(os.environ.get('SUPABASE_KEY'))}")
print(f"SUPABASE_SERVICE_KEY present: {bool(os.environ.get('SUPABASE_SERVICE_KEY'))}")

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')

# For Render deployment
is_production = os.environ.get('RENDER', False)

# Generate a more secure secret key
import secrets
secret_key = os.environ.get('SECRET_KEY', None)
if not secret_key:
    secret_key = secrets.token_hex(32)

# Configure Flask-Mail settings
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't', 'yes', 'y']
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't', 'yes', 'y']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', None)
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', None)
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', None)

# Security settings
app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_SECURE=is_production,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    DEBUG=not is_production
)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize CORS
CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "https://*.render.com"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
         "supports_credentials": True,
         "expose_headers": ["Content-Type", "Authorization"],
         "max_age": 3600
     }},
     supports_credentials=True)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = "strong"

# Initialize Supabase client - USING A FLAG TO MAKE IT OPTIONAL
ENABLE_SUPABASE = False

try:
    if ENABLE_SUPABASE:
        from .supabase_client import get_supabase_client
        supabase = get_supabase_client()
        if supabase is None:
            print("WARNING: Supabase client initialization returned None")
        else:
            print("Successfully initialized Supabase client")
    else:
        print("Supabase integration is disabled, skipping initialization")
        supabase = None
except Exception as e:
    print(f"ERROR initializing Supabase client: {str(e)}")
    print(f"Traceback: {traceback.format_exc()}")
    supabase = None

# Import translations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translations import translations

def translate(key):
    try:
        current_lang = getattr(g, 'lang', None)
        if not current_lang:
            current_lang = request.cookies.get('language')
        if not current_lang or current_lang not in ['ar', 'en']:
            current_lang = 'ar'
        
        if key in translations[current_lang]:
            return translations[current_lang][key]
        elif key in translations['en']:
            return translations['en'][key]
        else:
            return key
    except Exception as e:
        print(f"TRANSLATION ERROR: {e}")
        if key in translations['ar']:
            return translations['ar'][key]
        return key

@app.context_processor
def utility_processor():
    return dict(translate=translate)

@app.before_request
def before_request():
    if 'language' not in session and 'language' not in request.cookies:
        g.lang = 'ar'
        session['language'] = 'ar'
    else:
        lang = session.get('language') or request.cookies.get('language')
        if lang not in ['ar', 'en']:
            lang = 'ar'
            session['language'] = 'ar'
        g.lang = lang
    
    if current_user.is_authenticated and hasattr(current_user, 'theme'):
        g.theme = current_user.theme
    else:
        g.theme = request.cookies.get('theme', 'light')
    
    g.is_arabic = (g.lang == 'ar')
    g.is_english = (g.lang == 'en')

# Import Supabase models conditionally
if ENABLE_SUPABASE:
    try:
        from .supabase_models import SupabaseUser, SupabaseProduct, SupabaseNotification
    except ImportError as e:
        print(f"Failed to import Supabase models: {e}")
        
        # Define mock User class as fallback
        class SupabaseUser(UserMixin):
            def __init__(self, id=None, username=None, email=None):
                self.id = id
                self.username = username
                self.email = email
                self.theme = 'light'
                
            @staticmethod
            def get_by_id(user_id):
                print(f"Mock get_by_id called with {user_id}")
                return None
else:
    # Define mock User class
    class SupabaseUser(UserMixin):
        def __init__(self, id=None, username=None, email=None):
            self.id = id
            self.username = username
            self.email = email
            self.theme = 'light'
            
        @staticmethod
        def get_by_id(user_id):
            print(f"Mock get_by_id called with {user_id}")
            return None

@login_manager.user_loader
def load_user(id):
    if ENABLE_SUPABASE:
        return SupabaseUser.get_by_id(int(id))
    return None

# Add a health check endpoint
@app.route('/health')
def health_check():
    # Basic system health check
    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'supabase_available': supabase is not None,
        'environment': 'production' if is_production else 'development'
    }
    return jsonify(status)

# Add a simple index page for initial testing
@app.route('/')
def index():
    return """
    <html>
    <head><title>Zonar - Under Construction</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
        <h1>Zonar</h1>
        <p>This site is currently under construction.</p>
        <p>The server is running correctly!</p>
        <p>Status: <span style="color: green; font-weight: bold;">Active</span></p>
        <p><a href="/health">Health Check</a></p>
    </body>
    </html>
    """

# Initialize Supabase tables if they don't exist (but only if Supabase is enabled)
def init_supabase_tables():
    if not ENABLE_SUPABASE or supabase is None:
        print("WARNING: Skipping table initialization because Supabase is disabled")
        return
        
    try:
        print("Checking Supabase tables...")
        tables = ['users', 'products', 'notifications']
        for table in tables:
            try:
                result = supabase.table(table).select('id').limit(1).execute()
                print(f"Table '{table}' exists and is accessible")
            except Exception as table_error:
                print(f"Could not access table '{table}': {str(table_error)}")
                print("This is expected during first deployment")
        
        print("Supabase table check completed")
    except Exception as e:
        print(f"Error during table initialization: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        print("Continuing despite table initialization error")

# Initialize Supabase tables
try:
    if ENABLE_SUPABASE:
        init_supabase_tables()
    else:
        print("Skipping Supabase table initialization")
except Exception as e:
    print(f"Failed to initialize tables but continuing: {str(e)}")

# Import routes conditionally to avoid errors
if ENABLE_SUPABASE:
    try:
        from . import routes
        print("Successfully imported routes")
    except ImportError as e:
        print(f"Failed to import routes: {e}")
        print("Using minimal routes only")
else:
    print("Skipping import of main routes since Supabase is disabled") 