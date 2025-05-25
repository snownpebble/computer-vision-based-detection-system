"""
Twilio integration module for sending SMS alerts about critical pothole areas.
"""
import os
import logging
from datetime import datetime

# Check if Twilio is installed
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_twilio_credentials():
    """
    Check if Twilio credentials are configured.
    
    Returns:
        bool: True if Twilio credentials are available, False otherwise
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
    
    if not TWILIO_AVAILABLE:
        logger.warning("Twilio package is not installed.")
        return False
    
    if not all([account_sid, auth_token, phone_number]):
        logger.warning("Twilio credentials are not configured.")
        return False
    
    return True

def send_alert(to_phone_number, message):
    """
    Send an SMS alert using Twilio.
    
    Args:
        to_phone_number (str): The recipient's phone number with country code
        message (str): The alert message to send
        
    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    if not check_twilio_credentials():
        logger.warning("Cannot send SMS alert: Twilio credentials not configured.")
        return False
    
    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        client = Client(account_sid, auth_token)
        
        # Add timestamp to the message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[Pothole Alert - {timestamp}] {message}"
        
        # Send the message
        message = client.messages.create(
            body=full_message,
            from_=from_phone_number,
            to=to_phone_number
        )
        
        logger.info(f"SMS sent successfully. SID: {message.sid}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False

def send_batch_alerts(phone_numbers, message):
    """
    Send the same alert to multiple recipients.
    
    Args:
        phone_numbers (list): List of recipient phone numbers with country codes
        message (str): The alert message to send
        
    Returns:
        dict: Dictionary with phone numbers as keys and success status as values
    """
    results = {}
    
    for phone in phone_numbers:
        success = send_alert(phone.strip(), message)
        results[phone] = success
    
    return results