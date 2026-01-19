import json
from auth import get_credentials
from youtube_service import get_youtube_service
from uploader import upload_video

BASE = "project_A"

CLIENT_SECRET = f"{BASE}/client_secret.json"
TOKEN = f"{BASE}/token.json"
UPLOADS = f"{BASE}/uploads"
THUMBS = f"{BASE}/thumbnails"
META = f"{BASE}/metadata"

# === LOAD METADATA ===
with open(f"{META}/video1.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

video_path = f"{UPLOADS}/{meta['video_file']}"
thumb_path = f"{THUMBS}/{meta['thumbnail']}"

# === AUTH & SERVICE ===
creds = get_credentials(CLIENT_SECRET, TOKEN)
youtube = get_youtube_service(creds)

# === UPLOAD ===
video_id = upload_video(
    youtube=youtube,
    video_path=video_path,
    title=meta["title"],
    description=meta["description"],
    tags=meta.get("tags", []),
    privacy_status=meta.get("privacy", "private"),
    thumbnail_path=thumb_path
)

print("UPLOAD SUCCESS:", video_id)
