"""Extract dominant color and palette from images using Pillow."""

import os
from PIL import Image
from collections import Counter


def extract_colors(image_path: str, num_colors: int = 6) -> dict:
    """
    Extract dominant color and palette from an image.
    Returns: {"dominant": "#hex", "palette": ["#hex", ...]}
    """
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")

        # Resize for speed
        img = img.resize((150, 150), Image.Resampling.LANCZOS)

        pixels = list(img.getdata())

        # Quantize to reduce similar colors
        quantized = []
        for r, g, b in pixels:
            qr = (r // 16) * 16
            qg = (g // 16) * 16
            qb = (b // 16) * 16
            quantized.append((qr, qg, qb))

        counter = Counter(quantized)
        most_common = counter.most_common(num_colors)

        palette = [f"#{r:02x}{g:02x}{b:02x}" for (r, g, b), _ in most_common]
        dominant = palette[0] if palette else "#1e1e2e"

        return {
            "dominant": dominant,
            "palette": palette,
        }
    except Exception as e:
        return {
            "dominant": "#1e1e2e",
            "palette": ["#1e1e2e"],
        }
