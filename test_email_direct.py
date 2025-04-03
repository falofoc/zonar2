import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email settings (hardcoded for testing)
sender_email = "zoonarcom@gmail.com"
password = "vnmlzqhuvwktbucj"  # App password
receiver_email = "zoonarcom@gmail.com"  # Send to yourself for testing

# Create message
message = MIMEMultipart()
message["Subject"] = "Test Email from Zonar Direct Script"
message["From"] = sender_email
message["To"] = receiver_email

# Create body
body = """Hello,

This is a test email from a direct Python script.
If you received this email, it means your email credentials are working correctly.

Best regards,
ZONAR Team"""

message.attach(MIMEText(body, "plain"))

try:
    # Create a secure SSL context
    context = ssl.create_default_context()
    
    # Connect to Gmail SMTP server using SSL
    print("Connecting to Gmail using SSL on port 465...")
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
    print("Connected to Gmail")
    
    # Login
    print("Logging in...")
    server.login(sender_email, password)
    print("Login successful")
    
    # Send email
    print("Sending email...")
    server.sendmail(sender_email, receiver_email, message.as_string())
    print("Email sent successfully!")
    
    # Close connection
    server.quit()
    
except Exception as e:
    print(f"Error sending email: {e}") 