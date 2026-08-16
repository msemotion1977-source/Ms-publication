import random
import requests
from config import PIXABAY_API_KEY, PEXELS_API_KEY

PIXABAY_VIDEO_ENDPOINT = "https://pixabay.com/api/videos/"
PEXELS_VIDEO_ENDPOINT = "https://api.pexels.com/videos/search"


def _try_pixabay(query: str):
    resp = requests.get(PIXABAY_VIDEO_ENDPOINT, params={
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": 30,
        "safesearch": "true",
    })
    resp.raise_for_status()
    hits = resp.json().get("hits", [])
    if not hits:
        return None
    chosen = random.choice(hits)
    return chosen["videos"].get("large", {}).get("url") or chosen["videos"]["medium"]["url"]


def _try_pexels(query: str):
    if not PEXELS_API_KEY:
        return None
    resp = requests.get(PEXELS_VIDEO_ENDPOINT, params={
        "query": query,
        "per_page": 30,
        "orientation": "portrait",
    }, headers={"Authorization": PEXELS_API_KEY})
    resp.raise_for_status()
    videos = resp.json().get("videos", [])
    if not videos:
        return None
    chosen = random.choice(videos)
    files = sorted(chosen.get("video_files", []), key=lambda f: f.get("width", 0), reverse=True)
    return files[0]["link"] if files else None


def fetch_gameplay_clip(query: str, output_path: str) -> str:
    """Cherche un clip correspondant au mot-clé de la chaîne, en essayant
    plusieurs bibliothèques libres de droits l'une après l'autre (Pixabay
    puis Pexels en secours) pour élargir les chances de trouver un résultat."""
    video_url = _try_pixabay(query) or _try_pexels(query)
    if not video_url:
        raise RuntimeError(
            f"Aucun clip trouvé pour {query!r} sur Pixabay ni Pexels. "
            f"Essaie un mot-clé plus générique (ex: 'gaming' au lieu du nom exact du jeu)."
        )

    with requests.get(video_url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return output_path


if __name__ == "__main__":
    import sys
    fetch_gameplay_clip(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "/tmp/gameplay.mp4")
