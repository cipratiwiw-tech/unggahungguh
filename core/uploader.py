from googleapiclient.http import MediaFileUpload

def upload_video(youtube, video_path, title, desc, tags, privacy, thumb=None, progress_callback=None):
    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": tags.split(',') if tags else [], 
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    # Chunk size 1MB agar progress bar lebih halus
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)

    req = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    res = None
    while res is None:
        status, res = req.next_chunk()
        if status and progress_callback:
            # Mengirim persentase (0-100)
            progress = int(status.progress() * 100)
            progress_callback(progress)

    video_id = res["id"]

    if thumb:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=thumb
        ).execute()

    return video_id