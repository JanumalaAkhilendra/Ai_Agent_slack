# test_connection.py
from datetime import datetime, timedelta
from tools.google_calendar import GoogleCalendarToolsWrapper

calendar = GoogleCalendarToolsWrapper('../credentials/token.json')
print(calendar.create_event(
    summary="Connection Test",
    start_time=(datetime.now() + timedelta(hours=1)).isoformat()
))