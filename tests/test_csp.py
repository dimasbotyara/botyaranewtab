"""Content-Security-Policy: the page must work without inline styles/scripts."""

import re

import pytest

INLINE_STYLE_ATTR = re.compile(rb"<[a-zA-Z][^>]*\sstyle=")


def test_csp_header_is_strict(client):
    csp = client.get("/").headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    # the whole point: no unsafe-inline / unsafe-eval anywhere
    assert "unsafe-inline" not in csp
    assert "unsafe-eval" not in csp
    assert "*" not in csp


def test_csp_and_other_headers_on_api_too(client):
    headers = client.get("/api/settings").headers
    assert "Content-Security-Policy" in headers
    assert headers["Cache-Control"] == "no-store"
    assert "Permissions-Policy" in headers


def test_page_has_no_inline_style_attributes(client):
    html = client.get("/").data
    assert not INLINE_STYLE_ATTR.search(html), "inline style= attribute would be blocked by CSP"


def test_page_has_no_inline_style_blocks(client):
    html = client.get("/").data
    assert b"<style" not in html
    assert b"style=" not in html.replace(b'rel="stylesheet"', b"")


def test_page_has_no_inline_scripts_or_handlers(client):
    html = client.get("/").data
    assert b"<script>" not in html
    assert b"onclick=" not in html and b"onload=" not in html and b"onerror=" not in html


def test_custom_css_is_served_as_a_stylesheet(client):
    css = "body { color: red }\n.hero { opacity: .9 }"
    assert client.post("/api/settings", json={"custom_css": css}).status_code == 200

    resp = client.get("/api/custom.css")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/css")
    assert css in resp.get_data(as_text=True)

    client.post("/api/settings", json={"custom_css": ""})
    assert client.get("/api/custom.css").get_data(as_text=True).strip() == ""


def test_custom_fonts_stylesheet(client):
    import io

    data = b"wOF2" + b"\x00" * 1500
    assert client.post("/api/fonts/install", data={
        "file": (io.BytesIO(data), "TestFace.woff2"),
    }, content_type="multipart/form-data").status_code == 200

    css = client.get("/api/fonts/custom.css").get_data(as_text=True)
    assert "text/css" in client.get("/api/fonts/custom.css").headers["Content-Type"]
    assert "@font-face" in css
    assert "font-family: 'TestFace'" in css
    assert "/static/fonts/Custom/TestFace.woff2" in css


def test_page_links_generated_stylesheets(client):
    html = client.get("/").data.decode()
    assert 'href="/api/custom.css"' in html
    assert 'href="/api/fonts/custom.css"' in html


@pytest.mark.parametrize("path", ["/static/manifest.json"])
def test_manifest_icons_exist(client, path):
    import json

    manifest = json.loads(client.get(path).data)
    for icon in manifest["icons"]:
        assert client.get(icon["src"]).status_code == 200, icon["src"]


def test_no_inline_style_in_js_templates():
    """Generated markup must not carry style= attributes either."""
    from pathlib import Path

    js_dir = Path(__file__).resolve().parent.parent / "static" / "js"
    offenders = []
    for file in js_dir.glob("*.js"):
        for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(("*", "//", "/*")):   # comments may mention it
                continue
            if 'style="' in line and "style.cssText" not in line:
                offenders.append(f"{file.name}:{number}")
    assert offenders == [], f"inline styles in JS templates: {offenders}"


def test_framing_can_be_relaxed_for_embedding(monkeypatch):
    """BOTYARA_FRAME_ANCESTORS is the documented escape hatch (previews, kiosks)."""
    import importlib

    monkeypatch.setenv("BOTYARA_FRAME_ANCESTORS", "'self' https://example.com")
    import app as app_module
    importlib.reload(app_module)

    headers = app_module.app.test_client().get("/").headers
    assert "frame-ancestors 'self' https://example.com" in headers["Content-Security-Policy"]
    assert "X-Frame-Options" not in headers

    monkeypatch.delenv("BOTYARA_FRAME_ANCESTORS")
    importlib.reload(app_module)
    assert "X-Frame-Options" in app_module.app.test_client().get("/").headers


def _stylesheet_links(html: str):
    import re
    return re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', html)


def test_all_stylesheets_resolve(client):
    html = client.get("/").data.decode()
    links = _stylesheet_links(html)
    assert len(links) >= 13, links
    for href in links:
        resp = client.get(href.split("?")[0])
        assert resp.status_code == 200, href
        assert resp.headers["Content-Type"].startswith("text/css"), href


def test_service_worker_assets_resolve(client):
    import re

    sw = client.get("/sw.js").data.decode()
    # only real precache entries (the script also mentions '/api/' in logic)
    block = sw.split("STATIC_ASSETS = [", 1)[1].split("];", 1)[0]
    assets = re.findall(r"'([^']+)'", block)
    assert len(assets) >= 15, assets
    for path in assets:
        assert client.get(path).status_code == 200, path


def test_css_is_split_into_modules():
    from pathlib import Path

    css_dir = Path(__file__).resolve().parent.parent / "static" / "css"
    files = sorted(p.name for p in css_dir.glob("*.css"))
    assert "style.css" not in files, "monolithic stylesheet should be gone"
    assert len(files) == 14, files
    # nothing should be left empty after the split
    for name in files:
        assert (css_dir / name).stat().st_size > 200, name
