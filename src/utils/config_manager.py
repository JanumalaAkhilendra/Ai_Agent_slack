import json
import os
from dotenv import load_dotenv

load_dotenv()

class ConfigManager:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        try:
            with open(self.config_path) as f:
                config = json.load(f)
            
            # Override with environment variables
            if 'SLACK_TOKEN' in os.environ:
                config['slack']['token'] = os.environ['SLACK_TOKEN']
            
            return config
        except FileNotFoundError:
            return {
                "slack": {
                    "token": os.getenv('SLACK_TOKEN', ''),
                    "default_channel": "#general"
                },
                "google_calendar": {
                    "credentials": os.getenv('GOOGLE_CALENDAR_CREDENTIALS', ''),
                    "calendar_id": "primary"
                }
            }
    
    def update_config(self, new_config):
        self.config.update(new_config)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        return "Configuration updated successfully"