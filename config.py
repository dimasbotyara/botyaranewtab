"""botyaranewtab configuration."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "botyaranewtab.db")
ICONS_DIR = os.path.join(BASE_DIR, "static", "icons")
BACKGROUNDS_DIR = os.path.join(BASE_DIR, "static", "backgrounds")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
FONTS_DIR = os.path.join(BASE_DIR, "static", "fonts")
SOUNDS_DIR = os.path.join(BASE_DIR, "static", "sounds")
CUSTOM_FONTS_DIR = os.path.join(BASE_DIR, "static", "fonts", "Custom")

HOST = "127.0.0.1"
PORT = 12121

DB_VERSION = 1

# ensure dirs
for d in [ICONS_DIR, BACKGROUNDS_DIR, BACKUPS_DIR, CUSTOM_FONTS_DIR, SOUNDS_DIR]:
    os.makedirs(d, exist_ok=True)
