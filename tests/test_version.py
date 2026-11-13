"""Version is defined once and surfaces everywhere it is shown."""

import re

from config import APP_VERSION


def test_version_format():
    assert re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION), APP_VERSION
    assert APP_VERSION == "0.2.0"


def test_version_api(client):
    assert client.get("/api/version").get_json() == {"version": APP_VERSION}


def test_version_in_page(client):
    html = client.get("/").data.decode()
    assert f'<meta name="app-version" content="{APP_VERSION}">' in html
    assert f"Version</span> {APP_VERSION}" in html
    # the old hardcoded value must be gone
    assert "0.1.0" not in html


def test_version_is_not_in_the_shell_world():
    """Guard against a stray hardcoded version sneaking back into the template."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    template = (root / "templates" / "index.html").read_text(encoding="utf-8")
    assert "{{ version }}" in template
