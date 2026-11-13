"""Shared terminal styling for botyaranewtab.

One palette for every console message: warm amber/orange for the brand, teal
for accents and success, so the CLI looks like the app instead of a rainbow.
"""

from rich.console import Console
from rich.text import Text
from rich.theme import Theme

# ─── Palette ───────────────────────────────────────────
AMBER = "#ffc857"
AMBER_DEEP = "#ff9f1c"
AMBER_PALE = "#ffe9b3"
TEAL = "#4ecdc4"
TEAL_DIM = "#3b9d96"
RED = "#ff6b6b"

theme = Theme({
    "brand": f"bold {AMBER}",
    "brand.deep": f"bold {AMBER_DEEP}",
    "brand.pale": AMBER_PALE,
    "accent": TEAL,
    "accent.dim": TEAL_DIM,
    "ok": f"bold {TEAL}",
    "warn": AMBER_DEEP,
    "err": f"bold {RED}",
    "hint": f"dim {AMBER_PALE}",
    "value": f"bold {AMBER_PALE}",
    "link": f"underline {AMBER}",
})

# highlight=False: rich otherwise repaints numbers ("v0.2.0") on its own
console = Console(theme=theme, highlight=False)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def gradient_text(text: str, stops: list[str], bold: bool = True) -> Text:
    """Paint text with a smooth gradient across the given colour stops."""
    chars = list(text)
    if len(chars) < 2:
        return Text(text, style=("bold " if bold else "") + stops[0])

    rgb_stops = [_hex_to_rgb(c) for c in stops]
    segments = len(rgb_stops) - 1
    out = Text()

    for index, char in enumerate(chars):
        if char == " ":
            out.append(char)
            continue
        position = index / (len(chars) - 1) * segments
        seg = min(int(position), segments - 1)
        local = position - seg
        start, end = rgb_stops[seg], rgb_stops[seg + 1]
        color = _rgb_to_hex(tuple(s + (e - s) * local for s, e in zip(start, end)))
        out.append(char, style=("bold " if bold else "") + color)

    return out


BRAND_GRADIENT = [AMBER_PALE, AMBER, AMBER_DEEP]

TAGLINE = "your new tab, your rules"
SYMBOLS = {"ok": "✓", "warn": "!", "err": "✗", "bullet": "›", "arrow": "→"}
