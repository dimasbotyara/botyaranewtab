"""botyaranewtab configuration."""

# Public version of the app (independent of DB_VERSION, which tracks schema).
APP_VERSION = "0.2.1"

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("BOTYARA_DATA_DIR", BASE_DIR)

DB_PATH = os.path.join(DATA_DIR, "botyaranewtab.db")
ICONS_DIR = os.path.join(DATA_DIR, "static", "icons")
BACKGROUNDS_DIR = os.path.join(DATA_DIR, "static", "backgrounds")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
FONTS_DIR = os.path.join(DATA_DIR, "static", "fonts")
SOUNDS_DIR = os.path.join(DATA_DIR, "static", "sounds")
CUSTOM_FONTS_DIR = os.path.join(FONTS_DIR, "Custom")

HOST = os.environ.get("BOTYARA_HOST", "127.0.0.1")
PORT = int(os.environ.get("BOTYARA_PORT", "12121"))

DB_VERSION = 1

# ensure dirs
for d in [ICONS_DIR, BACKGROUNDS_DIR, BACKUPS_DIR, CUSTOM_FONTS_DIR, SOUNDS_DIR]:
    os.makedirs(d, exist_ok=True)
