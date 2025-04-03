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
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    language = db.Column(db.String(2), default='ar')  # ar or en
    theme = db.Column(db.String(10), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    verification_token = db.Column(db.String(100), nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Email verification fields
    verification_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    products = db.relationship('Product', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    # حقول PWA وإشعارات الويب
    push_subscription = db.Column(db.Text)  # تخزين بيانات اشتراك الإشعارات بتنسيق JSON
    notifications_enabled = db.Column(db.Boolean, default=False)
    device_info = db.Column(db.Text)  # معلومات الجهاز بتنسيق JSON (اختياري)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Generate a password reset token valid for 1 hour"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def generate_verification_token(self):
        """Generate an email verification token valid for 7 days (instead of 24 hours)"""
        self.verification_token = secrets.token_urlsafe(64)  # زيادة طول الرمز لتقليل احتمالية حدوث تكرار
        self.verification_token_expiry = datetime.utcnow() + timedelta(days=7)  # زيادة فترة الصلاحية من 24 ساعة إلى 7 أيام
        return self.verification_token
    
    def verify_reset_token(self, token):
        """Verify if the password reset token is valid"""
        if not self.reset_token or self.reset_token != token:
            return False
        if not self.reset_token_expiry or datetime.utcnow() > self.reset_token_expiry:
            return False
        return True
    
    def verify_verification_token(self, token):
        """Verify if the email verification token is valid"""
        if not self.verification_token or self.verification_token != token:
            return False
        if not self.verification_token_expiry or datetime.utcnow() > self.verification_token_expiry:
            return False
        return True
    
    def clear_reset_token(self):
        """Clear the password reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None
    
    def clear_verification_token(self):
        """Clear the email verification token after use"""
        self.verification_token = None
        self.verification_token_expiry = None
        self.email_verified = True
        
    def __repr__(self):
        return f'<User {self.username}>'

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