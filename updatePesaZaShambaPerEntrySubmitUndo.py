# updatePesaZaShambaPerEntrySubmitUndo.py
# ------------------------------------------------------------
# Updates the Dairy and Maize expense entry pages for:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# New behavior for every expense text entry:
# 1. The running tally appears above each text box.
# 2. A green Submit button appears below each text box.
#    - It adds the latest typed number to that field's running tally.
#    - It clears the text box after submitting.
# 3. A red Undo button appears beside Submit.
#    - It reverses the most recent submitted amount for that field.
#
# The final page-level "Submit Dairy Record" / "Submit Maize Record" button
# still saves the record using the running tallies.
#
# Run in PowerShell:
#   python C:\Users\kirwa\Documents\coding\codeScripts\updatePesaZaShambaPerEntrySubmitUndo.py
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

BACKUP_DIR = PROJECT_DIR / "python_update_backups"


def backup_main_activity() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / "MainActivity_before_per_entry_submit_undo.kt.bak"
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


def replace_state_and_total_block(text: str) -> str:
    if "val inputValues = remember" in text and "val fieldTotals = remember" in text:
        print("[INFO] Per-entry state maps already appear to exist.")
        return text

    function_marker = "fun ExpenseFormScreen("
    function_start = text.find(function_marker)

    if function_start == -1:
        print("[ERROR] Could not find ExpenseFormScreen function.")
        return text

    start = text.find("val expenseValues = remember", function_start)
    if start == -1:
        print("[ERROR] Could not find old expenseValues state block.")
        return text

    end = text.find("AppBackground {", start)
    if end == -1:
        print("[ERROR] Could not find AppBackground marker after expense state block.")
        return text

    new_block = """val inputValues = remember {
                mutableStateMapOf<String, String>().apply {
                    fields.forEach { put(it, "") }
                }
            }

            val fieldTotals = remember {
                mutableStateMapOf<String, Double>().apply {
                    fields.forEach { put(it, 0.0) }
                }
            }

            val lastSubmittedValues = remember {
                mutableStateMapOf<String, Double>().apply {
                    fields.forEach { put(it, 0.0) }
                }
            }

            val total = fieldTotals.values.sum()

            """

    text = text[:start] + new_block + text[end:]
    print("[OK] Replaced old expenseValues total logic with per-field running tally maps.")
    return text


def replace_entry_boxes_block(text: str) -> str:
    if "val submittedAmount = (inputValues[field] ?: \"\")" in text:
        print("[INFO] Entry boxes already have Submit/Undo logic.")
        return text

    function_marker = "fun ExpenseFormScreen("
    function_start = text.find(function_marker)

    if function_start == -1:
        print("[ERROR] Could not find ExpenseFormScreen function.")
        return text

    start = text.find("fields.forEach { field ->", function_start)
    if start == -1:
        print("[ERROR] Could not find fields.forEach entry box block.")
        return text

    end_marker = "Spacer(modifier = Modifier.height(14.dp))"
    end = text.find(end_marker, start)

    if end == -1:
        print("[ERROR] Could not find Spacer height 14 marker after entry boxes.")
        return text

    new_block = """fields.forEach { field ->
                                val currentTotal = fieldTotals[field] ?: 0.0
                                val lastSubmitted = lastSubmittedValues[field] ?: 0.0

                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 10.dp)
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
                                            text = formatKes(currentTotal),
                                            style = MaterialTheme.typography.bodyMedium,
                                            fontWeight = FontWeight.Bold,
                                            color = FarmGreen
                                        )
                                    }

                                    Spacer(modifier = Modifier.height(4.dp))

                                    OutlinedTextField(
                                        value = inputValues[field] ?: "",
                                        onValueChange = { value ->
                                            val cleaned = value.filter { it.isDigit() || it == '.' || it == ',' }
                                            inputValues[field] = cleaned
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

                                    Spacer(modifier = Modifier.height(8.dp))

                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                                    ) {
                                        Button(
                                            onClick = {
                                                val submittedAmount = (inputValues[field] ?: "")
                                                    .replace(",", "")
                                                    .trim()
                                                    .toDoubleOrNull() ?: 0.0

                                                if (submittedAmount != 0.0) {
                                                    fieldTotals[field] = (fieldTotals[field] ?: 0.0) + submittedAmount
                                                    lastSubmittedValues[field] = submittedAmount
                                                    inputValues[field] = ""
                                                }
                                            },
                                            modifier = Modifier
                                                .weight(1f)
                                                .height(46.dp),
                                            shape = RoundedCornerShape(14.dp),
                                            colors = ButtonDefaults.buttonColors(containerColor = FarmGreen)
                                        ) {
                                            Text("Submit")
                                        }

                                        Button(
                                            onClick = {
                                                if (lastSubmitted != 0.0) {
                                                    val updatedTotal = ((fieldTotals[field] ?: 0.0) - lastSubmitted)
                                                        .coerceAtLeast(0.0)
                                                    fieldTotals[field] = updatedTotal
                                                    lastSubmittedValues[field] = 0.0
                                                }
                                            },
                                            modifier = Modifier
                                                .weight(1f)
                                                .height(46.dp),
                                            shape = RoundedCornerShape(14.dp),
                                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFC62828))
                                        ) {
                                            Text("Undo")
                                        }
                                    }
                                }
                            }

                            """

    text = text[:start] + new_block + text[end:]
    print("[OK] Replaced entry boxes with per-field Submit and Undo buttons.")
    return text


def replace_record_items(text: str) -> str:
    replacements = [
        (
            "items = expenseValues.toMap()",
            'items = fieldTotals.mapValues { String.format(Locale.US, "%.2f", it.value) }'
        ),
        (
            "items = inputValues.toMap()",
            'items = fieldTotals.mapValues { String.format(Locale.US, "%.2f", it.value) }'
        ),
    ]

    changed = False
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            changed = True

    if changed:
        print("[OK] Final record saving now uses running tallies.")
    elif "items = fieldTotals.mapValues" in text:
        print("[INFO] Final record saving already uses fieldTotals.")
    else:
        print("[WARNING] Could not find record items assignment to update.")

    return text


def main() -> None:
    print("Updating Pesa Za Shamba per-entry Submit/Undo behavior...")
    print(f"Project folder: {PROJECT_DIR}")

    if not PROJECT_DIR.exists():
        raise FileNotFoundError(f"Project folder does not exist: {PROJECT_DIR}")

    if not MAIN_ACTIVITY_FILE.exists():
        raise FileNotFoundError(f"Could not find MainActivity.kt at: {MAIN_ACTIVITY_FILE}")

    remove_bad_resource_backups()
    backup_main_activity()

    text = MAIN_ACTIVITY_FILE.read_text(encoding="utf-8")

    text = replace_state_and_total_block(text)
    text = replace_entry_boxes_block(text)
    text = replace_record_items(text)

    MAIN_ACTIVITY_FILE.write_text(text, encoding="utf-8")

    print()
    print("[SUCCESS] Per-entry Submit/Undo update completed.")
    print()
    print("Expected behavior:")
    print("- Type a number in an entry box.")
    print("- Press green Submit under that box.")
    print("- The field tally above the box increases.")
    print("- The text box becomes empty.")
    print("- Press red Undo to reverse that field's most recent submitted amount.")
    print()
    print("Next steps in Android Studio:")
    print("1. File > Sync Project with Gradle Files")
    print("2. Build > Clean Project")
    print("3. Build > Assemble Project")
    print("4. Run the app")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("[ERROR] Update failed.")
        print(error)
        sys.exit(1)
