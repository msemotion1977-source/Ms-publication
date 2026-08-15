import json
import requests
from config import MISTRAL_API_KEY

MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-small-latest"  # disponible sur le niveau gratuit "Experiment"

PROMPT_TEMPLATE = """Tu écris le texte d'une courte vidéo verticale (format TikTok/Shorts) pour une chaîne
dont la niche est : "{niche}".

Contraintes :
- Le texte doit être accrocheur dès la première phrase (hook).
- Longueur : entre 45 et 80 secondes de narration à voix haute (environ 130 à 200 mots).
- Écrit pour être LU à voix haute par une voix off, phrases courtes, rythme punchy.
- Contenu 100% original, aucune citation d'un texte existant, aucune parole de chanson.
- N'invente pas de faits présentés comme réels si la niche est factuelle ; si tu n'es pas sûr,
  reste générique ou formule au conditionnel.

Réponds UNIQUEMENT en JSON valide, sans texte autour, avec ce format exact :
{{
  "hook": "la toute première phrase, celle qui doit accrocher en 2 secondes",
  "script": "le texte complet à lire par la voix off, hook inclus",
  "title": "titre court pour la vidéo (moins de 90 caractères)",
  "caption": "légende courte pour la description, avec 3 à 5 hashtags pertinents à la niche"
}}
"""


def generate_script(niche: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(niche=niche)

    resp = requests.post(
        MISTRAL_ENDPOINT,
        headers={
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.8,
        },
        timeout=60,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()

    # Filet de sécurité si le modèle entoure quand même sa réponse de ```json ... ```
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]

    return json.loads(text)


if __name__ == "__main__":
    import sys
    result = generate_script(sys.argv[1] if len(sys.argv) > 1 else "faits divers insolites")
    print(json.dumps(result, ensure_ascii=False, indent=2))
