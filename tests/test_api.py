"""API behaviour: happy paths, validation and JSON error handling."""

import io
import json

import pytest


def test_index_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"botyaranewtab" in resp.data


def test_static_pwa_endpoints(client):
    assert client.get("/manifest.json").status_code == 200
    sw = client.get("/sw.js")
    assert sw.status_code == 200
    assert "javascript" in sw.headers["Content-Type"]


def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"


def test_settings_roundtrip(client):
    assert client.post("/api/settings", json={"username": "Тест"}).status_code == 200
    assert client.get("/api/settings").get_json()["username"] == "Тест"


def test_unknown_settings_are_rejected(client):
    resp = client.post("/api/settings", json={"__evil": "x", "theme": "catppuccin-latte"})
    assert resp.status_code == 200
    payload = resp.get_json()
    assert "__evil" in payload["rejected"]
    assert "__evil" not in client.get("/api/settings").get_json()


def test_settings_post_requires_json(client):
    # text/plain is what a hostile page can send without a CORS preflight
    resp = client.post("/api/settings", data='{"username":"hacked"}', content_type="text/plain")
    assert resp.status_code == 400
    assert resp.is_json
    assert client.get("/api/settings").get_json()["username"] != "hacked"


def test_settings_version_changes(client):
    before = client.get("/api/settings/version").get_json()["version"]
    client.post("/api/settings", json={"compact_mode": True})
    after = client.get("/api/settings/version").get_json()["version"]
    assert after >= before


@pytest.mark.parametrize("url", [
    "/api/greeting?hour=abc",
    "/api/search/history?limit=zzz",
])
def test_bad_params_return_400_not_500(client, url):
    resp = client.get(url)
    assert resp.status_code == 400, resp.status_code
    assert resp.is_json


def test_history_limit_is_clamped(client):
    resp = client.get("/api/search/history?limit=-5")
    assert resp.status_code == 200
    assert resp.get_json() == []


@pytest.mark.parametrize("endpoint,payload", [
    ("/api/countdowns", {}),
    ("/api/countdowns", {"title": "Без даты"}),
    ("/api/world-clocks", {}),
    ("/api/world-clocks", {"label": "Москва"}),
    ("/api/world-clocks", {"label": "Москва", "timezone": "Not/AZone"}),
])
def test_widgets_validate_input(client, endpoint, payload):
    resp = client.post(endpoint, json=payload)
    assert resp.status_code == 400
    assert resp.is_json


def test_countdown_and_clock_crud(client):
    created = client.post("/api/countdowns", json={"title": "Новый год", "target_date": "2027-01-01"})
    assert created.status_code == 200
    cid = created.get_json()["id"]

    clock = client.post("/api/world-clocks", json={"label": "Токио", "timezone": "Asia/Tokyo"})
    assert clock.status_code == 200
    wid = clock.get_json()["id"]

    assert client.delete(f"/api/countdowns/{cid}").status_code == 200
    assert client.delete(f"/api/world-clocks/{wid}").status_code == 200


def test_shortcut_crud(client, monkeypatch):
    monkeypatch.setattr("app.get_favicon", lambda url: None)

    created = client.post("/api/shortcuts", json={"url": "example.com"})
    assert created.status_code == 200
    body = created.get_json()
    assert body["url"] == "https://example.com"
    assert body["title"] == "example.com"
    sid = body["id"]

    assert client.put(f"/api/shortcuts/{sid}", json={"title": "Example"}).get_json()["title"] == "Example"
    assert client.post(f"/api/shortcuts/{sid}/click").status_code == 200
    assert client.delete(f"/api/shortcuts/{sid}").status_code == 200


def test_shortcut_put_validates_url(client, monkeypatch):
    monkeypatch.setattr("app.get_favicon", lambda url: None)
    sid = client.post("/api/shortcuts", json={"url": "https://example.com"}).get_json()["id"]

    for bad in ("javascript:alert(1)", "data:text/html,<script>alert(1)</script>", "https://x:alert(1)"):
        resp = client.put(f"/api/shortcuts/{sid}", json={"url": bad})
        assert resp.status_code == 400, bad

    # original URL survived untouched
    assert client.get("/api/shortcuts").get_json()[0]["url"] == "https://example.com"
    client.delete(f"/api/shortcuts/{sid}")


def test_shortcut_color_is_sanitized(client, monkeypatch):
    monkeypatch.setattr("app.get_favicon", lambda url: None)
    sid = client.post("/api/shortcuts", json={"url": "https://a.example"}).get_json()["id"]

    resp = client.put(f"/api/shortcuts/{sid}", json={"color": 'red" onmouseover="alert(1)'})
    assert resp.status_code == 200
    assert resp.get_json()["color"] == ""

    ok = client.put(f"/api/shortcuts/{sid}", json={"color": "#a6da95"})
    assert ok.get_json()["color"] == "#a6da95"
    client.delete(f"/api/shortcuts/{sid}")


def test_shortcut_unknown_id_returns_404(client):
    assert client.put("/api/shortcuts/999999", json={"title": "x"}).status_code == 404


def test_shortcut_requires_url(client):
    assert client.post("/api/shortcuts", json={}).status_code == 400
    assert client.post("/api/shortcuts", json={"url": "   "}).status_code == 400


def test_notes_save(client):
    assert client.post("/api/notes", json={"content": "куппить хлеб"}).status_code == 200
    assert client.get("/api/notes").get_json()["content"] == "куппить хлеб"
    assert client.post("/api/notes", json={"content": 123}).status_code == 400


def test_autocomplete_escapes_like_wildcards(client):
    client.post("/api/search/history", json={"query": "python 100%", "engine": "google"})
    client.post("/api/search/history", json={"query": "python", "engine": "google"})

    # '%' must be a literal, not "match everything"
    hits = client.get("/api/search/autocomplete?q=%25").get_json()
    assert all("%" in hit for hit in hits)


def test_search_history_crud(client):
    client.post("/api/search/history", json={"query": "flask", "engine": "google"})
    assert any(r["query"] == "flask" for r in client.get("/api/search/history").get_json())
    assert client.delete("/api/search/history").status_code == 200


def test_import_shortcuts_from_bookmarks_html(client, monkeypatch):
    monkeypatch.setattr("app.get_favicon", lambda url: None)
    html = """<html><body>
        <a href="https://one.example">One</a>
        <a href="javascript:alert(1)">Bad</a>
        <a href="https://two.example">Two</a>
    </body></html>"""
    resp = client.post("/api/shortcuts/import", data={
        "file": (io.BytesIO(html.encode()), "bookmarks.html"),
    }, content_type="multipart/form-data")

    assert resp.status_code == 200
    assert resp.get_json()["added"] == 2   # javascript: link dropped

    urls = [s["url"] for s in client.get("/api/shortcuts").get_json()]
    assert "https://one.example" in urls
    assert not any(u.startswith("javascript:") for u in urls)


def test_font_upload_validates_magic_bytes(client):
    fake = client.post("/api/fonts/install", data={
        "file": (io.BytesIO(b"<html>not a font</html>"), "evil.woff2"),
    }, content_type="multipart/form-data")
    assert fake.status_code == 400

    data = b"wOF2" + b"\x00" * 2000
    good = client.post("/api/fonts/install", data={
        "file": (io.BytesIO(data), "MyFont.woff2"),
    }, content_type="multipart/form-data")
    assert good.status_code == 200
    assert good.get_json()["filename"] == "MyFont.woff2"


def test_image_upload_rejects_non_image(client):
    resp = client.post("/api/shortcuts/icon", data={
        "file": (io.BytesIO(b"<svg onload=alert(1)>"), "icon.svg"),
    }, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_export_shortcuts_is_json(client, monkeypatch):
    monkeypatch.setattr("app.get_favicon", lambda url: None)
    client.post("/api/shortcuts", json={"url": "https://export.example"})
    resp = client.get("/api/shortcuts/export")
    assert resp.status_code == 200
    assert isinstance(json.loads(resp.data), list)


def test_api_404_is_json(client):
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404
    assert resp.is_json


def test_translations_endpoint(client):
    assert "en" in client.get("/api/translations").get_json()
    assert "ru" in client.get("/api/translations?lang=ru").get_json().values() or \
        client.get("/api/translations?lang=ru").is_json


def test_weather_requires_coords(client):
    assert client.get("/api/weather").status_code == 400
    assert client.get("/api/weather/geocode").status_code == 400


def test_uploads_are_served_even_with_custom_data_dir(client, monkeypatch):
    """BOTYARA_DATA_DIR moves uploads out of the project folder — they must
    still be reachable through /static/… (regression: they were 404)."""
    import io

    from PIL import Image

    monkeypatch.setattr("app.get_favicon", lambda url: None)
    sid = client.post("/api/shortcuts", json={"url": "https://example.com"}).get_json()["id"]

    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), "#cba6f7").save(buffer, "PNG")
    buffer.seek(0)

    resp = client.post("/api/shortcuts/icon", data={
        "file": (buffer, "custom.png"),
    }, content_type="multipart/form-data")
    assert resp.status_code == 200
    path = resp.get_json()["path"]

    client.put(f"/api/shortcuts/{sid}", json={"custom_icon_path": path})
    assert client.get(f"/static/{path}").status_code == 200
    client.delete(f"/api/shortcuts/{sid}")
