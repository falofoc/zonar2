import os
import traceback
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client():
    """
    Returns the initialized Supabase client.
    
    Returns:
        The Supabase client instance
    Raises:
        ValueError: If required environment variables are not set
    """
    # Get Supabase credentials from environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    
    # Print diagnostic information
    print("\nSupabase Configuration:")
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_KEY present: {bool(os.environ.get('SUPABASE_KEY'))}")
    print(f"SUPABASE_SERVICE_KEY present: {bool(os.environ.get('SUPABASE_SERVICE_KEY'))}")
    print(f"Using key type: {'service_key' if os.environ.get('SUPABASE_SERVICE_KEY') else 'anon_key'}")
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is not set")
    if not supabase_key:
        raise ValueError("Neither SUPABASE_KEY nor SUPABASE_SERVICE_KEY environment variables are set")
    
    # Initialize and return Supabase client
    try:
        client = create_client(supabase_url, supabase_key)
        print("Successfully created Supabase client")
        
        # Test connection
        try:
            client.table('users').select("count", count='exact').execute()
            print("Successfully tested Supabase connection")
        except Exception as test_error:
            print(f"Warning: Could not test connection: {str(test_error)}")
            print("This is expected if tables don't exist yet")
            
        return client
    except Exception as e:
        print(f"Error creating Supabase client: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise

# Create a global client instance
try:
    supabase = get_supabase_client()
    print("Successfully initialized global Supabase client")
except Exception as e:
    print(f"Warning: Failed to initialize Supabase client: {e}")
    print("Application will continue with limited functionality")
    supabase = None 