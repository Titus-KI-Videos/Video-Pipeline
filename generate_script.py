#!/usr/bin/env python3
"""generate_script.py – Schreibt das vollständige Video-Skript via Gemini."""

import json, os, requests

API_KEY = os.environ["GEMINI_API_KEY"]
URL     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def generate_script(topic: dict) -> dict:
    prompt = f"""Du bist ein professioneller Texter für virale YouTube Shorts auf Deutsch.

Thema: {topic['thema']}
Bereich: {topic['bereich']}
Winkel: {topic['winkel']}
Einstieg: {topic['hook']}

Schreibe ein komplettes Video-Paket. Antworte NUR als reines JSON-Objekt ohne Markdown:
{{
  "titel": "Klickstarker Titel max 60 Zeichen (mit Zahl oder Frage wenn möglich)",
  "skript": "Vollständiges Sprecherskript für genau 60 Sekunden. Ca. 150 Wörter. Beginnt mit dem Hook. Lebhaft, Pausen eingebaut mit '...', kein Fachjargon. Endet mit einer Frage an die Zuschauer.",
  "beschreibung": "YouTube-Beschreibung ca. 100 Wörter mit Keywords. Endet mit Handlungsaufforderung.",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
  "suchbegriffe": ["englischer Pexels-Begriff 1","englischer Pexels-Begriff 2","englischer Pexels-Begriff 3"]
}}"""

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 2048}
    }

    resp = requests.post(URL, json=body, timeout=30)
    resp.raise_for_status()

    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = text.replace("```json", "").replace("```", "").strip()

    data = json.loads(text)
    required = ["titel", "skript", "beschreibung", "tags", "suchbegriffe"]
    for key in required:
        if key not in data:
            raise ValueError(f"Schlüssel fehlt: {key}")

    return data
