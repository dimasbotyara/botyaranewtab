"""Utility functions for botyaranewtab."""

import os
import re
import json
import shutil
import time
from config import DB_PATH, BACKUPS_DIR, FONTS_DIR, CUSTOM_FONTS_DIR


def create_backup() -> str:
    """Create a database backup. Returns filename."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"botyaranewtab_backup_{timestamp}.db"
    dest = os.path.join(BACKUPS_DIR, filename)
    shutil.copy2(DB_PATH, dest)
    return filename


def restore_backup(backup_path: str) -> bool:
    """Restore database from backup."""
    try:
        shutil.copy2(backup_path, DB_PATH)
        return True
    except Exception:
        return False


def get_available_fonts() -> list:
    """List all available fonts (built-in + custom)."""
    fonts = []

    builtin = {
        "Inter": {
            "family": "Inter",
            "files": _scan_font_dir(os.path.join(FONTS_DIR, "Inter")),
            "builtin": True,
        },
        "Geist": {
            "family": "Geist Sans",
            "files": _scan_font_dir(os.path.join(FONTS_DIR, "Geist")),
            "builtin": True,
        },
        "Manrope": {
            "family": "Manrope",
            "files": _scan_font_dir(os.path.join(FONTS_DIR, "Manrope")),
            "builtin": True,
        },
    }

    for name, data in builtin.items():
        if data["files"]:
            fonts.append({"name": name, "family": data["family"], "builtin": True})

    # Custom fonts
    if os.path.exists(CUSTOM_FONTS_DIR):
        for f in os.listdir(CUSTOM_FONTS_DIR):
            if f.endswith((".woff2", ".woff", ".ttf", ".otf")):
                name = os.path.splitext(f)[0]
                fonts.append({"name": name, "family": name, "builtin": False, "filename": f})

    # System fallbacks
    fonts.extend([
        {"name": "System", "family": "system-ui, -apple-system, sans-serif", "builtin": True},
        {"name": "Monospace", "family": "'Courier New', Courier, monospace", "builtin": True},
    ])

    return fonts


def _scan_font_dir(dir_path: str) -> list:
    """List font files in a directory."""
    if not os.path.exists(dir_path):
        return []
    return [f for f in os.listdir(dir_path) if f.endswith((".woff2", ".woff", ".ttf", ".otf"))]


def sanitize_filename(filename: str) -> str:
    """Make a filename safe."""
    name = re.sub(r'[^\w\-.]', '_', filename)
    return name[:100]
