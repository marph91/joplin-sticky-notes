# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


# Generate the executable name based on OS.
import platform
executable_name = f"joplin-sticky-notes-{platform.system().lower()}"


a = Analysis(
    ["joplin_sticky_notes/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("joplin_sticky_notes/logo_96_blue.png", "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["numpy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=executable_name,
    icon="img/logo_96_blue.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# for debugging
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name="joplin-sticky-notes-folder",
# )
