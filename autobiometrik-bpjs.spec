# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect autoit data files (including AutoItX3.dll / AutoItX3_x64.dll)
autoit_datas = []
autoit_hiddenimports = []

try:
    autoit_datas = collect_data_files('autoit')
    autoit_hiddenimports = collect_submodules('autoit')
except Exception:
    pass

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=autoit_datas,
    hiddenimports=['flask', 'flask_cors', 'autoit'] + autoit_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='autobiometrik-bpjs',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
