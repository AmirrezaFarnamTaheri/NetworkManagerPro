# -*- mode: python ; coding: utf-8 -*-
import os

import branding
from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(SPECPATH)

datas = []
binaries = []
hiddenimports = ["pystray._win32", "plugin_host"]
for pkg in ("customtkinter", "plyer", "pystray"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

assets_dir = os.path.join(ROOT, "assets")
if os.path.isdir(assets_dir):
    datas.append((assets_dir, "assets"))

docs_dir = os.path.join(ROOT, "docs")
if os.path.isdir(docs_dir):
    datas.append((docs_dir, "docs"))

plugins_dir = os.path.join(ROOT, "plugins")
if os.path.isdir(plugins_dir):
    datas.append((plugins_dir, "plugins"))

icon_path = os.path.join(ROOT, "assets", "app.ico")
icon_arg = icon_path if os.path.isfile(icon_path) else None

a = Analysis(
    ["main.py"],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    exclude_binaries=False,
    name=branding.INSTALLER_BASENAME,
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
    icon=icon_arg,
)
