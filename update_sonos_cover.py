#!/usr/local/bin/python3

import os
import hashlib
import json
import requests
from PIL import Image
from datetime import datetime
import logging

# --- Konfiguration ---
HA_URL = "http://192.168.1.22:8123"
COVER_URL = f"{HA_URL}/local/sonos-cover/vardagsrum.jpg"
LOCAL_PATH = "/config/www/sonos-cover/vardagsrum.jpg"
TEMP_PATH = "/config/www/sonos-cover/vardagsrum_temp.jpg"
HASH_FILE = "/config/www/sonos-cover/sonos_cover_hashes.json"
LOGFILE = "/config/python_scripts/sonos_cover_update.log"

# --- Logging ---
logging.basicConfig(
    filename=LOGFILE,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

def logprint(msg, level="info"):
    print(msg)
    getattr(logging, level)(msg)

def download_cover(url, output_path):
    logprint(f"Starte Download von {url}")
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logprint(f"Cover erfolgreich heruntergeladen: {output_path}")
            return True
        else:
            logprint(f"HTTP-Fehler beim Download: {response.status_code}", "error")
            return False
    except Exception as e:
        logprint(f"Ausnahme beim Download: {e}", "error")
        return False

def convert_image(input_path, output_path):
    logprint(f"Konvertiere Bild zu non-progressive JPEG...")
    try:
        with Image.open(input_path) as image:
            rgb_image = image.convert('RGB')
            rgb_image.save(output_path, format='JPEG', quality=95, progressive=False)
        logprint(f"Bild gespeichert: {output_path}")
        return True
    except Exception as e:
        logprint(f"Fehler bei der Konvertierung: {e}", "error")
        return False

def get_hash(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logprint(f"Fehler beim Hash: {e}", "error")
        return None

def load_hashes():
    if os.path.exists(HASH_FILE):
        try:
            with open(HASH_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logprint(f"Fehler beim Laden der Hash-Datei: {e}", "error")
    else:
        logprint("Keine Hash-Datei gefunden, starte neu.")
    return {}

def save_hashes(hashes):
    try:
        with open(HASH_FILE, 'w') as f:
            json.dump(hashes, f)
        logprint("Hash-Datei gespeichert.")
    except Exception as e:
        logprint(f"Fehler beim Speichern der Hash-Datei: {e}", "error")

def main():
    hashes = load_hashes()
    old_hash = hashes.get('vardagsrum')

    if download_cover(COVER_URL, TEMP_PATH):
        new_hash = get_hash(TEMP_PATH)
        if not new_hash:
            logprint("Hash konnte nicht berechnet werden. Abbruch.", "error")
            return

        if new_hash != old_hash:
            logprint("Neues Cover erkannt.")
            if convert_image(TEMP_PATH, LOCAL_PATH):
                hashes['vardagsrum'] = new_hash
                save_hashes(hashes)
                logprint("Cover aktualisiert!")
            else:
                logprint("Konvertierung fehlgeschlagen.", "error")
        else:
            logprint("Cover unverändert.")
        if os.path.exists(TEMP_PATH):
            os.remove(TEMP_PATH)
            logprint("Temporäre Datei gelöscht.")
    else:
        logprint("Download fehlgeschlagen. Kein Update möglich.", "error")

if __name__ == "__main__":
    main()

