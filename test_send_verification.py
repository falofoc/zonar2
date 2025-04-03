from app import app, db, translate
from app.models import User
from flask import g, url_for
from datetime import datetime, timedelta
import secrets
import os

def test_send_verification_email():
    """Test sending a verification email with orange branding"""
    with app.app_context():
        # Get test user (admin)
        user = User.query.filter_by(username='admin').first()
        
        if not user:
            print("No admin user found")
            return False
            
        print(f"Testing with user: {user.username}, Email: {user.email}")
        
        # Set language for translation context
        g.lang = user.language if user.language else 'ar'
        
        # Generate test verification token
        user.verification_token = secrets.token_urlsafe(64)
        user.verification_token_expiry = datetime.now() + timedelta(days=7)
        db.session.commit()
        
        print(f"Generated verification token: {user.verification_token[:15]}...")
        
        # Create verification link - hardcoded for testing
        timestamp = int(datetime.now().timestamp())
        # Set a base URL for testing
        app.config['SERVER_NAME'] = 'zonar.sa'
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        
        with app.test_request_context():
            verification_link = url_for('verify_email', token=user.verification_token, v=timestamp, _external=True)
        
        # Import the function directly from routes
        from app.routes import send_localized_email
        
        # Send the verification email
        success = send_localized_email(
            user,
            subject_key="verification_email_subject",
            greeting_key="verification_email_greeting",
            body_key="verification_email_body",
            footer_key="verification_email_footer",
            verification_link=verification_link
        )
        
        if success:
            print(f"Verification email sent successfully to {user.email}")
            print(f"Check your email to find the new orange-branded template")
            print(f"You can verify your email by visiting: {verification_link}")
            return True
        else:
            print(f"Failed to send verification email to {user.email}")
            return False

if __name__ == "__main__":
    test_send_verification_email() 