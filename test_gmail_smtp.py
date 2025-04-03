import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_connection():
    # Email settings - using environment variables
    sender_email = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
    password = os.environ.get("MAIL_PASSWORD", "vnmlzqhuvwktbucj")
    # For testing, send to the same address
    receiver_email = sender_email
    
    # Try TLS first (port 587)
    try:
        print(f"Trying TLS connection on port 587 for {sender_email}...")
        # Create a secure TLS context
        context = ssl.create_default_context()
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            
            # Log in
            print("Logging in...")
            server.login(sender_email, password)
            
            # Create message
            print("Creating test message...")
            message = MIMEMultipart()
            message["Subject"] = "Test Email via TLS"
            message["From"] = sender_email
            message["To"] = receiver_email
            
            # Add body text
            message.attach(MIMEText("This is a test email sent using TLS (port 587)", "plain"))
            
            # Send email
            print("Sending email...")
            server.sendmail(sender_email, receiver_email, message.as_string())
            
            print("Email sent successfully via TLS!")
            return True
    except Exception as e:
        print(f"TLS connection failed: {e}")
    
    # Then try SSL (port 465)
    try:
        print(f"\nTrying SSL connection on port 465 for {sender_email}...")
        # Create a secure SSL context
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            # Log in
            print("Logging in...")
            server.login(sender_email, password)
            
            # Create message
            print("Creating test message...")
            message = MIMEMultipart()
            message["Subject"] = "Test Email via SSL"
            message["From"] = sender_email
            message["To"] = receiver_email
            
            # Add body text
            message.attach(MIMEText("This is a test email sent using SSL (port 465)", "plain"))
            
            # Send email
            print("Sending email...")
            server.sendmail(sender_email, receiver_email, message.as_string())
            
            print("Email sent successfully via SSL!")
            return True
    except Exception as e:
        print(f"SSL connection failed: {e}")
        return False

if __name__ == "__main__":
    test_gmail_connection() 