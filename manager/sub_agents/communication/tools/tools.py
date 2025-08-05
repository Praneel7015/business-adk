import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from .schedule_event import schedule_event as _schedule_event
from .send_email import send_email as _send_email, get_recent_emails as _get_recent_emails

logger = logging.getLogger(__name__)

# ADK-compatible tool functions

def schedule_calendar_event(summary: str, start_time: str, duration_minutes: int = 60,
                           attendees: Optional[List[str]] = None, 
                           description: Optional[str] = None,
                           location: Optional[str] = None) -> Dict[str, Any]:
    """
    Schedule an event on Google Calendar.
    
    Args:
        summary: Title/subject of the event
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        duration_minutes: Duration of event in minutes (default 60)
        attendees: List of attendee email addresses
        description: Optional event description
        location: Optional event location
    
    Returns:
        Dict with status, event details, and event link
    """
    try:
        result = _schedule_event(
            summary=summary,
            start_time=start_time,
            duration_minutes=duration_minutes,
            attendees=attendees or [],
            description=description,
            location=location
        )
        return result
    except Exception as e:
        logger.error(f"Calendar event scheduling failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to schedule calendar event: {str(e)}"
        }

def send_gmail_message(to: str, subject: str, body: str,
                      from_name: Optional[str] = None,
                      html_body: Optional[str] = None,
                      cc: Optional[str] = None,
                      bcc: Optional[str] = None) -> Dict[str, Any]:
    """
    Send an email via Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content (plain text)
        from_name: Optional sender display name
        html_body: Optional HTML version of email body
        cc: Optional CC recipients (comma-separated)
        bcc: Optional BCC recipients (comma-separated)
    
    Returns:
        Dict with status, message ID, and send confirmation
    """
    try:
        result = _send_email(
            to=to,
            subject=subject,
            body=body,
            from_name=from_name,
            html_body=html_body,
            cc=cc,
            bcc=bcc
        )
        return result
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }

def get_gmail_messages(max_results: int = 10, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve recent Gmail messages.
    
    Args:
        max_results: Maximum number of messages to retrieve (default 10)
        query: Optional Gmail search query (e.g., "is:unread", "from:example@email.com")
    
    Returns:
        Dict with status and list of recent emails
    """
    try:
        result = _get_recent_emails(
            max_results=max_results,
            query=query
        )
        return result
    except Exception as e:
        logger.error(f"Gmail message retrieval failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to get Gmail messages: {str(e)}"
        }

def create_meeting_invitation(title: str, start_time: str, duration_minutes: int = 60,
                             attendees: Optional[List[str]] = None, 
                             agenda: Optional[str] = None,
                             location: Optional[str] = None,
                             send_invitation: bool = True) -> Dict[str, Any]:
    """
    Create a meeting invitation with calendar event and optional email notification.
    
    Args:
        title: Meeting title/subject
        start_time: Meeting start time in ISO format
        duration_minutes: Meeting duration in minutes
        attendees: List of attendee email addresses
        agenda: Optional meeting agenda/description
        location: Optional meeting location (physical or virtual)
        send_invitation: Whether to send email invitations
    
    Returns:
        Dict with calendar event details and email notification status
    """
    try:
        # Schedule the calendar event
        calendar_result = schedule_calendar_event(
            summary=title,
            start_time=start_time,
            duration_minutes=duration_minutes,
            attendees=attendees,
            description=agenda,
            location=location
        )
        
        if calendar_result.get("status") != "success":
            return calendar_result
        
        result = {
            "status": "success",
            "message": "Meeting invitation created successfully",
            "calendar_event": calendar_result,
            "email_notifications": []
        }
        
        # Send email invitations if requested
        if send_invitation and attendees:
            meeting_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            formatted_time = meeting_datetime.strftime("%B %d, %Y at %I:%M %p")
            
            email_subject = f"Meeting Invitation: {title}"
            email_body = f"""
You're invited to a meeting:

Title: {title}
Date & Time: {formatted_time}
Duration: {duration_minutes} minutes
Location: {location or 'To be determined'}

{f'Agenda: {agenda}' if agenda else ''}

Calendar Link: {calendar_result.get('event_link', 'N/A')}

Please confirm your attendance.

Best regards,
Business Assistant
            """.strip()
            
            for attendee in attendees:
                email_result = send_gmail_message(
                    to=attendee,
                    subject=email_subject,
                    body=email_body,
                    from_name="Business Assistant"
                )
                result["email_notifications"].append({
                    "attendee": attendee,
                    "status": email_result.get("status"),
                    "message_id": email_result.get("message_id")
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Meeting invitation creation failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to create meeting invitation: {str(e)}"
        }
