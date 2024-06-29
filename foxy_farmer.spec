# -*- mode: python ; coding: utf-8 -*-
import importlib
import pathlib
import platform
import sysconfig

from PyInstaller.utils.hooks import collect_submodules

THIS_IS_WINDOWS = platform.system().lower().startswith("win")

if THIS_IS_WINDOWS:
    hidden_imports_for_windows = ["win32timezone", "win32cred", "pywintypes", "win32ctypes.pywin32"]
    dll_paths = pathlib.Path(sysconfig.get_path("platlib")) / "*.dll"
    binaries = [
        (
            dll_paths,
            ".",
        ),
    ]
else:
    hidden_imports_for_windows = []
    binaries = []

hiddenimports = [
    *hidden_imports_for_windows,
]

DEP_ROOT = pathlib.Path(importlib.import_module("chia").__file__).absolute().parent.parent
datas = []
datas.append((f"{DEP_ROOT}/chia/util/english.txt", "chia/util"))
datas.append((f"{DEP_ROOT}/chia/util/initial-config.yaml", "chia/util"))
for path in sorted({path.parent for path in DEP_ROOT.joinpath("chia").rglob("*.hex")}):
    datas.append((f"{path}/*.hex", path.relative_to(DEP_ROOT)))
datas.append((f"{DEP_ROOT}/chia/ssl/*", "chia/ssl"))
datas.append((f"{DEP_ROOT}/mozilla-ca/*", "mozilla-ca"))

block_cipher = None

a = Analysis(
    ['foxy_farmer/foxy_farmer_main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
