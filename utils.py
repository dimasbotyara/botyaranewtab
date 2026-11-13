"""Utility functions for botyaranewtab."""

import os
import shutil
import sqlite3
import time
import uuid
from config import DB_PATH, BACKUPS_DIR, FONTS_DIR, CUSTOM_FONTS_DIR

# Tables a genuine botyaranewtab database must contain. Used to reject random
# uploads before they can replace a working database.
REQUIRED_TABLES = {"settings", "shortcuts"}


def _unique_backup_name(prefix: str = "botyaranewtab_backup") -> str:
    """Timestamped backup name that never collides within the same second."""
    stamp = time.strftime("%Y%m%d_%H%M%S")
    name = f"{prefix}_{stamp}.db"
    if os.path.exists(os.path.join(BACKUPS_DIR, name)):
        name = f"{prefix}_{stamp}_{uuid.uuid4().hex[:6]}.db"
    return name


def create_backup() -> str:
    """Create a database backup. Returns filename."""
    # Checkpoint the WAL so the copied file contains all committed data
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()

    filename = _unique_backup_name()
    dest = os.path.join(BACKUPS_DIR, filename)
    shutil.copy2(DB_PATH, dest)
    return filename


def is_valid_backup(backup_path: str) -> bool:
    """Check that a file really is a readable botyaranewtab SQLite database."""
    if not os.path.isfile(backup_path) or os.path.getsize(backup_path) < 1024:
        return False
    conn = None
    try:
        # Read-only + immutable: never creates WAL files next to the upload
        uri = f"file:{os.path.abspath(backup_path)}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not REQUIRED_TABLES <= tables:
            return False
        check = conn.execute("PRAGMA integrity_check").fetchone()
        return bool(check) and check[0] == "ok"
    except (sqlite3.Error, OSError):
        return False
    finally:
        if conn is not None:
            conn.close()


def restore_backup(backup_path: str) -> bool:
    """Restore database from backup.

    The current database is validated first and moved aside (not deleted) so a
    bad upload can never destroy user data: if anything fails, the previous
    database is put back in place.
    """
    if not is_valid_backup(backup_path):
        return False

    moved = []
    try:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        # Move the live database (and any WAL/SHM) out of the way
        for suffix in ("", "-wal", "-shm"):
            src = DB_PATH + suffix
            if os.path.exists(src):
                dest = os.path.join(BACKUPS_DIR, f"pre_restore_{stamp}.db{suffix}")
                shutil.move(src, dest)
                moved.append((dest, src))

        shutil.copy2(backup_path, DB_PATH)
        return True
    except (OSError, shutil.Error):
        # Roll back: put the original database back
        for dest, src in moved:
            try:
                if os.path.exists(src):
                    os.remove(src)
                shutil.move(dest, src)
            except OSError:
                pass
        return False


def detect_font_format(data: bytes) -> str | None:
    """Identify a font file by its magic bytes, not by its extension."""
    if data[:4] == b"wOF2":
        return "woff2"
    if data[:4] == b"wOFF":
        return "woff"
    if data[:5] == b"OTTO":
        return "otf"
    if data[:4] in (b"\x00\x01\x00\x00", b"true", b"ttcf"):
        return "ttf"
    return None


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
        for f in sorted(os.listdir(CUSTOM_FONTS_DIR)):
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
