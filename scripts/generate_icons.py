#!/usr/bin/env python3
"""Génère favicon / PWA / apple-touch à partir du motif pivoine (viewBox 24×24)."""

from pathlib import Path

from PIL import Image, ImageDraw

CREAM = "#FAF1EB"
PEONY = "#B86578"

# Géométrie identique à #i-peony dans frontend/index.html
PEONY_PARTS = [
    ("circle", 12, 12, 2.2, 2.2),
    ("ellipse", 12, 6.5, 2.4, 3.4),
    ("ellipse", 12, 17.5, 2.4, 3.4),
    ("ellipse", 6.5, 12, 3.4, 2.4),
    ("ellipse", 17.5, 12, 3.4, 2.4),
]

VIEW = 24.0
STROKE = 1.4
PADDING = 0.16  # marge égale — zone sûre maskable ~80 %


def render_icon(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size), CREAM)
    draw = ImageDraw.Draw(img)
    inner = size * (1 - 2 * PADDING)
    scale = inner / VIEW
    ox = size * PADDING
    stroke = max(1, round(STROKE * scale))

    def x(v: float) -> float:
        return ox + v * scale

    def y(v: float) -> float:
        return ox + v * scale

    for kind, cx, cy, rx, ry in PEONY_PARTS:
        bbox = (x(cx - rx), y(cy - ry), x(cx + rx), y(cy + ry))
        if kind == "circle":
            draw.ellipse(bbox, outline=PEONY, width=stroke)
        else:
            draw.ellipse(bbox, outline=PEONY, width=stroke)

    return img


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "frontend" / "icons"
    out.mkdir(parents=True, exist_ok=True)

    sizes = {
        "icon-512.png": 512,
        "icon-192.png": 192,
        "apple-touch-icon.png": 180,
        "favicon-32.png": 32,
    }
    for name, px in sizes.items():
        render_icon(px).save(out / name, optimize=True)
        print(f"  {out / name} ({px}×{px})")


if __name__ == "__main__":
    main()
