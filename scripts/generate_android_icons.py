#!/usr/bin/env python3
"""
Generate Android launcher icons from frontend/advanced_chat/icone.png

Usage:
  python scripts/generate_android_icons.py

Requirements:
  pip install pillow

This script resizes the source PNG into mipmap densities and writes
ic_launcher.png, ic_launcher_foreground.png and ic_launcher_round.png
into each `frontend/app/android/app/src/main/res/mipmap-*/` folder.
"""
from PIL import Image, ImageOps
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "frontend" / "advanced_chat" / "icone.png"
RES_BASE = ROOT / "frontend" / "app" / "android" / "app" / "src" / "main" / "res"

# density -> size (px) for launcher icons (approx common sizes)
SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

OUT_NAMES = ["ic_launcher.png", "ic_launcher_foreground.png", "ic_launcher_round.png"]


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def make_round(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    size = im.size
    mask = Image.new("L", size, 0)
    draw = Image.new("RGBA", size)
    ImageOps.fit(im, size)
    # create circular mask
    from PIL import ImageDraw
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size[0], size[1]), fill=255)
    out = Image.new("RGBA", size)
    out.paste(im, (0, 0), mask)
    return out


def generate():
    if not SRC.exists():
        print(f"Source icon not found: {SRC}")
        sys.exit(1)

    src_im = Image.open(SRC).convert("RGBA")

    for density, px in SIZES.items():
        out_dir = RES_BASE / density
        ensure_dir(out_dir)

        # resize keeping aspect ratio and filling background with transparency
        im = ImageOps.contain(src_im, (px, px))
        # create square canvas and paste centered
        canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        x = (px - im.width) // 2
        y = (px - im.height) // 2
        canvas.paste(im, (x, y), im)

        # save normal launcher
        canvas.save(out_dir / "ic_launcher.png")

        # save foreground (same as launcher)
        canvas.save(out_dir / "ic_launcher_foreground.png")

        # save round variant (circular mask)
        round_im = make_round(canvas)
        round_im.save(out_dir / "ic_launcher_round.png")

        print(f"Wrote icons to {out_dir} (size {px}x{px})")

    print("Done. Rebuild the Android project to apply the new icons.")


if __name__ == "__main__":
    generate()
