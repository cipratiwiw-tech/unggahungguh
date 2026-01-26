import os
import pytz
from PySide6.QtCore import QThread, Signal
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from core.auth_manager import AuthManager, SCOPES
from core.youtube_service import get_service
from core.uploader import upload_video
from datetime import datetime, timezone


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

            # 2. Persiapkan format waktu ISO 8601 jika ada jadwal
            publish_at_iso = None
            if self.data.get('schedule_date') and self.data.get('schedule_time'):
                # Menggabungkan date dan time
                dt_str = f"{self.data['schedule_date']} {self.data['schedule_time']}"
                
                
                # Parsing sebagai waktu lokal WIB
                dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

                # Localize ke Asia/Jakarta (WIB)
                tz_wib = pytz.timezone("Asia/Jakarta")
                dt_wib = tz_wib.localize(dt_naive)

                # Konversi ke UTC (WAJIB untuk YouTube API)
                dt_utc = dt_wib.astimezone(timezone.utc)

                # RFC3339 format
                publish_at_iso = dt_utc.isoformat().replace("+00:00", "Z")

            # 3. Proses Upload Video
            self.status_signal.emit("Uploading Video...")
            
            video_id = upload_video(
                youtube=youtube,
                video_path=self.data['video_path'],
                title=self.data['title'],
                description=self.data['desc'],        # [FIX] Sesuaikan nama parameter: desc -> description
                tags=self.data['tags'],
                privacy=self.data['privacy'], 
                thumbnail_path=self.data.get('thumb'), # [FIX] Sesuaikan nama parameter: thumb -> thumbnail_path
                progress_callback=self.emit_progress,
                publish_at=publish_at_iso             # Masukkan parameter jadwal
            )
            
            self.status_signal.emit("Finalizing...")
            print(f"UPLOAD SUCCESS: https://youtu.be/{video_id}")
            self.finished_signal.emit(True, f"Uploaded: {video_id}")

        except Exception as e:
            self.finished_signal.emit(False, str(e))

    def emit_progress(self, val):
        self.progress_signal.emit(val)
        


class ChannelInfoWorker(QThread):
    finished_signal = Signal(bool, dict, str) # success, data, error_msg

    def __init__(self, category, channel_name):
        super().__init__()
        self.category = category
        self.channel_name = channel_name

    def run(self):
        try:
            # 1. Autentikasi
            paths = AuthManager.get_paths(self.category, self.channel_name)
            if not os.path.exists(paths["token"]):
                self.finished_signal.emit(False, {}, "Token not found")
                return

            creds = Credentials.from_authorized_user_file(paths["token"], SCOPES)
            
            # Refresh token jika expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(paths["token"], "w") as token:
                    token.write(creds.to_json())
            
            youtube = get_service(creds)

            # 2. Ambil Statistik Channel & ID Playlist Uploads
            chan_resp = youtube.channels().list(
                mine=True, 
                part="statistics,contentDetails"
            ).execute()
            
            if not chan_resp.get("items"):
                self.finished_signal.emit(False, {}, "Channel data not found")
                return

            item = chan_resp["items"][0]
            stats = item["statistics"]
            uploads_playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]

            # 3. Ambil 5 Video Terakhir dari 'Uploads Playlist'
            pl_resp = youtube.playlistItems().list(
                playlistId=uploads_playlist_id,
                part="snippet,contentDetails,status",
                maxResults=5
            ).execute()

            video_ids = []
            videos_list = []
            
            for play_item in pl_resp.get("items", []):
                vid_id = play_item["contentDetails"]["videoId"]
                video_ids.append(vid_id)
                videos_list.append({
                    "id": vid_id,
                    "title": play_item["snippet"]["title"],
                    "status": play_item["status"]["privacyStatus"], 
                    "published": play_item["snippet"]["publishedAt"]
                })

            # 4. Ambil View Count untuk video-video tersebut
            vid_stats_map = {}
            if video_ids:
                vid_resp = youtube.videos().list(
                    id=",".join(video_ids),
                    part="statistics"
                ).execute()
                for v in vid_resp.get("items", []):
                    vid_stats_map[v["id"]] = v["statistics"].get("viewCount", "0")

            # Gabungkan data views ke list video
            for v in videos_list:
                raw_views = int(vid_stats_map.get(v["id"], "0"))
                if raw_views >= 1000000:
                    v["views_fmt"] = f"{raw_views/1000000:.1f}M"
                elif raw_views >= 1000:
                    v["views_fmt"] = f"{raw_views/1000:.1f}K"
                else:
                    v["views_fmt"] = str(raw_views)

            # 5. Kemas semua data
            result_data = {
                "subscriberCount": stats.get("subscriberCount", "0"),
                "viewCount": stats.get("viewCount", "0"),
                "videoCount": stats.get("videoCount", "0"),
                "videos": videos_list
            }

            self.finished_signal.emit(True, result_data, "Success")

        except Exception as e:
            self.finished_signal.emit(False, {}, str(e))