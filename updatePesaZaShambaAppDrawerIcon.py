# updatePesaZaShambaAppDrawerIcon.py
# ------------------------------------------------------------
# This script replaces the Android app drawer / launcher icon for:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# It uses this new icon image:
#   C:\Users\kirwa\Documents\coding\codeScripts\LogoforPesaExpenseApp2.png
#
# Before running:
#   Save the new icon image as:
#   C:\Users\kirwa\Documents\coding\codeScripts\LogoforPesaExpenseApp2.png
#
# Run in PowerShell:
#   python C:\Users\kirwa\Documents\coding\codeScripts\updatePesaZaShambaAppDrawerIcon.py
# ------------------------------------------------------------

from pathlib import Path
import shutil
import sys


PROJECT_DIR = Path(r"C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp")
ICON_SOURCE = Path(r"C:\Users\kirwa\Documents\coding\codeScripts\LogoforPesaExpenseApp2.png")

RES_DIR = PROJECT_DIR / "app" / "src" / "main" / "res"
MANIFEST_FILE = PROJECT_DIR / "app" / "src" / "main" / "AndroidManifest.xml"
BACKUP_DIR = PROJECT_DIR / "python_update_backups"

ICON_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
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


def remove_old_launcher_icons() -> None:
    for folder in RES_DIR.glob("mipmap-*"):
        if folder.is_dir():
            for name in [
                "ic_launcher.png",
                "ic_launcher.webp",
                "ic_launcher.xml",
                "ic_launcher_round.png",
                "ic_launcher_round.webp",
                "ic_launcher_round.xml",
                "ic_launcher_foreground.png",
                "ic_launcher_foreground.webp",
                "ic_launcher_foreground.xml",
                "ic_launcher_background.png",
                "ic_launcher_background.webp",
                "ic_launcher_background.xml",
            ]:
                path = folder / name
                if path.exists():
                    backup_file(path, "old_launcher_icon")
                    path.unlink()
                    print(f"[OK] Removed old icon: {path}")


def create_icons_with_pillow() -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False

    image = Image.open(ICON_SOURCE).convert("RGBA")

    for folder_name, size in ICON_SIZES.items():
        folder = RES_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        resized = image.resize((size, size), Image.LANCZOS)

        out_icon = folder / "ic_launcher.png"
        out_round = folder / "ic_launcher_round.png"

        resized.save(out_icon)
        resized.save(out_round)

        print(f"[OK] Created {size}x{size}: {out_icon}")
        print(f"[OK] Created {size}x{size}: {out_round}")

    return True


def create_icons_by_copying() -> None:
    for folder_name in ICON_SIZES.keys():
        folder = RES_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        out_icon = folder / "ic_launcher.png"
        out_round = folder / "ic_launcher_round.png"

        shutil.copy2(ICON_SOURCE, out_icon)
        shutil.copy2(ICON_SOURCE, out_round)

        print(f"[OK] Copied icon to: {out_icon}")
        print(f"[OK] Copied icon to: {out_round}")

    print()
    print("[NOTE] Pillow was not installed, so the same PNG was copied into each mipmap folder.")
    print("       This usually works, but resized icons are better.")
    print("       To enable resizing, run: pip install pillow")


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

    backup_file(MANIFEST_FILE, "before_launcher_icon_update")

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
    print("[OK] AndroidManifest.xml updated to use the new launcher icons.")


def main() -> None:
    print("Updating Pesa Za Shamba app drawer / launcher icon...")
    print(f"Project folder: {PROJECT_DIR}")
    print(f"New icon source: {ICON_SOURCE}")

    if not PROJECT_DIR.exists():
        raise FileNotFoundError(f"Project folder does not exist: {PROJECT_DIR}")

    if not ICON_SOURCE.exists():
        raise FileNotFoundError(
            "New icon image was not found.\n"
            f"Please save it here first:\n{ICON_SOURCE}"
        )

    remove_bad_resource_backups()
    remove_old_launcher_icons()

    if not create_icons_with_pillow():
        create_icons_by_copying()

    update_manifest()

    print()
    print("[SUCCESS] App drawer / launcher icon updated.")
    print()
    print("Next steps in Android Studio:")
    print("1. File > Sync Project with Gradle Files")
    print("2. Build > Clean Project")
    print("3. Build > Assemble Project")
    print("4. Run the app")
    print()
    print("If the old icon still appears on the phone:")
    print("- Uninstall the old app from the phone/emulator")
    print("- Run the app again from Android Studio")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("[ERROR] Launcher icon update failed.")
        print(error)
        sys.exit(1)
