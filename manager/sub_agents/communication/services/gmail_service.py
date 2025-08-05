from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import os
from ..config.scopes import SCOPES
from ..config.settings import SERVICE_ACCOUNT_FILE, DELEGATED_USER

logger = logging.getLogger(__name__)

def get_gmail_service():
    """Create and return a Gmail service object using service account credentials."""
    try:
        # Get the absolute path to the service account file
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            service_account_path = SERVICE_ACCOUNT_FILE
        else:
            # Try relative path from project root
            service_account_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", SERVICE_ACCOUNT_FILE)
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account file not found: {service_account_path}")
        
        # Load service account credentials with optional delegation
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=SCOPES
        )
        # Use domain-wide delegation if DELEGATED_USER is set
        if DELEGATED_USER:
            credentials = credentials.with_subject(DELEGATED_USER)
        service = build("gmail", "v1", credentials=credentials)
        logger.info("Gmail service created successfully (delegation: %s)", DELEGATED_USER)
        return service
        
    except Exception as e:
        logger.error(f"Failed to create Gmail service: {e}")
        raise Exception(f"Gmail service initialization failed: {str(e)}")

def test_gmail_connection():
    """Test the Gmail service connection."""
    try:
        service = get_gmail_service()
        # Try to get user profile to test connection
        profile = service.users().getProfile(userId="me").execute()
        logger.info(f"Gmail connection successful. Email: {profile.get('emailAddress')}")
        return True
    except Exception as e:
        logger.error(f"Gmail connection test failed: {e}")
        return False
