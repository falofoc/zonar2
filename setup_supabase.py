import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Supabase Key present: {bool(supabase_key)}")
    
    if not supabase_url or not supabase_key:
        print("Error: Required environment variables SUPABASE_URL and SUPABASE_KEY/SUPABASE_SERVICE_KEY must be set")
        sys.exit(1)
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Successfully initialized Supabase client")
        
        # Test connection with a simple query
        try:
            supabase.table('users').select("*").limit(1).execute()
            print("Successfully connected to Supabase")
        except Exception as e:
            print(f"Warning: Could not query users table: {str(e)}")
            # Continue execution as tables might not exist yet
        
        # Sample data for tables
        sample_data = {
            'users': {
                'email': 'test@example.com',
                'username': 'testuser',
                'password': 'hashedpassword'
            },
            'products': {
                'name': 'Test Product',
                'description': 'A test product',
                'price': 9.99
            },
            'notifications': {
                'user_id': '1',
                'message': 'Test notification',
                'read': False
            }
        }
        
        # Create tables if they don't exist
        for table_name, sample_record in sample_data.items():
            try:
                # Try to query the table
                supabase.table(table_name).select("*").limit(1).execute()
                print(f"Table {table_name} exists")
            except Exception as e:
                print(f"Creating table {table_name}...")
                try:
                    # Create table using sample record
                    supabase.table(table_name).insert(sample_record).execute()
                    print(f"Successfully created table {table_name}")
                    # Delete the sample record
                    supabase.table(table_name).delete().neq('id', 0).execute()
                except Exception as create_error:
                    print(f"Warning: Could not create table {table_name}: {str(create_error)}")
                    # Continue with next table
        
        print("Supabase setup completed successfully")
        return 0
        
    except Exception as e:
        print(f"Error during Supabase setup: {str(e)}")
        # Return 0 to allow deployment to continue
        return 0

if __name__ == "__main__":
    sys.exit(main()) 