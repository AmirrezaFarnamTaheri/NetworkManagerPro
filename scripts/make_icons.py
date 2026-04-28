"""Generate tray PNG and Windows .ico from vector-inspired geometry (Pillow only)."""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def draw_mark(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margin = max(2, size // 10)
    d.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=size // 6,
        fill=(30, 32, 38, 255),
    )
    inset = size // 4
    d.rounded_rectangle(
        (inset, inset, size - inset, size - inset),
        radius=size // 10,
        fill=(46, 164, 114, 255),
    )
    bar_w = size // 2
    bar_h = max(2, size // 16)
    cx, cy = size // 2, size // 2
    d.rectangle((cx - bar_w // 2, cy - size // 5, cx + bar_w // 2, cy - size // 5 + bar_h), fill=(255, 255, 255, 255))
    d.rectangle((cx - bar_w // 2, cy - size // 12, cx + bar_w // 2, cy - size // 12 + bar_h), fill=(255, 255, 255, 220))
    d.rectangle((cx - bar_w // 2, cy + size // 40, cx + bar_w // 3, cy + size // 40 + bar_h), fill=(255, 255, 255, 200))
    return img


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for name, s in (("tray_64.png", 64), ("tray_48.png", 48)):
        draw_mark(s).save(os.path.join(ASSETS, name), format="PNG")

    ico_path = os.path.join(ASSETS, "app.ico")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    imgs = [draw_mark(w) for w, h in sizes]
    imgs[0].save(ico_path, format="ICO", append_images=imgs[1:])
    print("Wrote tray PNGs + app.ico in", ASSETS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
