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
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is not set")
    if not supabase_key:
        raise ValueError("Neither SUPABASE_KEY nor SUPABASE_SERVICE_KEY environment variables are set")
    
    # Initialize and return Supabase client
    return create_client(supabase_url, supabase_key)

# Create a global client instance
try:
    supabase = get_supabase_client()
except ValueError as e:
    print(f"Warning: Failed to initialize Supabase client: {e}")
    supabase = None 