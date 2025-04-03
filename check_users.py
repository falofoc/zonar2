from app import app, db
from app.models import User
from datetime import datetime

# Use app context
with app.app_context():
    # Get all users
    users = User.query.all()
    
    print(f"Total users: {len(users)}")
    
    # Print info about each user
    for user in users:
        token_preview = user.verification_token[:15] + "..." if user.verification_token else None
        
        # Print user details
        print(f"User: {user.username}")
        print(f"Email: {user.email}")
        print(f"Email verified: {user.email_verified}")
        print(f"Verification token: {token_preview}")
        
        # Check token expiry
        if hasattr(user, 'verification_token_expiry'):
            if user.verification_token_expiry:
                now = datetime.utcnow()
                print(f"Token expiry: {user.verification_token_expiry}")
                print(f"Token valid: {now < user.verification_token_expiry}")
            else:
                print("No token expiry set")
        else:
            print("verification_token_expiry attribute not found")
        
        # Add divider
        print("------------------------------") 