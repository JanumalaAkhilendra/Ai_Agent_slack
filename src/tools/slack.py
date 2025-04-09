from slack_sdk import WebClient

class SlackTools:
    def __init__(self, token):
        self.client = WebClient(token=token)
    
    def send_message(self, channel, message):
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=message
            )
            return f"Message sent to Slack channel {channel}"
        except Exception as e:
            return f"Slack error: {str(e)}"