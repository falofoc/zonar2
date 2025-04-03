import os
import sys
from app import app, db
from app.models import User

def create_admin_user(username, password):
    """Create or update the admin user"""
    with app.app_context():
        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"Updating existing user '{username}' to admin...")
            user.is_admin = True
            user.email_verified = True
            if password:
                user.set_password(password)
        else:
            print(f"Creating new admin user '{username}'...")
            user = User(
                username=username, 
                email=f"{username}@zonar.local",
                is_admin=True,
                email_verified=True
            )
            user.set_password(password)
            db.session.add(user)
        
        db.session.commit()
        print(f"Admin user '{username}' has been set up successfully!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    create_admin_user(username, password) 