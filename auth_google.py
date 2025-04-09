# save as auth_google.py in your project root
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Corrected line: Changed 'secret_file' to 'secrets_file'
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials/google-calendar.json',
    SCOPES
)

creds = flow.run_local_server(port=0)

# Save credentials
with open('credentials/token.json', 'w') as token:
    token.write(creds.to_json())

print("Token generated successfully at credentials/token.json")