import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from PySide6.QtCore import QObject, Signal, QThread

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

class AuthManager:
    @staticmethod
    def get_paths(category, channel_name):
        # UPDATED: Includes category in path
        base = os.path.join("channels", category, channel_name)
        return {
            "secret": os.path.join(base, "client_secret.json"),
            "token": os.path.join(base, "token.json")
        }

    @staticmethod
    def check_status(category, channel_name):
        paths = AuthManager.get_paths(category, channel_name)
        
        if not os.path.exists(paths["secret"]):
            return "Missing Secret", "gray"
            
        if not os.path.exists(paths["token"]):
            return "Not Authorized", "#f38ba8" 
            
        try:
            creds = Credentials.from_authorized_user_file(paths["token"], SCOPES)
            if creds.valid:
                return "Connected", "#a6e3a1"
            elif creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(paths["token"], "w") as token:
                        token.write(creds.to_json())
                    return "Connected (Refreshed)", "#a6e3a1"
                except:
                    return "Token Expired", "#f9e2af"
            else:
                return "Invalid Token", "#f38ba8"
        except Exception:
            return "Corrupt Token", "#f38ba8"

class OAuthWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, category, channel_name):
        super().__init__()
        self.category = category
        self.channel_name = channel_name

    def run(self):
        paths = AuthManager.get_paths(self.category, self.channel_name)
        
        if not os.path.exists(paths["secret"]):
            self.finished.emit(False, "client_secret.json not found!")
            return

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                paths["secret"], SCOPES
            )
            creds = flow.run_local_server(port=0)
            
            with open(paths["token"], "w") as token:
                token.write(creds.to_json())
                
            self.finished.emit(True, "Authorization Successful!")
            
        except Exception as e:
            self.finished.emit(False, str(e))