# fixPesaZaShambaLauncherIconSizeAndRecents.py
# ------------------------------------------------------------
# Fixes two launcher icon issues for:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# It does this:
# 1. Makes the logo inside the app drawer icon slightly bigger.
# 2. Adds proper adaptive launcher icons so the Android Recent/Overview screen
#    uses your real app icon instead of the generic Android icon.
#
# Source icon expected here:
#   C:\Users\kirwa\Documents\coding\codeScripts\LogoforPesaExpenseApp2.png
#
# Run in PowerShell:
#   python C:\Users\kirwa\Documents\coding\codeScripts\fixPesaZaShambaLauncherIconSizeAndRecents.py
# ------------------------------------------------------------

from pathlib import Path
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
    "drawable-mdpi": 108,
    "drawable-hdpi": 162,
    "drawable-xhdpi": 216,
    "drawable-xxhdpi": 324,
    "drawable-xxxhdpi": 432,
}


def backup_file(path: Path, label: str) -> None:
    if path.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup = BACKUP_DIR / f"{path.name}.{label}.bak"
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


def replace_manifest_attribute(text: str, attr_name: str, new_value: str) -> str:
    start = text.find(attr_name + "=")
    if start == -1:
        return text

    quote_start = text.find('"', start)
    quote_end = text.find('"', quote_start + 1)

    if quote_start == -1 or quote_end == -1:
        return text

    return text[:quote_start + 1] + new_value + text[quote_end:]


def update_manifest() -> None:
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(f"Could not find AndroidManifest.xml at: {MANIFEST_FILE}")

    backup_file(MANIFEST_FILE, "before_recents_icon_fix")

    text = MANIFEST_FILE.read_text(encoding="utf-8")

    if "android:icon=" in text:
        text = replace_manifest_attribute(text, "android:icon", "@mipmap/ic_launcher")
    else:
        text = text.replace("<application", '<application\n                android:icon="@mipmap/ic_launcher"', 1)

    if "android:roundIcon=" in text:
        text = replace_manifest_attribute(text, "android:roundIcon", "@mipmap/ic_launcher_round")
    else:
        text = text.replace(
            'android:icon="@mipmap/ic_launcher"',
            'android:icon="@mipmap/ic_launcher"\n                android:roundIcon="@mipmap/ic_launcher_round"',
            1
        )

    MANIFEST_FILE.write_text(text, encoding="utf-8")
    print("[OK] AndroidManifest.xml points to @mipmap/ic_launcher and @mipmap/ic_launcher_round.")


def update_colors_xml() -> None:
    values_dir = RES_DIR / "values"
    values_dir.mkdir(parents=True, exist_ok=True)
    colors_file = values_dir / "colors.xml"

    if colors_file.exists():
        backup_file(colors_file, "before_launcher_background_color")
        text = colors_file.read_text(encoding="utf-8")

        if "ic_launcher_background_color" not in text:
            text = text.replace(
                "</resources>",
                '    <color name="ic_launcher_background_color">#064C43</color>\n</resources>'
            )
            colors_file.write_text(text, encoding="utf-8")
            print("[OK] Added ic_launcher_background_color to colors.xml.")
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

    icon_xml = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background_color" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
"""

    for name in ["ic_launcher.xml", "ic_launcher_round.xml"]:
        path = folder / name
        backup_file(path, "before_adaptive_icon_fix")
        path.write_text(icon_xml, encoding="utf-8")
        print(f"[OK] Wrote adaptive icon XML: {path}")


def crop_outer_padding(image):
    from PIL import Image, ImageChops

    image = image.convert("RGBA")

    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        image = image.crop(bbox)

    rgb = image.convert("RGB")
    bg = rgb.getpixel((0, 0))
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg))
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

        icon_path = folder / "ic_launcher.png"
        round_path = folder / "ic_launcher_round.png"

        backup_file(icon_path, "before_bigger_launcher_icon")
        backup_file(round_path, "before_bigger_launcher_icon")

        icon.save(icon_path)
        icon.save(round_path)

        print(f"[OK] Bigger legacy icon created: {icon_path}")
        print(f"[OK] Bigger round icon created: {round_path}")

    for folder_name, size in ADAPTIVE_FOREGROUND_SIZES.items():
        folder = RES_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        foreground = center_on_canvas(cropped, size, 0.86)
        foreground_path = folder / "ic_launcher_foreground.png"

        backup_file(foreground_path, "before_bigger_foreground")
        foreground.save(foreground_path)

        print(f"[OK] Bigger adaptive foreground created: {foreground_path}")

    return True


def create_icons_by_copying() -> None:
    for folder_name in LEGACY_ICON_SIZES.keys():
        folder = RES_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ICON_SOURCE, folder / "ic_launcher.png")
        shutil.copy2(ICON_SOURCE, folder / "ic_launcher_round.png")

    drawable_dir = RES_DIR / "drawable"
    drawable_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ICON_SOURCE, drawable_dir / "ic_launcher_foreground.png")

    print("[WARNING] Pillow is not installed, so the icon was copied without resizing.")
    print("          Run this, then run the script again for proper resizing:")
    print("          pip install pillow")


def main() -> None:
    print("Fixing Pesa Za Shamba launcher icon size and Recent/Overview icon...")
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
    print("[SUCCESS] Launcher icon size and Recent/Overview icon fix completed.")
    print()
    print("Next steps in Android Studio:")
    print("1. File > Sync Project with Gradle Files")
    print("2. Build > Clean Project")
    print("3. Build > Assemble Project")
    print("4. Uninstall the old app from your phone/emulator")
    print("5. Run the app again from Android Studio")
    print()
    print("Android often caches app icons, so uninstalling the old app is important.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("[ERROR] Icon fix failed.")
        print(error)
        sys.exit(1)
