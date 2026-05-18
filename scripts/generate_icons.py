#!/usr/bin/env python3
"""Génère favicon / PWA / apple-touch à partir de frontend/icons/logo.jpg."""

from pathlib import Path

from PIL import Image

CREAM = "#FAF1EB"
PADDING = 0.08  # marge autour du logo (zone sûre maskable)


def _load_square_logo(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def render_icon(logo: Image.Image, size: int) -> Image.Image:
    bg = Image.new("RGBA", (size, size), CREAM)
    inner = int(size * (1 - 2 * PADDING))
    scaled = logo.resize((inner, inner), Image.Resampling.LANCZOS)
    offset = (size - inner) // 2
    bg.paste(scaled, (offset, offset), scaled)
    return bg.convert("RGB")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    # Source : placer logo-source.jpg à la racine du repo ou dans frontend/icons/
    src = root / "frontend" / "icons" / "logo-source.jpg"
    if not src.is_file():
        src = root / "scripts" / "logo-source.jpg"
    out = root / "frontend" / "icons"
    if not src.is_file():
        raise SystemExit(f"Source introuvable : {src}")

    logo = _load_square_logo(src)
    sizes = {
        "icon-512.png": 512,
        "icon-192.png": 192,
        "apple-touch-icon.png": 180,
        "favicon-32.png": 32,
    }
    for name, px in sizes.items():
        render_icon(logo, px).save(out / name, optimize=True)
        print(f"  {out / name} ({px}×{px})")


if __name__ == "__main__":
    main()
