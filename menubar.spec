# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Numbers Workout menu bar app.

Build:  .venv/bin/pyinstaller --noconfirm --clean menubar.spec
Output: dist/Numbers Workout.app  (arm64, menu-bar-only: LSUIElement)
"""

import json
import os

with open(os.path.join(SPECPATH, "info.plist.json"), encoding="utf-8") as f:
    info_plist = json.load(f)

a = Analysis(
    ["menubar.py"],
    pathex=[SPECPATH],
    binaries=[],
    datas=[(os.path.join(SPECPATH, "menubar_icon.png"), ".")],
    hiddenimports=[],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Numbers Workout",
    debug=False,
    strip=False,
    upx=False,
    console=False,  # menu-bar app: no terminal window
    icon=os.path.join(SPECPATH, "app_icon.icns"),
    info_plist=info_plist,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Numbers Workout",
)

app = BUNDLE(
    coll,
    name="Numbers Workout.app",
    icon=os.path.join(SPECPATH, "app_icon.icns"),
    bundle_identifier="com.sergey.numbers-workout",
    info_plist=info_plist,
)
