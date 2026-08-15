"""启动打包好的 exe, 截图, 然后关闭。"""
import os
import sys
import time
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
EXE = PROJECT / "dist" / "星黎音频.exe"
LOG = PROJECT / "scripts" / "_exe_screenshot_log.txt"
SCREENSHOT = PROJECT / "scripts" / "_exe_running.png"

# 先把 PROJECT 加入 sys.path 以便 import core.* ui.*
sys.path.insert(0, str(PROJECT))

# 设置环境: 让它用真实 Windows 平台 (有中文渲染)
env = os.environ.copy()
env.pop("QT_QPA_PLATFORM", None)

# 先用真实设备写一个 config.json
import json
import shutil
from core.audio import list_output_devices
from core.config import Config

real = list_output_devices()
if len(real) < 2:
    print("需要至少 2 个输出设备, 当前:", len(real))
    sys.exit(1)

target_dir = PROJECT  # exe 启动时会从这个目录的 config.json 读
target_config = target_dir / "config.json"
backup = target_dir / "config.json.bak"
if target_config.exists():
    shutil.copy2(target_config, backup)

cfg = Config(path=target_config)
cfg.pairs = [
    {"hotkey": "ctrl+alt+1", "device_id": real[0].id, "device_name": real[0].name},
    {"hotkey": "ctrl+alt+2", "device_id": real[1].id, "device_name": real[1].name},
    {"hotkey": "ctrl+alt+f5", "device_id": "", "device_name": ""},
]
cfg.save()
print(f"已写入示例配置: {target_config}")

# 启动 exe
print(f"启动: {EXE}")
proc = subprocess.Popen(
    [str(EXE)],
    cwd=str(PROJECT),
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=0x00000008,  # DETACHED_PROCESS
)

# 等 5 秒让它启动
print("等待 exe 启动...")
for i in range(10):
    time.sleep(0.5)
    sys.stdout.write(".")
    sys.stdout.flush()
    if proc.poll() is not None:
        print(f"\nexe 已退出, code={proc.returncode}")
        out, err = proc.communicate(timeout=2)
        print("stdout:", out.decode("utf-8", errors="replace")[:500])
        print("stderr:", err.decode("utf-8", errors="replace")[:500])
        sys.exit(1)
print("\nexe 仍在运行")

# 找出窗口句柄
import ctypes
import ctypes.wintypes

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

hwnds = []

def foreach_window(hwnd, lParam):
    if IsWindowVisible(hwnd):
        length = GetWindowTextLength(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buf, length + 1)
            if "星黎" in buf.value:
                hwnds.append((hwnd, buf.value))
    return True

EnumWindows(EnumWindowsProc(foreach_window), 0)
print(f"找到 {len(hwnds)} 个 '星黎' 窗口:")
for hwnd, title in hwnds:
    print(f"  hwnd={hwnd}: {title!r}")

# 截图
if hwnds:
    hwnd, title = hwnds[0]
    from PIL import ImageGrab
    # Get window rect
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    bbox = (rect.left, rect.top, rect.right, rect.bottom)
    print(f"窗口位置: {bbox}")
    img = ImageGrab.grab(bbox=bbox)
    img.save(SCREENSHOT)
    print(f"已截图: {SCREENSHOT}")
else:
    print("未找到主窗口")

# 关闭
print("关闭 exe...")
proc.terminate()
try:
    proc.wait(timeout=3)
except subprocess.TimeoutExpired:
    proc.kill()

# 还原 config
if backup.exists():
    shutil.copy2(backup, target_config)
    backup.unlink()
    print(f"已还原 config.json")
else:
    if target_config.exists():
        target_config.unlink()

print("Done")
