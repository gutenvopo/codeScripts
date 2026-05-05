Windows Button Test for Kwa

This small script creates a simple Windows GUI titled "windows button test for Kwa" with two buttons:
- Produce output: plays a Windows system sound and opens a small "hello world" window.
- Exit: closes the application.

Files:
- windows_button_test.py : the Python script located in this folder.

Build an exe (Windows):
1. Open PowerShell and change directory to this folder:

   cd "$env:USERPROFILE\Documents\coding\codeScripts"

2. (Optional) Create/activate a virtual environment.

3. Install PyInstaller if you don't have it:

   python -m pip install --user pyinstaller

4. Build a single-file, windowed exe:

   python -m PyInstaller --onefile --noconsole --name "windows_button_test_for_Kwa" windows_button_test.py

5. If the build succeeds, the exe will be in the "dist" folder. Copy it to Downloads:

   Copy-Item -Path .\dist\windows_button_test_for_Kwa.exe -Destination "$env:USERPROFILE\Downloads" -Force

Run the exe from Downloads by double-clicking it.

Notes:
- The script uses only built-in modules (`tkinter`, `winsound`) so PyInstaller bundling should be straightforward.
- If your Python executable is named `py` or `python3`, replace `python` with the appropriate command.
