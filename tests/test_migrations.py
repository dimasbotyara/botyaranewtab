"""Schema migrations."""

import sqlite3
import time


def test_legacy_sync_key_is_migrated(tmp_path, monkeypatch):
    import json

    import database

    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT, updated_at REAL)")
    conn.execute(
        "INSERT INTO settings VALUES ('websocket_sync', ?, ?)",
        (json.dumps(False), time.time()),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    database.init_db()

    assert database.get_setting("sync_enabled") is False   # user value preserved
    assert database.get_setting("websocket_sync") is None  # old key removed
    assert database.get_setting("theme")                   # defaults still applied


def test_init_is_idempotent(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "twice.db"))
    database.init_db()
    database.set_setting("username", "димас")
    database.init_db()

    assert database.get_setting("username") == "димас"
