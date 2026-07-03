#!/usr/bin/env python3
"""Generate placeholder images for image files referenced in the HTML but not
yet present in assets/images/. Real images can later be dropped in with the
same filenames to replace them. The list of generated placeholders is written
to tools/placeholder-manifest.txt.

Usage: python3 tools/make_placeholders.py
"""
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "assets" / "images"
MANIFEST = Path(__file__).resolve().parent / "placeholder-manifest.txt"

BG = (31, 41, 51)        # #1f2933 brand dark
FRAME = (62, 76, 89)     # #3e4c59
ORANGE = (228, 123, 2)   # #e47b02 brand orange
GRAY = (123, 135, 148)   # #7b8794
W, H = 1200, 900

FONT_CANDIDATES = [
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def referenced_images():
    refs = set()
    pattern = re.compile(r'(?:src|href)="[^"]*assets/images/([^"]+)"')
    for html in list(ROOT.glob("*.html")) + list((ROOT / "events").glob("*.html")):
        refs.update(pattern.findall(html.read_text()))
    return sorted(refs)


def make_placeholder(name: str):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([24, 24, W - 25, H - 25], outline=FRAME, width=4)

    title_font = load_font(72)
    name_font = load_font(30)

    title = "IMAGE COMING SOON"
    tw = draw.textlength(title, font=title_font)
    draw.text(((W - tw) / 2, H / 2 - 80), title, fill=ORANGE, font=title_font)

    nw = draw.textlength(name, font=name_font)
    draw.text(((W - nw) / 2, H / 2 + 30), name, fill=GRAY, font=name_font)

    out = IMAGES / name
    if name.lower().endswith(".png"):
        img.save(out, "PNG", optimize=True)
    else:
        img.save(out, "JPEG", quality=60)


def main():
    made = []
    for name in referenced_images():
        if "/" in name or not (IMAGES / name).exists():
            if "/" in name:
                continue
            make_placeholder(name)
            made.append(name)
    MANIFEST.write_text("\n".join(made) + "\n" if made else "")
    print(f"Generated {len(made)} placeholders; manifest at {MANIFEST}")


if __name__ == "__main__":
    main()
