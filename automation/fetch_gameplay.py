import os
import random
import requests
from config import PIXABAY_API_KEY, PEXELS_API_KEY

PIXABAY_VIDEO_ENDPOINT = "https://pixabay.com/api/videos/"
PIXABAY_IMAGE_ENDPOINT = "https://pixabay.com/api/"
PEXELS_VIDEO_ENDPOINT = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_ENDPOINT = "https://api.pexels.com/v1/search"


def _download(url: str, output_path: str):
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return output_path


# ---------- Vidéos de fond (plusieurs, pour des cuts rapides) ----------

def _pixabay_video_urls(query: str, limit: int) -> list[str]:
    resp = requests.get(PIXABAY_VIDEO_ENDPOINT, params={
        "key": PIXABAY_API_KEY, "q": query, "per_page": 50, "safesearch": "true",
    })
    resp.raise_for_status()
    hits = resp.json().get("hits", [])
    random.shuffle(hits)
    urls = []
    for h in hits[:limit]:
        url = h["videos"].get("large", {}).get("url") or h["videos"].get("medium", {}).get("url")
        if url:
            urls.append(url)
    return urls


def _pexels_video_urls(query: str, limit: int) -> list[str]:
    if not PEXELS_API_KEY:
        return []
    resp = requests.get(PEXELS_VIDEO_ENDPOINT, params={
        "query": query, "per_page": 50, "orientation": "portrait",
    }, headers={"Authorization": PEXELS_API_KEY})
    resp.raise_for_status()
    videos = resp.json().get("videos", [])
    random.shuffle(videos)
    urls = []
    for v in videos[:limit]:
        files = sorted(v.get("video_files", []), key=lambda f: f.get("width", 0), reverse=True)
        if files:
            urls.append(files[0]["link"])
    return urls


def fetch_gameplay_clips(query: str, count: int, output_dir: str) -> list[str]:
    """Télécharge plusieurs extraits distincts (Pixabay, complété par Pexels si besoin)
    afin de pouvoir faire des cuts entre différents extraits plutôt qu'un seul en boucle."""
    urls = _pixabay_video_urls(query, count)
    if len(urls) < count:
        urls += _pexels_video_urls(query, count - len(urls))

    if not urls:
        raise RuntimeError(
            f"Aucun clip trouvé pour {query!r} sur Pixabay ni Pexels. "
            f"Essaie un mot-clé plus générique (ex: 'gaming' au lieu du nom exact du jeu)."
        )

    paths = []
    for i, url in enumerate(urls):
        p = os.path.join(output_dir, f"gameplay_{i}.mp4")
        try:
            _download(url, p)
            paths.append(p)
        except Exception:
            continue
    if not paths:
        raise RuntimeError(f"Échec du téléchargement de tous les clips pour {query!r}.")
    return paths


# ---------- Images mots-clés (cutaways) ----------

def _pixabay_image_url(keyword: str):
    resp = requests.get(PIXABAY_IMAGE_ENDPOINT, params={
        "key": PIXABAY_API_KEY, "q": keyword, "per_page": 20, "safesearch": "true", "image_type": "photo",
    })
    resp.raise_for_status()
    hits = resp.json().get("hits", [])
    if not hits:
        return None
    return random.choice(hits).get("largeImageURL")


def _pexels_image_url(keyword: str):
    if not PEXELS_API_KEY:
        return None
    resp = requests.get(PEXELS_PHOTO_ENDPOINT, params={
        "query": keyword, "per_page": 20, "orientation": "portrait",
    }, headers={"Authorization": PEXELS_API_KEY})
    resp.raise_for_status()
    photos = resp.json().get("photos", [])
    if not photos:
        return None
    chosen = random.choice(photos)
    return chosen["src"].get("large") or chosen["src"].get("original")


def fetch_keyword_images(keywords: list[str], output_dir: str) -> list[str]:
    """Télécharge une image par mot-clé fourni (Pixabay puis Pexels en secours).
    Les mots-clés sans résultat sont simplement ignorés (le montage s'adapte
    au nombre d'images réellement trouvées, jamais d'erreur bloquante ici)."""
    paths = []
    for i, kw in enumerate(keywords):
        try:
            url = _pixabay_image_url(kw) or _pexels_image_url(kw)
            if not url:
                continue
            p = os.path.join(output_dir, f"keyword_{i}.jpg")
            _download(url, p)
            paths.append(p)
        except Exception:
            continue
    return paths


if __name__ == "__main__":
    import sys
    clips = fetch_gameplay_clips(sys.argv[1], 3, "/tmp")
    print("Clips :", clips)
