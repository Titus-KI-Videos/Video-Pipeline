#!/usr/bin/env python3
"""Generiert täglich 3 frische, unterschiedliche Video-Themen via Gemini."""

import json, os, requests, datetime

API_KEY = os.environ["GEMINI_API_KEY"]
URL     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def generate_topics() -> list:
    heute = datetime.datetime.now().strftime("%A, %d. %B %Y")

    prompt = f"""Du bist Redakteur eines deutschen YouTube-Shorts-Kanals für Wissen & Fakten.

Heutiges Datum: {heute}

Erstelle GENAU 3 Video-Themen für heute. Die Themen müssen:
- Aus VERSCHIEDENEN Bereichen stammen (nie 2x dasselbe Genre)
- Fesselnd und alltagsnah sein
- Für ein 60-Sekunden-Video geeignet sein
- Sich von gestern und vorgestern unterscheiden (nutze das Datum als Variation)

Bereiche (rotiere täglich): Wissenschaft, Geschichte, Psychologie, Natur & Tiere, 
Medizin & Körper, Weltrekorde, Alltags-Geheimnisse, Technologie, Geografie, 
Kurioses, Essen & Chemie, Kriminalgeschichte, Architektur, Tiefsee, Astronomie

Antworte NUR als reines JSON-Array ohne Markdown:
[
  {{
    "thema": "Konkretes faszinierendes Thema",
    "bereich": "z.B. Psychologie",
    "winkel": "Welcher Aspekt beleuchtet wird",
    "hook": "Eröffnungssatz der sofort neugierig macht (max 15 Wörter)"
  }}
]"""

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 1024}
    }

    resp = requests.post(URL, json=body, timeout=30)
    resp.raise_for_status()

    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = text.replace("```json", "").replace("```", "").strip()

    topics = json.loads(text)
    if not isinstance(topics, list) or len(topics) < 3:
        raise ValueError(f"Unerwartetes Format: {text[:300]}")

    return topics[:3]
