import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from PySide6.QtCore import QObject, Signal, QThread

# Scopes yang dibutuhkan untuk upload
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

class AuthManager:
    """Class statis untuk manajemen token OAuth."""
    
    @staticmethod
    def get_paths(channel_name):
        base = os.path.join("channels", channel_name)
        return {
            "secret": os.path.join(base, "client_secret.json"),
            "token": os.path.join(base, "token.json")
        }

    @staticmethod
    def check_status(channel_name):
        """Cek status token tanpa memicu login flow."""
        paths = AuthManager.get_paths(channel_name)
        
        if not os.path.exists(paths["secret"]):
            return "Missing Secret", "gray"
            
        if not os.path.exists(paths["token"]):
            return "Not Authorized", "#f38ba8" # Merah
            
        # Cek validitas token
        try:
            creds = Credentials.from_authorized_user_file(paths["token"], SCOPES)
            if creds.valid:
                return "Connected", "#a6e3a1" # Hijau
            elif creds.expired and creds.refresh_token:
                # Coba refresh diam-diam
                try:
                    creds.refresh(Request())
                    # Simpan token baru
                    with open(paths["token"], "w") as token:
                        token.write(creds.to_json())
                    return "Connected (Refreshed)", "#a6e3a1"
                except:
                    return "Token Expired", "#f9e2af" # Kuning
            else:
                return "Invalid Token", "#f38ba8"
        except Exception:
            return "Corrupt Token", "#f38ba8"

# --- WORKER UNTUK OAUTH (Agar GUI tidak freeze saat browser buka) ---
class OAuthWorker(QThread):
    finished = Signal(bool, str) # Success, Message

    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name

    def run(self):
        paths = AuthManager.get_paths(self.channel_name)
        
        if not os.path.exists(paths["secret"]):
            self.finished.emit(False, "client_secret.json not found!")
            return

        try:
            # Flow OAuth Standar (Membuka Browser Default)
            flow = InstalledAppFlow.from_client_secrets_file(
                paths["secret"], SCOPES
            )
            # Run local server (blocking process)
            creds = flow.run_local_server(port=0)
            
            # Simpan Token
            with open(paths["token"], "w") as token:
                token.write(creds.to_json())
                
            self.finished.emit(True, "Authorization Successful!")
            
        except Exception as e:
            self.finished.emit(False, str(e))