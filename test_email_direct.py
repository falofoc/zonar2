import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

def test_email(connection_type='ssl'):
    try:
        # Email settings
        sender_email = "zoonarcom@gmail.com"
        receiver_email = "zoonarcom@gmail.com"  # Change this to your email
        password = "vnml zqhu vwkt bucj"  # App password
        
        # Create message
        message = MIMEMultipart()
        timestamp = datetime.utcnow().isoformat()
        message["Subject"] = f"ZONAR Email Test ({connection_type.upper()}) - {timestamp}"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Create body with Arabic test
        body = f"""
        Test Email from ZONAR
        ---------------------
        Connection Type: {connection_type.upper()}
        Time: {timestamp}
        
        Arabic Test: مرحباً بكم في تطبيق زونار
        
        If you receive this email, the {connection_type.upper()} connection is working correctly.
        """
        
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # Create secure context
        context = ssl.create_default_context()
        
        if connection_type.lower() == 'ssl':
            # Use SSL on port 465
            print("Testing SSL connection (Port 465)...")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                print("Logging in...")
                server.login(sender_email, password)
                print("Sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully via SSL!")
        else:
            # Use TLS on port 587
            print("Testing TLS connection (Port 587)...")
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                print("Starting TLS...")
                server.starttls(context=context)
                print("Logging in...")
                server.login(sender_email, password)
                print("Sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully via TLS!")
                
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing SSL connection...")
    ssl_result = test_email('ssl')
    print("\nTesting TLS connection...")
    tls_result = test_email('tls')
    
    print("\nTest Results:")
    print(f"SSL Test: {'✅ Passed' if ssl_result else '❌ Failed'}")
    print(f"TLS Test: {'✅ Passed' if tls_result else '❌ Failed'}") 