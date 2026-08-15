import random
import requests
from config import PIXABAY_API_KEY

PIXABAY_VIDEO_ENDPOINT = "https://pixabay.com/api/videos/"


def fetch_gameplay_clip(query: str, output_path: str) -> str:
    """Cherche un clip correspondant au mot-clé de la chaîne sur Pixabay
    (libre de droits, aucune attribution requise, utilisable en monétisé)
    et le télécharge à output_path."""
    resp = requests.get(PIXABAY_VIDEO_ENDPOINT, params={
        "key": PIXABAY_API_KEY,
        "q": query,
        "video_type": "film",
        "per_page": 30,
        "safesearch": "true",
    })
    resp.raise_for_status()
    hits = resp.json().get("hits", [])
    if not hits:
        raise RuntimeError(f"Aucun clip Pixabay trouvé pour la requête : {query!r}")

    chosen = random.choice(hits)
    # "large" = meilleure qualité dispo gratuitement sur Pixabay
    video_url = chosen["videos"].get("large", {}).get("url") or chosen["videos"]["medium"]["url"]

    with requests.get(video_url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return output_path


if __name__ == "__main__":
    import sys
    fetch_gameplay_clip(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "/tmp/gameplay.mp4")
