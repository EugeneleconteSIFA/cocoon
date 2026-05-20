#!/usr/bin/env python3
"""Génère favicon / PWA / apple-touch avec la pivoine Cocon (DA.md)."""

from pathlib import Path

from PIL import Image, ImageDraw

CREAM = "#FAF1EB"
PEONY = "#B86578"
PADDING = 0.14  # zone sûre maskable / home screen

# viewBox 0 0 24 24 — symbole #i-peony dans index.html
_PEONY_PARTS = (
    (12, 12, 2.2, 2.2),
    (12, 6.5, 2.4, 3.4),
    (12, 17.5, 2.4, 3.4),
    (6.5, 12, 3.4, 2.4),
    (17.5, 12, 3.4, 2.4),
)


def render_peony_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), CREAM)
    draw = ImageDraw.Draw(img)

    x0 = size * PADDING
    y0 = size * PADDING
    x1 = size * (1 - PADDING)
    y1 = size * (1 - PADDING)
    span = x1 - x0

    def tx(x: float) -> float:
        return x0 + (x / 24) * span

    def ty(y: float) -> float:
        return y0 + (y / 24) * span

    stroke = max(2, round(size * 1.45 / 24))

    for cx, cy, rx, ry in _PEONY_PARTS:
        draw.ellipse(
            (tx(cx - rx), ty(cy - ry), tx(cx + rx), ty(cy + ry)),
            outline=PEONY,
            width=stroke,
        )

    return img.convert("RGB")


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
        render_peony_icon(px).save(out / name, optimize=True)
        print(f"  {out / name} ({px}×{px})")


if __name__ == "__main__":
    main()
