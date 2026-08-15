import asyncio
import edge_tts

# Voix françaises naturelles disponibles gratuitement via edge-tts.
# Liste complète : `edge-tts --list-voices` en local.
VOICE = "fr-FR-HenriNeural"


async def _synthesize(text: str, output_path: str, voice: str = VOICE):
    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    await communicate.save(output_path)


def generate_voice(text: str, output_path: str, voice: str = VOICE):
    asyncio.run(_synthesize(text, output_path, voice))
    return output_path


if __name__ == "__main__":
    import sys
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/voice.mp3"
    generate_voice(sys.argv[1], out)
    print(f"Voix générée : {out}")
