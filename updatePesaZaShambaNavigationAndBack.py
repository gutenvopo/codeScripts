# updatePesaZaShambaNavigationAndBack.py
# ------------------------------------------------------------
# This script updates your existing Android Studio project:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# It makes these changes:
# 1. Sets the Android bottom navigation bar to match the app theme:
#      Dark green background + light/visible nav buttons.
#
# 2. Fixes the phone's physical/system Back button behavior:
#      Dairy/Maize/Records screen -> Selection screen
#      Selection screen -> Login screen
#      Login screen -> normal app exit
#
# Run in PowerShell:
#   python C:\Users\kirwa\Documents\coding\codeScripts\updatePesaZaShambaNavigationAndBack.py
# ------------------------------------------------------------

from pathlib import Path
import sys


PROJECT_DIR = Path(r"C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp")

MAIN_ACTIVITY_FILE = (
    PROJECT_DIR
    / "app"
    / "src"
    / "main"
    / "java"
    / "com"
    / "kirwa"
    / "pesazashamba"
    / "MainActivity.kt"
)

THEMES_FILE = (
    PROJECT_DIR
    / "app"
    / "src"
    / "main"
    / "res"
    / "values"
    / "themes.xml"
)


def backup_file(path: Path, suffix: str) -> None:
    if path.exists():
        backup = path.with_suffix(path.suffix + suffix)
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[BACKUP] {backup}")


def update_themes_xml() -> None:
    if not THEMES_FILE.exists():
        raise FileNotFoundError(f"Could not find themes.xml at: {THEMES_FILE}")

    backup_file(THEMES_FILE, ".navback.bak")

    content = """<resources>
    <style name="Theme.PesaZaShamba" parent="android:style/Theme.Material.Light.NoActionBar">
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:statusBarColor">#FFFDF3</item>

        <!-- Bottom Android navigation bar: dark green with visible light buttons -->
        <item name="android:navigationBarColor">#064C43</item>
        <item name="android:windowLightNavigationBar">false</item>
    </style>
</resources>
"""

    THEMES_FILE.write_text(content, encoding="utf-8")
    print("[OK] themes.xml updated: navigation bar set to dark app-theme color.")


def add_import_if_missing(text: str, import_line: str) -> str:
    if import_line in text:
        return text

    anchor = "import android.os.Bundle"
    if anchor in text:
        return text.replace(anchor, anchor + "\n        " + import_line)

    return import_line + "\n        " + text


def ensure_imports(text: str) -> str:
    imports_to_add = [
        "import android.os.Build",
        "import androidx.activity.compose.BackHandler",
        "import androidx.compose.runtime.SideEffect",
        "import androidx.compose.ui.platform.LocalView",
        "import androidx.core.view.WindowCompat",
    ]

    for import_line in imports_to_add:
        before = text
        text = add_import_if_missing(text, import_line)
        if text != before:
            print(f"[OK] Added import: {import_line}")

    return text


def insert_system_bar_composable(text: str) -> str:
    if "fun AppSystemBars()" in text:
        print("[INFO] AppSystemBars() already exists.")
        return text

    marker = "        @Composable\n        fun PesaZaShambaTheme(content: @Composable () -> Unit) {"

    insert_code = """
        @Composable
        fun AppSystemBars() {
            val view = LocalView.current

            SideEffect {
                val window = (view.context as android.app.Activity).window

                window.navigationBarColor = android.graphics.Color.rgb(6, 76, 67)
                window.statusBarColor = android.graphics.Color.rgb(255, 253, 243)

                WindowCompat.getInsetsController(window, view).apply {
                    // False means Android uses light/white nav buttons on the dark green bar.
                    isAppearanceLightNavigationBars = false

                    // True keeps dark status bar icons on the cream status bar.
                    isAppearanceLightStatusBars = true
                }

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    window.isNavigationBarContrastEnforced = true
                }
            }
        }

"""

    if marker in text:
        text = text.replace(marker, insert_code + marker)
        print("[OK] Added AppSystemBars() function.")
    else:
        print("[WARNING] Could not find PesaZaShambaTheme marker. AppSystemBars() was not inserted.")

    return text


def call_system_bar_composable(text: str) -> str:
    app_function_marker = "        fun PesaZaShambaApp(showMessage: (String) -> Unit) {"

    if app_function_marker not in text:
        print("[WARNING] Could not find PesaZaShambaApp() function marker.")
        return text

    start = text.find(app_function_marker)
    next_part = text[start:start + 700]

    if "AppSystemBars()" in next_part:
        print("[INFO] AppSystemBars() is already called.")
        return text

    text = text.replace(app_function_marker, app_function_marker + "\n            AppSystemBars()")
    print("[OK] AppSystemBars() is now called by PesaZaShambaApp().")
    return text


def insert_back_handler(text: str) -> str:
    if "BackHandler(enabled = currentScreen != Screen.Login)" in text:
        print("[INFO] BackHandler already exists.")
        return text

    target = '            val records = remember { mutableStateMapOf<String, ExpenseRecord>() }'

    back_handler = """
            BackHandler(enabled = currentScreen != Screen.Login) {
                currentScreen = when (currentScreen) {
                    Screen.Dairy,
                    Screen.Maize,
                    Screen.Records -> Screen.Selection

                    Screen.Selection -> Screen.Login
                    Screen.Login -> Screen.Login
                }
            }"""

    if target in text:
        text = text.replace(target, target + "\n" + back_handler)
        print("[OK] Added Android phone Back button navigation behavior.")
    else:
        print("[WARNING] Could not find records state line. BackHandler was not inserted.")
        print("          Manually add BackHandler inside PesaZaShambaApp() after currentScreen is declared.")

    return text


def update_main_activity() -> None:
    if not MAIN_ACTIVITY_FILE.exists():
        raise FileNotFoundError(f"Could not find MainActivity.kt at: {MAIN_ACTIVITY_FILE}")

    backup_file(MAIN_ACTIVITY_FILE, ".navback.bak")

    text = MAIN_ACTIVITY_FILE.read_text(encoding="utf-8")

    text = ensure_imports(text)
    text = insert_system_bar_composable(text)
    text = call_system_bar_composable(text)
    text = insert_back_handler(text)

    MAIN_ACTIVITY_FILE.write_text(text, encoding="utf-8")
    print("[OK] MainActivity.kt updated.")


def main() -> None:
    print("Updating Pesa Za Shamba navigation bar and Back button...")
    print(f"Project folder: {PROJECT_DIR}")

    if not PROJECT_DIR.exists():
        raise FileNotFoundError(f"Project folder does not exist: {PROJECT_DIR}")

    update_themes_xml()
    update_main_activity()

    print("\n[SUCCESS] Navigation bar and Back button updates completed.")
    print("\nNext steps in Android Studio:")
    print("1. File > Sync Project with Gradle Files")
    print("2. Build > Clean Project")
    print("3. Build > Assemble Project")
    print("4. Run the app")
    print("\nExpected Back button behavior:")
    print("- Dairy / Maize / Records -> Selection screen")
    print("- Selection screen -> Login screen")
    print("- Login screen -> exits app normally")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n[ERROR] Update failed.")
        print(error)
        sys.exit(1)
