from __future__ import annotations

import runpy
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

ROOT = Path(SPEC).resolve().parent.parent
SRC = ROOT / "src"
metadata = runpy.run_path(SRC / "qbsearch" / "version.py")
version = metadata["__version__"]
version_parts = tuple(int(part) for part in version.split("."))
version_tuple = (*version_parts, *(0 for _ in range(4 - len(version_parts))))

datas = (
    collect_data_files("customtkinter")
    + collect_data_files("truststore")
    + collect_data_files("certifi")
    + [(str(SRC / "qbsearch" / "assets" / "qbsearch.png"), "qbsearch/assets")]
)
hiddenimports = collect_submodules("keyring.backends")
icon_path = ROOT / "assets" / "app.ico"

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=version_tuple,
        prodvers=version_tuple,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", metadata["COMPANY_NAME"]),
                        StringStruct("FileDescription", metadata["APP_NAME"]),
                        StringStruct("FileVersion", version),
                        StringStruct("InternalName", "qbsearch"),
                        StringStruct("OriginalFilename", "qbsearch.exe"),
                        StringStruct("ProductName", metadata["APP_NAME"]),
                        StringStruct("ProductVersion", version),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

a = Analysis(
    [str(SRC / "qbsearch" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter.test"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="qbsearch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
    version=version_info,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="qbsearch",
)
