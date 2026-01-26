from googleapiclient.http import MediaFileUpload
from datetime import datetime, timezone

def upload_video(
    youtube,
    video_path,
    title,
    description,
    tags=None,
    privacy="public",
    thumbnail_path=None,
    publish_at=None,
    progress_callback=None,
    category_id="22",
    language="id"
):
    """
    Upload video YouTube dengan metadata lengkap & natural seperti creator manusia
    """

    # --- VALIDASI DASAR ---
    if publish_at:
        # publishAt WAJIB format RFC3339 + UTC
        # Jika string (sudah isoformat), biarkan. Jika datetime, konversi.
        if isinstance(publish_at, datetime):
            publish_at = publish_at.astimezone(timezone.utc).isoformat()
        privacy = "private"

    # --- SNIPPET ---
    snippet = {
        "title": title,
        "description": description,
        "categoryId": category_id,
        "defaultLanguage": language,
        "defaultAudioLanguage": language,
    }

    if tags:
        snippet["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

    # --- STATUS ---
    status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": False,
        "embeddable": True,
        "license": "youtube",
        "publicStatsViewable": True,
    }

    if publish_at:
        status["publishAt"] = publish_at

    body = {
        "snippet": snippet,
        "status": status,
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/*",
        chunksize=1024 * 1024,
        resumable=True,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        upload_status, response = request.next_chunk()
        if upload_status and progress_callback:
            progress_callback(int(upload_status.progress() * 100))

    video_id = response["id"]

    # --- SET THUMBNAIL (SELALU TERPISAH, SEPERTI MANUSIA) ---
    if thumbnail_path:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=thumbnail_path
        ).execute()

    return video_id