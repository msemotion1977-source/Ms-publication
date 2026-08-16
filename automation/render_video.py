import json
import random
import subprocess
from pathlib import Path


def _probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def _write_srt(script_text: str, duration: float, srt_path: str, words_per_chunk: int = 5):
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


def _build_segment_plan(total_duration: float, n_gameplay_clips: int, n_images: int):
    """Découpe la vidéo en segments courts (~3.5s) pour un effet de montage
    rythmé, en intercalant les images mots-clés parmi les extraits gameplay."""
    cut_length = 3.5
    n_segments = max(3, round(total_duration / cut_length))
    seg_duration = total_duration / n_segments

    image_slots = set()
    if n_images > 0 and n_segments > 3:
        step = n_segments // (n_images + 1)
        for k in range(1, n_images + 1):
            pos = min(step * k, n_segments - 2)
            image_slots.add(pos)

    plan = []
    gp_idx = 0
    img_idx = 0
    for i in range(n_segments):
        if i in image_slots and img_idx < n_images:
            plan.append({"type": "image", "duration": seg_duration, "index": img_idx})
            img_idx += 1
        else:
            plan.append({"type": "gameplay", "duration": seg_duration, "index": gp_idx % n_gameplay_clips})
            gp_idx += 1
    return plan


def render_video(
    gameplay_paths: list[str],
    voice_path: str,
    script_text: str,
    output_path: str,
    music_path: str | None = None,
    keyword_image_paths: list[str] | None = None,
    target_width: int = 1080,
    target_height: int = 1920,
):
    """Montage dynamique :
    - alterne plusieurs extraits gameplay en cuts courts (~3.5s) plutôt qu'un seul
      extrait en boucle statique
    - insère les images mots-clés en cutaway plein écran avec effet de zoom (Ken Burns)
    - sous-titres gros/gras avec effet d'apparition
    - stings sonores (whoosh) à chaque cut, générés par ffmpeg (pas de fichier externe)
    - voix nettoyée (normalisation, léger compresseur) + musique en fond, ducking automatique
    """
    workdir = Path(voice_path).parent
    voice_duration = _probe_duration(voice_path)
    keyword_image_paths = keyword_image_paths or []

    srt_path = str(workdir / "captions.srt")
    _write_srt(script_text, voice_duration, srt_path)

    clip_durations = [_probe_duration(p) for p in gameplay_paths]

    plan = _build_segment_plan(voice_duration, len(gameplay_paths), len(keyword_image_paths))

    inputs = []
    filters = []
    seg_labels = []
    input_index = 0
    cut_timestamps = []
    t_cursor = 0.0

    for i, seg in enumerate(plan):
        d = seg["duration"]
        if seg["type"] == "gameplay":
            clip_path = gameplay_paths[seg["index"]]
            clip_dur = clip_durations[seg["index"]]
            max_start = max(0.0, clip_dur - d - 0.2)
            start = random.uniform(0, max_start) if max_start > 0 else 0.0
            inputs += ["-i", clip_path]
            filters.append(
                f"[{input_index}:v]trim=start={start:.2f}:duration={d:.2f},setpts=PTS-STARTPTS,"
                f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
                f"crop={target_width}:{target_height},fps=30,format=yuv420p,setsar=1[seg{i}]"
            )
        else:
            img_path = keyword_image_paths[seg["index"]]
            inputs += ["-loop", "1", "-t", f"{d:.2f}", "-i", img_path]
            frames = max(1, int(d * 30))
            filters.append(
                f"[{input_index}:v]scale=8000:-2,zoompan="
                f"z='min(zoom+0.0018,1.25)':d={frames}:s={target_width}x{target_height}:fps=30,"
                f"format=yuv420p,setsar=1[seg{i}]"
            )
        seg_labels.append(f"[seg{i}]")
        input_index += 1
        t_cursor += d
        if i < len(plan) - 1:
            cut_timestamps.append(t_cursor)

    concat_inputs = "".join(seg_labels)
    filters.append(f"{concat_inputs}concat=n={len(plan)}:v=1:a=0[vconcat]")

    escaped_srt = srt_path.replace(":", "\\:")
    filters.append(
        f"[vconcat]subtitles='{escaped_srt}':force_style="
        f"'FontName=Arial,FontSize=22,Bold=1,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,"
        f"BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=110'[vout]"
    )

    # ---- Audio ----
    voice_input_index = input_index
    inputs += ["-i", voice_path]
    input_index += 1
    filters.append(f"[{voice_input_index}:a]loudnorm=I=-16:TP=-1.5:LRA=11,acompressor=threshold=-18dB:ratio=3[voice_clean]")
    audio_parts = ["[voice_clean]"]

    if music_path:
        music_input_index = input_index
        inputs += ["-i", music_path]
        input_index += 1
        filters.append(f"[{music_input_index}:a]aloop=loop=-1:size=2e9,volume=0.10[music]")
        audio_parts.append("[music]")

    # Stings : un bruit blanc très court (whoosh) synthétisé à chaque cut, sans fichier externe
    sting_labels = []
    for k, ts in enumerate(cut_timestamps):
        sting_index = input_index
        inputs += ["-f", "lavfi", "-i", "anoisesrc=color=white:duration=0.18:sample_rate=44100"]
        input_index += 1
        delay_ms = int(ts * 1000)
        filters.append(
            f"[{sting_index}:a]afade=t=in:st=0:d=0.02,afade=t=out:st=0.10:d=0.08,"
            f"volume=0.18,adelay={delay_ms}|{delay_ms}[sting{k}]"
        )
        sting_labels.append(f"[sting{k}]")
        audio_parts.append(f"[sting{k}]")

    filters.append(f"{''.join(audio_parts)}amix=inputs={len(audio_parts)}:duration=first:dropout_transition=2[aout]")

    filter_complex = ";".join(filters)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-t", str(voice_duration),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path
