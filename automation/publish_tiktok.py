import os
import time
import requests
from config import TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET

API_BASE = "https://open.tiktokapis.com"


def _refresh_access_token(refresh_token: str) -> dict:
    # Les access tokens TikTok expirent vite (24h) : on rafraîchit systématiquement avant de poster.
    resp = requests.post(f"{API_BASE}/v2/oauth/token/", data={
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })
    resp.raise_for_status()
    return resp.json()


def publish_to_tiktok(channel_row: dict, video_path: str, caption: str) -> dict:
    """Retourne {"status": "published"|"private_pending_tiktok_audit", "url": str|None}.

    Tant que l'app n'a pas passé l'audit TikTok (channel_row["tiktok_audited"] == False),
    la vidéo est forcée en SELF_ONLY par l'API elle-même : c'est une contrainte TikTok,
    pas un choix de ce script. Elle reste alors visible uniquement depuis le compte,
    à rendre publique manuellement dans l'app une fois auditée.
    """
    tokens = _refresh_access_token(channel_row["oauth_refresh_token"])
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"}

    audited = bool(channel_row.get("tiktok_audited"))
    privacy_level = "PUBLIC_TO_EVERYONE" if audited else "SELF_ONLY"

    video_size = os.path.getsize(video_path)
    init_resp = requests.post(
        f"{API_BASE}/v2/post/publish/video/init/",
        headers=headers,
        json={
            "post_info": {
                "title": caption[:150],
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            },
        },
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()["data"]
    publish_id = init_data["publish_id"]
    upload_url = init_data["upload_url"]

    with open(video_path, "rb") as f:
        video_bytes = f.read()
    requests.put(
        upload_url,
        headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{video_size - 1}/{video_size}"},
        data=video_bytes,
    ).raise_for_status()

    # Poll du statut de publication (le traitement TikTok prend quelques dizaines de secondes)
    status = "PROCESSING_UPLOAD"
    for _ in range(20):
        time.sleep(5)
        status_resp = requests.post(
            f"{API_BASE}/v2/post/publish/status/fetch/",
            headers=headers,
            json={"publish_id": publish_id},
        )
        status = status_resp.json()["data"]["status"]
        if status in ("PUBLISH_COMPLETE", "FAILED"):
            break

    if status == "FAILED":
        raise RuntimeError(f"Publication TikTok échouée pour publish_id={publish_id}")

    return {
        "status": "published" if audited else "private_pending_tiktok_audit",
        "url": None,  # TikTok ne renvoie pas d'URL publique directement dans cette réponse
    }
