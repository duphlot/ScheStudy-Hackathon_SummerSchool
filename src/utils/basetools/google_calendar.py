"""
Google Calendar Tool for reading and creating calendar events
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


# Pydantic Models for Input/Output
class CalendarInfo(BaseModel):
    """Calendar information model"""
    id: str
    summary: str
    description: str = ""
    timeZone: str = ""
    accessRole: str = ""
    primary: bool = False


class EventAttendee(BaseModel):
    """Event attendee model"""
    email: str
    responseStatus: str = ""


class EventInfo(BaseModel):
    """Event information model"""
    id: str
    summary: str
    description: str = ""
    start: str
    end: str
    location: str = ""
    attendees: List[EventAttendee] = []
    htmlLink: str = ""
    status: str = ""
    created: str = ""
    updated: str = ""


class GetEventsInput(BaseModel):
    """Input model for getting events"""
    calendar_id: str = Field(default='primary', description="Calendar ID to read from")
    start_date: Optional[str] = Field(default=None, description="Start date in ISO format (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date in ISO format (YYYY-MM-DD)")
    max_results: int = Field(default=50, description="Maximum number of events to return")


class GetEventsOutput(BaseModel):
    """Output model for getting events"""
    events: List[EventInfo]
    success: bool = True
    message: str = ""


class CreateEventInput(BaseModel):
    """Input model for creating an event"""
    title: str = Field(description="Event title")
    start_datetime: str = Field(description="Start datetime in ISO format (YYYY-MM-DDTHH:MM)")
    end_datetime: str = Field(description="End datetime in ISO format (YYYY-MM-DDTHH:MM)")
    description: str = Field(default="", description="Event description")
    location: str = Field(default="", description="Event location")
    attendees: List[str] = Field(default_factory=list, description="List of attendee email addresses")
    calendar_id: str = Field(default='primary', description="Calendar ID to create event in")


class CreateEventOutput(BaseModel):
    """Output model for creating an event"""
    event: Optional[EventInfo] = None
    success: bool = True
    message: str = ""


class UpdateEventInput(BaseModel):
    """Input model for updating an event"""
    event_id: str = Field(description="ID of event to update")
    title: Optional[str] = Field(default=None, description="New event title")
    start_datetime: Optional[str] = Field(default=None, description="New start datetime in ISO format")
    end_datetime: Optional[str] = Field(default=None, description="New end datetime in ISO format")
    description: Optional[str] = Field(default=None, description="New description")
    location: Optional[str] = Field(default=None, description="New location")
    calendar_id: str = Field(default='primary', description="Calendar ID")


class UpdateEventOutput(BaseModel):
    """Output model for updating an event"""
    event: Optional[EventInfo] = None
    success: bool = True
    message: str = ""


class DeleteEventInput(BaseModel):
    """Input model for deleting an event"""
    event_id: str = Field(description="ID of event to delete")
    calendar_id: str = Field(default='primary', description="Calendar ID")


class DeleteEventOutput(BaseModel):
    """Output model for deleting an event"""
    success: bool = True
    message: str = ""


class SearchEventsInput(BaseModel):
    """Input model for searching events"""
    query: str = Field(description="Search query")
    calendar_id: str = Field(default='primary', description="Calendar ID to search in")
    max_results: int = Field(default=20, description="Maximum number of results")


class SearchEventsOutput(BaseModel):
    """Output model for searching events"""
    events: List[EventInfo]
    success: bool = True
    message: str = ""


class GetCalendarListOutput(BaseModel):
    """Output model for getting calendar list"""
    calendars: List[CalendarInfo]
    success: bool = True
    message: str = ""


class GoogleCalendarTool:
    """Tool for interacting with Google Calendar API"""
    
    # Quyền truy cập cần thiết cho Google Calendar
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, token_file: str = 'token.pickle'):
        """
        Initialize Google Calendar tool
        
        Args:
            token_file: Path to store authentication token
        """
        self.token_file = token_file
        self.service = None
        
        # Create credentials from environment variables
        self.credentials_info = {
            "installed": {
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
                "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
                "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_X509_CERT_URL'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                "redirect_uris": ["http://localhost"]
            }
        }
        
        # Validate required environment variables
        required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_PROJECT_ID']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Create flow from environment variables
                flow = InstalledAppFlow.from_client_config(
                    self.credentials_info, self.SCOPES)
                # Let Python auto-select available port (Desktop app flow)
                creds = flow.run_local_server(port=0, open_browser=True)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def get_calendar_list(self) -> GetCalendarListOutput:
        """
        Get list of all calendars
        
        Returns:
            GetCalendarListOutput with calendar information
        """
        try:
            if self.service is None:
                raise Exception("Service not initialized")
            calendar_list = self.service.calendarList().list().execute()
            calendars = []
            
            for calendar in calendar_list.get('items', []):
                calendars.append(CalendarInfo(
                    id=calendar['id'],
                    summary=calendar.get('summary', 'No title'),
                    description=calendar.get('description', ''),
                    timeZone=calendar.get('timeZone', ''),
                    accessRole=calendar.get('accessRole', ''),
                    primary=calendar.get('primary', False)
                ))
            
            return GetCalendarListOutput(calendars=calendars)
        except HttpError as error:
            error_msg = f'An error occurred: {error}'
            print(error_msg)
            return GetCalendarListOutput(calendars=[], success=False, message=error_msg)
    
    def get_events(self, input_data: GetEventsInput) -> GetEventsOutput:
        """
        Get events from a calendar
        
        Args:
            input_data: GetEventsInput with calendar parameters
            
        Returns:
            GetEventsOutput with events list
        """
        try:
            if self.service is None:
                raise Exception("Service not initialized")
            
            # Parse dates from input
            start_date = datetime.fromisoformat(input_data.start_date) if input_data.start_date else datetime.utcnow()
            end_date = datetime.fromisoformat(input_data.end_date) if input_data.end_date else start_date + timedelta(days=7)
            
            # Convert to RFC3339 format
            start_time = start_date.isoformat() + 'Z'
            end_time = end_date.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=input_data.calendar_id,
                timeMin=start_time,
                timeMax=end_time,
                maxResults=input_data.max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            formatted_events = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                attendees = [
                    EventAttendee(
                        email=attendee.get('email', ''),
                        responseStatus=attendee.get('responseStatus', '')
                    )
                    for attendee in event.get('attendees', [])
                ]
                
                formatted_events.append(EventInfo(
                    id=event['id'],
                    summary=event.get('summary', 'No title'),
                    description=event.get('description', ''),
                    start=start,
                    end=end,
                    location=event.get('location', ''),
                    attendees=attendees,
                    htmlLink=event.get('htmlLink', ''),
                    status=event.get('status', ''),
                    created=event.get('created', ''),
                    updated=event.get('updated', '')
                ))
            
            return GetEventsOutput(events=formatted_events)
        except HttpError as error:
            error_msg = f'An error occurred: {error}'
            print(error_msg)
            return GetEventsOutput(events=[], success=False, message=error_msg)
    
    def create_event(self, input_data: CreateEventInput) -> CreateEventOutput:
        """
        Create a new event in calendar
        
        Args:
            input_data: CreateEventInput with event details
            
        Returns:
            CreateEventOutput with created event information
        """
        try:
            if self.service is None:
                raise Exception("Service not initialized")
            
            # Parse datetime strings
            start_datetime = datetime.fromisoformat(input_data.start_datetime)
            end_datetime = datetime.fromisoformat(input_data.end_datetime)
            
            event = {
                'summary': input_data.title,
                'description': input_data.description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if input_data.location:
                event['location'] = input_data.location
            
            if input_data.attendees:
                event['attendees'] = [{'email': email} for email in input_data.attendees]
            
            created_event = self.service.events().insert(
                calendarId=input_data.calendar_id,
                body=event
            ).execute()
            
            event_info = EventInfo(
                id=created_event['id'],
                summary=created_event.get('summary', ''),
                description=created_event.get('description', ''),
                start=created_event['start'].get('dateTime', created_event['start'].get('date')),
                end=created_event['end'].get('dateTime', created_event['end'].get('date')),
                location=created_event.get('location', ''),
                attendees=[],
                htmlLink=created_event.get('htmlLink', ''),
                status=created_event.get('status', ''),
                created=created_event.get('created', ''),
                updated=created_event.get('updated', '')
            )
            
            return CreateEventOutput(event=event_info)
        except HttpError as error:
            error_msg = f'An error occurred: {error}'
            print(error_msg)
            return CreateEventOutput(success=False, message=error_msg)
    
    def update_event(self, input_data: UpdateEventInput) -> UpdateEventOutput:
        """
        Update an existing event
        
        Args:
            input_data: UpdateEventInput with update parameters
            
        Returns:
            UpdateEventOutput with updated event information
        """
        try:
            if self.service is None:
                raise Exception("Service not initialized")
            # Get existing event
            event = self.service.events().get(
                calendarId=input_data.calendar_id,
                eventId=input_data.event_id
            ).execute()
            
            # Update fields
            if input_data.title is not None:
                event['summary'] = input_data.title
            if input_data.description is not None:
                event['description'] = input_data.description
            if input_data.location is not None:
                event['location'] = input_data.location
            if input_data.start_datetime is not None:
                start_dt = datetime.fromisoformat(input_data.start_datetime)
                event['start'] = {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'UTC',
                }
            if input_data.end_datetime is not None:
                end_dt = datetime.fromisoformat(input_data.end_datetime)
                event['end'] = {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'UTC',
                }
            
            updated_event = self.service.events().update(
                calendarId=input_data.calendar_id,
                eventId=input_data.event_id,
                body=event
            ).execute()
            
            event_info = EventInfo(
                id=updated_event['id'],
                summary=updated_event.get('summary', ''),
                description=updated_event.get('description', ''),
                start=updated_event['start'].get('dateTime', updated_event['start'].get('date')),
                end=updated_event['end'].get('dateTime', updated_event['end'].get('date')),
                location=updated_event.get('location', ''),
                attendees=[],
                htmlLink=updated_event.get('htmlLink', ''),
                status=updated_event.get('status', ''),
                created=updated_event.get('created', ''),
                updated=updated_event.get('updated', '')
            )
            
            return UpdateEventOutput(event=event_info)
        except HttpError as error:
            error_msg = f'An error occurred: {error}'
            print(error_msg)
            return UpdateEventOutput(success=False, message=error_msg)
    
    def delete_event(self, input_data: DeleteEventInput) -> DeleteEventOutput:
        """
        Delete an event
        
        Args:
            input_data: DeleteEventInput with event ID and calendar ID
            
        Returns:
            DeleteEventOutput with success status
        """
        try:
            if self.service is None:
                raise Exception("Service not initialized")
            self.service.events().delete(
                calendarId=input_data.calendar_id,
                eventId=input_data.event_id
            ).execute()
            return DeleteEventOutput(success=True, message="Event deleted successfully")
        except HttpError as error:
            error_msg = f'An error occurred: {error}'
            print(error_msg)
            return DeleteEventOutput(success=False, message=error_msg)
    
    def search_events(self, input_data: SearchEventsInput) -> SearchEventsOutput:
        """
        Search for events containing specific text
        
        Args:
            input_data: SearchEventsInput with search parameters
            
        Returns:
            SearchEventsOutput with matching events
        """
        try:
            if self.service is None:
                raise Exception("Service not initialized")
            events_result = self.service.events().list(
                calendarId=input_data.calendar_id,
                q=input_data.query,
                maxResults=input_data.max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            formatted_events = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append(EventInfo(
                    id=event['id'],
                    summary=event.get('summary', 'No title'),
                    description=event.get('description', ''),
                    start=start,
                    end=end,
                    location=event.get('location', ''),
                    attendees=[],
                    htmlLink=event.get('htmlLink', ''),
                    status=event.get('status', ''),
                    created=event.get('created', ''),
                    updated=event.get('updated', '')
                ))
            
            return SearchEventsOutput(events=formatted_events)
        except HttpError as error:
            error_msg = f'An error occurred: {error}'
            print(error_msg)
            return SearchEventsOutput(events=[], success=False, message=error_msg)


class ReadCalendarInput(BaseModel):
    """Input model for reading calendar events"""
    days_ahead: int = Field(default=7, description="Number of days ahead to read events")

class ReadCalendarOutput(BaseModel):
    """Output model for reading calendar events"""
    events: List[EventInfo] = Field(default_factory=list, description="List of calendar events")
    success: bool = True
    message: str = ""

def read_calendar_events(days_ahead: int = 7) -> str:
    """
    Read calendar events from Google Calendar.
    
    Args:
        days_ahead: Number of days ahead to read events (default: 7)
        
    Returns:
        A string describing the calendar events found
    """
    try:
        calendar_tool = GoogleCalendarTool()
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        input = GetEventsInput(
            calendar_id='primary',
            end_date=end_date.isoformat()
        )
        
        result = calendar_tool.get_events(input)
        
        if result.success:
            if not result.events:
                return "No events found in the calendar for the next 7 days."
            
            events_text = f"Found {len(result.events)} events in primary calendar:\n"
            for event in result.events:
                events_text += f"- {event.summary} ({event.start} - {event.end})\n"
                if event.location:
                    events_text += f"  Location: {event.location}\n"
                if event.description:
                    events_text += f"  Description: {event.description}\n"
                events_text += "\n"
            return events_text
        else:
            return f"Error reading calendar: {result.message}"
    except Exception as e:
        return f"Error reading calendar: {str(e)}"


class CreateEventInputSimple(BaseModel):
    """Input model for simple event creation"""
    title: str = Field(description="Event title")
    start_time: str = Field(description="Start time in format 'YYYY-MM-DD HH:MM'")
    end_time: str = Field(description="End time in format 'YYYY-MM-DD HH:MM'")
    description: str = Field(default="", description="Event description")
    location: str = Field(default="", description="Event location")
    attendees: Optional[List[str]] = Field(default_factory=list, description="List of attendee emails")
    
class CreateEventOutputSimple(BaseModel):
    """Output model for simple event creation"""
    event: Optional[EventInfo] = None
    success: bool = True
    message: str = ""
    
def create_calendar_event_simple(title: str, start_time: str, end_time: str, description: str = "", location: str = "") -> str:
    """
    Create a new event in Google Calendar.
    
    Args:
        title: The title of the event
        start_time: Start time in format 'YYYY-MM-DD HH:MM'
        end_time: End time in format 'YYYY-MM-DD HH:MM'
        description: Optional description of the event
        location: Optional location of the event
        
    Returns:
        A string describing the result of creating the event
    """
    try:
        calendar_tool = GoogleCalendarTool()
        
        # Parse datetime strings
        start_dt = datetime.fromisoformat(start_time.replace(' ', 'T'))
        end_dt = datetime.fromisoformat(end_time.replace(' ', 'T'))
        
        event_input = CreateEventInput(
            title=title,
            start_datetime=start_dt.isoformat(),
            end_datetime=end_dt.isoformat(),
            description=description,
            location=location,
            attendees=[]
        )
        
        result = calendar_tool.create_event(event_input)
        
        if result.success and result.event:
            event = result.event
            return f"✅ Event created successfully!\nTitle: {event.summary}\nTime: {event.start} - {event.end}\nLocation: {event.location}\nLink: {event.htmlLink}"
        else:
            return f"❌ Failed to create event: {result.message}"
    except Exception as e:
        return f"❌ Error creating event: {str(e)}"


# Simple tool functions for Pydantic AI
def get_calendar_events(days_ahead: int = 7) -> str:
    """
    Tool function to get calendar events for Pydantic AI
    Uses primary calendar automatically - no calendar ID needed
    
    Args:
        days_ahead: Number of days ahead to read
        
    Returns:
        String description of events
    """
    try:
        calendar_tool = GoogleCalendarTool()
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        input_data = GetEventsInput(
            calendar_id='primary',
            end_date=end_date.isoformat()
        )
        
        result = calendar_tool.get_events(input_data)
        
        if result.success and result.events:
            events_text = f"Found {len(result.events)} events:\n"
            for event in result.events:
                events_text += f"- {event.summary} ({event.start} - {event.end})\n"
                if event.location:
                    events_text += f"  Location: {event.location}\n"
                if event.description:
                    events_text += f"  Description: {event.description}\n"
                events_text += "\n"
            return events_text
        else:
            return f"No events found. {result.message if not result.success else ''}"
    except Exception as e:
        return f"Error getting calendar events: {str(e)}"


def create_calendar_event(title: str, start_datetime: str, end_datetime: str, 
                         description: str = '', location: str = '') -> str:
    """
    Tool function to create calendar event for Pydantic AI
    Uses primary calendar automatically - no calendar ID needed
    
    Args:
        title: Event title
        start_datetime: Start datetime in ISO format (YYYY-MM-DDTHH:MM)
        end_datetime: End datetime in ISO format (YYYY-MM-DDTHH:MM)
        description: Event description
        location: Event location
        
    Returns:
        String description of created event
    """
    try:
        calendar_tool = GoogleCalendarTool()
        
        input_data = CreateEventInput(
            title=title,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            location=location,
            calendar_id='primary'
        )
        
        result = calendar_tool.create_event(input_data)
        
        if result.success and result.event:
            event = result.event
            return f"✅ Event created successfully!\nTitle: {event.summary}\nTime: {event.start} - {event.end}\nLocation: {event.location}\nLink: {event.htmlLink}"
        else:
            return f"❌ Failed to create event: {result.message}"
    except Exception as e:
        return f"❌ Error creating event: {str(e)}"

def search_calendar_events(query: str, calendar_id: str = 'primary') -> str:
    """
    Tool function to search calendar events for Pydantic AI
    
    Args:
        query: Search query
        calendar_id: Calendar ID to search in
        
    Returns:
        String description of found events
    """
    try:
        calendar_tool = GoogleCalendarTool()
        
        input_data = SearchEventsInput(
            query=query,
            calendar_id=calendar_id
        )
        
        result = calendar_tool.search_events(input_data)
        
        if result.success and result.events:
            events_text = f"Found {len(result.events)} events matching '{query}':\n"
            for event in result.events:
                events_text += f"- {event.summary} ({event.start} - {event.end})\n"
                if event.location:
                    events_text += f"  Location: {event.location}\n"
                if event.description:
                    events_text += f"  Description: {event.description}\n"
                events_text += f"  Event ID: {event.id}\n\n"
            return events_text
        else:
            return f"No events found matching '{query}'. {result.message if not result.success else ''}"
    except Exception as e:
        return f"Error searching calendar events: {str(e)}"


def update_calendar_event(event_id: str, title: Optional[str] = None, start_datetime: Optional[str] = None, 
                         end_datetime: Optional[str] = None, description: Optional[str] = None, 
                         location: Optional[str] = None) -> str:
    """
    Tool function to update calendar event for Pydantic AI
    
    Args:
        event_id: ID of event to update
        title: New title (optional)
        start_datetime: New start datetime (optional)
        end_datetime: New end datetime (optional)
        description: New description (optional)
        location: New location (optional)
        
    Returns:
        String description of updated event
    """
    try:
        calendar_tool = GoogleCalendarTool()
        
        input_data = UpdateEventInput(
            event_id=event_id,
            title=title,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            location=location
        )
        
        result = calendar_tool.update_event(input_data)
        
        if result.success and result.event:
            event = result.event
            return f"✅ Event updated successfully!\nTitle: {event.summary}\nTime: {event.start} - {event.end}\nLocation: {event.location}"
        else:
            return f"❌ Failed to update event: {result.message}"
    except Exception as e:
        return f"❌ Error updating event: {str(e)}"


def delete_calendar_event(event_id: str) -> str:
    """
    Tool function to delete calendar event for Pydantic AI
    
    Args:
        event_id: ID of event to delete
        
    Returns:
        String description of deletion result
    """
    try:
        calendar_tool = GoogleCalendarTool()
        
        input_data = DeleteEventInput(event_id=event_id)
        
        result = calendar_tool.delete_event(input_data)
        
        if result.success:
            return f"✅ Event deleted successfully!"
        else:
            return f"❌ Failed to delete event: {result.message}"
    except Exception as e:
        return f"❌ Error deleting event: {str(e)}"
