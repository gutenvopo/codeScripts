"""
Car Mech Pro — Icon Installer
Replaces the launcher icon in your existing Android project
with the uploaded Gemini-generated wrench icon.

Steps:
  1. Put this script in the same folder as your uploaded icon PNG
     OR update SOURCE_IMAGE below to point to the PNG's full path.
  2. pip install Pillow
  3. python install_icon.py
"""

import os, shutil
from PIL import Image
import numpy as np

# ── CONFIGURE THESE PATHS ─────────────────────────────────────────
PROJECT_DIR  = r"C:\Users\kirwa\AndroidStudioProjects\CarMechPro"
SOURCE_IMAGE = r"C:\Users\kirwa\Documents\coding\codeScripts\rwakiDev_v3\proper_wrench_icon.png"   # put in same folder as this script
# ─────────────────────────────────────────────────────────────────

MIPMAP_SIZES = {
    "mipmap-mdpi":    48,
    "mipmap-hdpi":    72,
    "mipmap-xhdpi":   96,
    "mipmap-xxhdpi":  144,
    "mipmap-xxxhdpi": 192,
}

RES_DIR = os.path.join(PROJECT_DIR, "app", "src", "main", "res")

ADAPTIVE_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_fg"/>
</adaptive-icon>
"""

COLORS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#FF6B00</color>
</resources>
"""

def crop_icon(path: str) -> Image.Image:
    """Crop the icon tightly from the checkerboard background."""
    img = Image.open(path).convert("RGB")
    arr = np.array(img)

    # Find orange pixels (the icon's rounded-square background)
    orange = (arr[:,:,0] > 180) & (arr[:,:,1] > 60) & \
             (arr[:,:,1] < 160) & (arr[:,:,2] < 80)

    rows = np.any(orange, axis=1)
    cols = np.any(orange, axis=0)

    if not rows.any():
        print("  WARNING: Could not detect orange icon area — using full image.")
        return img

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    # Make square crop centred on the icon
    cx   = (cmin + cmax) // 2
    cy   = (rmin + rmax) // 2
    half = max(cmax - cmin, rmax - rmin) // 2 + 20

    x0 = max(0, cx - half);  x1 = min(img.width,  cx + half)
    y0 = max(0, cy - half);  y1 = min(img.height, cy + half)

    return img.crop((x0, y0, x1, y1))


def write_text(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def install():
    print("=" * 58)
    print("  Car Mech Pro — Icon Installer")
    print("=" * 58)

    if not os.path.exists(SOURCE_IMAGE):
        print(f"\n  ERROR: Cannot find source image:\n  {SOURCE_IMAGE}")
        print("  Update SOURCE_IMAGE in this script to the correct path.")
        return

    print(f"\n  Source : {SOURCE_IMAGE}")
    print(f"  Project: {PROJECT_DIR}\n")

    # 1. Crop the icon
    print("  Cropping icon from image...")
    icon = crop_icon(SOURCE_IMAGE)
    print(f"  Cropped size: {icon.size[0]}x{icon.size[1]}px")

    # 2. Write mipmap PNGs
    for folder, size in MIPMAP_SIZES.items():
        dest_dir = os.path.join(RES_DIR, folder)
        os.makedirs(dest_dir, exist_ok=True)

        resized = icon.resize((size, size), Image.LANCZOS)

        # Main icon (rounded-square — Android applies the shape mask)
        resized.save(os.path.join(dest_dir, "ic_launcher.png"))
        # Round icon (same image — Android clips it to a circle)
        resized.save(os.path.join(dest_dir, "ic_launcher_round.png"))
        # Foreground layer for adaptive icon (same image)
        resized.save(os.path.join(dest_dir, "ic_launcher_fg.png"))

        print(f"  OK  res/{folder}/  ({size}x{size}px)")

    # 3. Write adaptive icon XMLs (API 26+)
    anydpi_dir = os.path.join(RES_DIR, "mipmap-anydpi-v26")
    write_text(os.path.join(anydpi_dir, "ic_launcher.xml"),       ADAPTIVE_XML)
    write_text(os.path.join(anydpi_dir, "ic_launcher_round.xml"), ADAPTIVE_XML)
    print("  OK  mipmap-anydpi-v26/ic_launcher.xml")
    print("  OK  mipmap-anydpi-v26/ic_launcher_round.xml")

    # 4. Ensure the background colour resource exists
    write_text(os.path.join(RES_DIR, "values", "colors.xml"), COLORS_XML)
    print("  OK  values/colors.xml")

    # 5. Make sure AndroidManifest.xml uses @mipmap/ic_launcher
    manifest = os.path.join(PROJECT_DIR, "app", "src", "main", "AndroidManifest.xml")
    if os.path.exists(manifest):
        with open(manifest, "r", encoding="utf-8") as f:
            content = f.read()
        changed = False
        if '@android:drawable/ic_menu_manage' in content:
            content = content.replace(
                'android:icon="@android:drawable/ic_menu_manage"',
                'android:icon="@mipmap/ic_launcher"'
            ).replace(
                'android:roundIcon="@android:drawable/ic_menu_manage"',
                'android:roundIcon="@mipmap/ic_launcher_round"'
            )
            changed = True
        if changed:
            with open(manifest, "w", encoding="utf-8") as f:
                f.write(content)
            print("  OK  AndroidManifest.xml  (updated icon references)")
        else:
            print("  OK  AndroidManifest.xml  (already correct)")

    print()
    print("=" * 58)
    print("  Done! Next steps in Android Studio:")
    print("  1. File -> Sync Project with Gradle Files")
    print("  2. Build -> Clean Project")
    print("  3. Run on emulator or device ▶")
    print("=" * 58)


if __name__ == "__main__":
    install()
