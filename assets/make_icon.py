#!/usr/bin/env python3
"""Draw the Work Buddy icon set.

Kept as code rather than checked-in art so the whole set can be regenerated at any
size. The mark is a companion whose eyes are open while tracking and closed while
paused — the only metaphor that stays legible at the 22pt the menu bar gives you.

Run: python3 assets/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
SS = 16  # supersample factor, downsampled at the end for clean edges

INK = (24, 26, 43, 255)        # near-black indigo, the body
FACE = (247, 244, 236, 255)    # warm cream, the eyes
ACCENT = (108, 227, 176, 255)  # mint, the "recording" pip


def _face(size, body, eye, *, asleep=False, pip=None, radius_ratio=0.28):
    """One buddy at `size` px: rounded square, two eyes, optional corner pip."""
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    pad = s * 0.06
    d.rounded_rectangle([pad, pad, s - pad, s - pad],
                        radius=s * radius_ratio, fill=body)

    # eyes sit slightly above centre — below it the face reads as a sad mask
    cy = s * 0.46
    dx = s * 0.17
    r = s * 0.085
    for cx in (s / 2 - dx, s / 2 + dx):
        if asleep:
            # a closed eye is a bar, not a thin line: a 1px line vanishes at 22pt
            h = r * 0.62
            d.rounded_rectangle([cx - r * 1.15, cy - h / 2, cx + r * 1.15, cy + h / 2],
                                radius=h / 2, fill=eye)
        else:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=eye)

    # a small smile, only at sizes where it survives the downsample
    if size >= 64 and not asleep:
        w = s * 0.16
        d.arc([s / 2 - w, cy + r * 0.9, s / 2 + w, cy + r * 0.9 + w * 1.5],
              start=15, end=165, fill=eye, width=int(s * 0.022))

    if pip:
        pr = s * 0.085
        px, py = s - pad - pr * 1.9, pad + pr * 1.9
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=pip)

    return img.resize((size, size), Image.LANCZOS)


def app_icon(size, asleep=False):
    return _face(size, INK, FACE, asleep=asleep,
                 pip=None if asleep else ACCENT)


def menubar(size, asleep=False):
    """Monochrome template image: macOS inverts these for light/dark automatically."""
    black = (0, 0, 0, 255)
    # the eyes must be punched out, not painted, so the icon works on any background
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # generous transparent margin: SwiftBar renders this at the bar's full height, so
    # a glyph drawn edge to edge looks enormous next to normal menu bar icons
    # snap the box to whole output pixels so its edges land on pixel boundaries
    # instead of straddling them, which is what reads as blur at this size
    unit = SS
    pad = round(s * 0.19 / unit) * unit
    d.rounded_rectangle([pad, pad, s - pad - 1, s - pad - 1],
                        radius=s * 0.11, fill=black)
    cy, dx, r = s * 0.50, s * 0.105, s * 0.058
    for cx in (s / 2 - dx, s / 2 + dx):
        if asleep:
            h = r * 0.62
            d.rounded_rectangle([cx - r * 1.15, cy - h / 2, cx + r * 1.15, cy + h / 2],
                                radius=h / 2, fill=(0, 0, 0, 0))
        else:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, 0))
    img = img.resize((size, size), Image.LANCZOS)
    if asleep:
        # a template image keeps its alpha, so a dimmed glyph reads as "asleep" in the
        # bar itself — the closed eyes alone are easy to miss at this size
        a = img.split()[3].point(lambda v: int(v * 0.55))
        img.putalpha(a)
    return img


def main():
    for n in (1024, 512, 256, 128, 64, 32):
        app_icon(n).save(OUT / f"icon-{n}.png")
    app_icon(256, asleep=True).save(OUT / "icon-paused-256.png")
    # menu bar wants 22pt: ship @1x and @2x, awake and asleep
    for tag, asleep in (("tracking", False), ("paused", True)):
        menubar(22, asleep).save(OUT / f"menubar-{tag}.png")
        menubar(44, asleep).save(OUT / f"menubar-{tag}@2x.png")
    print("wrote:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
