import os
import smtplib
import ssl
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def check_and_fix_email_config():
    """
    Check and fix email configuration issues
    """
    try:
        # Get current environment variables
        mail_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        mail_port = os.environ.get("MAIL_PORT", "465")
        mail_use_tls = os.environ.get("MAIL_USE_TLS", "False")
        mail_use_ssl = os.environ.get("MAIL_USE_SSL", "True")
        mail_username = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
        mail_password = os.environ.get("MAIL_PASSWORD", "vnmlzqhuvwktbucj")
        mail_default_sender = os.environ.get("MAIL_DEFAULT_SENDER", "zoonarcom@gmail.com")
        
        print("Current email configuration:")
        print(f"MAIL_SERVER: {mail_server}")
        print(f"MAIL_PORT: {mail_port}")
        print(f"MAIL_USE_TLS: {mail_use_tls}")
        print(f"MAIL_USE_SSL: {mail_use_ssl}")
        print(f"MAIL_USERNAME: {mail_username}")
        print(f"MAIL_PASSWORD: {'*' * len(mail_password) if mail_password else 'Not set'}")
        print(f"MAIL_DEFAULT_SENDER: {mail_default_sender}")
        
        # Check for common issues
        issues = []
        
        # Check if port and SSL/TLS settings are consistent
        if mail_port == "465" and mail_use_ssl.lower() != "true":
            issues.append("Port 465 is used but SSL is not enabled. Port 465 requires SSL.")
        
        if mail_port == "587" and mail_use_tls.lower() != "true":
            issues.append("Port 587 is used but TLS is not enabled. Port 587 requires TLS.")
        
        # Check if username and sender match
        if mail_username != mail_default_sender:
            issues.append(f"Username ({mail_username}) and default sender ({mail_default_sender}) don't match.")
        
        # Test SMTP connection
        try:
            print("\nTesting SMTP connection...")
            context = ssl.create_default_context()
            
            mail_port_int = int(mail_port)
            mail_use_ssl_bool = mail_use_ssl.lower() in ['true', '1', 't', 'yes', 'y']
            
            if mail_use_ssl_bool:
                print(f"Connecting to {mail_server}:{mail_port} using SSL...")
                with smtplib.SMTP_SSL(mail_server, mail_port_int, context=context) as server:
                    print("Logging in...")
                    server.login(mail_username, mail_password)
                    print("Login successful!")
            else:
                print(f"Connecting to {mail_server}:{mail_port} using TLS...")
                with smtplib.SMTP(mail_server, mail_port_int) as server:
                    server.ehlo()
                    print("Starting TLS...")
                    server.starttls(context=context)
                    server.ehlo()
                    print("Logging in...")
                    server.login(mail_username, mail_password)
                    print("Login successful!")
                    
            print("SMTP connection test PASSED")
        except Exception as e:
            print(f"SMTP connection test FAILED: {e}")
            issues.append(f"SMTP connection failed: {str(e)}")
        
        # Report issues
        if issues:
            print("\nIssues found:")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. {issue}")
                
            print("\nRecommended fixes:")
            
            # Generate recommendations based on issues
            for issue in issues:
                if "Port 465 is used but SSL is not enabled" in issue:
                    print("- Set MAIL_USE_SSL=True and MAIL_USE_TLS=False for port 465")
                elif "Port 587 is used but TLS is not enabled" in issue:
                    print("- Set MAIL_USE_TLS=True and MAIL_USE_SSL=False for port 587")
                elif "Username" in issue and "default sender" in issue:
                    print("- Set MAIL_DEFAULT_SENDER to match MAIL_USERNAME")
                elif "SMTP connection failed" in issue:
                    if "authentication" in issue.lower() or "login" in issue.lower():
                        print("- Check if the Gmail password is an App Password (not regular password)")
                        print("- Verify App Password is current and valid")
                        print("- Check if Less secure app access is enabled in Gmail settings")
                        print("- Check if there's a security alert in your Gmail account")
                    elif "network" in issue.lower() or "timeout" in issue.lower():
                        print("- Check network connectivity to SMTP server")
                    else:
                        print("- Check Gmail account security settings")
                        print("- Try generating a new App Password in Gmail")
        else:
            print("\nNo issues found with email configuration!")
        
        # Ask to send a test email
        if input("\nWould you like to send a test email? (y/n): ").lower() == 'y':
            test_email = input("Enter recipient email address: ")
            if test_email:
                print(f"Sending test email to {test_email}...")
                timestamp = datetime.utcnow().isoformat()
                
                # Create message
                message = MIMEMultipart()
                message["Subject"] = f"ZONAR Email Diagnostic Test - {timestamp}"
                message["From"] = mail_username
                message["To"] = test_email
                
                # Create body
                body = f"""Hello,

This is a diagnostic test email from ZONAR.
Sent at: {timestamp}

Email configuration:
- Server: {mail_server}
- Port: {mail_port}
- TLS: {mail_use_tls}
- SSL: {mail_use_ssl}

If you received this email, the email configuration is working correctly.

Best regards,
ZONAR Technical Support"""
                
                message.attach(MIMEText(body, "plain", "utf-8"))
                
                try:
                    context = ssl.create_default_context()
                    mail_port_int = int(mail_port)
                    mail_use_ssl_bool = mail_use_ssl.lower() in ['true', '1', 't', 'yes', 'y']
                    
                    if mail_use_ssl_bool:
                        with smtplib.SMTP_SSL(mail_server, mail_port_int, context=context) as server:
                            server.login(mail_username, mail_password)
                            server.sendmail(mail_username, test_email, message.as_string())
                    else:
                        with smtplib.SMTP(mail_server, mail_port_int) as server:
                            server.ehlo()
                            server.starttls(context=context)
                            server.ehlo()
                            server.login(mail_username, mail_password)
                            server.sendmail(mail_username, test_email, message.as_string())
                    
                    print("Test email sent successfully!")
                except Exception as e:
                    print(f"Failed to send test email: {e}")
        
        print("\nEmail diagnostic complete.")
        
    except Exception as e:
        import traceback
        print(f"Error during email configuration check: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    check_and_fix_email_config() 