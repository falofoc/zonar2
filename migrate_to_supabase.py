import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# For Render deployment, use /tmp directory if we're in production
is_production = os.environ.get('RENDER', False)
if is_production:
    db_path = '/tmp/amazon_tracker.db'
    print(f"Using production database path: {db_path}")
else:
    instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "instance"))
    db_path = os.path.join(instance_path, "amazon_tracker.db")
    print(f"Using local database path: {db_path}")

def migrate_users():
    """Migrate users from SQLite to Supabase"""
    print("Migrating users...")
    
    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    for user in users:
        # Convert user to dictionary
        user_dict = dict(user)
        
        # Format dates as ISO strings
        if user_dict.get('created_at'):
            user_dict['created_at'] = datetime.fromisoformat(user_dict['created_at']).isoformat() if isinstance(user_dict['created_at'], str) else user_dict['created_at'].isoformat()
        
        if user_dict.get('reset_token_expiry'):
            user_dict['reset_token_expiry'] = datetime.fromisoformat(user_dict['reset_token_expiry']).isoformat() if isinstance(user_dict['reset_token_expiry'], str) else user_dict['reset_token_expiry'].isoformat()
            
        if user_dict.get('verification_token_expiry'):
            user_dict['verification_token_expiry'] = datetime.fromisoformat(user_dict['verification_token_expiry']).isoformat() if isinstance(user_dict['verification_token_expiry'], str) else user_dict['verification_token_expiry'].isoformat()
        
        # Insert user to Supabase
        try:
            supabase.table('users').insert(user_dict).execute()
            print(f"Migrated user: {user_dict['username']}")
        except Exception as e:
            print(f"Error migrating user {user_dict['username']}: {e}")
    
    conn.close()
    print("Users migration completed.")

def migrate_products():
    """Migrate products from SQLite to Supabase"""
    print("Migrating products...")
    
    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all products
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    
    for product in products:
        # Convert product to dictionary
        product_dict = dict(product)
        
        # Format dates as ISO strings
        if product_dict.get('created_at'):
            product_dict['created_at'] = datetime.fromisoformat(product_dict['created_at']).isoformat() if isinstance(product_dict['created_at'], str) else product_dict['created_at'].isoformat()
        
        if product_dict.get('last_checked'):
            product_dict['last_checked'] = datetime.fromisoformat(product_dict['last_checked']).isoformat() if isinstance(product_dict['last_checked'], str) else product_dict['last_checked'].isoformat()
        
        # Insert product to Supabase
        try:
            supabase.table('products').insert(product_dict).execute()
            print(f"Migrated product: {product_dict['name']}")
        except Exception as e:
            print(f"Error migrating product {product_dict['name']}: {e}")
    
    conn.close()
    print("Products migration completed.")

def migrate_notifications():
    """Migrate notifications from SQLite to Supabase"""
    print("Migrating notifications...")
    
    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all notifications
    cursor.execute("SELECT * FROM notification")
    notifications = cursor.fetchall()
    
    for notification in notifications:
        # Convert notification to dictionary
        notification_dict = dict(notification)
        
        # Format dates as ISO strings
        if notification_dict.get('created_at'):
            notification_dict['created_at'] = datetime.fromisoformat(notification_dict['created_at']).isoformat() if isinstance(notification_dict['created_at'], str) else notification_dict['created_at'].isoformat()
        
        # Insert notification to Supabase
        try:
            supabase.table('notifications').insert(notification_dict).execute()
            print(f"Migrated notification: {notification_dict['id']}")
        except Exception as e:
            print(f"Error migrating notification {notification_dict['id']}: {e}")
    
    conn.close()
    print("Notifications migration completed.")

def main():
    """Main migration function"""
    print("Starting migration from SQLite to Supabase...")
    
    # Check if SQLite database exists
    if not os.path.exists(db_path):
        print(f"SQLite database does not exist at {db_path}. Nothing to migrate.")
        return
    
    # Migrate data
    migrate_users()
    migrate_products()
    migrate_notifications()
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    main() 