import os
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
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    # Print diagnostic information
    print("Environment variables:")
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_KEY present: {bool(os.getenv('SUPABASE_KEY'))}")
    print(f"SUPABASE_SERVICE_KEY present: {bool(os.getenv('SUPABASE_SERVICE_KEY'))}")
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is not set")
    if not supabase_key:
        raise ValueError("Neither SUPABASE_KEY nor SUPABASE_SERVICE_KEY environment variables are set")
    
    # Initialize and return Supabase client
    try:
        client = create_client(supabase_url, supabase_key)
        print("Successfully created Supabase client")
        return client
    except Exception as e:
        print(f"Error creating Supabase client: {str(e)}")
        raise

# Create a global client instance
try:
    supabase = get_supabase_client()
    print("Successfully initialized global Supabase client")
except ValueError as e:
    print(f"Warning: Failed to initialize Supabase client: {e}")
    supabase = None
except Exception as e:
    print(f"Error: Unexpected error initializing Supabase client: {str(e)}")
    supabase = None 