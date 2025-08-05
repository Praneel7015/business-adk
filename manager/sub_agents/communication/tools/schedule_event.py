from ..services.calendar_service import get_calendar_service
from ..config.settings import DEFAULT_TIMEZONE
from datetime import datetime, timedelta
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

def schedule_event(summary: str, start_time: str, duration_minutes: int, 
                  attendees: Optional[List[str]] = None, 
                  description: Optional[str] = None,
                  location: Optional[str] = None) -> Dict[str, Any]:
    """
    Schedule an event on Google Calendar.
    
    Args:
        summary: Title of the event
        start_time: ISO 8601 format, e.g. '2025-08-05T15:00:00'
        duration_minutes: Duration of the event in minutes
        attendees: List of email addresses of attendees
        description: Optional description of the event
        location: Optional location of the event
    
    Returns:
        Dictionary with status and event details
    """
    try:
        service = get_calendar_service()
        
        # Parse start time and calculate end time
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        
        # Create event object
        event = {
            "summary": summary,
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": DEFAULT_TIMEZONE
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": DEFAULT_TIMEZONE
            }
        }
        
        # Add optional fields
        if description:
            event["description"] = description
        
        if location:
            event["location"] = location
        
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        
        # Insert the event
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        
        logger.info(f"Event created successfully: {created_event.get('id')}")
        
        return {
            "status": "success",
            "message": "Event scheduled successfully",
            "event_id": created_event.get("id"),
            "event_link": created_event.get("htmlLink"),
            "summary": created_event.get("summary"),
            "start_time": created_event.get("start", {}).get("dateTime"),
            "end_time": created_event.get("end", {}).get("dateTime")
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule event: {e}")
        return {
            "status": "error",
            "message": f"Failed to schedule event: {str(e)}"
        }
