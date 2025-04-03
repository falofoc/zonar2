"""
This module exists to handle the case where Render tries to import 'your_application'.
It simply redirects to our actual app module.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our actual app safely
try:
    from app import app
except ImportError as e:
    # Print useful error information for debugging
    print(f"Error importing app in your_application/__init__.py: {e}")
    # Re-raise the exception to maintain normal error behavior
    raise 