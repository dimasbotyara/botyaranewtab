"""Regression tests for the security fixes (CSRF, data loss, DoS, SSRF)."""

import io
import os
import time

import pytest


# ─── CSRF / DNS rebinding ──────────────────────────────

def test_cross_site_origin_is_blocked(client):
    resp = client.post(
        "/api/settings",
        json={"username": "hacked"},
        headers={"Origin": "https://evil.example"},
    )
    assert resp.status_code == 403
    assert client.get("/api/settings").get_json()["username"] != "hacked"


def test_cross_site_fetch_metadata_is_blocked(client):
    resp = client.post(
        "/api/notes",
        json={"content": "pwned"},
        headers={"Sec-Fetch-Site": "cross-site"},
    )
    assert resp.status_code == 403


def test_same_origin_requests_still_work(client):
    resp = client.post(
        "/api/settings",
        json={"username": "ok"},
        headers={"Origin": "http://localhost", "Sec-Fetch-Site": "same-origin"},
    )
    assert resp.status_code == 200


def test_rebinding_host_is_blocked(client):
    # Attacker DNS points evil.example at 127.0.0.1: Host would be evil.example
    resp = client.post(
        "/api/settings",
        json={"username": "rebound"},
        environ_overrides={"HTTP_HOST": "evil.example"},
    )
    assert resp.status_code == 403


def test_lan_ip_host_is_allowed(client):
    resp = client.post(
        "/api/settings",
        json={"sync_enabled": True},
        environ_overrides={"HTTP_HOST": "192.168.1.20:12121"},
    )
    assert resp.status_code == 200


# ─── Backup / restore must never destroy data ──────────

def test_restore_rejects_garbage_and_keeps_database(client):
    client.post("/api/settings", json={"username": "живой"})

    resp = client.post("/api/backup/restore", data={
        "file": (io.BytesIO(b"definitely not a database"), "evil.db"),
    }, content_type="multipart/form-data")

    assert resp.status_code == 400
    # The app still works and the data is intact
    assert client.get("/api/settings").status_code == 200
    assert client.get("/api/settings").get_json()["username"] == "живой"


def test_restore_roundtrip_with_real_backup(client):
    client.post("/api/settings", json={"username": "до бэкапа"})
    backup = client.get("/api/backup/create")
    assert backup.status_code == 200
    assert backup.data[:15] == b"SQLite format 3"

    client.post("/api/settings", json={"username": "после бэкапа"})

    resp = client.post("/api/backup/restore", data={
        "file": (io.BytesIO(backup.data), "backup.db"),
    }, content_type="multipart/form-data")

    assert resp.status_code == 200
    assert client.get("/api/settings").status_code == 200
    assert client.get("/api/settings").get_json()["username"] == "до бэкапа"


def test_restore_leaves_no_temp_files(client):
    from config import BACKUPS_DIR

    client.post("/api/backup/restore", data={
        "file": (io.BytesIO(b"junk" * 100), "x.db"),
    }, content_type="multipart/form-data")
    leftovers = [f for f in os.listdir(BACKUPS_DIR) if f.startswith("restore_")]
    assert leftovers == []


# ─── Calculator DoS ────────────────────────────────────

@pytest.mark.parametrize("query", [
    "9**9**9**9",
    "9**99999",
    "10**10**10",
    "(" * 50 + "1" + ")" * 50,
])
def test_calculator_rejects_expensive_expressions_fast(client, query):
    started = time.monotonic()
    resp = client.get("/api/search/parse", query_string={"q": query})
    elapsed = time.monotonic() - started

    assert resp.status_code == 200
    assert elapsed < 1.0, f"{query!r} took {elapsed:.2f}s"
    assert resp.get_json()["type"] != "calculator"


# ─── SSRF in the favicon fetcher ───────────────────────

@pytest.mark.parametrize("url", [
    "http://127.0.0.1:12121/api/settings",
    "http://localhost/admin",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/",
])
def test_favicon_refuses_internal_targets(url):
    from favicon_parser import get_favicon

    assert get_favicon(url) is None


def test_public_host_check():
    from favicon_parser import is_public_host

    assert is_public_host("example.com") is True
    assert is_public_host("127.0.0.1") is False
    assert is_public_host("10.0.0.1") is False
    assert is_public_host("192.168.1.1") is False
    assert is_public_host("169.254.169.254") is False


# ─── Search input handling ─────────────────────────────

def test_search_query_is_percent_encoded(client):
    url = client.get("/api/search/parse", query_string={"q": "cat & dog"}).get_json()["url"]
    assert " " not in url and "& dog" not in url
    assert "cat+%26+dog" in url


def test_decimal_numbers_are_not_treated_as_domains(client):
    result = client.get("/api/search/parse", query_string={"q": "1.5"}).get_json()
    assert result["type"] == "redirect"
    assert result["url"].startswith("https://www.google.com/search")


def test_calculator_still_works(client):
    result = client.get("/api/search/parse", query_string={"q": "2+2"}).get_json()
    assert result["type"] == "calculator"
    assert result["result"] == "4"
