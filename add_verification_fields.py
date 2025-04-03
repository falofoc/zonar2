from app import app, db
from flask_migrate import Migrate
import sqlite3
import os

# Path to database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'amazon_tracker.db')

def add_missing_fields():
    """Add verification and notification fields to the users table"""
    try:
        print(f"Using database at: {DB_PATH}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Existing columns: {column_names}")
        
        # Add verification columns if they don't exist
        if 'verification_token_expiry' not in column_names:
            print("Adding verification_token_expiry column...")
            cursor.execute("ALTER TABLE users ADD COLUMN verification_token_expiry TIMESTAMP;")
            print("Column added successfully")
        else:
            print("verification_token_expiry column already exists")
            
        if 'reset_token_expiry' not in column_names:
            print("Adding reset_token_expiry column...")
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expiry TIMESTAMP;")
            print("Column added successfully")
        else:
            print("reset_token_expiry column already exists")
        
        # Add PWA notification columns
        if 'push_subscription' not in column_names:
            print("Adding push_subscription column...")
            cursor.execute("ALTER TABLE users ADD COLUMN push_subscription TEXT;")
            print("Column added successfully")
        else:
            print("push_subscription column already exists")
            
        if 'notifications_enabled' not in column_names:
            print("Adding notifications_enabled column...")
            cursor.execute("ALTER TABLE users ADD COLUMN notifications_enabled BOOLEAN DEFAULT 0;")
            print("Column added successfully")
        else:
            print("notifications_enabled column already exists")
            
        if 'device_info' not in column_names:
            print("Adding device_info column...")
            cursor.execute("ALTER TABLE users ADD COLUMN device_info TEXT;")
            print("Column added successfully")
        else:
            print("device_info column already exists")
        
        # Commit changes
        conn.commit()
        print("Changes committed successfully")
        
        # Close connection
        conn.close()
        print("Database connection closed")
        
        print("Database update completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the update
    add_missing_fields() 