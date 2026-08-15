"""简化截图: 用 PIL.ImageGrab 抓窗口"""
import os, sys, time, subprocess, shutil, ctypes
import ctypes.wintypes
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from core.audio import list_output_devices

real = list_output_devices()
target_dir = PROJECT / "dist"
target_config = target_dir / "config.json"
backup = target_dir / "config.json.bak"
if target_config.exists() and not backup.exists():
    shutil.copy2(target_config, backup)

import json
config_data = {
    "close_behavior": "minimize",
    "notify_on_switch": True,
    "start_minimized": False,
    "auto_start": True,
    "hotkey_device_pairs": [
        {"hotkey": "ctrl+alt+1", "device_id": real[0].id, "device_name": real[0].name},
        {"hotkey": "ctrl+alt+2", "device_id": real[1].id, "device_name": real[1].name},
        {"hotkey": "ctrl+shift+f5", "device_id": "", "device_name": ""},
    ],
}
target_config.write_text(json.dumps(config_data, ensure_ascii=False, indent=2), encoding="utf-8")

EXE = PROJECT / "dist" / "星黎音频.exe"
env = os.environ.copy()
env.pop("QT_QPA_PLATFORM", None)
proc = subprocess.Popen([str(EXE)], cwd=str(PROJECT), env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"exe pid: {proc.pid}")
for i in range(15):
    time.sleep(0.5)
    if proc.poll() is not None:
        out, err = proc.communicate(timeout=2)
        print(f"!! exe 异常: {proc.returncode}")
        sys.exit(1)

EnumWindows = ctypes.windll.user32.EnumWindows
GetWindowTextW = ctypes.windll.user32.GetWindowTextW
GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
SetWindowPos = ctypes.windll.user32.SetWindowPos
GetWindowRect = ctypes.windll.user32.GetWindowRect
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

hwnds = []
def foreach(hwnd, lParam):
    if IsWindowVisible(hwnd):
        length = GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            GetWindowTextW(hwnd, buf, length + 1)
            if buf.value.strip() == "星黎音频":
                hwnds.append(hwnd)
    return True
EnumWindows(EnumWindowsProc(foreach), 0)
print(f"找到 {len(hwnds)} 个窗口")

if hwnds:
    hwnd = hwnds[0]
    SetWindowPos(hwnd, 0, 80, 30, 760, 980, 0x0040)
    time.sleep(2.5)

    from PIL import ImageGrab
    rect = ctypes.wintypes.RECT()
    GetWindowRect(hwnd, ctypes.byref(rect))
    bbox = (rect.left, rect.top, rect.right, rect.bottom)
    print(f"窗口 bbox: {bbox}, size = {rect.right-rect.left}x{rect.bottom-rect.top}")
    img = ImageGrab.grab(bbox=bbox)
    out_png = PROJECT / "scripts" / "_exe_v2_clean.png"
    img.save(out_png)
    print(f"已截图: {out_png}")

proc.terminate()
try: proc.wait(timeout=3)
except subprocess.TimeoutExpired: proc.kill()

if backup.exists():
    shutil.copy2(backup, target_config)
    backup.unlink()
