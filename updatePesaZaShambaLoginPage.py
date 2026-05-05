# updatePesaZaShambaLoginPage.py
# ------------------------------------------------------------
# This script updates your existing Android Studio project:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# It makes these login page changes:
# 1. Changes subtitle text from:
#      "Farm Expense Tracker for Kesses Farmers"
#    to:
#      "Expense Tracker for Farmers"
#
# 2. Makes the login text-box labels smaller by using placeholder text.
#
# 3. Confirms login is admin / 1234.
#
# Run in PowerShell:
#   python C:\Users\kirwa\Documents\coding\codeScripts\updatePesaZaShambaLoginPage.py
# ------------------------------------------------------------

from pathlib import Path
import re
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


def backup_file(path: Path) -> None:
    if path.exists():
        backup = path.with_suffix(path.suffix + ".loginpage.bak")
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[BACKUP] {backup}")


def replace_subtitle(text: str) -> str:
    old = 'text = "Farm Expense Tracker for Kesses Farmers"'
    new = 'text = "Expense Tracker for Farmers"'

    if old in text:
        text = text.replace(old, new)
        print("[OK] Login subtitle changed to: Expense Tracker for Farmers")
    elif new in text:
        print("[INFO] Login subtitle is already updated.")
    else:
        print("[WARNING] Could not find the exact old subtitle text.")

    return text


def add_small_label_style_imports(text: str) -> str:
    if "import androidx.compose.ui.unit.sp" not in text:
        text = text.replace(
            "import androidx.compose.ui.unit.dp",
            "import androidx.compose.ui.unit.dp\n        import androidx.compose.ui.unit.sp"
        )
        print("[OK] Added sp import for small text sizing.")
    else:
        print("[INFO] sp import already exists.")

    return text


def update_login_text_fields(text: str) -> str:
    old_username = '''label = { Text("Username or Phone Number") },
                                leadingIcon = {
                                    Icon(Icons.Default.Person, contentDescription = null)
                                },
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()'''

    new_username = '''placeholder = {
                                    Text(
                                        text = "Username or Phone Number",
                                        style = MaterialTheme.typography.bodySmall,
                                        fontSize = 12.sp
                                    )
                                },
                                leadingIcon = {
                                    Icon(Icons.Default.Person, contentDescription = null)
                                },
                                singleLine = true,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(64.dp)'''

    if old_username in text:
        text = text.replace(old_username, new_username)
        print("[OK] Username text box label changed to smaller placeholder text.")
    elif 'text = "Username or Phone Number"' in text and "fontSize = 12.sp" in text:
        print("[INFO] Username text box already appears updated.")
    else:
        text_new = re.sub(
            r'label\s*=\s*\{\s*Text\("Username or Phone Number"\)\s*\}',
            '''placeholder = {
                                    Text(
                                        text = "Username or Phone Number",
                                        style = MaterialTheme.typography.bodySmall,
                                        fontSize = 12.sp
                                    )
                                }''',
            text
        )
        if text_new != text:
            text = text_new
            print("[OK] Username text box updated using flexible replacement.")
        else:
            print("[WARNING] Could not find username label to update.")

    old_password = '''label = { Text("Password") },
                                leadingIcon = {
                                    Icon(Icons.Default.Lock, contentDescription = null)
                                },
                                visualTransformation = PasswordVisualTransformation(),
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()'''

    new_password = '''placeholder = {
                                    Text(
                                        text = "Password",
                                        style = MaterialTheme.typography.bodySmall,
                                        fontSize = 12.sp
                                    )
                                },
                                leadingIcon = {
                                    Icon(Icons.Default.Lock, contentDescription = null)
                                },
                                visualTransformation = PasswordVisualTransformation(),
                                singleLine = true,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(64.dp)'''

    if old_password in text:
        text = text.replace(old_password, new_password)
        print("[OK] Password text box label changed to smaller placeholder text.")
    elif 'text = "Password"' in text and "fontSize = 12.sp" in text:
        print("[INFO] Password text box already appears updated.")
    else:
        text_new = re.sub(
            r'label\s*=\s*\{\s*Text\("Password"\)\s*\}',
            '''placeholder = {
                                    Text(
                                        text = "Password",
                                        style = MaterialTheme.typography.bodySmall,
                                        fontSize = 12.sp
                                    )
                                }''',
            text
        )
        if text_new != text:
            text = text_new
            print("[OK] Password text box updated using flexible replacement.")
        else:
            print("[WARNING] Could not find password label to update.")

    return text


def update_login_button_credentials(text: str) -> str:
    old_any_login = '''if (username.isNotBlank() && password.isNotBlank()) {
                                        onLoginSuccess()
                                    }'''
    new_admin_login = '''if (username == "admin" && password == "1234") {
                                        onLoginSuccess()
                                    }'''

    if old_any_login in text:
        text = text.replace(old_any_login, new_admin_login)
        print("[OK] Login credentials set to admin / 1234.")
    elif 'username == "admin" && password == "1234"' in text:
        print("[INFO] Login credentials are already admin / 1234.")
    else:
        print("[INFO] Login credential block was not changed.")

    text = text.replace(
        'text = "Demo: enter any username and password"',
        'text = "Demo Login: admin / 1234"'
    )

    return text


def main() -> None:
    print("Updating Pesa Za Shamba login page...")
    print(f"Project folder: {PROJECT_DIR}")

    if not MAIN_ACTIVITY_FILE.exists():
        raise FileNotFoundError(f"Could not find MainActivity.kt at: {MAIN_ACTIVITY_FILE}")

    backup_file(MAIN_ACTIVITY_FILE)

    text = MAIN_ACTIVITY_FILE.read_text(encoding="utf-8")

    text = replace_subtitle(text)
    text = add_small_label_style_imports(text)
    text = update_login_text_fields(text)
    text = update_login_button_credentials(text)

    MAIN_ACTIVITY_FILE.write_text(text, encoding="utf-8")

    print("\n[SUCCESS] Login page update completed.")
    print("\nNext steps in Android Studio:")
    print("1. File > Sync Project with Gradle Files")
    print("2. Build > Clean Project")
    print("3. Build > Assemble Project")
    print("4. Run the app")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n[ERROR] Update failed.")
        print(error)
        sys.exit(1)
