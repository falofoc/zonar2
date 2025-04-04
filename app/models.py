import json
import traceback
from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON

# Import db from app
from app import db

class User(UserMixin, db.Model):
    """User model for SQLAlchemy"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(10), default='ar')
    theme = db.Column(db.String(20), default='light')
    created_at = db.Column(db.DateTime, default=func.now())
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    verification_token = db.Column(db.String(255), nullable=True)
    verification_token_expiry = db.Column(db.DateTime, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    notifications_enabled = db.Column(db.Boolean, default=False)
    push_subscription = db.Column(db.Text, nullable=True)
    device_info = db.Column(db.Text, nullable=True)
    
    # Relationships
    products = db.relationship('Product', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_active(self):
        return True
        
    @property
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        reset_token = secrets.token_urlsafe(32)
        self.reset_token = reset_token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return reset_token
    
    def generate_verification_token(self):
        verification_token = secrets.token_urlsafe(64)
        self.verification_token = verification_token
        self.verification_token_expiry = datetime.utcnow() + timedelta(days=7)
        db.session.commit()
        return verification_token
    
    def verify_reset_token(self, token):
        if not self.reset_token or self.reset_token != token:
            return False
            
        if not self.reset_token_expiry:
            return False
            
        if datetime.utcnow() > self.reset_token_expiry:
            return False
            
        return True
    
    def verify_verification_token(self, token):
        if not self.verification_token or self.verification_token != token:
            return False
            
        if not self.verification_token_expiry:
            return False
            
        if datetime.utcnow() > self.verification_token_expiry:
            return False
            
        return True
    
    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiry = None
        db.session.commit()
        return True
    
    def clear_verification_token(self):
        self.verification_token = None
        self.verification_token_expiry = None
        self.email_verified = True
        db.session.commit()
        return True
    
    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    """Product model for SQLAlchemy"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(1024), nullable=False)
    image_url = db.Column(db.String(1024), nullable=True)
    price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default='SAR')
    price_history = db.Column(db.Text, default='[]')  # JSON string
    target_price = db.Column(db.Float, nullable=True)
    custom_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    last_checked = db.Column(db.DateTime, default=func.now())
    track_price = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    @property
    def display_name(self):
        return self.custom_name if self.custom_name else self.name
    
    def get_price_history(self):
        try:
            return json.loads(self.price_history)
        except:
            return []
    
    def add_price_point(self, price, timestamp=None):
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
            
        history = self.get_price_history()
        history.append({
            'price': price,
            'timestamp': timestamp
        })
        
        # Keep only the last 100 price points
        if len(history) > 100:
            history = history[-100:]
            
        self.price_history = json.dumps(history)
        db.session.commit()
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Notification(db.Model):
    """Notification model for SQLAlchemy"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    notification_type = db.Column(db.String(50), default='price_drop')
    
    product = db.relationship('Product', backref='notifications')
    
    @classmethod
    def mark_all_as_read(cls, user_id):
        notifications = cls.query.filter_by(user_id=user_id, read=False).all()
        for notification in notifications:
            notification.read = True
        db.session.commit()
        return True
    
    def __repr__(self):
        return f'<Notification {self.id}>'

def init_db():
    """Initialize the database - can be called from scripts"""
    db.create_all()
    print("Database tables created successfully") 