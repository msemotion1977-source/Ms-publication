import os

# Toutes ces valeurs viennent des "Secrets" du repo GitHub (Settings > Secrets and variables > Actions)
# — jamais écrites en dur ici. Voir README pour la liste complète à créer.

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
PIXABAY_API_KEY = os.environ["PIXABAY_API_KEY"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")  # optionnel : source de secours

YOUTUBE_CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
YOUTUBE_CLIENT_SECRET = os.environ["YOUTUBE_CLIENT_SECRET"]

TIKTOK_CLIENT_KEY = os.environ["TIKTOK_CLIENT_KEY"]
TIKTOK_CLIENT_SECRET = os.environ["TIKTOK_CLIENT_SECRET"]

# Dossier de travail temporaire (nettoyé à chaque run par GitHub Actions)
WORKDIR = os.environ.get("WORKDIR", "/tmp/ms_publication")
os.makedirs(WORKDIR, exist_ok=True)
