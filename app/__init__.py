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
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

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

# Configure SQLAlchemy with PostgreSQL
# Get database URL from environment or use SQLite as fallback
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Render uses "postgres://" but SQLAlchemy needs "postgresql://"
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print(f"Using PostgreSQL database URL: {DATABASE_URL[:25]}...")
else:
    # Use SQLite for development (but PostgreSQL strongly recommended for production)
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    print(f"Using database URL: {DATABASE_URL}")

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verify connections before use to avoid stale connections
    'pool_recycle': 300,    # Recycle connections every 5 minutes
    'pool_timeout': 30,     # Connection timeout of 30 seconds
    'max_overflow': 10,     # Allow 10 connections above pool size
    'pool_size': 5          # Maintain 5 connections in the pool
}

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

# Initialize SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Migrate for database migrations
migrate = Migrate(app, db)

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

# Import models
from .models import User, Product, Notification

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add a health check endpoint
@app.route('/health')
def health_check():
    # Basic system health check
    db_status = "healthy"
    try:
        # Test DB connection
        db.session.execute("SELECT 1")
        db.session.commit()
    except Exception as e:
        db_status = f"error: {str(e)}"
        print(f"Database health check failed: {e}")
    
    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database_status': db_status,
        'environment': 'production' if is_production else 'development',
        'database_type': 'PostgreSQL' if 'postgresql' in str(app.config['SQLALCHEMY_DATABASE_URI']) else 'SQLite'
    }
    return jsonify(status)

# Add a simple index page for initial testing
@app.route('/')
def index():
    # Show a proper homepage
    try:
        # Try to count users to verify DB access (we'll still show the page even if this fails)
        user_count = User.query.count()
        print(f"Database connection successful: {user_count} users in database")
        db_connected = True
    except Exception as e:
        print(f"Error connecting to database: {e}")
        db_connected = False
    
    # Always show homepage with helpful information
    return """
    <html>
    <head>
        <title>Zonar - Product Price Tracker</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            .feature {
                background: #f9f9f9;
                border-left: 4px solid #3498db;
                margin: 20px 0;
                padding: 15px;
                border-radius: 4px;
            }
            .cta {
                background: #3498db;
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 4px;
                display: inline-block;
                margin-top: 20px;
                font-weight: bold;
            }
            .status {
                color: green;
                font-weight: bold;
            }
            .status.warning {
                color: orange;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to Zonar</h1>
        <p>Your ultimate product price tracker for Amazon and other online retailers.</p>
        
        <div class="feature">
            <h2>Track Product Prices</h2>
            <p>Add products from Amazon and other supported sites to track their prices over time.</p>
        </div>
        
        <div class="feature">
            <h2>Get Price Drop Alerts</h2>
            <p>Receive notifications when prices drop for your tracked products.</p>
        </div>
        
        <div class="feature">
            <h2>Analyze Price History</h2>
            <p>View price history charts to make informed purchasing decisions.</p>
        </div>
        
        <p>Status: <span class="status""" + (" warning" if not db_connected else "") + """">
            """ + ("Partially Active - Database Connection Issues" if not db_connected else "Fully Active") + """
        </span></p>
        <p>Server is running correctly! """ + ("Database connection needs attention." if not db_connected else "All features are available.") + """</p>
        
        <a href="/health" class="cta">Check Health Status</a>
    </body>
    </html>
    """

# Initialize the database if not already done
@app.before_first_request
def initialize_database():
    try:
        # Create tables if they don't exist
        db.create_all()
        print("Database tables created/verified successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        print("Application will continue but database features may be limited")

# Import routes
try:
    from . import routes
    print("Successfully imported routes")
except ImportError as e:
    print(f"Failed to import routes: {e}")
    print("Using minimal routes only") 