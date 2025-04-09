from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_new_token():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials/google-calendar.json',
        SCOPES
    )
    
    creds = flow.run_local_server(port=0)
    
    # Create properly formatted token
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    
    with open('credentials/token.json', 'w') as token_file:
        json.dump(token_data, token_file)
    
    print("New token generated with refresh_token")

if __name__ == '__main__':
    get_new_token()