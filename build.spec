# PyInstaller spec for 星黎音频 (Xingli Audio)
# Build with: pyinstaller build.spec --noconfirm
# Output:    dist/星黎音频.exe (single-file, portable)

import sys
from pathlib import Path

PROJECT_DIR = Path(SPECPATH).resolve()
ICON_PATH = PROJECT_DIR / "assets" / "icon_512_for_exe.ico"
ASSETS_DIR = PROJECT_DIR / "assets"

# Collect all our generated icon assets (bundled into the exe)
datas = [
    (str(ASSETS_DIR / "icon.ico"),    "assets"),
    (str(ASSETS_DIR / "icon_32.png"), "assets"),
    (str(ASSETS_DIR / "icon_512.png"), "assets"),
    (str(ASSETS_DIR / "icon_512_for_exe.ico"), "assets"),
]

# Some pycaw / comtypes modules need to be force-included for PyInstaller
hiddenimports = [
    "comtypes",
    "comtypes.client",
    "pycaw",
    "pycaw.pycaw",
    "pycaw.constants",
    "pycaw.utils",
    "keyboard",
    "PySide6.QtSvg",  # 防 icon 渲染问题
    "PySide6.QtWidgets",
    "PySide6.QtGui",
    "PySide6.QtCore",
    "PySide6.QtNetwork",  # QLocalServer/QLocalSocket (单实例锁)
]

# On Windows, subsystem='windows' => no console window
block_cipher = None

a = Analysis(
    [str(PROJECT_DIR / "main.py")],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
        "PySide6.QtBluetooth",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtLocation",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtNetworkAuth",
        "PySide6.QtPositioning",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtTest",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets",
        "numpy",
        "pandas",
        "matplotlib",
        "scipy",
        "IPython",
        "jupyter",
    ],
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
    name="星黎音频",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                  # 不弹黑色控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH) if ICON_PATH.exists() else None,
    version=None,
)
