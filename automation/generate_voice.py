import os
import subprocess
from pathlib import Path

# Voix française neutre et claire (~60 Mo, téléchargée une fois par exécution
# du job GitHub Actions, mise en cache le temps de traiter toutes les chaînes).
VOICE_NAME = "fr_FR-siwis-medium"
MODEL_DIR = Path(os.environ.get("PIPER_VOICE_DIR", "/tmp/piper_voices"))
MODEL_PATH = MODEL_DIR / f"{VOICE_NAME}.onnx"


def _ensure_voice_downloaded():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists():
        return
    subprocess.run(
        ["python3", "-m", "piper.download_voices", VOICE_NAME],
        cwd=str(MODEL_DIR),
        check=True,
    )


def generate_voice(text: str, output_path: str) -> str:
    """Synthétise la voix off avec Piper : TTS local et open source, sans
    dépendance à un service tiers non officiel (contrairement à edge-tts)."""
    _ensure_voice_downloaded()
    subprocess.run(
        ["piper", "--model", str(MODEL_PATH), "--output_file", output_path],
        input=text,
        text=True,
        check=True,
    )
    return output_path


if __name__ == "__main__":
    import sys
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/voice.wav"
    generate_voice(sys.argv[1], out)
    print(f"Voix générée : {out}")
