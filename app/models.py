import json
import traceback
from datetime import datetime
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
    password_hash = db.Column(db.String(128), nullable=False)
    language = db.Column(db.String(10), default='ar')  # Default to Arabic
    theme = db.Column(db.String(10), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='user', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
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

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 