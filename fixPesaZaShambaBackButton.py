# fixPesaZaShambaBackButton.py
# Fixes phone/system Back button behavior for PesaZaShambaApp.
from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp")
MAIN_ACTIVITY_FILE = PROJECT_DIR / "app" / "src" / "main" / "java" / "com" / "kirwa" / "pesazashamba" / "MainActivity.kt"
BACKUP_DIR = PROJECT_DIR / "python_update_backups"

def backup_main_activity() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / "MainActivity_before_back_button_fix.kt.bak"
    backup.write_text(MAIN_ACTIVITY_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[BACKUP] {backup}")

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
    else:
        print("[INFO] No .bak files found inside res folder.")

def ensure_backhandler_import(text: str) -> str:
    import_line = "import androidx.activity.compose.BackHandler"
    if import_line in text:
        print("[INFO] BackHandler import already exists.")
        return text
    anchor = "import androidx.activity.ComponentActivity"
    if anchor in text:
        text = text.replace(anchor, anchor + "\n        " + import_line)
        print("[OK] Added BackHandler import.")
    else:
        text = import_line + "\n" + text
        print("[OK] Added BackHandler import at top.")
    return text

def remove_existing_backhandler(text: str) -> str:
    marker = "BackHandler(enabled = currentScreen != Screen.Login)"
    index = text.find(marker)
    if index == -1:
        print("[INFO] No old BackHandler block found.")
        return text
    start = text.rfind("\n", 0, index)
    start = 0 if start == -1 else start + 1
    first_brace = text.find("{", index)
    if first_brace == -1:
        return text
    depth = 0
    end = first_brace
    for i in range(first_brace, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < len(text) and text[end] == "\n":
        end += 1
    print("[OK] Removed old BackHandler block.")
    return text[:start] + text[end:]

def insert_backhandler_after_current_screen(text: str) -> str:
    if "BackHandler(enabled = currentScreen != Screen.Login)" in text:
        print("[INFO] BackHandler already exists.")
        return text
    target = "var currentScreen by remember { mutableStateOf(Screen.Login) }"
    back_handler = (
        "\n            BackHandler(enabled = currentScreen != Screen.Login) {\n"
        "                currentScreen = when (currentScreen) {\n"
        "                    Screen.Dairy -> Screen.Selection\n"
        "                    Screen.Maize -> Screen.Selection\n"
        "                    Screen.Records -> Screen.Selection\n"
        "                    Screen.Selection -> Screen.Login\n"
        "                    Screen.Login -> Screen.Login\n"
        "                }\n"
        "            }\n"
    )
    if target in text:
        text = text.replace(target, target + back_handler, 1)
        print("[OK] Inserted BackHandler immediately after currentScreen state.")
        return text
    print("[ERROR] Could not find currentScreen declaration.")
    print(f"Expected to find: {target}")
    return text

def add_debug_text_comment(text: str) -> str:
    marker = "fun PesaZaShambaApp(showMessage: (String) -> Unit) {"
    comment = "// System Back button is handled inside this composable."
    if comment in text:
        return text
    if marker in text:
        text = text.replace(marker, marker + "\n            " + comment, 1)
        print("[OK] Added Back button comment.")
    return text

def main() -> None:
    print("Fixing Pesa Za Shamba phone Back button behavior...")
    print(f"Project folder: {PROJECT_DIR}")
    if not PROJECT_DIR.exists():
        raise FileNotFoundError(f"Project folder does not exist: {PROJECT_DIR}")
    if not MAIN_ACTIVITY_FILE.exists():
        raise FileNotFoundError(f"Could not find MainActivity.kt at: {MAIN_ACTIVITY_FILE}")
    remove_bad_resource_backups()
    backup_main_activity()
    text = MAIN_ACTIVITY_FILE.read_text(encoding="utf-8")
    text = ensure_backhandler_import(text)
    text = remove_existing_backhandler(text)
    text = insert_backhandler_after_current_screen(text)
    text = add_debug_text_comment(text)
    MAIN_ACTIVITY_FILE.write_text(text, encoding="utf-8")
    print("\n[SUCCESS] Back button fix applied.")
    print("\nNow do this in Android Studio:")
    print("1. File > Sync Project with Gradle Files")
    print("2. Build > Clean Project")
    print("3. Build > Assemble Project")
    print("4. Run the app")
    print("\nExpected behavior:")
    print("- From Dairy/Maize/Records, phone Back returns to the Selection page.")
    print("- From Selection, phone Back returns to Login.")
    print("- From Login, phone Back exits the app.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n[ERROR] Back button fix failed.")
        print(error)
        sys.exit(1)
