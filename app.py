"""botyaranewtab — Flask application."""

import os
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from flask import (
    Flask, render_template, jsonify, request,
    send_from_directory, Response
)
from werkzeug.utils import secure_filename
from PIL import Image
from rich.console import Console

from config import (
    ICONS_DIR, BACKGROUNDS_DIR, BACKUPS_DIR, CUSTOM_FONTS_DIR
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
from utils import create_backup, restore_backup, get_available_fonts

console = Console()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

SEARCH_HISTORY_LIMIT = 500
ALLOWED_BG_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
ALLOWED_ICON_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico"}


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


# ─── Pages ──────────────────────────────────────────────

@app.route("/")
def index():
    settings = get_all_settings()
    return render_template("index.html", settings=settings)


# ─── Settings API ───────────────────────────────────────

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify(get_all_settings())


@app.route("/api/settings", methods=["POST"])
def api_update_settings():
    data = request.get_json(force=True)
    if data:
        updated_at = bulk_update_settings(data)
        return jsonify({"ok": True, "updated_at": updated_at})
    return jsonify({"ok": True})


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
    hour = int(request.args.get("hour", 12))
    lang = request.args.get("lang", "en")
    name = request.args.get("name", "")
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
    limit = int(request.args.get("limit", 20))
    conn = get_db()
    rows = conn.execute(
        "SELECT query, engine, searched_at FROM search_history ORDER BY searched_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/search/history", methods=["POST"])
def api_add_search_history():
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute(
        "INSERT INTO search_history (query, engine, searched_at) VALUES (?, ?, ?)",
        (data.get("query", ""), data.get("engine", ""), time.time())
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

    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT query FROM search_history WHERE lower(query) LIKE ? ORDER BY searched_at DESC LIMIT 10",
        (f"%{q}%",)
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
    data = request.get_json(force=True)
    url = data.get("url", "").strip()
    title = data.get("title", "").strip()

    if not url:
        return jsonify({"error": "URL required"}), 400

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    icon_path = get_favicon(url)

    if not title:
        from urllib.parse import urlparse
        title = urlparse(url).netloc.replace("www.", "")

    conn = get_db()
    now = time.time()
    c = conn.execute(
        """INSERT INTO shortcuts (title, url, icon_path, custom_icon_path, color, group_name, position, clicks, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
        (
            title, url, icon_path,
            data.get("custom_icon_path"),
            data.get("color", ""),
            data.get("group_name", ""),
            data.get("position", 0),
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
    data = request.get_json(force=True)
    conn = get_db()

    fields = []
    values = []
    for key in ["title", "url", "icon_path", "custom_icon_path", "color", "group_name", "position"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])

    if fields:
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

    valid = [
        s for s in shortcuts
        if isinstance(s, dict) and str(s.get("url", "")).startswith(("http://", "https://"))
    ]
    # Fetch favicons in parallel — sequential fetching makes large imports crawl
    with ThreadPoolExecutor(max_workers=8) as pool:
        icons = list(pool.map(lambda s: get_favicon(s["url"]), valid))

    for s, icon_path in zip(valid, icons):
        conn.execute(
            """INSERT INTO shortcuts (title, url, icon_path, group_name, position, clicks, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 0, ?, ?)""",
            (s.get("title", s["url"]), s["url"], icon_path, s.get("group_name", ""), 0, now, now)
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
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute(
        "UPDATE notes SET content = ?, updated_at = ? WHERE id = 1",
        (data.get("content", ""), time.time())
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
    data = request.get_json(force=True)
    conn = get_db()
    c = conn.execute(
        "INSERT INTO countdowns (title, target_date, count_up, emoji, created_at) VALUES (?, ?, ?, ?, ?)",
        (data["title"], data["target_date"], data.get("count_up", 0), data.get("emoji", "📅"), time.time())
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
    data = request.get_json(force=True)
    conn = get_db()
    c = conn.execute(
        "INSERT INTO world_clocks (label, timezone, position) VALUES (?, ?, ?)",
        (data["label"], data["timezone"], data.get("position", 0))
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
    return jsonify({"error": "Could not fetch weather"}), 500


@app.route("/api/weather/geocode")
def api_geocode():
    city = request.args.get("city", "")
    if not city:
        return jsonify({"error": "city required"}), 400
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
        return jsonify({"error": "Invalid font format"}), 400

    save_path = os.path.join(CUSTOM_FONTS_DIR, filename)
    f.save(save_path)

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
    return send_from_directory(BACKUPS_DIR, filename, as_attachment=True)


@app.route("/api/backup/restore", methods=["POST"])
def api_restore_backup():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    temp_path = os.path.join(BACKUPS_DIR, "temp_restore.db")
    f.save(temp_path)

    if restore_backup(temp_path):
        os.remove(temp_path)
        init_db()
        return jsonify({"ok": True})
    return jsonify({"error": "Restore failed"}), 500


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
        data = request.get_json(force=True)
    else:
        content = request.files["file"].read().decode("utf-8")
        data = json.loads(content)

    if data:
        bulk_update_settings(data)
        return jsonify({"ok": True})
    return jsonify({"error": "Invalid data"}), 400


# ─── Translations API ────────────────────────────────

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
