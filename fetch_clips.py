#!/usr/bin/env python3
"""fetch_clips.py – Holt Videoclips von der Pexels API."""

import os, requests

PEXELS_KEY = os.environ["PEXELS_API_KEY"]

def fetch_clips(suchbegriffe: list, max_clips: int = 4) -> list:
    """Gibt eine Liste von Direktlinks zu Pexels-Videoclips zurück."""
    urls = []

    for term in suchbegriffe[:3]:
        try:
            resp = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": term, "per_page": 5,
                        "orientation": "portrait", "size": "medium"},
                timeout=15
            )
            resp.raise_for_status()
            videos = resp.json().get("videos", [])

            for vid in videos:
                best = None
                for f in vid.get("video_files", []):
                    if f.get("height", 0) > f.get("width", 0):  # Hochformat
                        if best is None or f.get("quality") == "hd":
                            best = f
                if best:
                    urls.append(best["link"])
                    break   # 1 Clip pro Suchbegriff reicht

        except Exception as e:
            print(f"  ⚠ Pexels-Fehler für '{term}': {e}")

    if not urls:
        raise RuntimeError("Keine Pexels-Clips gefunden!")

    return urls[:max_clips]
