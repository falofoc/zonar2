"""
This module exists to handle the case where Render tries to import 'your_application'.
It simply redirects to our actual app module.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our actual app
from app import app 