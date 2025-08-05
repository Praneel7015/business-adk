# Communication Agent Setup and Usage Guide

## Overview
The Communication Agent provides comprehensive email and calendar management capabilities using Gmail and Google Calendar APIs with service account authentication.

## Setup Status
✅ **Calendar API**: Fully functional
⚠️ **Gmail API**: Requires additional permissions (see troubleshooting below)
✅ **Agent Structure**: Complete ADK integration
✅ **Tools**: 4 communication tools available

## Available Tools

### 1. `schedule_calendar_event`
Schedule events on Google Calendar with attendee management.

**Parameters:**
- `summary` (required): Event title/subject
- `start_time` (required): ISO format datetime (YYYY-MM-DDTHH:MM:SS)
- `duration_minutes` (optional): Event duration (default 60 minutes)
- `attendees` (optional): List of attendee email addresses
- `description` (optional): Event description/agenda
- `location` (optional): Event location

### 2. `send_gmail_message`
Send professional emails via Gmail API.

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject line
- `body` (required): Email content (plain text)
- `from_name` (optional): Sender display name
- `html_body` (optional): HTML version of email
- `cc` (optional): CC recipients (comma-separated)
- `bcc` (optional): BCC recipients (comma-separated)

### 3. `get_gmail_messages`
Retrieve recent Gmail messages.

**Parameters:**
- `max_results` (optional): Number of messages to retrieve (default 10)
- `query` (optional): Gmail search query (e.g., "is:unread")

### 4. `create_meeting_invitation`
Create comprehensive meeting invitations with calendar events and email notifications.

**Parameters:**
- `title` (required): Meeting title
- `start_time` (required): Meeting start time (ISO format)
- `duration_minutes` (optional): Meeting duration (default 60)
- `attendees` (optional): List of attendee emails
- `agenda` (optional): Meeting agenda/description
- `location` (optional): Meeting location
- `send_invitation` (optional): Send email invitations (default true)

## Example Prompts

### Calendar Management
1. **"Schedule a team meeting for tomorrow at 2 PM for 90 minutes"**
2. **"Create a calendar event: Project Review on August 10th at 10 AM with john@company.com and jane@company.com"**
3. **"Schedule a client presentation next Friday at 3 PM in Conference Room A"**
4. **"Set up a recurring weekly standup meeting every Monday at 9 AM"**

### Email Communications
5. **"Send an email to client@company.com about project update with subject 'Weekly Progress Report'"**
6. **"Compose a professional email to suppliers about payment terms"**
7. **"Send a follow-up email to the sales team about Q4 targets"**
8. **"Get my recent unread emails from the last week"**

### Meeting Coordination
9. **"Create a meeting invitation for budget review on August 15th at 2 PM with finance team"**
10. **"Schedule a product demo with clients and send invitation emails"**
11. **"Set up a board meeting with agenda and location details"**
12. **"Create a training session invitation for new employees"**

### Business Integration
13. **"Send payment reminder emails to overdue customers (integrate with Financial Agent)"**
14. **"Schedule supplier meetings based on purchase analysis (integrate with Purchase Agent)"**
15. **"Create customer follow-up calendar events (integrate with Sales Agent)"**
16. **"Send stock alert notifications to inventory team (integrate with Inventory Agent)"**

## Gmail API Troubleshooting

### Current Issue
Gmail API returns "Precondition check failed" error. This typically occurs when:

1. **Service Account Permissions**: The service account may need domain-wide delegation
2. **API Scopes**: Gmail API requires specific scope authorization
3. **Workspace/Personal Account**: Different authentication for Google Workspace vs personal accounts

### Solutions

#### Option 1: Domain-Wide Delegation (Google Workspace)
If using Google Workspace:
1. Enable domain-wide delegation in Google Cloud Console
2. Add OAuth scopes in Google Workspace Admin Console
3. Grant service account access to Gmail API

#### Option 2: OAuth2 Flow (Personal Gmail)
For personal Gmail accounts:
1. Switch to OAuth2 authentication instead of service account
2. Use user consent flow for Gmail access
3. Store refresh tokens for ongoing access

#### Option 3: Alternative Email Service
Consider using:
- SMTP for email sending
- Alternative email APIs
- Webhook-based email services

## File Structure
```
manager/sub_agents/communication/
├── __init__.py
├── agent.py                 # Main communication agent
├── config/
│   ├── __init__.py
│   ├── scopes.py           # API scopes configuration
│   └── settings.py         # Service account settings
├── services/
│   ├── __init__.py
│   ├── calendar_service.py # Google Calendar API service
│   └── gmail_service.py    # Gmail API service
└── tools/
    ├── __init__.py
    ├── tools.py            # ADK-compatible tool functions
    ├── schedule_event.py   # Calendar event scheduling
    └── send_email.py       # Email sending functionality
```

## Integration with Manager Agent

The Communication Agent is fully integrated with the Manager Agent:

### Delegation Keywords
- email, calendar, meeting, schedule, invitation, communication, gmail

### Cross-Functional Capabilities
- **Financial Communications**: Payment reminders, invoice notifications
- **Sales Communications**: Customer follow-ups, meeting scheduling
- **Purchase Communications**: Supplier correspondence, order confirmations
- **Inventory Communications**: Stock alerts, warehouse notifications

## Next Steps

1. **Resolve Gmail API permissions** for full email functionality
2. **Test calendar scheduling** with real meeting scenarios
3. **Implement cross-agent communication workflows**
4. **Add email templates** for common business scenarios
5. **Set up monitoring** for communication success rates

## Professional Use Cases

### Executive Assistant Functions
- Schedule executive meetings and board calls
- Send professional correspondence on behalf of management
- Coordinate cross-departmental meetings
- Manage calendar conflicts and reschedule events

### Business Operations
- Automate payment reminder emails
- Send customer onboarding communications
- Coordinate supplier meetings and negotiations
- Distribute meeting minutes and action items

### Customer Relationship Management
- Schedule customer check-in calls
- Send project update notifications
- Coordinate product demonstrations
- Manage event invitations and RSVPs

The Communication Agent provides a robust foundation for business communication automation and can be extended with additional features as needed.
