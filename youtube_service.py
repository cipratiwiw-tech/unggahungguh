from googleapiclient.discovery import build

def get_youtube_service(creds):
    return build(
        "youtube",
        "v3",
        credentials=creds,
        cache_discovery=False
    )
