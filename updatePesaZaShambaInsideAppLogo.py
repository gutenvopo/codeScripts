# updatePesaZaShambaInsideAppLogo.py
# ------------------------------------------------------------
# This script replaces the logo used INSIDE the app UI for:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# It does NOT change the Android app drawer / launcher icon.
#
# New inside-app logo source:
#   C:\Users\kirwa\Documents\Graphic Design\Logo for Pesa Expense App4.png
#
# It copies that image into:
#   app/src/main/res/drawable/pesa_za_shamba_logo.png
#
# This is the drawable used by MainActivity.kt:
#   R.drawable.pesa_za_shamba_logo
#
# Run in PowerShell:
#   python "C:\Users\kirwa\Documents\coding\codeScripts\updatePesaZaShambaInsideAppLogo.py"
# ------------------------------------------------------------

from pathlib import Path
import shutil
import sys


PROJECT_DIR = Path(r"C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp")
NEW_LOGO_SOURCE = Path(r"C:\Users\kirwa\Documents\Graphic Design\Logo for Pesa Expense App4.png")

DRAWABLE_DIR = PROJECT_DIR / "app" / "src" / "main" / "res" / "drawable"
DESTINATION_LOGO = DRAWABLE_DIR / "pesa_za_shamba_logo.png"
BACKUP_DIR = PROJECT_DIR / "python_update_backups"


def remove_bad_resource_backups() -> None:
    res_dir = PROJECT_DIR / "app" / "src" / "main" / "res"

    if not res_dir.exists():
        return

    removed = 0
    for file in res_dir.rglob("*.bak"):
        file.unlink()
        removed += 1

    if removed:
        print(f"[OK] Removed {removed} .bak file(s) from res folder.")


def backup_existing_logo() -> None:
    if DESTINATION_LOGO.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup = BACKUP_DIR / "pesa_za_shamba_logo_before_inside_app_logo_update.png.bak"
        backup.write_bytes(DESTINATION_LOGO.read_bytes())
        print("[BACKUP] Existing inside-app logo backed up to:")
        print(f"         {backup}")


def copy_new_logo() -> None:
    if not NEW_LOGO_SOURCE.exists():
        raise FileNotFoundError(
            "New inside-app logo was not found.\n"
            f"Please confirm the file exists here:\n{NEW_LOGO_SOURCE}"
        )

    DRAWABLE_DIR.mkdir(parents=True, exist_ok=True)

    backup_existing_logo()
    shutil.copy2(NEW_LOGO_SOURCE, DESTINATION_LOGO)

    print("[OK] New inside-app logo copied successfully.")
    print(f"     From: {NEW_LOGO_SOURCE}")
    print(f"     To:   {DESTINATION_LOGO}")


def main() -> None:
    print("Updating Pesa Za Shamba inside-app logo...")
    print(f"Project folder: {PROJECT_DIR}")

    if not PROJECT_DIR.exists():
        raise FileNotFoundError(f"Project folder does not exist:\n{PROJECT_DIR}")

    remove_bad_resource_backups()
    copy_new_logo()

    print()
    print("[SUCCESS] Inside-app logo updated.")
    print()
    print("Next steps in Android Studio:")
    print("1. File > Sync Project with Gradle Files")
    print("2. Build > Clean Project")
    print("3. Build > Assemble Project")
    print("4. Run the app")
    print()
    print("Note:")
    print("This changes the logo shown inside the app screens.")
    print("It does not change the app drawer / launcher icon.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("[ERROR] Inside-app logo update failed.")
        print(error)
        sys.exit(1)
