from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import os
import pickle
from ..config.scopes import SCOPES

logger = logging.getLogger(__name__)

OAUTH_CLIENT_SECRETS = "details.json"  # Path to your OAuth client secrets file
TOKEN_PICKLE = "token.pickle"  # Where to store the user's access/refresh token

def get_gmail_service():
    """Create and return a Gmail service object using OAuth 2.0 user credentials."""
    creds = None
    # Try to load existing token
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as token:
            creds = pickle.load(token)
    # If no valid creds, start OAuth flow
    if not creds or not creds.valid:
        from google.auth.transport.requests import Request
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PICKLE, "wb") as token:
            pickle.dump(creds, token)
    try:
        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail service created successfully (OAuth user)")
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
