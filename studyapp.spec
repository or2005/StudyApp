# -*- mode: python ; coding: utf-8 -*-
"""בנייה: python tools/build_release.py"""
from __future__ import annotations

import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_data_files

ROOT = os.path.abspath(os.path.dirname(SPEC))
ICON = os.path.join(ROOT, "assets", "icon.ico")
ICON_PNG = os.path.join(ROOT, "assets", "icon.png")
VERSION_FILE = os.path.join(ROOT, "packaging", "file_version_info.txt")

ctk_datas, ctk_binaries, ctk_hidden = collect_all("customtkinter")

datas = [
    (os.path.join(ROOT, "data"), "data"),
    (os.path.join(ROOT, "assets"), "assets"),
    (os.path.join(ROOT, "docs", "TERMS.md"), "docs"),
    (os.path.join(ROOT, "docs", "latest.json"), "docs"),
    (os.path.join(ROOT, "LICENSE"), "."),
]
datas += ctk_datas
datas += collect_data_files("customtkinter")

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=ctk_binaries,
    datas=datas,
    hiddenimports=[
        "customtkinter",
        "darkdetect",
        "packaging",
        "packaging.version",
        "core.updates",
        "core.telemetry",
        "core.display",
        *ctk_hidden,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(ROOT, "packaging", "windows", "pyi_rth_dpi.py")]
    if sys.platform == "win32"
    else [],
    excludes=[
        "pytest",
        "unittest",
        "tkinter.test",
        "numpy",
        "pandas",
        "matplotlib",
        "scipy",
        "notebook",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe_kwargs = dict(
    exclude_binaries=True,
    name="StudyApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
if sys.platform == "win32":
    if os.path.isfile(ICON):
        exe_kwargs["icon"] = ICON
    if os.path.isfile(VERSION_FILE):
        exe_kwargs["version"] = VERSION_FILE
    manifest = os.path.join(ROOT, "packaging", "windows", "dpi.manifest")
    if os.path.isfile(manifest):
        exe_kwargs["manifest"] = manifest
elif os.path.isfile(ICON_PNG):
    exe_kwargs["icon"] = ICON_PNG

exe = EXE(pyz, a.scripts, [], **exe_kwargs)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="StudyApp",
)
