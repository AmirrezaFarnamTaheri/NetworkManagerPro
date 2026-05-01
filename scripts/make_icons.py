"""Generate Lucid Net tray PNG and Windows .ico assets with Pillow only."""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _gradient(size: int) -> Image.Image:
    top = (15, 118, 110, 255)
    mid = (19, 78, 74, 255)
    bottom = (11, 18, 32, 255)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    for y in range(size):
        t = y / max(1, size - 1)
        if t < 0.52:
            local = t / 0.52
            color = tuple(_lerp(top[i], mid[i], local) for i in range(4))
        else:
            local = (t - 0.52) / 0.48
            color = tuple(_lerp(mid[i], bottom[i], local) for i in range(4))
        for x in range(size):
            shade = int((x / max(1, size - 1)) * 10)
            pixels[x, y] = (
                max(0, color[0] - shade),
                max(0, color[1] - shade),
                max(0, color[2] - shade),
                color[3],
            )
    return img


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    margin = max(1, size // 16)
    d.rounded_rectangle((margin, margin, size - margin, size - margin), radius=radius, fill=255)
    return mask


def draw_mark(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = _rounded_mask(size, max(6, size // 5))
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_alpha = mask.filter(ImageFilter.GaussianBlur(max(1, size // 24)))
    shadow.putalpha(shadow_alpha.point(lambda p: int(p * 0.35)))
    img.alpha_composite(shadow)
    bg = _gradient(size)
    bg.putalpha(mask)
    img.alpha_composite(bg)

    d = ImageDraw.Draw(img)
    s = size / 128
    line_w = max(2, round(size * 0.075))
    accent_w = max(2, round(size * 0.07))

    d.line(
        [(31 * s, 82 * s), (31 * s, 43 * s), (47 * s, 43 * s), (47 * s, 73 * s), (76 * s, 73 * s)],
        fill=(248, 250, 252, 255),
        width=line_w,
        joint="curve",
    )
    d.line(
        [(53 * s, 84 * s), (53 * s, 47 * s), (84 * s, 81 * s), (84 * s, 44 * s)],
        fill=(94, 234, 212, 255),
        width=accent_w,
        joint="curve",
    )
    if size >= 32:
        dot_r = max(2, round(size * 0.04))
        for x, y in ((31, 43), (47, 73), (84, 44), (84, 81)):
            d.ellipse(
                ((x * s) - dot_r, (y * s) - dot_r, (x * s) + dot_r, (y * s) + dot_r),
                fill=(224, 242, 254, 255),
            )
    if size >= 48:
        d.arc(
            (24 * s, 76 * s, 106 * s, 112 * s),
            start=20,
            end=157,
            fill=(153, 246, 228, 190),
            width=max(1, round(size * 0.03)),
        )
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
