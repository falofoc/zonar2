import smtplib
import ssl
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('zonar.email')

class EmailError(Exception):
    """Base exception class for email-related errors"""
    pass

class EmailConfigError(EmailError):
    """Raised when there's an issue with email configuration"""
    pass

class EmailConnectionError(EmailError):
    """Raised when there's an issue connecting to the email server"""
    pass

class EmailAuthenticationError(EmailError):
    """Raised when there's an issue with email authentication"""
    pass

class EmailSendError(EmailError):
    """Raised when there's an issue sending the email"""
    pass

class EmailHandler:
    def __init__(self):
        self.config = self._load_email_config()
        self._validate_config()
        self.context = ssl.create_default_context()
    
    def _load_email_config(self) -> Dict[str, str]:
        """Load email configuration from environment variables"""
        config = {
            'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
            'MAIL_PORT': os.environ.get('MAIL_PORT', '587'),
            'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'True'),
            'MAIL_USE_SSL': os.environ.get('MAIL_USE_SSL', 'False'),
            'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', ''),
            'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD', ''),
            'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', '')
        }
        
        logger.debug("Email configuration loaded")
        return config
    
    def _validate_config(self) -> None:
        """Validate email configuration"""
        required_fields = ['MAIL_USERNAME', 'MAIL_PASSWORD']
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            error_msg = f"Missing required email configuration: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise EmailConfigError(error_msg)
        
        # Validate port and protocol combination
        port = int(self.config['MAIL_PORT'])
        use_ssl = self.config['MAIL_USE_SSL'].lower() == 'true'
        use_tls = self.config['MAIL_USE_TLS'].lower() == 'true'
        
        if port == 465 and not use_ssl:
            error_msg = "Port 465 requires SSL to be enabled"
            logger.error(error_msg)
            raise EmailConfigError(error_msg)
        
        if port == 587 and not use_tls:
            error_msg = "Port 587 requires TLS to be enabled"
            logger.error(error_msg)
            raise EmailConfigError(error_msg)
        
        logger.debug("Email configuration validated successfully")
    
    def _create_message(self, subject: str, body: str, to_email: str) -> MIMEMultipart:
        """Create email message"""
        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = self.config['MAIL_USERNAME']
        message["To"] = to_email
        message.attach(MIMEText(body, "plain", "utf-8"))
        return message
    
    def _connect_to_server(self) -> Tuple[Any, bool]:
        """Establish connection to email server"""
        port = int(self.config['MAIL_PORT'])
        use_ssl = self.config['MAIL_USE_SSL'].lower() == 'true'
        
        try:
            if use_ssl:
                logger.debug(f"Establishing SSL connection to {self.config['MAIL_SERVER']}:{port}")
                server = smtplib.SMTP_SSL(self.config['MAIL_SERVER'], port, context=self.context)
                return server, True
            else:
                logger.debug(f"Establishing TLS connection to {self.config['MAIL_SERVER']}:{port}")
                server = smtplib.SMTP(self.config['MAIL_SERVER'], port)
                server.ehlo()
                server.starttls(context=self.context)
                server.ehlo()
                return server, False
        except (smtplib.SMTPException, ssl.SSLError) as e:
            error_msg = f"Failed to connect to email server: {str(e)}"
            logger.error(error_msg)
            raise EmailConnectionError(error_msg)
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send an email with proper error handling and logging
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            
        Returns:
            bool: True if email was sent successfully, False otherwise
            
        Raises:
            EmailError: Base class for all email-related errors
        """
        start_time = datetime.now()
        logger.info(f"Sending email to {to_email}")
        
        try:
            message = self._create_message(subject, body, to_email)
            server, is_ssl = self._connect_to_server()
            
            try:
                logger.debug("Attempting to log in to email server")
                server.login(self.config['MAIL_USERNAME'], self.config['MAIL_PASSWORD'])
            except smtplib.SMTPAuthenticationError as e:
                error_msg = "Failed to authenticate with email server"
                logger.error(f"{error_msg}: {str(e)}")
                raise EmailAuthenticationError(error_msg)
            
            try:
                server.sendmail(self.config['MAIL_USERNAME'], to_email, message.as_string())
            except smtplib.SMTPException as e:
                error_msg = "Failed to send email"
                logger.error(f"{error_msg}: {str(e)}")
                raise EmailSendError(error_msg)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Email sent successfully to {to_email} in {duration:.2f} seconds")
            return True
            
        except EmailError:
            # Already logged, just re-raise
            raise
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise EmailError(error_msg)
        finally:
            if 'server' in locals():
                server.quit()
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test email server connection and authentication
        
        Returns:
            dict: Connection test results
        """
        results = {
            'success': False,
            'connection': False,
            'authentication': False,
            'error': None
        }
        
        try:
            server, is_ssl = self._connect_to_server()
            results['connection'] = True
            
            try:
                server.login(self.config['MAIL_USERNAME'], self.config['MAIL_PASSWORD'])
                results['authentication'] = True
                results['success'] = True
                logger.info("Email connection test successful")
            except smtplib.SMTPAuthenticationError as e:
                error_msg = f"Authentication failed: {str(e)}"
                logger.error(error_msg)
                results['error'] = error_msg
            finally:
                server.quit()
        except EmailConnectionError as e:
            results['error'] = str(e)
            logger.error(f"Connection test failed: {str(e)}")
        
        return results

# Create a singleton instance
email_handler = EmailHandler()

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Convenience function to send an email using the singleton EmailHandler
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body text
        
    Returns:
        bool: True if email was sent successfully
        
    Raises:
        EmailError: If there was an error sending the email
    """
    return email_handler.send_email(to_email, subject, body) 