import os
from PySide6.QtCore import QThread, Signal
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from core.auth_manager import AuthManager, SCOPES
from core.youtube_service import get_service
from core.uploader import upload_video

class UploadWorker(QThread):
    progress_signal = Signal(int)       # Update persentase
    status_signal = Signal(str)         # Update teks status
    finished_signal = Signal(bool, str) # Selesai (Success/Fail)

    def __init__(self, category, channel_name, data):
        super().__init__()
        self.category = category
        self.channel_name = channel_name
        self.data = data 

    def run(self):
        try:
            self.status_signal.emit("Authenticating...")
            
            # 1. Ambil Kredensial
            paths = AuthManager.get_paths(self.category, self.channel_name)
            if not os.path.exists(paths["token"]):
                raise Exception("Token not found. Please login via OAuth first.")

            creds = Credentials.from_authorized_user_file(paths["token"], SCOPES)
            
            # Auto-refresh jika expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(paths["token"], "w") as token:
                    token.write(creds.to_json())

            youtube = get_service(creds)

            # 2. Proses Upload Video
            self.status_signal.emit("Uploading Video...")
            
            video_id = upload_video(
                youtube=youtube,
                video_path=self.data['video_path'],
                title=self.data['title'],
                desc=self.data['desc'],
                tags=self.data['tags'],
                privacy=self.data['privacy'], 
                thumb=self.data.get('thumb'),
                progress_callback=self.emit_progress
            )

            self.status_signal.emit("Finalizing...")
            print(f"UPLOAD SUCCESS: https://youtu.be/{video_id}")
            self.finished_signal.emit(True, f"Uploaded: {video_id}")

        except Exception as e:
            self.finished_signal.emit(False, str(e))

    def emit_progress(self, val):
        self.progress_signal.emit(val)