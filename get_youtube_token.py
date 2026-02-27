#!/usr/bin/env python3
"""
get_youtube_token.py
════════════════════
EINMALIG auf deinem eigenen PC ausführen!
Erzeugt den YouTube-Token der dann als GitHub Secret gespeichert wird.

Voraussetzung (einmalig installieren):
  pip install google-auth-oauthlib google-api-python-client

Dann ausführen:
  python get_youtube_token.py
"""
import json, os, sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit("Bitte zuerst ausführen:\n  pip install google-auth-oauthlib google-api-python-client")

SCOPES      = ["https://www.googleapis.com/auth/youtube.upload"]
SECRET_FILE = "youtube_client_secret.json"

if not os.path.exists(SECRET_FILE):
    sys.exit(
        f"❌ Datei nicht gefunden: {SECRET_FILE}\n"
        "Bitte aus Google Cloud Console herunterladen und in diesen Ordner legen."
    )

print()
print("╔══════════════════════════════════════════════════════╗")
print("║  YouTube Einmalig-Authentifizierung                 ║")
print("╠══════════════════════════════════════════════════════╣")
print("║  1. Browser öffnet sich gleich                      ║")
print("║  2. Mit YouTube-Kanal-Account einloggen             ║")
print("║  3. 'Zulassen' klicken                              ║")
print("║  4. Zwei Strings werden ausgegeben → in GitHub      ║")
print("║     Secrets einfügen (Anleitung erklärt wie)        ║")
print("╚══════════════════════════════════════════════════════╝")
print()

flow  = InstalledAppFlow.from_client_secrets_file(SECRET_FILE, SCOPES)
creds = flow.run_local_server(port=0)

token_json  = creds.to_json()
client_json = open(SECRET_FILE).read()

# Token-Datei speichern (als Backup)
with open("youtube_token.json", "w") as f:
    f.write(token_json)

print()
print("✅ Authentifizierung erfolgreich!")
print()
print("━" * 60)
print("GITHUB SECRET #1 — Name: YOUTUBE_TOKEN")
print("━" * 60)
print("Wert (alles zwischen den Linien kopieren):")
print("▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼")
print(token_json)
print("▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲")
print()
print("━" * 60)
print("GITHUB SECRET #2 — Name: YOUTUBE_CLIENT")
print("━" * 60)
print("Wert (alles zwischen den Linien kopieren):")
print("▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼")
print(client_json)
print("▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲")
print()
print("Jetzt in GitHub einfügen:")
print("  Repository → Settings → Secrets and variables")
print("  → Actions → New repository secret")
