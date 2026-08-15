from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET


def publish_to_youtube(channel_row: dict, video_path: str, title: str, description: str, is_short: bool = True) -> str:
    """channel_row = la ligne Supabase de la chaîne (contient les tokens OAuth stockés
    lors de la connexion depuis le dashboard)."""
    creds = Credentials(
        token=channel_row["oauth_access_token"],
        refresh_token=channel_row["oauth_refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
    )
    youtube = build("youtube", "v3", credentials=creds)

    tag_suffix = " #shorts" if is_short else ""
    body = {
        "snippet": {
            "title": title[:95] + tag_suffix,
            "description": description,
            "categoryId": "20",  # Gaming
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]
    return f"https://youtube.com/watch?v={video_id}"


if __name__ == "__main__":
    print("Ce module s'utilise via main.py — voir README.")
