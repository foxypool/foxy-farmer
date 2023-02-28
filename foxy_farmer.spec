# -*- mode: python ; coding: utf-8 -*-
import importlib
import pathlib

block_cipher = None

DEP_ROOT = pathlib.Path(importlib.import_module("chia").__file__).absolute().parent.parent
datas = []
datas.append((f"{DEP_ROOT}/chia/util/english.txt", "chia/util"))
datas.append((f"{DEP_ROOT}/chia/util/initial-config.yaml", "chia/util"))
datas.append((f"{DEP_ROOT}/chia/wallet/puzzles/*.hex", "chia/wallet/puzzles"))
datas.append((f"{DEP_ROOT}/chia/ssl/*", "chia/ssl"))
datas.append((f"{DEP_ROOT}/mozilla-ca/*", "mozilla-ca"))


a = Analysis(
    ['foxy_farmer/foxy_farmer.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name='foxy-farmer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='foxy.ico',
)
