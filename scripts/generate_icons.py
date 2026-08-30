"""
Génère les icônes Android (launcher) et favicon pour SUP'ONE AI.
Dessine le logo directement avec Pillow (pas de dépendance Cairo).
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import math

try:
    from PIL import ImageFont
except ImportError:
    pass

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
APP_DIR = os.path.join(BASE, "frontend", "app")
PUBLIC_DIR = os.path.join(APP_DIR, "public")
RES_DIR = os.path.join(APP_DIR, "android", "app", "src", "main", "res")

ACCENT = (16, 163, 127)  # #10a37f
ACCENT_DARK = (13, 140, 109)  # #0d8c6d
WHITE = (255, 255, 255)
BG_DARK = "#171717"


def create_logo(size, with_bg=True, bg_color=ACCENT, shape="square"):
    """
    Crée le logo SUP'ONE AI à la taille donnée.
    - with_bg: dessine le fond coloré
    - shape: 'square', 'round', 'circle'
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.08)
    radius = int(size * 0.22)

    if with_bg:
        if shape == "circle":
            draw.ellipse([(0, 0), (size - 1, size - 1)], fill=bg_color)
        else:
            draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=bg_color)

    # Coordonnées relatives
    cx, cy = size / 2, size / 2
    scale = size / 512

    # --- Bulle de dialogue (blanche) ---
    bubble_margin = int(100 * scale)
    bubble_r = int(40 * scale)
    bx1 = int(136 * scale)
    by1 = int(120 * scale)
    bx2 = int(376 * scale)
    by2 = int(328 * scale)

    # Forme de bulle avec queue
    bubble = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bubble)

    # Corps principal de la bulle
    bd.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=bubble_r, fill=(*WHITE, 240))

    # Queue de la bulle (triangle)
    tail_points = [
        (int(180 * scale), by2),
        (int(176 * scale), int(370 * scale)),
        (int(220 * scale), by2),
    ]
    bd.polygon(tail_points, fill=(*WHITE, 240))

    img = Image.alpha_composite(img, bubble)
    draw = ImageDraw.Draw(img)

    # --- Points de chat (3 ronds verts) ---
    dot_r = int(16 * scale)
    dot_y = int(224 * scale)
    dot_positions = [int(216 * scale), int(256 * scale), int(296 * scale)]
    opacities = [0.95, 0.75, 0.55]

    for dx, alpha in zip(dot_positions, opacities):
        r, g, b = ACCENT
        draw.ellipse(
            [(dx - dot_r, dot_y - dot_r), (dx + dot_r, dot_y + dot_r)],
            fill=(r, g, b, int(255 * alpha))
        )

    # --- Étoile IA (sparkle) ---
    sparkle_cx = int(320 * scale)
    sparkle_cy = int(155 * scale)
    sparkle_size = int(28 * scale)

    # Étoile à 4 branches
    points = []
    for i in range(8):
        angle = math.radians(i * 45 - 90)
        r = sparkle_size if i % 2 == 0 else sparkle_size * 0.25
        px = sparkle_cx + r * math.cos(angle)
        py = sparkle_cy + r * math.sin(angle)
        points.append((px, py))
    draw.polygon(points, fill=(*ACCENT, 230))

    # Petits cercles d'accent
    small_r1 = int(5 * scale)
    draw.ellipse([
        (sparkle_cx + int(20 * scale) - small_r1, sparkle_cy - int(20 * scale) - small_r1),
        (sparkle_cx + int(20 * scale) + small_r1, sparkle_cy - int(20 * scale) + small_r1)
    ], fill=(*ACCENT, 160))

    small_r2 = int(3 * scale)
    draw.ellipse([
        (sparkle_cx - int(16 * scale) - small_r2, sparkle_cy - int(24 * scale) - small_r2),
        (sparkle_cx - int(16 * scale) + small_r2, sparkle_cy - int(24 * scale) + small_r2)
    ], fill=(*ACCENT, 100))

    # Masquer les parties hors du cercle/carré arrondi si with_bg
    if with_bg:
        mask = Image.new("L", (size, size), 0)
        md = ImageDraw.Draw(mask)
        if shape == "circle":
            md.ellipse([(0, 0), (size - 1, size - 1)], fill=255)
        else:
            md.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
        img.putalpha(mask)

    return img


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")
    kb = os.path.getsize(path) / 1024
    rel = os.path.relpath(path, BASE)
    print(f"  {rel:65s} {kb:6.1f} KB")


print("=== Generation des icones SUP'ONE AI ===\n")

# --- [1] Favicon & icon.png ---
print("[1/4] Favicon & icon PNG")
for s in [16, 32, 48, 192, 512]:
    img = create_logo(s, with_bg=True, shape="square")
    save(img, os.path.join(PUBLIC_DIR, f"icon-{s}.png"))
    if s == 512:
        save(img, os.path.join(PUBLIC_DIR, "icon.png"))
    if s == 48:
        save(img, os.path.join(PUBLIC_DIR, "favicon-48.png"))
    if s == 32:
        save(img, os.path.join(PUBLIC_DIR, "favicon-32.png"))
    if s == 16:
        save(img, os.path.join(PUBLIC_DIR, "favicon-16.png"))

# --- [2] Android Launcher Icons ---
print("\n[2/4] Android Launcher Icons")
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}

for density, size in DENSITIES.items():
    folder = os.path.join(RES_DIR, f"mipmap-{density}")

    # ic_launcher (carré arrondi)
    img = create_logo(size, with_bg=True, shape="square")
    save(img, os.path.join(folder, "ic_launcher.png"))

    # ic_launcher_round (circulaire)
    img_r = create_logo(size, with_bg=True, shape="circle")
    save(img_r, os.path.join(folder, "ic_launcher_round.png"))

    # ic_launcher_foreground (sans fond, pour adaptive icon)
    fg = create_logo(size, with_bg=False)
    save(fg, os.path.join(folder, "ic_launcher_foreground.png"))

# --- [3] Splash Screens ---
print("\n[3/4] Splash Screens")
SPLASH_SIZES = {
    "drawable": (960, 1600),
    "drawable-port-mdpi": (960, 1600),
    "drawable-port-hdpi": (1440, 2560),
    "drawable-port-xhdpi": (1920, 3440),
    "drawable-port-xxhdpi": (2560, 4480),
    "drawable-port-xxxhdpi": (3200, 5600),
    "drawable-land-mdpi": (1600, 960),
    "drawable-land-hdpi": (2560, 1440),
    "drawable-land-xhdpi": (3440, 1920),
    "drawable-land-xxhdpi": (4480, 2560),
    "drawable-land-xxxhdpi": (5600, 3200),
}

for folder_name, (w, h) in SPLASH_SIZES.items():
    splash = Image.new("RGB", (w, h), BG_DARK)
    logo_size = min(w, h) // 4
    logo = create_logo(logo_size, with_bg=True, shape="square")
    x = (w - logo_size) // 2
    y = (h - logo_size) // 2
    splash.paste(logo, (x, y), logo)
    save(splash, os.path.join(RES_DIR, folder_name, "splash.png"))

# --- [4] Colors XML update ---
print("\n[4/4] Mise a jour colors.xml")
colors_xml = os.path.join(RES_DIR, "values", "colors.xml")
with open(colors_xml, "r") as f:
    content = f.read()
content = content.replace("#070f1f", BG_DARK).replace("#0a1628", BG_DARK)
with open(colors_xml, "w") as f:
    f.write(content)
print(f"  colors.xml mis a jour avec {BG_DARK}")

# --- Update capacitor.config.json splash color ---
cap_config = os.path.join(APP_DIR, "capacitor.config.json")
with open(cap_config, "r") as f:
    cap = f.read()
cap = cap.replace("#070f1f", BG_DARK).replace("#0a1628", BG_DARK)
with open(cap_config, "w") as f:
    f.write(cap)
print(f"  capacitor.config.json mis a jour")

print("\n=== Termine ! ===")
