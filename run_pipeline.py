#!/usr/bin/env python3
"""
run_pipeline.py  –  Hauptskript der Video-Pipeline
Läuft täglich via GitHub Actions.
Erstellt 3 deutsche Videos und lädt sie auf YouTube hoch.
"""

import json, os, sys, time, tempfile, datetime
sys.path.insert(0, os.path.dirname(__file__))

from generate_topics  import generate_topics
from generate_script  import generate_script
from fetch_clips      import fetch_clips
from assemble_video   import assemble_video
from upload_youtube   import upload_to_youtube

LOG_FILE = os.path.join(os.path.dirname(__file__),
                        f"log_{datetime.date.today()}.txt")

def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def main():
    log("=" * 55)
    log(f"🎬 VIDEO PIPELINE START – {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
    log("=" * 55)

    # ── Schritt 1: 3 Themen generieren ─────────────────────────────────────
    log("\n[1/4] 3 Themen generieren...")
    topics = generate_topics()
    log(f"  ✓ Themen erhalten:")
    for i, t in enumerate(topics):
        log(f"    #{i+1}: {t['thema']} ({t['bereich']})")

    results = []

    # ── Schritt 2–4: Für jedes Thema ein Video erstellen ────────────────────
    for idx, topic in enumerate(topics):
        log(f"\n{'─'*55}")
        log(f"📹 VIDEO {idx+1}/3: {topic['thema']}")
        log(f"{'─'*55}")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Script generieren
                log(f"  [2a] Skript schreiben...")
                script_data = generate_script(topic)
                log(f"  ✓ Titel: {script_data['titel']}")

                # Clips holen
                log(f"  [2b] Videoclips von Pexels laden...")
                clip_urls = fetch_clips(script_data['suchbegriffe'], max_clips=4)
                log(f"  ✓ {len(clip_urls)} Clips gefunden")

                # Video bauen
                log(f"  [3]  Video zusammenbauen (FFmpeg + edge-tts)...")
                video_path = os.path.join(tmpdir, f"video_{idx}.mp4")
                assemble_video(
                    skript    = script_data['skript'],
                    titel     = script_data['titel'],
                    clip_urls = clip_urls,
                    output    = video_path,
                )
                size_mb = os.path.getsize(video_path) / 1_048_576
                log(f"  ✓ Video fertig ({size_mb:.1f} MB)")

                # YouTube Upload
                log(f"  [4]  YouTube Shorts Upload...")
                yt_id = upload_to_youtube(
                    video_path   = video_path,
                    titel        = script_data['titel'],
                    beschreibung = script_data['beschreibung'],
                    tags         = script_data['tags'],
                )
                url = f"https://youtu.be/{yt_id}"
                log(f"  ✅ Hochgeladen: {url}")
                results.append({"titel": script_data['titel'], "url": url, "ok": True})

            except Exception as e:
                log(f"  ❌ FEHLER bei Video {idx+1}: {e}")
                results.append({"titel": topic['thema'], "url": "FEHLER", "ok": False})

        # Kurze Pause zwischen Videos (YouTube-API Rate Limit)
        if idx < 2:
            log("  ⏳ 10 Sekunden Pause...")
            time.sleep(10)

    # ── Zusammenfassung ─────────────────────────────────────────────────────
    log(f"\n{'='*55}")
    log("📊 ERGEBNIS")
    log(f"{'='*55}")
    ok = sum(1 for r in results if r['ok'])
    log(f"  Erfolgreich: {ok}/3")
    for r in results:
        status = "✅" if r['ok'] else "❌"
        log(f"  {status} {r['titel']}")
        if r['ok']:
            log(f"     → {r['url']}")

    if ok == 0:
        log("\n❌ Alle Videos fehlgeschlagen!")
        sys.exit(1)

    log(f"\n✅ PIPELINE ABGESCHLOSSEN")

if __name__ == "__main__":
    main()
