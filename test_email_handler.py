import os
from utils.email_handler import email_handler, EmailError
from datetime import datetime

def test_email_functionality():
    """Test the email handler functionality"""
    print("\n=== Testing Email Handler ===\n")
    
    # Test 1: Connection Test
    print("1. Testing email server connection...")
    results = email_handler.test_connection()
    if results['success']:
        print("✅ Connection test passed")
    else:
        print(f"❌ Connection test failed: {results['error']}")
    
    # Test 2: Send Test Email
    print("\n2. Testing email sending...")
    try:
        # Get test recipient email (default to sender if not specified)
        recipient = os.environ.get("TEST_EMAIL", email_handler.config['MAIL_USERNAME'])
        
        # Send test email
        subject = f"ZONAR Email Handler Test ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        body = """
        This is a test email from the ZONAR Email Handler.
        
        If you received this email, the new email handling system is working correctly.
        
        Configuration:
        - Server: {server}
        - Port: {port}
        - Security: {security}
        - Username: {username}
        """.format(
            server=email_handler.config['MAIL_SERVER'],
            port=email_handler.config['MAIL_PORT'],
            security="SSL" if email_handler.config['MAIL_USE_SSL'].lower() == 'true' else "TLS",
            username=email_handler.config['MAIL_USERNAME']
        )
        
        email_handler.send_email(recipient, subject, body)
        print(f"✅ Test email sent successfully to {recipient}")
        
    except EmailError as e:
        print(f"❌ Failed to send test email: {str(e)}")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run tests
    test_email_functionality() 