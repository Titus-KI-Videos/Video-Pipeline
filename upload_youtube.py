#!/usr/bin/env python3
"""upload_youtube.py – Lädt ein Video zu YouTube Shorts hoch."""

import json, os, tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES      = ["https://www.googleapis.com/auth/youtube.upload"]
CATEGORY_ID = "27"   # Education
BASE_TAGS   = ["#Shorts","Wissen","Fakten","Lernen","Bildung","WusstetIhr","Wissenschaft"]


def _get_credentials() -> Credentials:
    """Lädt Credentials aus GitHub Secrets (Umgebungsvariablen)."""
    token_json  = os.environ["YOUTUBE_TOKEN"]    # JSON-String aus Secret
    client_json = os.environ["YOUTUBE_CLIENT"]   # JSON-String aus Secret

    # Token temporär auf Disk schreiben (google-auth benötigt Dateipfade)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False) as tf:
        tf.write(token_json)
        token_path = tf.name

    creds = Credentials.from_authorized_user_info(
        json.loads(token_json), SCOPES
    )

    # Token automatisch erneuern wenn abgelaufen
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Erneuertes Token zurück ins Env schreiben (für diesen Run)
        os.environ["YOUTUBE_TOKEN"] = creds.to_json()

    os.unlink(token_path)
    return creds


def upload_to_youtube(video_path: str, titel: str,
                      beschreibung: str, tags: list) -> str:
    """Gibt die YouTube Video-ID zurück."""
    creds   = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    yt_titel  = (titel if "#Shorts" in titel else f"{titel} #Shorts")[:100]
    alle_tags = list(dict.fromkeys(tags + BASE_TAGS))

    body = {
        "snippet": {
            "title":           yt_titel,
            "description":     beschreibung + "\n\n" + " ".join(BASE_TAGS[:4]),
            "tags":            alle_tags,
            "categoryId":      CATEGORY_ID,
            "defaultLanguage": "de",
        },
        "status": {
            "privacyStatus":          "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media   = MediaFileUpload(video_path, chunksize=-1,
                              resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"    Upload: {int(status.progress()*100)}%", flush=True)
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504):
                import time; time.sleep(5)
            else:
                raise

    return response["id"]
