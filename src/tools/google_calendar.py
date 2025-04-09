from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json
import os

class GoogleCalendarToolsWrapper:
    def __init__(self, credentials_path, calendar_id='primary'):
        try:
            with open(credentials_path) as f:
                token_data = json.load(f)
            
            # Validate required fields
            required_fields = ['token', 'refresh_token', 'client_id', 'client_secret']
            if not all(field in token_data for field in required_fields):
                raise ValueError("Token file missing required fields")
            
            self.credentials = Credentials(
                token=token_data['token'],
                refresh_token=token_data['refresh_token'],
                token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=token_data['client_id'],
                client_secret=token_data['client_secret'],
                scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/calendar'])
            )
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.calendar_id = calendar_id
            
        except Exception as e:
            raise ValueError(f"Calendar initialization failed: {str(e)}")

    def create_event(self, summary, start_time, end_time=None, description=""):
        try:
            if not end_time:
                end_time = (datetime.fromisoformat(start_time) + timedelta(hours=1)).isoformat()
            
            event = {
                'summary': summary,
                'description': description,
                'start': {'dateTime': start_time, 'timeZone': 'UTC'},
                'end': {'dateTime': end_time, 'timeZone': 'UTC'},
            }
            
            return self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
        except Exception as e:
            return f"Error creating event: {str(e)}"