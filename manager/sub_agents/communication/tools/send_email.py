from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import logging
from typing import Optional, Dict, Any
from ..services.gmail_service import get_gmail_service
from ..config.settings import DEFAULT_FROM_NAME

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, body: str, 
               from_name: Optional[str] = None,
               html_body: Optional[str] = None,
               cc: Optional[str] = None,
               bcc: Optional[str] = None) -> Dict[str, Any]:
    """
    Send an email using Gmail API.
    
    Args:
        to: Recipient email address
        subject: Subject line of the email
        body: Text content of the email
        from_name: Optional sender name
        html_body: Optional HTML version of the email
        cc: Optional CC email addresses (comma-separated)
        bcc: Optional BCC email addresses (comma-separated)
    
    Returns:
        Dictionary with status and message details
    """
    try:
        service = get_gmail_service()
        
        # Create message
        if html_body:
            # Create multipart message for both text and HTML
            message = MIMEMultipart('alternative')
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(html_body, 'html')
            message.attach(text_part)
            message.attach(html_part)
        else:
            # Simple text message
            message = MIMEText(body, 'plain')
        
        # Set headers
        message['to'] = to
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc
        
        if bcc:
            message['bcc'] = bcc
        
        # Set from name if provided
        if from_name:
            message['from'] = f"{from_name} <{service.users().getProfile(userId='me').execute().get('emailAddress')}>"
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send the message
        send_result = service.users().messages().send(
            userId="me", 
            body={"raw": raw_message}
        ).execute()
        
        logger.info(f"Email sent successfully: {send_result.get('id')}")
        
        return {
            "status": "success",
            "message": "Email sent successfully",
            "message_id": send_result.get("id"),
            "to": to,
            "subject": subject,
            "thread_id": send_result.get("threadId")
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }

def get_recent_emails(max_results: int = 10, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Get recent emails from Gmail.
    
    Args:
        max_results: Maximum number of emails to retrieve
        query: Optional Gmail search query
    
    Returns:
        Dictionary with status and email list
    """
    try:
        service = get_gmail_service()
        
        # Get message IDs
        results = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        
        email_list = []
        for message in messages:
            # Get full message details
            msg = service.users().messages().get(
                userId="me", 
                id=message['id']
            ).execute()
            
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            email_list.append({
                "id": message['id'],
                "thread_id": msg.get('threadId'),
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": msg.get('snippet', '')
            })
        
        return {
            "status": "success",
            "emails": email_list,
            "count": len(email_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to get emails: {e}")
        return {
            "status": "error",
            "message": f"Failed to get emails: {str(e)}"
        }
