"""Database layer with migrations for botyaranewtab."""

import sqlite3
import json
import os
import time
from config import DB_PATH, DB_VERSION


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS shortcuts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            icon_path TEXT,
            custom_icon_path TEXT,
            color TEXT,
            group_name TEXT DEFAULT '',
            position INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            created_at REAL,
            updated_at REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS backgrounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT,
            dominant_color TEXT,
            palette TEXT,
            created_at REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT DEFAULT '',
            updated_at REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS countdowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_date TEXT NOT NULL,
            count_up INTEGER DEFAULT 0,
            emoji TEXT DEFAULT '📅',
            created_at REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS world_clocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            timezone TEXT NOT NULL,
            position INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            engine TEXT,
            searched_at REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS custom_fonts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at REAL
        )
    """)

    defaults = get_default_settings()
    for key, value in defaults.items():
        c.execute(
            "INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time())
        )

    c.execute("INSERT OR IGNORE INTO notes (id, content, updated_at) VALUES (1, '', ?)", (time.time(),))

    c.execute(
        "INSERT OR IGNORE INTO meta (key, value) VALUES ('db_version', ?)",
        (str(DB_VERSION),)
    )

    conn.commit()
    conn.close()


def get_default_settings():
    return {
        # General
        "language": "auto",
        "username": "",
        "first_run": True,
        "title_template": "{time} — botyaranewtab",

        # Search
        "search_engine": "google",
        "search_bangs": True,
        "search_history_enabled": True,
        "search_autocomplete": True,
        "search_calculator": True,
        "search_color_preview": True,
        "search_unit_converter": True,

        # Appearance
        "theme": "catppuccin-mocha",
        "accent_color": "#cba6f7",
        "auto_theme": False,
        "auto_theme_light": "catppuccin-latte",
        "auto_theme_dark": "catppuccin-mocha",
        "font_family": "Inter",
        "font_size_global": 16,
        "font_size_clock": 72,
        "font_size_greeting": 24,
        "font_size_shortcuts": 13,
        "border_radius": 12,
        "element_opacity": 0.85,
        "backdrop_blur": 20,
        "compact_mode": False,
        "layout": "center",
        "animation_type": "fade",

        # Background
        "bg_source": "theme",
        "bg_image_id": None,
        "bg_scale_mode": "cover",
        "bg_position": "center",
        "bg_solid_color": "#1e1e2e",
        "bg_gradient_from": "#1e1e2e",
        "bg_gradient_to": "#313244",
        "bg_gradient_angle": 135,
        "bg_blur": 0,
        "bg_dim": 0,
        "bg_brightness": 100,
        "bg_saturation": 100,
        "bg_grayscale": False,
        "bg_vignette": False,
        "bg_sepia": 0,
        "bg_parallax": False,
        "bg_ken_burns": False,
        "bg_rotate_enabled": False,
        "bg_rotate_interval": 30,
        "bg_adaptive_color": False,
        "bg_fill_blur": False,

        # Shortcuts
        "shortcuts_size": "medium",
        "shortcuts_show_labels": True,
        "shortcuts_columns": 0,

        # Widgets
        "widget_clock": True,
        "widget_greeting": True,
        "widget_weather": False,
        "widget_notes": False,
        "widget_countdowns": False,
        "widget_world_clocks": False,
        "widget_calendar": False,
        "widget_day_progress": False,

        # Clock
        "clock_format": "24h",         # "24h" | "12h"
        "clock_show_seconds": False,

        # Weather
        "weather_city": "",
        "weather_lat": None,
        "weather_lon": None,
        "weather_units": "celsius",

        # Sounds
        "sound_enabled": False,
        "sound_click": "",

        # Focus
        "focus_mode": False,
        "zen_mode": False,

        # Settings button
        "settings_button_style": "icon_corner",
        "settings_button_position": "bottom-right",
        "settings_right_click": True,
        "settings_click_greeting": False,
        "settings_in_search": False,

        # Advanced
        "pwa_enabled": True,
        "websocket_sync": True,
        "custom_css": "",
    }


def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return row["value"]
    return default


def set_setting(key, value):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), time.time())
    )
    conn.commit()
    conn.close()


def get_all_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    result = {}
    for row in rows:
        try:
            result[row["key"]] = json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            result[row["key"]] = row["value"]
    return result


def bulk_update_settings(data: dict):
    conn = get_db()
    now = time.time()
    for key, value in data.items():
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), now)
        )
    conn.commit()
    conn.close()
