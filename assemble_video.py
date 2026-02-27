#!/usr/bin/env python3
"""assemble_video.py – Baut das fertige Video aus Clips + Voiceover."""

import json, os, shutil, subprocess, sys, tempfile, urllib.request

VOICE      = "de-DE-KillianNeural"   # Natürliche deutsche Männerstimme
MUSIC_URL  = "https://cdn.pixabay.com/audio/2024/01/08/audio_8efc1aa6e6.mp3"
MUSIC_VOL  = "0.07"
W, H       = 1080, 1920              # Hochformat für Shorts


def _run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} Fehler:\n{r.stderr[-500:]}")
    return r


def _download(url, dest, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
        f.write(r.read())


def _duration(path) -> float:
    r = _run(["ffprobe", "-v", "quiet", "-print_format", "json",
              "-show_streams", path])
    for s in json.loads(r.stdout).get("streams", []):
        if s.get("codec_type") == "audio":
            return float(s.get("duration", 60))
    return 60.0


def assemble_video(skript: str, titel: str, clip_urls: list, output: str):
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        voice_mp3 = os.path.join(tmp, "voice.mp3")
        music_mp3 = os.path.join(tmp, "music.mp3")
        raw_vid   = os.path.join(tmp, "raw.mp4")
        assembled = os.path.join(tmp, "assembled.mp4")

        # 1. Voiceover
        print("    → edge-tts Voiceover...", flush=True)
        _run(["edge-tts", "--voice", VOICE, "--text", skript,
              "--write-media", voice_mp3])
        duration = _duration(voice_mp3)
        print(f"    → Dauer: {duration:.1f}s")

        # 2. Clips herunterladen + skalieren
        print("    → Clips herunterladen...", flush=True)
        scaled = []
        for i, url in enumerate(clip_urls[:4]):
            raw  = os.path.join(tmp, f"raw_{i}.mp4")
            sc   = os.path.join(tmp, f"sc_{i}.mp4")
            try:
                _download(url, raw)
                _run(["ffmpeg", "-y", "-i", raw,
                      "-vf", (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                              f"crop={W}:{H},setsar=1,fps=30"),
                      "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-an", sc])
                scaled.append(sc)
            except Exception as e:
                print(f"    ⚠ Clip {i+1} übersprungen: {e}")

        if not scaled:
            raise RuntimeError("Keine Clips verfügbar!")

        # 3. Concat-Liste (Clips wiederholen bis Länge reicht)
        concat = os.path.join(tmp, "concat.txt")
        total, lines = 0.0, []
        while total < duration + 3:
            for s in scaled:
                r = _run(["ffprobe", "-v", "quiet", "-print_format", "json",
                          "-show_streams", s])
                for st in json.loads(r.stdout).get("streams", []):
                    if st.get("codec_type") == "video":
                        lines.append(f"file '{s}'\n")
                        total += float(st.get("duration", 10))
                        break
                if total >= duration + 3:
                    break
        with open(concat, "w") as f:
            f.writelines(lines)

        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
              "-i", concat, "-t", str(duration + 1),
              "-c:v", "copy", "-an", raw_vid])

        # 4. Hintergrundmusik
        print("    → Musik laden...", flush=True)
        try:
            _download(MUSIC_URL, music_mp3, timeout=20)
        except Exception:
            _run(["ffmpeg", "-y", "-f", "lavfi",
                  "-i", "anullsrc=r=44100:cl=stereo", "-t", "300", music_mp3])

        # 5. Audio-Mix
        fc = (f"[1:a]volume=1.0[v];"
              f"[2:a]volume={MUSIC_VOL},"
              f"afade=t=in:st=0:d=1.5,"
              f"afade=t=out:st={max(0,duration-2)}:d=2[m];"
              f"[v][m]amix=inputs=2:duration=first[aout]")
        _run(["ffmpeg", "-y",
              "-i", raw_vid, "-i", voice_mp3, "-i", music_mp3,
              "-filter_complex", fc,
              "-map", "0:v", "-map", "[aout]",
              "-t", str(duration),
              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
              assembled])

        # 6. Titel-Overlay
        print("    → Titel-Overlay...", flush=True)
        safe = (titel.replace("\\","\\\\").replace("'","\\'")
                     .replace(":","\\:").replace(",","\\,"))
        vf = (f"drawbox=x=0:y=ih-210:w=iw:h=210:color=black@0.72:t=fill,"
              f"drawtext=text='{safe}':fontsize=44:fontcolor=white:"
              f"x=(w-text_w)/2:y=h-170:font='DejaVu-Sans-Bold':"
              f"line_spacing=6:borderw=2:bordercolor=black")
        r = _run(["ffmpeg", "-y", "-i", assembled,
                  "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                  "-c:a", "copy", output], check=False)
        if r.returncode != 0:
            shutil.copy(assembled, output)   # Fallback ohne Overlay

    print(f"    ✓ Video fertig: {output}", flush=True)
