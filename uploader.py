from googleapiclient.http import MediaFileUpload

def upload_video(
    youtube,
    video_path,
    title,
    description,
    tags,
    privacy_status="private",
    thumbnail_path=None
):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]

    if thumbnail_path:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=thumbnail_path
        ).execute()

    return video_id
