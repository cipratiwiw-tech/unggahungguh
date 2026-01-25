import os
import socket
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
    auth_url_signal = Signal(str) # Signal untuk mengirim URL ke GUI

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

            # [FIX] 1. Cari port yang kosong secara manual
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', 0))
            port = sock.getsockname()[1]
            sock.close()

            # [FIX] 2. Set Redirect URI DULUAN sebelum generate URL
            # Ini penting agar parameter redirect_uri masuk ke link
            redirect_uri = f'http://localhost:{port}/'
            flow.redirect_uri = redirect_uri

            # [FIX] 3. Generate URL yang sudah valid (mengandung port)
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            # Kirim URL valid ke GUI
            self.auth_url_signal.emit(auth_url)
            
            # [FIX] 4. Jalankan server TEPAT di port yang sudah kita tentukan tadi
            # authorization_prompt_message="" agar tidak double print di terminal
            creds = flow.run_local_server(
                port=port, 
                open_browser=False, 
                authorization_prompt_message=""
            )
            
            with open(paths["token"], "w") as token:
                token.write(creds.to_json())
                
            self.finished.emit(True, "Authorization Successful!")
            
        except Exception as e:
            # Jika user cancel atau error lain
            self.finished.emit(False, str(e))