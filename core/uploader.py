from googleapiclient.http import MediaFileUpload

def upload_video(youtube, video, title, desc, tags, privacy, thumb=None):
    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": tags,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video, resumable=True)

    req = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    res = None
    while res is None:
        _, res = req.next_chunk()

    if thumb:
        youtube.thumbnails().set(
            videoId=res["id"],
            media_body=thumb
        ).execute()

    return res["id"]
