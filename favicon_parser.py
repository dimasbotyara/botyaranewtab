"""Favicon parser — download and cache site icons for offline use."""

import os
import hashlib
import ipaddress
import socket
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from config import ICONS_DIR
from console_ui import SYMBOLS, console

PAGE_MAX_BYTES = 2 * 1024 * 1024    # 2 MB of HTML is more than enough for <head>
ICON_MAX_BYTES = 5 * 1024 * 1024    # icons should be tiny; refuse anything bigger
REQUEST_TIMEOUT = 5
MAX_REDIRECTS = 2

USER_AGENT = "Mozilla/5.0 (compatible; botyaranewtab/1.0)"


def is_public_host(host: str) -> bool:
    """Reject loopback/private/link-local targets (SSRF guard).

    Imported bookmark files can contain any URL, so without this a batch
    import would happily scan the local network and cloud metadata endpoints.
    """
    if not host:
        return False
    host = host.strip("[]").lower()
    if host in ("localhost", "localhost.localdomain"):
        return False

    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except (socket.gaierror, UnicodeError):
        return False

    for addr in addresses:
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return False
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    return True


def _get(url: str, max_bytes: int) -> requests.Response | None:
    """GET with redirect + SSRF + size guards. Returns None if not acceptable."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not is_public_host(parsed.hostname or ""):
        return None

    resp = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        allow_redirects=False,
        stream=True,
    )

    hops = 0
    while resp.is_redirect and hops < MAX_REDIRECTS:
        target = resp.headers.get("location")
        resp.close()
        if not target:
            return None
        url = urljoin(url, target)
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not is_public_host(parsed.hostname or ""):
            return None
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=False,
            stream=True,
        )
        hops += 1

    if resp.is_redirect:
        resp.close()
        return None

    if resp.status_code != 200:
        resp.close()
        return None

    # Read with a hard cap instead of trusting Content-Length
    content = b""
    try:
        for chunk in resp.iter_content(64 * 1024):
            content += chunk
            if len(content) > max_bytes:
                content = b""
                break
    finally:
        resp.close()

    if not content:
        return None
    return content


def get_favicon(url: str) -> str | None:
    """
    Try to fetch the best favicon for a URL.
    Returns the local path relative to static/ or None.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            url = "https://" + url
            parsed = urlparse(url)
        if not is_public_host(parsed.hostname or ""):
            return None

        domain = parsed.netloc
        url_hash = hashlib.md5(domain.encode()).hexdigest()[:12]
        ext = ".png"

        # Check cache first
        for cached_ext in [".png", ".ico", ".svg", ".jpg"]:
            cached_path = os.path.join(ICONS_DIR, f"{url_hash}{cached_ext}")
            if os.path.exists(cached_path):
                return f"icons/{url_hash}{cached_ext}"

        # Try to find icon from page
        icon_url = None
        try:
            page = _get(url, PAGE_MAX_BYTES)
            if page:
                soup = BeautifulSoup(page, "html.parser")
                icon_url = _find_best_icon(soup, url)
        except Exception as e:
            console.print(f"[hint]  {SYMBOLS['bullet']} could not fetch page {url}: {e}[/hint]")

        # Fallback: try /favicon.ico
        if not icon_url:
            icon_url = f"{parsed.scheme}://{domain}/favicon.ico"

        if icon_url:
            try:
                content = _get(icon_url, ICON_MAX_BYTES)
                if content:
                    content_type = _detect_content_type(content)

                    if content_type == "svg":
                        # SVG is markup: refuse anything scriptable before saving
                        if b"<script" in content.lower() or b"onload" in content.lower():
                            content = None
                        ext = ".svg"
                    elif content_type == "ico":
                        ext = ".ico"
                    elif content_type == "jpg":
                        ext = ".jpg"
                    elif content_type == "png":
                        ext = ".png"
                    else:
                        content = None   # HTML/JSON/whatever — not an icon

                    if content:
                        save_path = os.path.join(ICONS_DIR, f"{url_hash}{ext}")
                        with open(save_path, "wb") as fh:
                            fh.write(content)
                        console.print(f"  [ok]{SYMBOLS['ok']}[/] [accent.dim]cached icon for[/] [brand.pale]{domain}[/]")
                        return f"icons/{url_hash}{ext}"
            except Exception as e:
                console.print(f"  [warn]{SYMBOLS['warn']}[/] [hint]could not download icon: {e}[/hint]")

    except Exception as e:
        console.print(f"  [err]{SYMBOLS['err']}[/] [hint]favicon error: {e}[/hint]")

    return None


def _detect_content_type(content: bytes) -> str | None:
    """Identify image bytes by signature — never trust the header."""
    head = content[:512]
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x00\x00\x01\x00"):
        return "ico"
    if head.startswith(b"\x00\x00\x02\x00"):
        return "ico"   # cursor, close enough
    stripped = head.lstrip()
    if stripped.startswith(b"<svg") or (stripped.startswith(b"<?xml") and b"<svg" in head):
        return "svg"
    return None


def _find_best_icon(soup: BeautifulSoup, base_url: str) -> str | None:
    """Find the best icon from HTML head."""
    candidates = []

    # Look for various link tags
    for rel in ["apple-touch-icon", "icon", "shortcut icon"]:
        links = soup.find_all("link", rel=lambda r: r and rel in (r if isinstance(r, str) else " ".join(r)).lower())
        for link in links:
            href = link.get("href")
            if href:
                size = 0
                sizes = link.get("sizes", "")
                if sizes and sizes != "any":
                    try:
                        size = int(sizes.split("x")[0])
                    except (ValueError, IndexError):
                        pass
                candidates.append((size, href))

    # Also check meta og:image as last resort
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        candidates.append((0, og["content"]))

    if not candidates:
        return None

    # Sort by size (prefer larger)
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_href = candidates[0][1]

    # Make absolute URL
    if best_href.startswith("//"):
        best_href = "https:" + best_href
    elif not best_href.startswith("http"):
        best_href = urljoin(base_url, best_href)

    return best_href
