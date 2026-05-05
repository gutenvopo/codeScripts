#!/usr/bin/env python3
"""
enable_long_paths.py
Enables Windows long path support (removes the legacy 260-char MAX_PATH limit for modern apps).

What it does:
- Checks for admin; if not admin, auto-relaunches itself with elevation
- Sets: HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1 (REG_DWORD)
- Prints the resulting value and a reminder to reboot

Usage:
    python enable_long_paths.py
"""

import sys
import ctypes
import winreg
import subprocess

REG_PATH = r"SYSTEM\CurrentControlSet\Control\FileSystem"
REG_NAME = "LongPathsEnabled"

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def elevate():
    # Relaunch the current script with admin privileges
    params = " ".join(f'"{a}"' for a in sys.argv)
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    # ShellExecute returns >32 on success; otherwise it's an error code
    if ret <= 32:
        sys.exit("Elevation declined or failed.")

def set_long_paths_enabled():
    # Open HKLM with write access
    with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hklm:
        with winreg.OpenKey(hklm, REG_PATH, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as key:
            winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_DWORD, 1)

def get_current_value():
    try:
        with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hklm:
            with winreg.OpenKey(hklm, REG_PATH, 0, winreg.KEY_QUERY_VALUE) as key:
                val, typ = winreg.QueryValueEx(key, REG_NAME)
                return int(val)
    except FileNotFoundError:
        return None

def main():
    if not is_admin():
        print("[i] Elevation required. Prompting for Administrator...")
        elevate()
        return  # Elevated instance will run the code again

    try:
        print("[+] Writing registry value to enable long paths...")
        set_long_paths_enabled()
        val = get_current_value()
        if val == 1:
            print("[✓] Long paths ENABLED (LongPathsEnabled=1).")
        else:
            print(f"[?] Unexpected value for {REG_NAME}: {val!r}")
    except PermissionError:
        print("[x] Permission denied. Please run as Administrator.")
        sys.exit(1)
    except Exception as e:
        print(f"[x] Error: {e}")
        sys.exit(1)

    print("\nNext steps:")
    print(" • Restart Windows to ensure all apps pick up the change.")
    print(" • Note: Some legacy apps may still enforce old limits unless they use modern APIs.")
    print(" • For domain-managed PCs, a Group Policy may override this setting.")

if __name__ == "__main__":
    main()
