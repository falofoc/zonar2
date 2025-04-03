#!/usr/bin/env python3
"""
Utility script to set a user as admin so they can access the email testing page.
Run with: python set_admin.py <username>
"""

import sys
import os
from app import app, db
from app.models import User

def set_user_as_admin(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"Error: User '{username}' not found.")
            return False
            
        user.is_admin = True
        db.session.commit()
        print(f"Success! User '{username}' is now an admin.")
        return True
        
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    success = set_user_as_admin(username)
    
    if success:
        print(f"The user '{username}' can now access the email testing page at /email_testing")
    else:
        sys.exit(1) 