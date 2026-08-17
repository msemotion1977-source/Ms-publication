import os
import sys
import random
import traceback
from datetime import datetime, timedelta
from supabase import create_client

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, WORKDIR
from generate_script import generate_script
from generate_voice import generate_voice
from fetch_gameplay import fetch_gameplay_clips, fetch_keyword_images
from render_video import render_video
from publish_youtube import publish_to_youtube
from publish_tiktok import publish_to_tiktok

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def is_weekly_long_video_day(channel: dict) -> bool:
    if not channel.get("weekly_long_video"):
        return False
    return datetime.utcnow().isoweekday() == channel.get("long_video_day", 1)


def download_from_storage(bucket: str, path: str, dest: str):
    data = supabase.storage.from_(bucket).download(path)
    with open(dest, "wb") as f:
        f.write(data)
    return dest


def process_channel(channel: dict):
    channel_id = channel["id"]
    run_dir = os.path.join(WORKDIR, channel_id)
    os.makedirs(run_dir, exist_ok=True)
    print(f"--- Traitement de la chaîne : {channel['display_name']} ({channel['platform']}) ---")

    is_long = is_weekly_long_video_day(channel)

    # 1) Script
    script_data = generate_script(channel["niche"])
    print("Script généré :", script_data["title"])

    # 2) Voix off
    voice_path = os.path.join(run_dir, "voice.wav")
    generate_voice(script_data["script"], voice_path)

# 3) Fonds gameplay : priorité aux clips perso uploadés (bien plus adaptés que
    # les banques génériques pour ce type de contenu) ; sinon repli sur Pixabay/Pexels
    user_clips = supabase.table("gameplay_clips").select("*").eq("channel_id", channel_id).execute().data
    if user_clips:
        gameplay_paths = []
        for i in range(4):
            chosen = random.choice(user_clips)
            p = os.path.join(run_dir, f"user_gameplay_{i}.mp4")
            download_from_storage("gameplay", chosen["storage_path"], p)
            gameplay_paths.append(p)
    else:
        gameplay_paths = fetch_gameplay_clips(channel["gameplay_query"], count=4, output_dir=run_dir)

    # 4) Musique utilisateur (si fournie) — on en prend une au hasard parmi celles uploadées
    music_path = None
    tracks = supabase.table("music_tracks").select("*").eq("channel_id", channel_id).execute().data
    if tracks:
        chosen = random.choice(tracks)
        music_path = os.path.join(run_dir, "music.mp3")
        download_from_storage("music", chosen["storage_path"], music_path)

    # 5) Images à insérer dans le montage : d'abord celles fournies par l'utilisateur,
    # complétées par des images trouvées automatiquement à partir des mots-clés du script
    image_paths = []
    images = supabase.table("user_images").select("*").eq("channel_id", channel_id).execute().data
    for i, img in enumerate(images):
        p = os.path.join(run_dir, f"user_image_{i}.jpg")
        download_from_storage("images", img["storage_path"], p)
        image_paths.append(p)

    remaining_slots = max(0, 4 - len(image_paths))
    if remaining_slots and script_data.get("visual_keywords"):
        image_paths += fetch_keyword_images(script_data["visual_keywords"][:remaining_slots], run_dir)

    # 6) Montage
    output_path = os.path.join(run_dir, "final.mp4")
    render_video(
        gameplay_paths=gameplay_paths,
        voice_path=voice_path,
        script_text=script_data["script"],
        output_path=output_path,
        music_path=music_path,
        keyword_image_paths=image_paths,
    )
    print("Montage terminé :", output_path)

    # 7) Publication
    status = "failed"
    video_url = None
    error_message = None
    try:
        if channel["platform"] == "youtube":
            video_url = publish_to_youtube(
                channel, output_path, script_data["title"], script_data["caption"], is_short=not is_long
            )
            status = "published"
        else:
            result = publish_to_tiktok(channel, output_path, script_data["caption"])
            status = result["status"]
            video_url = result["url"]
    except Exception as e:
        error_message = str(e)
        traceback.print_exc()

    supabase.table("publications").insert({
        "channel_id": channel_id,
        "status": status,
        "title": script_data["title"],
        "video_url": video_url,
        "is_long_video": is_long,
        "error_message": error_message,
    }).execute()

    print(f"Résultat : {status}")


def main():
    single_channel_id = os.environ.get("TARGET_CHANNEL_ID", "").strip()

    query = supabase.table("channels").select("*").eq("active", True)
    if single_channel_id:
        query = supabase.table("channels").select("*").eq("id", single_channel_id)
    channels = query.execute().data

    if not channels:
        print("Aucune chaîne à traiter.")
        return

    for channel in channels:
        if not channel.get("oauth_refresh_token"):
            print(f"Chaîne {channel['display_name']} ignorée : pas encore connectée (OAuth manquant).")
            continue
        try:
            process_channel(channel)
        except Exception:
            print(f"Échec complet pour la chaîne {channel['display_name']} :")
            traceback.print_exc()


if __name__ == "__main__":
    main()
