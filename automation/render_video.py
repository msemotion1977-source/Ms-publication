import json
import math
import subprocess
from pathlib import Path


def _probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def _write_srt(script_text: str, duration: float, srt_path: str, words_per_chunk: int = 6):
    words = script_text.split()
    chunks = [" ".join(words[i:i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
    if not chunks:
        chunks = [script_text]
    per_chunk = duration / len(chunks)

    def fmt(t):
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        ms = int((s - int(s)) * 1000)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            start = i * per_chunk
            end = start + per_chunk
            f.write(f"{i+1}\n{fmt(start)} --> {fmt(end)}\n{chunk}\n\n")


def render_video(
    gameplay_path: str,
    voice_path: str,
    script_text: str,
    output_path: str,
    music_path: str | None = None,
    image_paths: list[str] | None = None,
    target_width: int = 1080,
    target_height: int = 1920,
):
    """Assemble le montage final :
    - fond gameplay recadré en vertical, bouclé pour couvrir toute la durée de la voix
    - voix off au premier plan
    - musique fournie par l'utilisateur en fond, volume réduit
    - sous-titres générés à partir du script, incrustés en bas de l'écran
    - images utilisateur en incrustation ponctuelle si fournies
    """
    workdir = Path(voice_path).parent
    voice_duration = _probe_duration(voice_path)

    srt_path = str(workdir / "captions.srt")
    _write_srt(script_text, voice_duration, srt_path)

    filters = []
    # -stream_loop -1 sur le gameplay : le clip Pixabay est souvent plus court que la voix,
    # on le boucle en continu et on coupe à la bonne durée avec -t plus bas.
    inputs = ["-stream_loop", "-1", "-i", gameplay_path, "-i", voice_path]
    input_index = 2

    # 1) Gameplay : boucle + recadrage vertical + durée calée sur la voix
    filters.append(
        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"crop={target_width}:{target_height},setpts=PTS-STARTPTS[bg]"
    )

    # 2) Sous-titres incrustés
    escaped_srt = srt_path.replace(":", "\\:")
    filters.append(
        f"[bg]subtitles='{escaped_srt}':force_style="
        f"'FontName=Arial,FontSize=20,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,"
        f"BorderStyle=1,Outline=2,Alignment=2,MarginV=90'[with_subs]"
    )
    last_video_label = "with_subs"

    # 3) Images utilisateur en incrustation, réparties dans la vidéo (3s chacune)
    image_paths = image_paths or []
    for idx, img in enumerate(image_paths[:5]):  # 5 max pour rester raisonnable
        inputs += ["-i", img]
        start = 4 + idx * (voice_duration / (len(image_paths) + 1))
        end = start + 3
        out_label = f"imgstep{idx}"
        filters.append(
            f"[{last_video_label}][{input_index}:v]overlay="
            f"(main_w-overlay_w)/2:main_h-overlay_h-260:"
            f"enable='between(t,{start:.2f},{end:.2f})'[{out_label}]"
        )
        last_video_label = out_label
        input_index += 1

    # 4) Audio : voix + musique de fond mixées
    if music_path:
        inputs += ["-i", music_path]
        music_index = input_index
        filters.append(f"[{music_index}:a]aloop=loop=-1:size=2e9,volume=0.12[music]")
        filters.append("[1:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]")
        audio_label = "aout"
    else:
        audio_label = "1:a"

    filter_complex = ";".join(filters)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{last_video_label}]",
        "-map", f"[{audio_label}]" if music_path else "1:a",
        "-t", str(voice_duration),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path
