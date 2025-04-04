import os
from dotenv import load_dotenv
from supabase import create_client
import time
import sys

# Load environment variables
load_dotenv()

def main():
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment")
        sys.exit(1)
    
    print(f"Connecting to Supabase...")
    
    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection
        supabase.auth.get_user()
        print("Successfully connected to Supabase")
        
        # Create tables
        create_tables(supabase)
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

def create_tables(supabase):
    """Create necessary tables in Supabase"""
    
    tables = {
        'users': {
            'sample': {
                'username': 'dummy_setup',
                'email': 'dummy_setup@example.com',
                'password_hash': 'dummy',
                'language': 'ar',
                'theme': 'light',
                'email_verified': False,
                'is_admin': False,
                'notifications_enabled': False
            }
        },
        'products': {
            'sample': {
                'url': 'https://example.com/dummy',
                'name': 'Dummy Product',
                'current_price': 0.0,
                'price_history': '[]',
                'tracking_enabled': True,
                'notify_on_any_change': False,
                'user_id': 0
            }
        },
        'notifications': {
            'sample': {
                'message': 'Dummy notification',
                'read': False,
                'user_id': 0
            }
        }
    }
    
    for table_name, config in tables.items():
        print(f"Checking '{table_name}' table...")
        try:
            # Try to query the table
            response = supabase.table(table_name).select('id').limit(1).execute()
            print(f"'{table_name}' table already exists.")
        except Exception as e:
            print(f"Creating '{table_name}' table...")
            try:
                # Try creating a dummy record
                supabase.table(table_name).insert(config['sample']).execute()
                print(f"'{table_name}' table created successfully!")
                
                # Delete the dummy record
                if 'username' in config['sample']:
                    supabase.table(table_name).delete().eq('username', config['sample']['username']).execute()
                elif 'name' in config['sample']:
                    supabase.table(table_name).delete().eq('name', config['sample']['name']).execute()
                elif 'message' in config['sample']:
                    supabase.table(table_name).delete().eq('message', config['sample']['message']).execute()
            except Exception as e:
                print(f"Warning: Could not create '{table_name}' table: {e}")
                print("Please ensure the table exists in Supabase dashboard")
    
    print("Table setup complete.")

if __name__ == "__main__":
    main() 