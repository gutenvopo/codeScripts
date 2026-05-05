# fixPesaZaShambaOverviewIconPersistent.py
# ------------------------------------------------------------
# Fixes a persistent generic icon in Android Recent/Overview for:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# This script does more than replace the app drawer icon:
# 1. Creates legacy launcher icons in mipmap-mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi.
# 2. Creates adaptive icon foreground images in mipmap-* folders.
# 3. Creates mipmap-anydpi-v26/ic_launcher.xml and ic_launcher_round.xml.
# 4. Sets android:icon, android:roundIcon, and android:logo on the application.
# 5. Sets android:icon, android:roundIcon, and android:logo on MainActivity too.
# 6. Removes .bak files from res folders because Android resource folders reject them.
#
# Source icon expected here:
#   C:\Users\kirwa\Documents\coding\codeScripts\LogoforPesaExpenseApp2.png
#
# Run in PowerShell:
#   python C:\Users\kirwa\Documents\coding\codeScripts\fixPesaZaShambaOverviewIconPersistent.py
# ------------------------------------------------------------

from pathlib import Path
import re
import shutil
import sys


PROJECT_DIR = Path(r"C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp")
ICON_SOURCE = Path(r"C:\Users\kirwa\Documents\coding\codeScripts\LogoforPesaExpenseApp2.png")

RES_DIR = PROJECT_DIR / "app" / "src" / "main" / "res"
MANIFEST_FILE = PROJECT_DIR / "app" / "src" / "main" / "AndroidManifest.xml"
BACKUP_DIR = PROJECT_DIR / "python_update_backups"

LEGACY_ICON_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

ADAPTIVE_FOREGROUND_SIZES = {
    "mipmap-mdpi": 108,
    "mipmap-hdpi": 162,
    "mipmap-xhdpi": 216,
    "mipmap-xxhdpi": 324,
    "mipmap-xxxhdpi": 432,
}


def backup_file(path: Path, label: str) -> None:
    if path.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = str(path.relative_to(PROJECT_DIR)).replace("\\", "__").replace("/", "__")
        backup = BACKUP_DIR / f"{safe_name}.{label}.bak"
        backup.write_bytes(path.read_bytes())
        print(f"[BACKUP] {backup}")


def remove_bad_resource_backups() -> None:
    if not RES_DIR.exists():
        return

    removed = 0
    for file in RES_DIR.rglob("*.bak"):
        file.unlink()
        removed += 1

    if removed:
        print(f"[OK] Removed {removed} .bak file(s) from res folder.")
    else:
        print("[INFO] No .bak files found inside res folder.")


def update_colors_xml() -> None:
    values_dir = RES_DIR / "values"
    values_dir.mkdir(parents=True, exist_ok=True)
    colors_file = values_dir / "colors.xml"

    if colors_file.exists():
        backup_file(colors_file, "before_overview_icon_fix")
        text = colors_file.read_text(encoding="utf-8")

        if "ic_launcher_background_color" not in text:
            text = text.replace(
                "</resources>",
                '    <color name="ic_launcher_background_color">#064C43</color>\n</resources>'
            )
            colors_file.write_text(text, encoding="utf-8")
            print("[OK] Added ic_launcher_background_color.")
        else:
            print("[INFO] ic_launcher_background_color already exists.")
    else:
        colors_file.write_text(
            '<resources>\n    <color name="ic_launcher_background_color">#064C43</color>\n</resources>\n',
            encoding="utf-8"
        )
        print("[OK] Created colors.xml with launcher background color.")


def create_adaptive_icon_xml() -> None:
    folder = RES_DIR / "mipmap-anydpi-v26"
    folder.mkdir(parents=True, exist_ok=True)

    adaptive_xml = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background_color" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
"""

    for filename in ["ic_launcher.xml", "ic_launcher_round.xml"]:
        path = folder / filename
        backup_file(path, "before_overview_icon_fix")
        path.write_text(adaptive_xml, encoding="utf-8")
        print(f"[OK] Wrote adaptive icon XML: {path}")


def crop_outer_padding(image):
    from PIL import Image, ImageChops

    image = image.convert("RGBA")

    alpha_bbox = image.getchannel("A").getbbox()
    if alpha_bbox:
        image = image.crop(alpha_bbox)

    rgb = image.convert("RGB")
    background = rgb.getpixel((0, 0))
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, background))
    bbox = diff.getbbox()
    if bbox:
        image = image.crop(bbox)

    return image


def center_on_canvas(image, canvas_size: int, fill_ratio: float):
    from PIL import Image

    image = image.convert("RGBA")
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))

    max_size = int(canvas_size * fill_ratio)
    image.thumbnail((max_size, max_size), Image.LANCZOS)

    x = (canvas_size - image.width) // 2
    y = (canvas_size - image.height) // 2
    canvas.alpha_composite(image, (x, y))

    return canvas


def create_icons_with_pillow() -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False

    source = Image.open(ICON_SOURCE).convert("RGBA")
    cropped = crop_outer_padding(source)

    for folder_name, size in LEGACY_ICON_SIZES.items():
        folder = RES_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        icon = center_on_canvas(cropped, size, 0.98)

        for filename in ["ic_launcher.png", "ic_launcher_round.png"]:
            out = folder / filename
            backup_file(out, "before_overview_icon_fix")
            icon.save(out)
            print(f"[OK] Wrote {size}x{size}: {out}")

    for folder_name, size in ADAPTIVE_FOREGROUND_SIZES.items():
        folder = RES_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        foreground = center_on_canvas(cropped, size, 0.90)
        out = folder / "ic_launcher_foreground.png"
        backup_file(out, "before_overview_icon_fix")
        foreground.save(out)
        print(f"[OK] Wrote adaptive foreground {size}x{size}: {out}")

    return True


def create_icons_by_copying() -> None:
    for folder_name in LEGACY_ICON_SIZES.keys():
        folder = RES_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ICON_SOURCE, folder / "ic_launcher.png")
        shutil.copy2(ICON_SOURCE, folder / "ic_launcher_round.png")
        shutil.copy2(ICON_SOURCE, folder / "ic_launcher_foreground.png")

    print("[WARNING] Pillow is not installed. Icons were copied without resizing.")
    print("          For better results, run: pip install pillow")
    print("          Then run this script again.")


def set_or_add_attr(tag_text: str, attr_name: str, attr_value: str) -> str:
    pattern = re.compile(rf'{re.escape(attr_name)}\s*=\s*"[^"]*"')
    replacement = f'{attr_name}="{attr_value}"'

    if pattern.search(tag_text):
        return pattern.sub(replacement, tag_text, count=1)

    if tag_text.endswith(">"):
        return tag_text[:-1] + f'\n                {replacement}>'

    return tag_text


def update_manifest() -> None:
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(f"Could not find AndroidManifest.xml at: {MANIFEST_FILE}")

    backup_file(MANIFEST_FILE, "before_overview_icon_fix")
    text = MANIFEST_FILE.read_text(encoding="utf-8")

    app_match = re.search(r'<application\b[^>]*>', text, flags=re.DOTALL)
    if app_match:
        app_tag = app_match.group(0)
        app_tag_new = set_or_add_attr(app_tag, "android:icon", "@mipmap/ic_launcher")
        app_tag_new = set_or_add_attr(app_tag_new, "android:roundIcon", "@mipmap/ic_launcher_round")
        app_tag_new = set_or_add_attr(app_tag_new, "android:logo", "@mipmap/ic_launcher")
        text = text[:app_match.start()] + app_tag_new + text[app_match.end():]
        print("[OK] Application icon, roundIcon, and logo updated.")
    else:
        print("[WARNING] Could not find <application> tag.")

    activity_pattern = re.compile(r'<activity\b(?=[^>]*android:name="\.MainActivity")[^>]*>', flags=re.DOTALL)
    activity_match = activity_pattern.search(text)

    if activity_match:
        activity_tag = activity_match.group(0)
        activity_tag_new = set_or_add_attr(activity_tag, "android:icon", "@mipmap/ic_launcher")
        activity_tag_new = set_or_add_attr(activity_tag_new, "android:roundIcon", "@mipmap/ic_launcher_round")
        activity_tag_new = set_or_add_attr(activity_tag_new, "android:logo", "@mipmap/ic_launcher")
        text = text[:activity_match.start()] + activity_tag_new + text[activity_match.end():]
        print("[OK] MainActivity icon, roundIcon, and logo updated.")
    else:
        print("[WARNING] Could not find MainActivity <activity> tag.")

    MANIFEST_FILE.write_text(text, encoding="utf-8")


def main() -> None:
    print("Fixing persistent generic icon in Android Recent/Overview...")
    print(f"Project folder: {PROJECT_DIR}")
    print(f"Icon source: {ICON_SOURCE}")

    if not PROJECT_DIR.exists():
        raise FileNotFoundError(f"Project folder does not exist: {PROJECT_DIR}")

    if not ICON_SOURCE.exists():
        raise FileNotFoundError(
            "Icon source was not found.\n"
            f"Please save the icon here first:\n{ICON_SOURCE}"
        )

    remove_bad_resource_backups()
    update_colors_xml()
    create_adaptive_icon_xml()

    if not create_icons_with_pillow():
        create_icons_by_copying()

    update_manifest()

    print()
    print("[SUCCESS] Persistent Overview icon fix completed.")
    print()
    print("Now do this:")
    print("1. Android Studio > File > Sync Project with Gradle Files")
    print("2. Build > Clean Project")
    print("3. Build > Assemble Project")
    print("4. On the phone/emulator, uninstall the current Pesa Za Shamba app")
    print("5. Run the app again from Android Studio")
    print("6. Open Recent/Overview again")
    print()
    print("Uninstalling is important because Android launchers and the Overview screen cache app icons.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("[ERROR] Overview icon fix failed.")
        print(error)
        sys.exit(1)
