"""完整截图: 让窗口稍大, 把 3 行配置都显示出来。"""
import os
import sys
import time
import subprocess
import ctypes
import ctypes.wintypes
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from core.audio import list_output_devices
from core.config import Config

real = list_output_devices()
# exe 在 dist/ 下, config.json 也在 dist/ 下
target_dir = PROJECT / "dist"
target_config = target_dir / "config.json"
backup = target_dir / "config.json.bak"
if target_config.exists() and not backup.exists():
    import shutil
    shutil.copy2(target_config, backup)

cfg = Config(path=target_config)
cfg.close_behavior = "minimize"
cfg.notify_on_switch = True
cfg.pairs = [
    {"hotkey": "ctrl+alt+1", "device_id": real[0].id, "device_name": real[0].name},
    {"hotkey": "ctrl+alt+2", "device_id": real[1].id, "device_name": real[1].name},
    {"hotkey": "ctrl+alt+f5", "device_id": "", "device_name": ""},
]
cfg.save()
print(f"config 写入: {len(cfg.pairs)} 对")

# 启动 exe
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
        print(f"!! exe 异常退出 code={proc.returncode}")
        print("stderr:", err.decode("utf-8", errors="replace")[:1000])
        sys.exit(1)
print("exe 已运行 7.5 秒")

# 找窗口
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
            if "星黎" in buf.value:
                hwnds.append((hwnd, buf.value))
    return True
EnumWindows(EnumWindowsProc(foreach), 0)
print(f"窗口数: {len(hwnds)}")

if hwnds:
    hwnd, title = hwnds[0]
    # 调整窗口位置和大小, 让所有内容都显示
    SetWindowPos(hwnd, 0, 100, 100, 720, 600, 0x0040)  # SWP_SHOWWINDOW
    time.sleep(1.0)  # 等布局完成

    from PIL import ImageGrab
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    bbox = (rect.left, rect.top, rect.right, rect.bottom)
    print(f"窗口位置: {bbox}, size = {rect.right-rect.left}x{rect.bottom-rect.top}")
    img = ImageGrab.grab(bbox=bbox)
    out_png = PROJECT / "scripts" / "_exe_full.png"
    img.save(out_png)
    print(f"已截图: {out_png}")

# 关闭
proc.terminate()
try:
    proc.wait(timeout=3)
except subprocess.TimeoutExpired:
    proc.kill()

# 还原 config
import shutil
if backup.exists():
    shutil.copy2(backup, target_config)
    backup.unlink()
    print("config.json 已还原")
