# updatePesaZaShambaDairyEntryBoxes.py
# ------------------------------------------------------------
# This script updates your existing Android Studio project:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# It changes the expense entry boxes so that:
# 1. The name of each entry box appears above the entry box.
# 2. A running amount/tally for that specific entry appears above the entry box.
# 3. The existing total expenses card will still keep updating as values are entered.
#
# Note:
# The Dairy and Maize screens use the same reusable ExpenseFormScreen function.
# This script updates that shared form, so the improvement will appear on both
# Dairy and Maize screens.
#
# Run in PowerShell:
#   python C:\Users\kirwa\Documents\coding\codeScripts\updatePesaZaShambaDairyEntryBoxes.py
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


def backup_file(path: Path) -> None:
    if path.exists():
        backup = path.with_suffix(path.suffix + ".entryboxes.bak")
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[BACKUP] {backup}")


def update_expense_text_boxes(text: str) -> str:
    old_block = '''fields.forEach { field ->
                                OutlinedTextField(
                                    value = expenseValues[field] ?: "",
                                    onValueChange = { value ->
                                        val cleaned = value.filter { it.isDigit() || it == '.' || it == ',' }
                                        expenseValues[field] = cleaned
                                    },
                                    label = { Text(field + " - KES") },
                                    prefix = { Text("KSh ") },
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    singleLine = true,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 6.dp)
                                )
                            }'''

    new_block = '''fields.forEach { field ->
                                val currentAmount = (expenseValues[field] ?: "")
                                    .replace(",", "")
                                    .trim()
                                    .toDoubleOrNull() ?: 0.0

                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 8.dp)
                                ) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = field,
                                            style = MaterialTheme.typography.bodyMedium,
                                            fontWeight = FontWeight.SemiBold,
                                            color = DeepForest
                                        )

                                        Text(
                                            text = formatKes(currentAmount),
                                            style = MaterialTheme.typography.bodyMedium,
                                            fontWeight = FontWeight.Bold,
                                            color = FarmGreen
                                        )
                                    }

                                    Spacer(modifier = Modifier.height(4.dp))

                                    OutlinedTextField(
                                        value = expenseValues[field] ?: "",
                                        onValueChange = { value ->
                                            val cleaned = value.filter { it.isDigit() || it == '.' || it == ',' }
                                            expenseValues[field] = cleaned
                                        },
                                        placeholder = {
                                            Text(
                                                text = "Enter amount in KES",
                                                style = MaterialTheme.typography.bodySmall
                                            )
                                        },
                                        prefix = { Text("KSh ") },
                                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                        singleLine = true,
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                }
                            }'''

    if old_block in text:
        print("[OK] Found the old entry-box block.")
        return text.replace(old_block, new_block)

    if 'val currentAmount = (expenseValues[field] ?: "")' in text:
        print("[INFO] Entry boxes already appear to be updated.")
        return text

    print("[WARNING] Could not find the exact old entry-box block.")
    print("          I will try a simpler replacement method.")

    start_marker = "fields.forEach { field ->"
    start = text.find(start_marker)

    if start == -1:
        print("[ERROR] Could not find: fields.forEach { field ->")
        return text

    end_marker = "Spacer(modifier = Modifier.height(14.dp))"
    end = text.find(end_marker, start)

    if end == -1:
        print("[ERROR] Could not find the end marker after the entry boxes.")
        return text

    before = text[:start]
    after = text[end:]

    print("[OK] Updated entry boxes using simple marker replacement.")
    return before + new_block + "\n\n                            " + after


def main() -> None:
    print("Updating Pesa Za Shamba entry boxes...")
    print(f"Project folder: {PROJECT_DIR}")

    if not MAIN_ACTIVITY_FILE.exists():
        raise FileNotFoundError(f"Could not find MainActivity.kt at: {MAIN_ACTIVITY_FILE}")

    backup_file(MAIN_ACTIVITY_FILE)

    text = MAIN_ACTIVITY_FILE.read_text(encoding="utf-8")
    text = update_expense_text_boxes(text)
    MAIN_ACTIVITY_FILE.write_text(text, encoding="utf-8")

    print("\n[SUCCESS] Entry-box update completed.")
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
