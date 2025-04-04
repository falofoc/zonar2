import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from .supabase_client import get_supabase_client

# Initialize supabase with error handling
try:
    supabase = get_supabase_client()
except Exception as e:
    print(f"WARNING: Failed to initialize supabase in models: {str(e)}")
    supabase = None

class SupabaseUser(UserMixin):
    """
    User model adapted for Supabase instead of SQLAlchemy
    """
    def __init__(self, user_data: Dict[str, Any]):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')
        self.language = user_data.get('language', 'ar')
        self.theme = user_data.get('theme', 'light')
        self.created_at = user_data.get('created_at')
        self.reset_token = user_data.get('reset_token')
        self.reset_token_expiry = user_data.get('reset_token_expiry')
        self.verification_token = user_data.get('verification_token')
        self.email_verified = user_data.get('email_verified', False)
        self.is_admin = user_data.get('is_admin', False)
        self.verification_token_expiry = user_data.get('verification_token_expiry')
        self.push_subscription = user_data.get('push_subscription')
        self.notifications_enabled = user_data.get('notifications_enabled', False)
        self.device_info = user_data.get('device_info')
        
    @staticmethod
    def get_by_id(user_id: int) -> Optional['SupabaseUser']:
        """Get user by ID"""
        if not supabase:
            print("Supabase client not available in get_by_id")
            return None
            
        try:
            # Old version API compatibility
            response = supabase.table('users').select('*').eq('id', user_id).execute()
            
            # In older versions, data might be directly in response
            data = getattr(response, 'data', response)
            
            if data and len(data) > 0:
                return SupabaseUser(data[0])
            return None
        except Exception as e:
            print(f"Error in get_by_id: {str(e)}")
            return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional['SupabaseUser']:
        """Get user by email"""
        if not supabase:
            return None
            
        try:
            response = supabase.table('users').select('*').eq('email', email).execute()
            
            # In older versions, data might be directly in response
            data = getattr(response, 'data', response)
            
            if data and len(data) > 0:
                return SupabaseUser(data[0])
            return None
        except Exception as e:
            print(f"Error in get_by_email: {str(e)}")
            return None
    
    @staticmethod
    def get_by_username(username: str) -> Optional['SupabaseUser']:
        """Get user by username"""
        response = supabase.table('users').select('*').eq('username', username).execute()
        
        if response.data and len(response.data) > 0:
            return SupabaseUser(response.data[0])
        return None
        
    @staticmethod
    def create(username: str, email: str, password: str) -> 'SupabaseUser':
        """Create a new user"""
        password_hash = generate_password_hash(password)
        
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'language': 'ar',
            'theme': 'light',
            'created_at': datetime.utcnow().isoformat(),
            'email_verified': False,
            'is_admin': False,
            'notifications_enabled': False
        }
        
        response = supabase.table('users').insert(user_data).execute()
        
        if response.data and len(response.data) > 0:
            return SupabaseUser(response.data[0])
        return None
    
    def update(self, data: Dict[str, Any]) -> bool:
        """Update user data"""
        response = supabase.table('users').update(data).eq('id', self.id).execute()
        
        if response.data and len(response.data) > 0:
            # Update local attributes
            for key, value in data.items():
                setattr(self, key, value)
            return True
        return False
    
    def set_password(self, password: str) -> bool:
        """Set user password"""
        password_hash = generate_password_hash(password)
        return self.update({'password_hash': password_hash})
    
    def check_password(self, password: str) -> bool:
        """Check if password is correct"""
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self) -> str:
        """Generate a password reset token valid for 1 hour"""
        reset_token = secrets.token_urlsafe(32)
        reset_token_expiry = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        self.update({
            'reset_token': reset_token,
            'reset_token_expiry': reset_token_expiry
        })
        
        return reset_token
    
    def generate_verification_token(self) -> str:
        """Generate an email verification token valid for 7 days"""
        verification_token = secrets.token_urlsafe(64)
        verification_token_expiry = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        self.update({
            'verification_token': verification_token,
            'verification_token_expiry': verification_token_expiry
        })
        
        return verification_token
    
    def verify_reset_token(self, token: str) -> bool:
        """Verify if the password reset token is valid"""
        if not self.reset_token or self.reset_token != token:
            return False
            
        if not self.reset_token_expiry:
            return False
            
        expiry = datetime.fromisoformat(self.reset_token_expiry) if isinstance(self.reset_token_expiry, str) else self.reset_token_expiry
        if datetime.utcnow() > expiry:
            return False
            
        return True
    
    def verify_verification_token(self, token: str) -> bool:
        """Verify if the email verification token is valid"""
        if not self.verification_token or self.verification_token != token:
            return False
            
        if not self.verification_token_expiry:
            return False
            
        expiry = datetime.fromisoformat(self.verification_token_expiry) if isinstance(self.verification_token_expiry, str) else self.verification_token_expiry
        if datetime.utcnow() > expiry:
            return False
            
        return True
    
    def clear_reset_token(self) -> bool:
        """Clear the password reset token after use"""
        return self.update({
            'reset_token': None,
            'reset_token_expiry': None
        })
    
    def clear_verification_token(self) -> bool:
        """Clear the email verification token after use"""
        return self.update({
            'verification_token': None,
            'verification_token_expiry': None,
            'email_verified': True
        })
    
    def get_products(self) -> List[Dict[str, Any]]:
        """Get all products associated with this user"""
        response = supabase.table('products').select('*').eq('user_id', self.id).execute()
        return response.data if response.data else []
    
    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get all notifications associated with this user"""
        response = supabase.table('notifications').select('*').eq('user_id', self.id).execute()
        return response.data if response.data else []
        
    def __repr__(self) -> str:
        return f'<User {self.username}>'


class SupabaseProduct:
    """
    Product model adapted for Supabase
    """
    @staticmethod
    def get_by_id(product_id: int) -> Dict[str, Any]:
        """Get product by ID"""
        response = supabase.table('products').select('*').eq('id', product_id).execute()
        return response.data[0] if response.data and len(response.data) > 0 else None
    
    @staticmethod
    def get_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        """Get all products for a user"""
        response = supabase.table('products').select('*').eq('user_id', user_id).execute()
        return response.data if response.data else []
    
    @staticmethod
    def create(product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product"""
        if 'created_at' not in product_data:
            product_data['created_at'] = datetime.utcnow().isoformat()
            
        if 'last_checked' not in product_data:
            product_data['last_checked'] = datetime.utcnow().isoformat()
            
        response = supabase.table('products').insert(product_data).execute()
        return response.data[0] if response.data and len(response.data) > 0 else None
    
    @staticmethod
    def update(product_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a product"""
        response = supabase.table('products').update(data).eq('id', product_id).execute()
        return response.data[0] if response.data and len(response.data) > 0 else None
    
    @staticmethod
    def delete(product_id: int) -> bool:
        """Delete a product"""
        response = supabase.table('products').delete().eq('id', product_id).execute()
        return len(response.data) > 0 if response.data else False
    
    @staticmethod
    def get_display_name(product: Dict[str, Any]) -> str:
        """Return custom name if available, otherwise product name"""
        return product.get('custom_name') if product.get('custom_name') else product.get('name')
    
    @staticmethod
    def get_price_history(product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get price history for a product"""
        price_history = product.get('price_history', '[]')
        
        if not price_history:
            return []
        
        history = json.loads(price_history if isinstance(price_history, str) else '[]')
        return history


class SupabaseNotification:
    """
    Notification model adapted for Supabase
    """
    @staticmethod
    def get_by_id(notification_id: int) -> Dict[str, Any]:
        """Get notification by ID"""
        response = supabase.table('notifications').select('*').eq('id', notification_id).execute()
        return response.data[0] if response.data and len(response.data) > 0 else None
    
    @staticmethod
    def get_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        """Get all notifications for a user"""
        response = supabase.table('notifications').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return response.data if response.data else []
    
    @staticmethod
    def create(notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notification"""
        if 'created_at' not in notification_data:
            notification_data['created_at'] = datetime.utcnow().isoformat()
            
        if 'read' not in notification_data:
            notification_data['read'] = False
            
        response = supabase.table('notifications').insert(notification_data).execute()
        return response.data[0] if response.data and len(response.data) > 0 else None
    
    @staticmethod
    def mark_as_read(notification_id: int) -> Dict[str, Any]:
        """Mark a notification as read"""
        response = supabase.table('notifications').update({'read': True}).eq('id', notification_id).execute()
        return response.data[0] if response.data and len(response.data) > 0 else None
    
    @staticmethod
    def mark_all_as_read(user_id: int) -> bool:
        """Mark all notifications as read for a user"""
        response = supabase.table('notifications').update({'read': True}).eq('user_id', user_id).execute()
        return len(response.data) > 0 if response.data else False
    
    @staticmethod
    def delete(notification_id: int) -> bool:
        """Delete a notification"""
        response = supabase.table('notifications').delete().eq('id', notification_id).execute()
        return len(response.data) > 0 if response.data else False 