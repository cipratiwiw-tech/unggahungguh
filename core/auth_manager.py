import os
import socket
import re
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from PySide6.QtCore import QObject, Signal, QThread

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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
    auth_url_signal = Signal(str)

    def __init__(self, category, channel_name):
        super().__init__()
        self.category = category
        self.channel_name = channel_name

    def run(self):
        paths = AuthManager.get_paths(self.category, self.channel_name)
        
        if not os.path.exists(paths["secret"]):
            self.finished.emit(False, "client_secret.json not found!")
            return

        server_sock = None
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                paths["secret"], SCOPES
            )

            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('localhost', 0))
            server_sock.listen(1)
            
            port = server_sock.getsockname()[1]
            redirect_uri = f'http://localhost:{port}/'
            flow.redirect_uri = redirect_uri

            auth_url, _ = flow.authorization_url(prompt='consent')
            self.auth_url_signal.emit(auth_url)
            
            while True:
                client_sock, addr = server_sock.accept()
                try:
                    request_data = client_sock.recv(1024).decode('utf-8')
                    match = re.search(r'GET\s+(\S+)\s+HTTP', request_data)
                    if not match:
                        client_sock.close()
                        continue
                    
                    path_url = match.group(1)
                    
                    if 'favicon.ico' in path_url:
                        client_sock.close()
                        continue
                        
                    if 'state=' not in path_url or 'code=' not in path_url:
                        client_sock.close()
                        continue

                    # Kirim HTML Sukses
                    success_html = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head><title>Login Berhasil</title>
<style>body{background:#121212;color:#e0e0e0;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0} .card{background:#1e1e1e;padding:40px;border-radius:12px;text-align:center;border:1px solid #333} h1{color:#4caf50}</style>
</head><body><div class="card"><h1>Login Berhasil!</h1><p>Aplikasi sedang menyimpan token...</p><script>setTimeout(function(){window.close()},3000);</script></div></body></html>"""
                    
                    client_sock.sendall(success_html.encode('utf-8'))
                    client_sock.close()
                    
                    # [FIX] Pastikan tidak ada double slash saat menggabungkan URL
                    # Terkadang redirect_uri sudah ada '/' di akhir dan path_url juga mulai dg '/'
                    clean_redirect = redirect_uri.rstrip('/')
                    clean_path = path_url if path_url.startswith('/') else '/' + path_url
                    authorization_response = clean_redirect + clean_path
                    
                    flow.fetch_token(authorization_response=authorization_response)
                    
                    creds = flow.credentials
                    with open(paths["token"], "w") as token:
                        token.write(creds.to_json())
                    
                    self.finished.emit(True, "Authorization Successful!")
                    break 
                    
                except Exception as inner_e:
                    print(f"Socket inner error: {inner_e}")
                    if client_sock: client_sock.close()

        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            if server_sock:
                server_sock.close()