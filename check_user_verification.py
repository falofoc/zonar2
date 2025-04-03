from app import app
from app.models import User

with app.app_context():
    # Get all users
    users = User.query.all()
    
    print(f"Total users: {len(users)}")
    
    # Print user details
    for user in users:
        print(f"User: {user.username}")
        print(f"Email: {user.email}")
        print(f"Email verified: {user.email_verified}")
        print(f"Verification token: {user.verification_token}")
        print(f"Token expiry: {user.verification_token_expiry}")
        print("------------------------------") 