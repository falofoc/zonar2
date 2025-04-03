from app import app, db
from app.models import User
from flask_login import login_user, current_user, logout_user
import traceback

def test_admin_login():
    """Test login functionality for admin user"""
    with app.app_context():
        # Make sure admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Admin user not found. Creating...")
            admin = User(
                username='admin',
                email='admin@zonar.local',
                is_admin=True,
                email_verified=True
            )
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
            admin = User.query.filter_by(username='admin').first()
        
        print(f"Found admin user: id={admin.id}, username={admin.username}")
        print(f"Admin password check: {admin.check_password('123456')}")
        
        # Test the login_user function directly
        print("\nTesting login_user function...")
        try:
            # Force logout first
            if current_user.is_authenticated:
                logout_user()
                print("Logged out current user")
            
            # Try to login
            result = login_user(admin)
            print(f"login_user result: {result}")
            print(f"current_user authenticated: {current_user.is_authenticated}")
            if current_user.is_authenticated:
                print(f"Logged in as: {current_user.username}, id={current_user.id}")
            else:
                print("Login failed!")
                
        except Exception as e:
            print(f"Login error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    print("Starting login test...")
    test_admin_login() 