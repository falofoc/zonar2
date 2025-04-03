import json
import traceback
from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True) # Nullable for social logins
    language = db.Column(db.String(10), default='ar') # Default language set to Arabic
    theme = db.Column(db.String(10), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Fields for Google OAuth
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)

    # Field for Firebase Authentication
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True, index=True)
    
    # Relationships
    products = db.relationship('Product', backref='owner', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Generate a password reset token valid for 1 hour"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def generate_verification_token(self):
        """Generate an email verification token valid for 24 hours"""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        return self.verification_token
    
    def verify_reset_token(self, token):
        """Verify if the password reset token is valid"""
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return True
    
    def verify_verification_token(self, token):
        """Verify if the email verification token is valid"""
        if self.verification_token != token:
            return False
        if datetime.utcnow() > self.verification_token_expires:
            return False
        return True
    
    def clear_reset_token(self):
        """Clear the password reset token after use"""
        self.reset_token = None
        self.reset_token_expires = None
    
    def clear_verification_token(self):
        """Clear the email verification token after use"""
        self.verification_token = None
        self.verification_token_expires = None
        self.email_verified = True
        
    def __repr__(self):
        return f'<User {self.username}>'

    @staticmethod
    def get_or_create_google_user(google_data):
        # Try to find user by Google ID
        user = User.query.filter_by(google_id=google_data['sub']).first()
        if user:
            # Update profile picture if necessary
            if user.profile_pic != google_data.get('picture'):
                user.profile_pic = google_data.get('picture')
                db.session.commit()
            return user
        
        # Try to find user by email
        user = User.query.filter_by(email=google_data['email']).first()
        if user:
            # Link Google ID to existing email account
            user.google_id = google_data['sub']
            user.profile_pic = google_data.get('picture')
            user.email_verified = google_data.get('email_verified', False)
            db.session.commit()
            return user
        
        # If user not found by ID or email, create a new user
        new_user = User(
            google_id=google_data['sub'],
            email=google_data['email'],
            username=google_data.get('name', google_data['email'].split('@')[0]), # Use name or part of email
            profile_pic=google_data.get('picture'),
            email_verified=google_data.get('email_verified', False), # Set based on Google verification
            # No password hash needed for Google login initially
            password_hash=None 
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"Created new user via Google OAuth: {new_user.email}")
        return new_user

    # Add similar method for Firebase if needed later
    @staticmethod
    def get_or_create_firebase_user(firebase_user_info):
        # Find user by Firebase UID
        user = User.query.filter_by(firebase_uid=firebase_user_info['uid']).first()
        if user:
            # Update user info if necessary (e.g., email verification status, photo)
            updated = False
            if user.email_verified != firebase_user_info.get('email_verified', False):
                user.email_verified = firebase_user_info.get('email_verified', False)
                updated = True
            if user.profile_pic != firebase_user_info.get('photo_url'):
                user.profile_pic = firebase_user_info.get('photo_url')
                updated = True
            if updated:
                db.session.commit()
            return user
        
        # Try finding user by email (if provided by Firebase)
        if firebase_user_info.get('email'):
            user = User.query.filter_by(email=firebase_user_info['email']).first()
            if user:
                # Link Firebase UID to existing email account
                user.firebase_uid = firebase_user_info['uid']
                user.email_verified = firebase_user_info.get('email_verified', False)
                user.profile_pic = firebase_user_info.get('photo_url')
                db.session.commit()
                return user

        # Create new user if not found
        new_user = User(
            firebase_uid=firebase_user_info['uid'],
            email=firebase_user_info.get('email'),
            username=firebase_user_info.get('display_name', firebase_user_info.get('email', firebase_user_info['uid'])),
            profile_pic=firebase_user_info.get('photo_url'),
            email_verified=firebase_user_info.get('email_verified', False),
            password_hash=None # No password needed for Firebase auth initially
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"Created new user via Firebase Auth: {new_user.email or new_user.username}")
        return new_user

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    custom_name = db.Column(db.String(200))
    current_price = db.Column(db.Float, nullable=False)
    target_price = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    price_history = db.Column(db.Text, default='[]')  # JSON string of price history
    tracking_enabled = db.Column(db.Boolean, default=True)
    notify_on_any_change = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_display_name(self):
        return self.custom_name if self.custom_name else self.name
        
    def get_price_history(self):
        if not self.price_history:
            return []
        
        history = json.loads(self.price_history)
        # Convert string dates to datetime objects
        for entry in history:
            entry['date'] = datetime.fromisoformat(entry['date'])
        
        return history
        
    # Properties for template compatibility
    @property
    def tracking(self):
        return self.tracking_enabled
        
    @property
    def notify_always(self):
        return self.notify_on_any_change

    @property
    def display_name(self):
        """Return custom name if available, otherwise product name"""
        return self.custom_name if self.custom_name else self.name

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 