from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import logging
import smtplib
import ssl
from datetime import datetime
from typing import Optional, Dict, Any
from ..services.gmail_service import get_gmail_service
from ..config.settings import DEFAULT_FROM_NAME

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, body: str, 
               from_name: Optional[str] = None,
               html_body: Optional[str] = None,
               cc: Optional[str] = None,
               bcc: Optional[str] = None,
               smtp_config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Send an email using Gmail API with SMTP fallback.
    
    Args:
        to: Recipient email address
        subject: Subject line of the email
        body: Text content of the email
        from_name: Optional sender name
        html_body: Optional HTML version of the email
        cc: Optional CC email addresses (comma-separated)
        bcc: Optional BCC email addresses (comma-separated)
        smtp_config: Optional SMTP configuration for fallback
    
    Returns:
        Dictionary with status and message details
    """
    
    # Method 1: Try Gmail API first
    try:
        result = send_via_gmail_api(to, subject, body, from_name, html_body, cc, bcc)
        if result["status"] == "success":
            return result
        else:
            logger.warning(f"Gmail API failed: {result['message']}")
    except Exception as e:
        logger.warning(f"Gmail API method failed: {e}")
    
    # Method 2: Try SMTP if configured
    if smtp_config:
        try:
            result = send_via_smtp(to, subject, body, from_name, html_body, smtp_config)
            if result["status"] == "success":
                return result
        except Exception as e:
            logger.warning(f"SMTP method failed: {e}")
    
    # Method 3: Fallback to file output
    return save_email_to_file(to, subject, body, html_body, from_name)

def send_via_gmail_api(to: str, subject: str, body: str, 
                      from_name: Optional[str] = None,
                      html_body: Optional[str] = None,
                      cc: Optional[str] = None,
                      bcc: Optional[str] = None) -> Dict[str, Any]:
    """Send email using Gmail API (original implementation)"""
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
            try:
                profile = service.users().getProfile(userId='me').execute()
                service_email = profile.get('emailAddress', 'assistant@business.com')
                message['from'] = f"{from_name} <{service_email}>"
            except:
                message['from'] = f"{from_name} <assistant@business.com>"
        
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
            "method": "Gmail API",
            "message": "Email sent successfully via Gmail API",
            "message_id": send_result.get("id"),
            "to": to,
            "subject": subject,
            "thread_id": send_result.get("threadId")
        }
        
    except Exception as e:
        logger.error(f"Failed to send email via Gmail API: {e}")
        return {
            "status": "error",
            "method": "Gmail API",
            "message": f"Gmail API failed: {str(e)}"
        }

def send_via_smtp(to: str, subject: str, body: str, 
                 from_name: Optional[str], html_body: Optional[str],
                 smtp_config: Dict) -> Dict[str, Any]:
    """Send email using SMTP as fallback"""
    try:
        # Extract SMTP configuration
        smtp_server = smtp_config.get('server', 'smtp.gmail.com')
        smtp_port = smtp_config.get('port', 587)
        sender_email = smtp_config.get('email')
        sender_password = smtp_config.get('password')
        
        if not sender_email or not sender_password:
            return {
                "status": "error",
                "method": "SMTP",
                "message": "SMTP configuration incomplete (missing email or password)"
            }
        
        # Create message
        if html_body:
            message = MIMEMultipart("alternative")
            text_part = MIMEText(body, "plain")
            html_part = MIMEText(html_body, "html")
            message.attach(text_part)
            message.attach(html_part)
        else:
            message = MIMEText(body, "plain")
        
        message["Subject"] = subject
        message["From"] = f"{from_name or 'Assistant'} <{sender_email}>"
        message["To"] = to
        
        # Send via SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to, message.as_string())
        
        return {
            "status": "success",
            "method": "SMTP",
            "message": "Email sent successfully via SMTP",
            "to": to,
            "subject": subject,
            "sender": sender_email
        }
        
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        return {
            "status": "error",
            "method": "SMTP", 
            "message": f"SMTP failed: {str(e)}"
        }

def save_email_to_file(to: str, subject: str, body: str, 
                      html_body: Optional[str] = None,
                      from_name: Optional[str] = None) -> Dict[str, Any]:
    """Save email to file as final fallback"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_output_{timestamp}.txt"
        
        email_content = f"""
EMAIL OUTPUT - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
================================================================

To: {to}
From: {from_name or 'Business Assistant'}
Subject: {subject}

TEXT CONTENT:
{'-' * 50}
{body}

{'HTML CONTENT:' if html_body else ''}
{'-' * 50 if html_body else ''}
{html_body or ''}

================================================================
Note: This email was saved to file because Gmail API and SMTP delivery failed.
To enable actual email sending:
1. Configure Gmail API permissions in Google Cloud Console
2. Set up SMTP credentials in smtp_config parameter
3. Enable domain-wide delegation for service account (if using Gmail API)
        """.strip()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(email_content)
        
        logger.info(f"Email content saved to {filename}")
        
        return {
            "status": "saved",
            "method": "File Output",
            "message": f"Email content saved to {filename} (delivery methods unavailable)",
            "filename": filename,
            "to": to,
            "subject": subject,
            "note": "Configure Gmail API or SMTP to enable actual email sending"
        }
        
    except Exception as e:
        logger.error(f"File save failed: {e}")
        return {
            "status": "error",
            "method": "File Output",
            "message": f"Failed to save email: {str(e)}"
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
