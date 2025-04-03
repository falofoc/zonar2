"""
This script can be run on Render.com to test email functionality.
Add it to your repository and run it on Render using the Shell feature.
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

def test_email_config():
    # Print environment variables without revealing password
    print("Environment Variables:")
    print(f"MAIL_SERVER: {os.environ.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {os.environ.get('MAIL_PORT')}")
    print(f"MAIL_USE_TLS: {os.environ.get('MAIL_USE_TLS')}")
    print(f"MAIL_USE_SSL: {os.environ.get('MAIL_USE_SSL')}")
    print(f"MAIL_USERNAME: {os.environ.get('MAIL_USERNAME')}")
    print(f"MAIL_PASSWORD: {'*' * 8 if os.environ.get('MAIL_PASSWORD') else 'Not set'}")
    print(f"MAIL_DEFAULT_SENDER: {os.environ.get('MAIL_DEFAULT_SENDER')}")
    print(f"RENDER: {os.environ.get('RENDER')}")

def send_test_email():
    # Email settings
    sender_email = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
    password = os.environ.get("MAIL_PASSWORD", "")
    receiver_email = sender_email
    
    # Server settings
    mail_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    mail_port = int(os.environ.get("MAIL_PORT", 587))
    mail_use_tls = os.environ.get("MAIL_USE_TLS", "True").lower() in ['true', '1', 't', 'yes', 'y']
    mail_use_ssl = os.environ.get("MAIL_USE_SSL", "False").lower() in ['true', '1', 't', 'yes', 'y']
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\nSending test email at {timestamp}")
    print(f"From: {sender_email} To: {receiver_email}")
    print(f"Using: {'SSL' if mail_use_ssl else 'TLS'} on port {mail_port}")
    
    try:
        # Create message
        message = MIMEMultipart()
        message["Subject"] = f"Render Test Email - {timestamp}"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Email content with Arabic test text
        email_content = f"""
        Hello / مرحباً،
        
        This is a test email sent from Render.com at {timestamp}.
        هذه رسالة اختبار مرسلة من Render.com في {timestamp}.
        
        Email configuration:
        - Server: {mail_server}
        - Port: {mail_port}
        - TLS: {mail_use_tls}
        - SSL: {mail_use_ssl}
        
        This email confirms that your SMTP settings are working correctly.
        تؤكد هذه الرسالة الإلكترونية أن إعدادات SMTP الخاصة بك تعمل بشكل صحيح.
        
        Regards,
        مع تحياتي،
        The Test Script
        """
        
        # Explicitly use UTF-8 encoding for the message
        message.attach(MIMEText(email_content, "plain", "utf-8"))
        
        # Create secure context
        context = ssl.create_default_context()
        
        # Send using appropriate method
        if mail_use_ssl:
            print("Using SSL connection...")
            with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as server:
                print("Logging in...")
                server.login(sender_email, password)
                print("Sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully!")
        else:
            print("Using TLS connection...")
            with smtplib.SMTP(mail_server, mail_port) as server:
                server.ehlo()
                print("Starting TLS...")
                server.starttls(context=context)
                server.ehlo()
                print("Logging in...")
                server.login(sender_email, password)
                print("Sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully!")
                
        return True
    except Exception as e:
        import traceback
        print(f"Error sending email: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Email Configuration Test ===")
    test_email_config()
    print("\n=== Email Sending Test ===")
    send_test_email() 