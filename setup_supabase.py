import os
from dotenv import load_dotenv
from supabase import create_client
import time

# Load environment variables
load_dotenv()

def main():
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return
    
    print(f"Connecting to Supabase at {supabase_url}")
    
    # Initialize Supabase client
    supabase = create_client(supabase_url, supabase_key)
    
    # Create tables
    create_tables(supabase)

def create_tables(supabase):
    """Create necessary tables in Supabase"""
    
    # Create users table if it doesn't exist
    print("Creating 'users' table...")
    try:
        # Try to query the users table
        response = supabase.table('users').select('id').limit(1).execute()
        print("'users' table already exists.")
    except Exception as e:
        print(f"Creating 'users' table: {e}")
        try:
            # For Supabase, we need to use a different approach to execute SQL
            # Try creating a dummy record in the table - if it fails, we'll need to use a different approach
            supabase.table('users').insert({
                'username': 'dummy_setup',
                'email': 'dummy_setup@example.com',
                'password_hash': 'dummy',
                'language': 'ar',
                'theme': 'light',
                'email_verified': False,
                'is_admin': False,
                'notifications_enabled': False
            }).execute()
            print("'users' table created successfully!")
            
            # Now delete the dummy record
            supabase.table('users').delete().eq('username', 'dummy_setup').execute()
        except Exception as e:
            print(f"Error creating users table: {e}")
            print("Please create the tables manually in the Supabase dashboard.")
            print("See SUPABASE_SETUP.md for schema details.")
    
    # Create products table if it doesn't exist
    print("Creating 'products' table...")
    try:
        response = supabase.table('products').select('id').limit(1).execute()
        print("'products' table already exists.")
    except Exception as e:
        print(f"Creating 'products' table: {e}")
        try:
            # Try creating a dummy record in the table
            supabase.table('products').insert({
                'url': 'https://example.com/dummy',
                'name': 'Dummy Product',
                'current_price': 0.0,
                'price_history': '[]',
                'tracking_enabled': True,
                'notify_on_any_change': False,
                'user_id': 0
            }).execute()
            print("'products' table created successfully!")
            
            # Now delete the dummy record
            supabase.table('products').delete().eq('name', 'Dummy Product').execute()
        except Exception as e:
            print(f"Error creating products table: {e}")
            print("Please create the tables manually in the Supabase dashboard.")
            print("See SUPABASE_SETUP.md for schema details.")
    
    # Create notifications table if it doesn't exist
    print("Creating 'notifications' table...")
    try:
        response = supabase.table('notifications').select('id').limit(1).execute()
        print("'notifications' table already exists.")
    except Exception as e:
        print(f"Creating 'notifications' table: {e}")
        try:
            # Try creating a dummy record in the table
            supabase.table('notifications').insert({
                'message': 'Dummy notification',
                'read': False,
                'user_id': 0
            }).execute()
            print("'notifications' table created successfully!")
            
            # Now delete the dummy record
            supabase.table('notifications').delete().eq('message', 'Dummy notification').execute()
        except Exception as e:
            print(f"Error creating notifications table: {e}")
            print("Please create the tables manually in the Supabase dashboard.")
            print("See SUPABASE_SETUP.md for schema details.")
    
    print("Table setup complete.")

if __name__ == "__main__":
    main() 