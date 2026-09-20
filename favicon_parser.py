"""Favicon parser — download and cache site icons for offline use."""

import os
import hashlib
import time
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from config import ICONS_DIR
from rich.console import Console

console = Console()


def get_favicon(url: str) -> str | None:
    """
    Try to fetch the best favicon for a URL.
    Returns the local path relative to static/ or None.
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)

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
            resp = requests.get(url, timeout=5, headers={
                "User-Agent": "Mozilla/5.0 (compatible; botyaranewtab/1.0)"
            })
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                icon_url = _find_best_icon(soup, url)
        except Exception as e:
            console.print(f"[dim]Could not fetch page {url}: {e}[/dim]")

        # Fallback: try /favicon.ico
        if not icon_url:
            icon_url = f"{parsed.scheme}://{domain}/favicon.ico"

        # Fallback: Google favicon service (works offline once cached)
        if not icon_url:
            icon_url = f"https://www.google.com/s2/favicons?sz=64&domain={domain}"

        # Download icon
        if icon_url:
            try:
                icon_resp = requests.get(icon_url, timeout=5, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; botyaranewtab/1.0)"
                })
                if icon_resp.status_code == 200 and len(icon_resp.content) > 0:
                    content_type = icon_resp.headers.get("content-type", "")
                    if "svg" in content_type:
                        ext = ".svg"
                    elif "ico" in content_type or icon_url.endswith(".ico"):
                        ext = ".ico"
                    elif "jpg" in content_type or "jpeg" in content_type:
                        ext = ".jpg"
                    else:
                        ext = ".png"

                    save_path = os.path.join(ICONS_DIR, f"{url_hash}{ext}")
                    with open(save_path, "wb") as f:
                        f.write(icon_resp.content)

                    console.print(f"[green]  Cached icon for {domain}[/green]")
                    return f"icons/{url_hash}{ext}"
            except Exception as e:
                console.print(f"[yellow]  Could not download icon: {e}[/yellow]")

    except Exception as e:
        console.print(f"[red]  Favicon error: {e}[/red]")

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
    elif best_href.startswith("/"):
        best_href = urljoin(base_url, best_href)
    elif not best_href.startswith("http"):
        best_href = urljoin(base_url, best_href)

    return best_href
