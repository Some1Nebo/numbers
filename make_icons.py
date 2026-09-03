"""Generate the app icons for Numbers Workout.

Requires Pillow (build-time only):  .venv/bin/pip install pillow

Produces:
    menubar_icon.png   - 44x44 monochrome dumbbell, used as the menu bar (template) icon
    app_icon_1024.png  - 1024x1024 rounded-square app icon (white dumbbell on a slate gradient)
    app_icon.icns      - .icns for the .app bundle (via iconutil)
"""

import os
import shutil
import subprocess

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))

SLATE_TOP = (76, 86, 106)      # #4C566A
SLATE_BOTTOM = (46, 52, 64)    # #2E3440


def draw_dumbbell(draw, size, color, center):
    """Draw a dumbbell of `size` (bar + 4 plates) centered at `center` (canvas coords).

    `center` is required on purpose: the dumbbell's own coordinate space is
    NOT the canvas, and centering it on itself silently lands in the corner.
    """
    cx, cy = center
    bar_half = size * 0.28
    bar_h = size * 0.10
    gap = size * 0.02
    plate_w = size * 0.11
    inner_h = size * 0.46
    outer_w = size * 0.09
    outer_h = size * 0.34

    def rect(x, y, w, h, color):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=min(w, h) / 2 * 0.6, fill=color)

    # bar
    rect(cx - bar_half, cy - bar_h / 2, bar_half * 2, bar_h, color)

    for side in (-1, 1):
        if side < 0:
            inner_x = cx - gap - bar_half - plate_w
        else:
            inner_x = cx + gap + bar_half
        # inner (taller) plate
        rect(inner_x, cy - inner_h / 2, plate_w, inner_h, color)
        # outer (shorter) plate
        outer_x = inner_x - gap - outer_w if side < 0 else inner_x + plate_w + gap
        rect(outer_x, cy - outer_h / 2, outer_w, outer_h, color)


def make_menubar_icon(out_path, size=44):
    """Monochrome template icon (22pt @2x); macOS tints it for light/dark menu bars."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw_dumbbell(ImageDraw.Draw(img), size * 0.92, (0, 0, 0, 255), center=(size / 2, size / 2))
    img.save(out_path)


def make_app_icon(out_path, size=1024):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # vertical gradient built from a 1px-wide column (fast)
    column = Image.new("RGB", (1, size))
    col_px = column.load()
    for y in range(size):
        t = y / (size - 1)
        col_px[0, y] = tuple(int(a + (b - a) * t) for a, b in zip(SLATE_TOP, SLATE_BOTTOM))
    gradient = column.resize((size, size))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.225), fill=255)
    img.paste(gradient, (0, 0), mask)

    draw_dumbbell(ImageDraw.Draw(img), int(size * 0.62), (255, 255, 255, 255), center=(size / 2, size / 2))
    img.save(out_path)


def make_icns(master_png, out_path):
    iconset_dir = os.path.join(HERE, "app_icon.iconset")
    os.makedirs(iconset_dir, exist_ok=True)

    specs = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]
    master = Image.open(master_png)
    try:
        for name, s in specs:
            master.resize((s, s), Image.Resampling.LANCZOS).save(os.path.join(iconset_dir, name))
        subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", out_path], check=True)
    finally:
        shutil.rmtree(iconset_dir, ignore_errors=True)


if __name__ == "__main__":
    menubar_png = os.path.join(HERE, "menubar_icon.png")
    app_png = os.path.join(HERE, "app_icon_1024.png")
    icns = os.path.join(HERE, "app_icon.icns")

    make_menubar_icon(menubar_png)
    make_app_icon(app_png)
    make_icns(app_png, icns)
    print("Wrote {0}, {1}, {2}".format(menubar_png, app_png, icns))
