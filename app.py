"""botyaranewtab — Flask application."""

import ipaddress
import json
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlparse

from flask import (
    Flask, render_template, jsonify, request,
    send_from_directory, Response
)
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from PIL import Image

from config import (
    APP_VERSION, ICONS_DIR, BACKGROUNDS_DIR, BACKUPS_DIR, CUSTOM_FONTS_DIR
)
from database import (
    init_db, get_db, get_all_settings, bulk_update_settings, get_default_settings,
    get_settings_version
)
from greetings import get_greeting, get_all_greetings, get_time_period
from search_engine import parse_query, get_engines_list, get_bangs_list
from favicon_parser import get_favicon
from color_extractor import extract_colors
from weather import get_weather, geocode_city, reverse_geocode
from translations import TRANSLATIONS
from utils import (
    create_backup, restore_backup, get_available_fonts, detect_font_format, is_valid_backup
)

from console_ui import SYMBOLS, console

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

SEARCH_HISTORY_LIMIT = 500
MAX_IMPORT_ITEMS = 500
MAX_FONT_BYTES = 10 * 1024 * 1024
FONT_FAMILY_RE = re.compile(r"^[\w\- ]{1,64}$")
ALLOWED_BG_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
ALLOWED_ICON_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico"}

# ─── Local-only API hardening ───────────────────────────
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
LOCAL_HOST_SUFFIXES = (".local", ".lan", ".home", ".internal", ".localdomain", ".home.arpa")

# Extra hosts (e.g. a LAN name) allowed through, comma separated
_EXTRA_HOSTS = {
    h.strip().lower()
    for h in os.environ.get("BOTYARA_ALLOWED_HOSTS", "").split(",")
    if h.strip()
}

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{3,8}$")
MAX_SETTING_STR = 200_000          # generous, custom_css lives here
MAX_TEXT_FIELD = 2_000


def api_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def get_json_body():
    """Parse a JSON body from any content type, without raising.

    Returns (data, error_response). `force=True` is deliberately not used:
    ignoring Content-Type lets any web page POST here without a preflight.
    """
    data = request.get_json(silent=True)
    if data is None:
        return None, api_error("JSON body required", 400)
    if not isinstance(data, dict):
        return None, api_error("JSON object required", 400)
    return data, None


def get_db_setting_global(key: str):
    """Read one setting through a short-lived connection."""
    conn = get_db()
    try:
        return get_db_setting(conn, key)
    finally:
        conn.close()


def get_db_setting(conn, key: str):
    """Read a JSON setting value using an existing connection."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        return row["value"]


def is_valid_timezone(name: str) -> bool:
    """Validate an IANA timezone name (prevents junk in toLocaleTimeString)."""
    if not name or len(name) > 64:
        return False
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(name)
        return True
    except Exception:
        return False


def clean_text(value, limit: int = MAX_TEXT_FIELD) -> str:
    """Coerce to a trimmed, length-capped string (never None)."""
    if value is None:
        return ""
    text = str(value)
    return text[:limit]


def clean_color(value) -> str:
    """Only #rgb/#rrggbb/#rrggbbaa pass through; anything else becomes ''."""
    text = str(value or "").strip()
    return text if COLOR_RE.match(text) else ""


HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9\-._]*[a-z0-9])?$")


def clean_url(value) -> str:
    """Normalise a shortcut URL; only real http(s) URLs with a sane host pass.

    Blocks `javascript:`, `data:`, embedded quotes/newlines and ports that are
    not numbers (urlparse raises on those, which used to slip through).
    """
    url = str(value or "").strip()
    if not url:
        raise ValueError("URL required")
    if any(c.isspace() for c in url) or any(c in url for c in '"\'<>`\\'):
        raise ValueError("Invalid URL")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Invalid URL")

    try:
        host = parsed.hostname or ""
        parsed.port  # raises ValueError for "host:alert(1)"
    except ValueError:
        raise ValueError("Invalid URL")

    try:
        ascii_host = host.encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError):
        raise ValueError("Invalid URL")
    if not ascii_host or not HOST_RE.match(ascii_host):
        raise ValueError("Invalid URL")

    return url[:2048]


def clean_shortcut_fields(data: dict) -> dict:
    """Whitelist + validate every writable shortcut field."""
    out = {}
    if "url" in data:
        out["url"] = clean_url(data["url"])
    if "title" in data:
        out["title"] = clean_text(data["title"]) or clean_url(data.get("url", out.get("url", "")))
    for key in ("icon_path", "custom_icon_path"):
        if key in data:
            value = str(data[key] or "").strip()
            # only relative paths inside static/, no traversal, no scheme
            if value and ("://" in value or ".." in value or value.startswith(("/", "\\"))):
                value = ""
            out[key] = value[:255] or None
    if "color" in data:
        out["color"] = clean_color(data["color"])
    if "group_name" in data:
        out["group_name"] = clean_text(data["group_name"], 100)
    if "position" in data:
        try:
            out["position"] = int(data["position"])
        except (TypeError, ValueError):
            out["position"] = 0
    return out


def _hostname_of(value: str) -> str:
    """Hostname from a URL or a bare Host header value (IPv6-safe)."""
    if "://" not in value:
        value = "//" + value
    try:
        return (urlparse(value).hostname or "").lower()
    except ValueError:
        return ""


def is_trusted_host(host: str) -> bool:
    """Allow loopback, private/LAN IPs and local-looking hostnames only.

    Set BOTYARA_ALLOWED_HOSTS=* to disable the host check entirely — needed when
    the page is reached through a reverse proxy (no effect on JSON/Origin checks).
    """
    if "*" in _EXTRA_HOSTS:
        return True
    if not host:
        return False
    if host in LOOPBACK_HOSTS or host in _EXTRA_HOSTS:
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_private or ip.is_link_local
    except ValueError:
        pass
    if host.endswith(LOCAL_HOST_SUFFIXES):
        return True
    return "." not in host  # single-label machine name


@app.before_request
def guard_local_api():
    """Reject cross-site writes to the local API (CSRF / DNS rebinding).

    A page on another origin can send a "simple" text/plain POST here without a
    preflight; browsers set Sec-Fetch-Site / Origin for those, so we check them.
    """
    if not request.path.startswith("/api/"):
        return None
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None

    if request.headers.get("Sec-Fetch-Site", "").lower() == "cross-site":
        return api_error("Cross-site request blocked", 403)

    host = _hostname_of(request.host)
    if not is_trusted_host(host):
        return api_error("Host not allowed", 403)

    origin = request.headers.get("Origin")
    if origin:
        origin_host = _hostname_of(origin)
        if not is_trusted_host(origin_host) and origin_host != host:
            return api_error("Origin not allowed", 403)
    return None


# Strict Content-Security-Policy: no inline scripts, no inline styles, no
# third-party origins. Everything is served from this app.
# User customisation is delivered through /api/custom.css instead of <style>.
# Framing is denied by default (this page shows your private data).
# Set BOTYARA_FRAME_ANCESTORS to allow embedding, e.g. "*" or "'self' https://host".
FRAME_ANCESTORS = os.environ.get("BOTYARA_FRAME_ANCESTORS", "'none'").strip() or "'none'"

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self'",
    "worker-src 'self'",
    "manifest-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'none'",
    f"frame-ancestors {FRAME_ANCESTORS}",
])


@app.after_request
def security_headers(response):
    response.headers.setdefault("Content-Security-Policy", CSP)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    if FRAME_ANCESTORS == "'none'":
        response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "geolocation=(self), microphone=(), camera=()")
    if request.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.errorhandler(HTTPException)
def handle_http_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": error.description}), error.code
    return error


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    console.print(f"[err]{SYMBOLS['err']} unhandled error on {request.path}: {error!r}[/err]")
    if request.path.startswith("/api/"):
        return api_error("Internal server error", 500)
    return "Internal server error", 500


def verify_image(file_storage, allowed_extensions: set) -> bool:
    """Validate that an uploaded file is a real image of an allowed type."""
    filename = (file_storage.filename or "").lower()
    ext = os.path.splitext(filename)[1]
    if ext not in allowed_extensions:
        return False
    try:
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)
        img.verify()
        file_storage.stream.seek(0)
        return True
    except Exception:
        return False


# ─── User media (works with BOTYARA_DATA_DIR) ──────────
# Flask serves /static from the project folder, but uploads live in
# DATA_DIR/static/… which can be elsewhere. These routes are more specific
# than the static route, so they win and keep the existing URLs/DB paths.

@app.route("/static/icons/<path:filename>")
def media_icon(filename):
    return send_from_directory(ICONS_DIR, filename, max_age=86400)


@app.route("/static/backgrounds/<path:filename>")
def media_background(filename):
    return send_from_directory(BACKGROUNDS_DIR, filename, max_age=86400)


@app.route("/static/fonts/Custom/<path:filename>")
def media_font(filename):
    return send_from_directory(CUSTOM_FONTS_DIR, filename, max_age=86400)


# ─── Pages ──────────────────────────────────────────────

@app.route("/")
def index():
    # Settings are fetched by the page itself; only the version is rendered in
    return render_template("index.html", version=APP_VERSION)


@app.route("/api/version")
def api_version():
    return jsonify({"version": APP_VERSION})


# ─── Settings API ───────────────────────────────────────

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify(get_all_settings())


def filter_settings(data: dict) -> tuple[dict, dict]:
    """Keep known setting keys with sane, length-capped values."""
    known = get_default_settings()
    clean, rejected = {}, {}
    for key, value in data.items():
        if key not in known:
            rejected[key] = "unknown setting"
            continue
        if isinstance(value, str) and len(value) > MAX_SETTING_STR:
            rejected[key] = "value too long"
            continue
        if isinstance(value, (dict, list)) and len(json.dumps(value)) > MAX_SETTING_STR:
            rejected[key] = "value too large"
            continue
        if not isinstance(value, (str, int, float, bool, type(None), list, dict)):
            rejected[key] = "unsupported type"
            continue
        clean[key] = value
    return clean, rejected


@app.route("/api/settings", methods=["POST"])
def api_update_settings():
    data, error = get_json_body()
    if error:
        return error

    clean, rejected = filter_settings(data)
    if not clean:
        return api_error("No valid settings in request", 400)

    updated_at = bulk_update_settings(clean)
    payload = {"ok": True, "updated_at": updated_at}
    if rejected:
        payload["rejected"] = rejected
    return jsonify(payload)


@app.route("/api/settings/version")
def api_settings_version():
    return jsonify({"version": get_settings_version()})


@app.route("/api/settings/reset", methods=["POST"])
def api_reset_settings():
    defaults = get_default_settings()
    bulk_update_settings(defaults)
    return jsonify({"ok": True, "settings": defaults})


# ─── Greeting API ──────────────────────────────────────

@app.route("/api/greeting")
def api_greeting():
    # type=int falls back to the default on bad input, so check presence first
    hour = request.args.get("hour", type=int)
    if hour is None:
        if "hour" in request.args:
            return api_error("hour must be an integer", 400)
        hour = 12
    hour = min(max(hour, 0), 23)
    lang = request.args.get("lang", "en")
    if lang not in TRANSLATIONS:
        lang = "en"
    name = clean_text(request.args.get("name", ""), 60)
    return jsonify({
        "greeting": get_greeting(hour, lang, name),
        "period": get_time_period(hour),
    })


@app.route("/api/greetings/all")
def api_all_greetings():
    return jsonify(get_all_greetings())


# ─── Search API ────────────────────────────────────────

@app.route("/api/search/parse")
def api_search_parse():
    query = request.args.get("q", "")
    engine = request.args.get("engine", "google")
    result = parse_query(query, engine)
    return jsonify(result)


@app.route("/api/search/engines")
def api_search_engines():
    return jsonify(get_engines_list())


@app.route("/api/search/bangs")
def api_search_bangs():
    return jsonify(get_bangs_list())


@app.route("/api/search/history", methods=["GET"])
def api_search_history():
    limit = request.args.get("limit", type=int)
    if limit is None:
        if "limit" in request.args:
            return api_error("limit must be an integer", 400)
        limit = 20
    limit = min(max(limit, 1), 200)
    conn = get_db()
    rows = conn.execute(
        "SELECT query, engine, searched_at FROM search_history ORDER BY searched_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/search/history", methods=["POST"])
def api_add_search_history():
    data, error = get_json_body()
    if error:
        return error

    query = clean_text(data.get("query", ""), 500).strip()
    if not query:
        return api_error("query required", 400)

    conn = get_db()
    conn.execute(
        "INSERT INTO search_history (query, engine, searched_at) VALUES (?, ?, ?)",
        (query, clean_text(data.get("engine", ""), 40), time.time())
    )
    # Rotate: keep only the newest N entries
    conn.execute(
        f"""DELETE FROM search_history WHERE id NOT IN (
                SELECT id FROM search_history ORDER BY searched_at DESC LIMIT {SEARCH_HISTORY_LIMIT}
            )"""
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/search/history", methods=["DELETE"])
def api_clear_search_history():
    conn = get_db()
    conn.execute("DELETE FROM search_history")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/search/autocomplete")
def api_autocomplete():
    q = request.args.get("q", "").lower()
    if not q:
        return jsonify([])

    if len(q) > 200:
        return jsonify([])

    pattern = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT query FROM search_history "
        "WHERE lower(query) LIKE ? ESCAPE '\\' ORDER BY searched_at DESC LIMIT 10",
        (pattern,)
    ).fetchall()
    conn.close()
    return jsonify([r["query"] for r in rows])


# ─── Shortcuts API ─────────────────────────────────────

@app.route("/api/shortcuts", methods=["GET"])
def api_get_shortcuts():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM shortcuts ORDER BY group_name, position, id"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/shortcuts", methods=["POST"])
def api_add_shortcut():
    data, error = get_json_body()
    if error:
        return error

    if not str(data.get("url") or "").strip():
        return api_error("URL required", 400)

    try:
        fields = clean_shortcut_fields(data)
    except ValueError as exc:
        return api_error(str(exc), 400)

    url = fields["url"]
    icon_path = get_favicon(url)

    title = fields.get("title") or ""
    if not title:
        title = urlparse(url).netloc.replace("www.", "")

    conn = get_db()
    now = time.time()
    c = conn.execute(
        """INSERT INTO shortcuts (title, url, icon_path, custom_icon_path, color, group_name, position, clicks, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
        (
            title[:MAX_TEXT_FIELD], url, icon_path,
            fields.get("custom_icon_path"),
            fields.get("color", ""),
            fields.get("group_name", ""),
            fields.get("position", 0),
            now, now
        )
    )
    conn.commit()
    shortcut_id = c.lastrowid
    row = conn.execute("SELECT * FROM shortcuts WHERE id = ?", (shortcut_id,)).fetchone()
    conn.close()

    return jsonify(dict(row))


@app.route("/api/shortcuts/<int:sid>", methods=["PUT"])
def api_update_shortcut(sid):
    data, error = get_json_body()
    if error:
        return error

    try:
        # Same whitelist/validation as create: no javascript: URLs, no CSS breakout
        updates = clean_shortcut_fields(data)
    except ValueError as exc:
        return api_error(str(exc), 400)

    conn = get_db()
    if conn.execute("SELECT 1 FROM shortcuts WHERE id = ?", (sid,)).fetchone() is None:
        conn.close()
        return api_error("Shortcut not found", 404)

    if updates:
        fields = [f"{key} = ?" for key in updates]
        values = list(updates.values())
        fields.append("updated_at = ?")
        values.append(time.time())
        values.append(sid)
        conn.execute(f"UPDATE shortcuts SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()

    row = conn.execute("SELECT * FROM shortcuts WHERE id = ?", (sid,)).fetchone()
    conn.close()
    return jsonify(dict(row) if row else {})


@app.route("/api/shortcuts/<int:sid>", methods=["DELETE"])
def api_delete_shortcut(sid):
    conn = get_db()
    conn.execute("DELETE FROM shortcuts WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/shortcuts/<int:sid>/click", methods=["POST"])
def api_click_shortcut(sid):
    conn = get_db()
    conn.execute("UPDATE shortcuts SET clicks = clicks + 1 WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/shortcuts/icon", methods=["POST"])
def api_upload_shortcut_icon():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    if not verify_image(f, ALLOWED_ICON_EXTENSIONS):
        return jsonify({"error": "Invalid image file"}), 400

    filename = f"{uuid.uuid4().hex[:12]}_{secure_filename(f.filename)}"
    save_path = os.path.join(ICONS_DIR, filename)
    f.save(save_path)
    return jsonify({"path": f"icons/{filename}"})


@app.route("/api/shortcuts/export")
def api_export_shortcuts():
    conn = get_db()
    rows = conn.execute("SELECT * FROM shortcuts ORDER BY group_name, position").fetchall()
    conn.close()
    data = [dict(r) for r in rows]
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=shortcuts.json"}
    )


@app.route("/api/shortcuts/import", methods=["POST"])
def api_import_shortcuts():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    if not f.filename:
        return api_error("No file", 400)
    content = f.read().decode("utf-8", errors="ignore")

    shortcuts = []
    try:
        if f.filename.endswith(".json"):
            shortcuts = json.loads(content)
        elif f.filename.endswith((".html", ".htm")):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            for a in soup.find_all("a", href=True):
                shortcuts.append({
                    "title": a.get_text(strip=True) or a["href"],
                    "url": a["href"],
                })
    except (json.JSONDecodeError, ValueError):
        return jsonify({"error": "Could not parse file"}), 400

    if not isinstance(shortcuts, list):
        return jsonify({"error": "Could not parse file"}), 400

    conn = get_db()
    now = time.time()
    added = 0

    valid = []
    for item in shortcuts[:MAX_IMPORT_ITEMS]:
        if not isinstance(item, dict):
            continue
        try:
            url = clean_url(item.get("url", ""))
        except ValueError:
            continue
        valid.append({
            "url": url,
            "title": clean_text(item.get("title") or url)[:MAX_TEXT_FIELD],
            "group_name": clean_text(item.get("group_name"), 100),
        })
    # Fetch favicons in parallel — sequential fetching makes large imports crawl
    with ThreadPoolExecutor(max_workers=8) as pool:
        icons = list(pool.map(lambda s: get_favicon(s["url"]), valid))

    for s, icon_path in zip(valid, icons):
        conn.execute(
            """INSERT INTO shortcuts (title, url, icon_path, group_name, position, clicks, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 0, ?, ?)""",
            (s["title"] or s["url"], s["url"], icon_path, s["group_name"], 0, now, now)
        )
        added += 1
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "added": added})


# ─── Backgrounds API ──────────────────────────────────

@app.route("/api/backgrounds", methods=["GET"])
def api_get_backgrounds():
    conn = get_db()
    rows = conn.execute("SELECT * FROM backgrounds ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/backgrounds", methods=["POST"])
def api_upload_background():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    if not verify_image(f, ALLOWED_BG_EXTENSIONS):
        return jsonify({"error": "Invalid image file"}), 400

    original = f.filename
    filename = f"{uuid.uuid4().hex[:12]}_{secure_filename(original)}"
    save_path = os.path.join(BACKGROUNDS_DIR, filename)
    f.save(save_path)

    colors = extract_colors(save_path)

    conn = get_db()
    c = conn.execute(
        "INSERT INTO backgrounds (filename, original_name, dominant_color, palette, created_at) VALUES (?, ?, ?, ?, ?)",
        (filename, original, colors["dominant"], json.dumps(colors["palette"]), time.time())
    )
    conn.commit()
    bg_id = c.lastrowid
    row = conn.execute("SELECT * FROM backgrounds WHERE id = ?", (bg_id,)).fetchone()
    conn.close()

    return jsonify(dict(row))


@app.route("/api/backgrounds/<int:bid>", methods=["DELETE"])
def api_delete_background(bid):
    conn = get_db()
    row = conn.execute("SELECT filename FROM backgrounds WHERE id = ?", (bid,)).fetchone()
    if row:
        filepath = os.path.join(BACKGROUNDS_DIR, row["filename"])
        if os.path.exists(filepath):
            os.remove(filepath)
        conn.execute("DELETE FROM backgrounds WHERE id = ?", (bid,))
        # Don't leave the page pointing at a file that no longer exists
        if get_db_setting(conn, "bg_image_id") == bid:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('bg_image_id', 'null', ?)",
                (time.time(),)
            )
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('bg_source', ?, ?)",
                (json.dumps("theme"), time.time())
            )
        conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/backgrounds/<int:bid>/colors")
def api_bg_colors(bid):
    conn = get_db()
    row = conn.execute("SELECT filename FROM backgrounds WHERE id = ?", (bid,)).fetchone()
    conn.close()
    if row:
        filepath = os.path.join(BACKGROUNDS_DIR, row["filename"])
        colors = extract_colors(filepath)
        return jsonify(colors)
    return jsonify({"error": "Not found"}), 404


# ─── Notes API ─────────────────────────────────────────

@app.route("/api/notes", methods=["GET"])
def api_get_notes():
    conn = get_db()
    row = conn.execute("SELECT content, updated_at FROM notes WHERE id = 1").fetchone()
    conn.close()
    return jsonify(dict(row) if row else {"content": "", "updated_at": 0})


@app.route("/api/notes", methods=["POST"])
def api_save_notes():
    data, error = get_json_body()
    if error:
        return error

    content = data.get("content", "")
    if not isinstance(content, str):
        return api_error("content must be a string", 400)
    if len(content) > 100_000:
        return api_error("note too long", 413)

    conn = get_db()
    conn.execute(
        "UPDATE notes SET content = ?, updated_at = ? WHERE id = 1",
        (content, time.time())
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ─── Countdowns API ───────────────────────────────────

@app.route("/api/countdowns", methods=["GET"])
def api_get_countdowns():
    conn = get_db()
    rows = conn.execute("SELECT * FROM countdowns ORDER BY target_date").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/countdowns", methods=["POST"])
def api_add_countdown():
    data, error = get_json_body()
    if error:
        return error

    title = clean_text(data.get("title"), 120).strip()
    target_date = clean_text(data.get("target_date"), 40).strip()
    if not title:
        return api_error("title required", 400)
    if not target_date:
        return api_error("target_date required", 400)

    conn = get_db()
    c = conn.execute(
        "INSERT INTO countdowns (title, target_date, count_up, emoji, created_at) VALUES (?, ?, ?, ?, ?)",
        (title, target_date, 1 if data.get("count_up") else 0,
         clean_text(data.get("emoji") or "📅", 16), time.time())
    )
    conn.commit()
    cid = c.lastrowid
    row = conn.execute("SELECT * FROM countdowns WHERE id = ?", (cid,)).fetchone()
    conn.close()
    return jsonify(dict(row))


@app.route("/api/countdowns/<int:cid>", methods=["DELETE"])
def api_delete_countdown(cid):
    conn = get_db()
    conn.execute("DELETE FROM countdowns WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ─── World Clocks API ─────────────────────────────────

@app.route("/api/world-clocks", methods=["GET"])
def api_get_world_clocks():
    conn = get_db()
    rows = conn.execute("SELECT * FROM world_clocks ORDER BY position").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/world-clocks", methods=["POST"])
def api_add_world_clock():
    data, error = get_json_body()
    if error:
        return error

    label = clean_text(data.get("label"), 60).strip()
    timezone_name = clean_text(data.get("timezone"), 64).strip()
    if not label:
        return api_error("label required", 400)
    if not is_valid_timezone(timezone_name):
        return api_error("unknown timezone", 400)

    try:
        position = int(data.get("position", 0))
    except (TypeError, ValueError):
        position = 0

    conn = get_db()
    c = conn.execute(
        "INSERT INTO world_clocks (label, timezone, position) VALUES (?, ?, ?)",
        (label, timezone_name, position)
    )
    conn.commit()
    wid = c.lastrowid
    row = conn.execute("SELECT * FROM world_clocks WHERE id = ?", (wid,)).fetchone()
    conn.close()
    return jsonify(dict(row))


@app.route("/api/world-clocks/<int:wid>", methods=["DELETE"])
def api_delete_world_clock(wid):
    conn = get_db()
    conn.execute("DELETE FROM world_clocks WHERE id = ?", (wid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ─── Weather API ──────────────────────────────────────

@app.route("/api/weather")
def api_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    units = request.args.get("units", "celsius")

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400

    data = get_weather(lat, lon, units)
    if data:
        return jsonify(data)
    return jsonify({"error": "Weather providers unavailable"}), 502


@app.route("/api/weather/geocode")
def api_geocode():
    city = clean_text(request.args.get("city", ""), 120).strip()
    if not city:
        return api_error("city required", 400)
    result = geocode_city(city)
    if result:
        return jsonify(result)
    return jsonify({"error": "City not found"}), 404


@app.route("/api/weather/reverse")
def api_reverse_geocode():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400
    result = reverse_geocode(lat, lon)
    if result:
        return jsonify(result)
    return jsonify({"error": "Location not found"}), 404


# ─── Fonts API ────────────────────────────────────────

@app.route("/api/fonts")
def api_get_fonts():
    return jsonify(get_available_fonts())


@app.route("/api/fonts/install", methods=["POST"])
def api_install_font():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename)
    if not filename.endswith((".woff2", ".woff", ".ttf", ".otf")):
        return api_error("Invalid font format", 400)

    # Extension alone proves nothing: check the real font signature
    data = f.read()
    if len(data) > MAX_FONT_BYTES:
        return api_error("Font file too large", 413)
    fmt = detect_font_format(data)
    if fmt is None:
        return api_error("File is not a valid font", 400)

    filename = os.path.splitext(filename)[0][:80] + "." + fmt
    save_path = os.path.join(CUSTOM_FONTS_DIR, filename)
    with open(save_path, "wb") as out:
        out.write(data)

    name = os.path.splitext(filename)[0]

    conn = get_db()
    conn.execute(
        "INSERT INTO custom_fonts (name, filename, created_at) VALUES (?, ?, ?)",
        (name, filename, time.time())
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "name": name, "filename": filename})


# ─── Data / Backup API ────────────────────────────────

@app.route("/api/backup/create")
def api_create_backup():
    filename = create_backup()
    return send_from_directory(BACKUPS_DIR, os.path.basename(filename), as_attachment=True)


@app.route("/api/backup/restore", methods=["POST"])
def api_restore_backup():
    if "file" not in request.files:
        return api_error("No file", 400)

    f = request.files["file"]
    if not f.filename:
        return api_error("No file", 400)
    # Unique temp file: two concurrent restores must not overwrite each other
    temp_path = os.path.join(BACKUPS_DIR, f"restore_{uuid.uuid4().hex[:12]}.db")

    try:
        f.save(temp_path)
        if not is_valid_backup(temp_path):
            # Nothing has been touched yet — the live database is intact
            return api_error("Not a valid botyaranewtab backup", 400)

        if not restore_backup(temp_path):
            return api_error("Restore failed, your data is unchanged", 500)

        init_db()
        return jsonify({"ok": True})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.route("/api/settings/export")
def api_export_settings():
    settings = get_all_settings()
    return Response(
        json.dumps(settings, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=botyaranewtab_settings.json"}
    )


@app.route("/api/settings/import", methods=["POST"])
def api_import_settings():
    if "file" not in request.files:
        data = request.get_json(silent=True)
    else:
        raw = request.files["file"].read()
        if len(raw) > 4 * 1024 * 1024:
            return api_error("Settings file too large", 413)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return api_error("Could not parse settings file", 400)

    if not isinstance(data, dict) or not data:
        return api_error("Invalid data", 400)

    clean, rejected = filter_settings(data)
    if not clean:
        return api_error("No valid settings in file", 400)

    bulk_update_settings(clean)
    payload = {"ok": True}
    if rejected:
        payload["rejected"] = rejected
    return jsonify(payload)


# ─── Translations API ────────────────────────────────

# ─── User stylesheets ─────────────────────────────────

@app.route("/api/custom.css")
def custom_css():
    """User's custom CSS, served as a real stylesheet (CSP-friendly)."""
    css = get_db_setting_global("custom_css") or ""
    if not isinstance(css, str):
        css = ""
    return Response(css, mimetype="text/css",
                    headers={"Cache-Control": "no-store"})


@app.route("/api/fonts/custom.css")
def custom_fonts_css():
    """@font-face rules for user-installed fonts."""
    rules = []
    if os.path.isdir(CUSTOM_FONTS_DIR):
        for filename in sorted(os.listdir(CUSTOM_FONTS_DIR)):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in (".woff2", ".woff", ".ttf", ".otf"):
                continue
            family = os.path.splitext(filename)[0]
            if not FONT_FAMILY_RE.match(family):
                continue
            fmt = ext.lstrip(".")
            rules.append(
                "@font-face {"
                f" font-family: '{family}';"
                f" src: url('/static/fonts/Custom/{quote(filename)}') format('{fmt}');"
                " font-weight: 100 900; font-style: normal; font-display: swap;"
                " }"
            )
    return Response("\n".join(rules), mimetype="text/css",
                    headers={"Cache-Control": "no-store"})


@app.route("/api/translations")
def api_translations():
    lang = request.args.get("lang")
    if lang and lang in TRANSLATIONS:
        return jsonify(TRANSLATIONS[lang])
    return jsonify(TRANSLATIONS)


# ─── Service Worker & PWA ────────────────────────────

@app.route("/sw.js")
def service_worker():
    return send_from_directory("static/js", "sw.js", mimetype="application/javascript")


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json", mimetype="application/json")
