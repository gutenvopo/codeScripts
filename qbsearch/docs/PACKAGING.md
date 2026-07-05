# Packaging qbSearch for Windows

## Prerequisites

- Windows 11 with 64-bit Python 3.13.x available to `uv`. Do not build with
  Python 3.14 because the supported Tk stack is pinned to Python 3.13.
- [`uv`](https://docs.astral.sh/uv/) on `PATH`.
- [Inno Setup 6](https://jrsoftware.org/isinfo.php), installed in its default
  location or supplied with `-IsccPath`.

PyInstaller is a development dependency and is installed by `uv sync`. The
end-user machine does not need Python, `uv`, or Inno Setup.

## Build

From a fresh PowerShell terminal in the `qbsearch` directory:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build.ps1
```

If Inno Setup is installed in a nonstandard location:

```powershell
.\scripts\build.ps1 -IsccPath 'D:\Tools\Inno Setup 6\ISCC.exe'
```

The script synchronizes the Python 3.13 environment, activates `.venv`, removes
generated PyInstaller and distribution output, creates the windowed onedir app
at `dist\qbsearch\`, and writes the installer to `dist\installer\`.

The build uses `uv sync --system-certs` so Norton and other HTTPS inspection
products can be validated through the Windows certificate store. The frozen app
also keeps `truststore` and `certifi` data so that behavior remains available.

## Test on a clean machine

1. Confirm `dist\qbsearch\qbsearch.exe` starts locally, renders its
   CustomTkinter theme, and can connect to qBittorrent with Norton enabled.
2. Copy only `dist\installer\qbsearch-<version>-setup.exe` to Windows Sandbox or
   a clean Windows 11 VM with no Python installation.
3. Install once for the current user and confirm no administrator prompt
   appears. Launch qbSearch from the Start Menu and optional desktop shortcut.
4. Repeat in a fresh snapshot, choose the all-users installation mode, and
   confirm Windows requests elevation.
5. Save settings, uninstall, answer **No** to the user-data prompt, and confirm
   `%LOCALAPPDATA%\qbsearch` remains.
6. Reinstall and uninstall again, answer **Yes**, and confirm that directory is
   removed while the installed program files are always removed.

The generated binaries are unsigned. Configure your signing service after the
build, sign `dist\qbsearch\qbsearch.exe`, rebuild the installer if required by
your signing policy, and sign the final installer before release.

## Bump the version

Edit only `src\qbsearch\version.py`:

```python
__version__ = "0.2.0"
```

Hatch reads that value for package metadata, the app imports it at runtime, the
PyInstaller spec embeds it in Windows version resources, and `build.ps1` passes
it to Inno Setup for installer metadata and the output filename.
