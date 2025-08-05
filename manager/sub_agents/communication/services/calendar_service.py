from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import os
from ..config.scopes import SCOPES
from ..config.settings import SERVICE_ACCOUNT_FILE, DELEGATED_USER

logger = logging.getLogger(__name__)

def get_calendar_service():
    """Create and return a Google Calendar service object using service account credentials."""
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
        service = build("calendar", "v3", credentials=credentials)
        logger.info("Google Calendar service created successfully (delegation: %s)", DELEGATED_USER)
        return service
        
    except Exception as e:
        logger.error(f"Failed to create Calendar service: {e}")
        raise Exception(f"Calendar service initialization failed: {str(e)}")

def test_calendar_connection():
    """Test the calendar service connection."""
    try:
        service = get_calendar_service()
        # Try to get calendar list to test connection
        calendar_list = service.calendarList().list().execute()
        logger.info(f"Calendar connection successful. Found {len(calendar_list.get('items', []))} calendars")
        return True
    except Exception as e:
        logger.error(f"Calendar connection test failed: {e}")
        return False
