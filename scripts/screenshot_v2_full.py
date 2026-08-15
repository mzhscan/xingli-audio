"""完整截图: 整个主窗口, 包括底部按钮。"""
import os
import sys
import time
import subprocess
import shutil
import ctypes
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
    "auto_start": True,  # 这次开 auto_start 看看勾选状态
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
for i in range(20):
    time.sleep(0.5)
    if proc.poll() is not None:
        out, err = proc.communicate(timeout=2)
        print(f"!! exe 异常: {proc.returncode}")
        print("stderr:", err.decode("utf-8", errors="replace")[:1000])
        sys.exit(1)
print("exe 已运行 10 秒")

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
SetWindowPos = ctypes.windll.user32.SetWindowPos

hwnds = []
def foreach(hwnd, lParam):
    if IsWindowVisible(hwnd):
        length = GetWindowTextLength(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buf, length + 1)
            if buf.value.strip() == "星黎音频":
                hwnds.append((hwnd, buf.value))
    return True
EnumWindows(EnumWindowsProc(foreach), 0)
print(f"找到 {len(hwnds)} 个星黎音频窗口")

if hwnds:
    hwnd, title = hwnds[0]
    # 调整窗口大小让所有内容都显示
    SetWindowPos(hwnd, 0, 100, 40, 760, 900, 0x0040)
    time.sleep(3.0)
    # 强制窗口重绘
    ctypes.windll.user32.RedrawWindow(hwnd, None, None, 0x0001 | 0x0004)
    time.sleep(1.5)

    # 用 PrintWindow API 抓窗口内容 (即使被遮挡也能抓到)
    import ctypes.wintypes as wt
    hdc_window = ctypes.windll.user32.GetWindowDC(hwnd)
    hdc_mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc_window)
    rect = wt.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    print(f"客户端大小: {w}x{h}")
    hbm = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc_window, w, h)
    ctypes.windll.gdi32.SelectObject(hdc_mem, hbm)
    # PW_RENDERFULLCONTENT = 0x00000002
    ctypes.windll.user32.PrintWindow(hwnd, hdc_mem, 0x00000002)
    # 转成 PIL Image
    from PIL import Image
    img = Image.frombuffer('RGB', (w, h), ctypes.string_at(hbm, w*h*4), 'raw', 'BGRA', 0, 1)
    out_png = PROJECT / "scripts" / "_exe_v2_full.png"
    img.save(out_png)
    print(f"已截图: {out_png}, size = {w}x{h}")
    ctypes.windll.gdi32.DeleteObject(hbm)
    ctypes.windll.gdi32.DeleteDC(hdc_mem)
    ctypes.windll.user32.ReleaseDC(hwnd, hdc_window)

proc.terminate()
try: proc.wait(timeout=3)
except subprocess.TimeoutExpired: proc.kill()
time.sleep(0.5)

if backup.exists():
    shutil.copy2(backup, target_config)
    backup.unlink()
