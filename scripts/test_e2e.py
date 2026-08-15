"""端到端测试: 启动 exe -> 等待注册 -> 模拟按键 -> 验证默认设备切换 -> 关闭。

需要: dist/星黎音频.exe 已经构建好。
"""
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

from core.audio import list_output_devices, get_default_output_device_id

# === 1. 准备配置 ===
real = list_output_devices()
if len(real) < 2:
    print(f"需要至少 2 个输出设备, 当前 {len(real)}")
    sys.exit(1)

target_dir = PROJECT / "dist"
target_config = target_dir / "config.json"
backup = target_dir / "config.json.bak"
if target_config.exists() and not backup.exists():
    shutil.copy2(target_config, backup)

# config: ctrl+alt+1 -> 设备0, ctrl+alt+2 -> 设备1
import json
config_data = {
    "close_behavior": "minimize",
    "notify_on_switch": False,  # 测试时关掉通知, 避免干扰
    "start_minimized": False,
    "hotkey_device_pairs": [
        {"hotkey": "ctrl+alt+1", "device_id": real[0].id, "device_name": real[0].name},
        {"hotkey": "ctrl+alt+2", "device_id": real[1].id, "device_name": real[1].name},
    ],
}
target_config.write_text(json.dumps(config_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"config 写入: {target_config}")
print(f"  目标 [0]: {real[0].name}")
print(f"  目标 [1]: {real[1].name}")

before_id = get_default_output_device_id()
before_name = next((d.name for d in real if d.id == before_id), "<unknown>")
print(f"当前默认: {before_name}")

# === 2. 启动 exe ===
EXE = PROJECT / "dist" / "星黎音频.exe"
env = os.environ.copy()
env.pop("QT_QPA_PLATFORM", None)
proc = subprocess.Popen([str(EXE)], cwd=str(PROJECT), env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"exe pid: {proc.pid}")

# 等它启动并注册热键
for i in range(20):
    time.sleep(0.5)
    if proc.poll() is not None:
        out, err = proc.communicate(timeout=2)
        print(f"!! exe 异常退出: {proc.returncode}")
        print("stderr:", err.decode("utf-8", errors="replace")[:1000])
        sys.exit(1)
print("exe 已运行 10 秒, 应该已经注册好热键了")

# === 3. 模拟按下 ctrl+alt+1 (切到设备0) ===
print()
print("--- 模拟按下 Ctrl+Alt+1 ---")
import keyboard  # type: ignore
# 模拟组合键: 按下 ctrl, alt, 1, 释放 1, alt, ctrl
try:
    # 切到目标 [0]
    target_id = real[0].id
    keyboard.press_and_release("ctrl+alt+1")
    time.sleep(1.5)  # 等切换生效
    after_id = get_default_output_device_id()
    after_name = next((d.name for d in real if d.id == after_id), "<unknown>")
    print(f"  切换后: {after_name}")
    if after_id == target_id:
        print("  [OK] ctrl+alt+1 切换到目标设备成功")
    else:
        print(f"  [!!] 切换失败: expected {target_id}, got {after_id}")

    # === 4. 模拟按下 ctrl+alt+2 (切到设备1) ===
    print()
    print("--- 模拟按下 Ctrl+Alt+2 ---")
    target_id = real[1].id
    keyboard.press_and_release("ctrl+alt+2")
    time.sleep(1.5)
    after_id = get_default_output_device_id()
    after_name = next((d.name for d in real if d.id == after_id), "<unknown>")
    print(f"  切换后: {after_name}")
    if after_id == target_id:
        print("  [OK] ctrl+alt+2 切换到目标设备成功")
    else:
        print(f"  [!!] 切换失败: expected {target_id}, got {after_id}")
except Exception as e:
    print(f"模拟按键失败: {e}")

# === 5. 关闭 ===
print()
print("关闭 exe...")
proc.terminate()
try:
    proc.wait(timeout=3)
except subprocess.TimeoutExpired:
    proc.kill()
time.sleep(0.5)

# === 6. 还原 ===
if backup.exists():
    shutil.copy2(backup, target_config)
    backup.unlink()
    print("config.json 已还原")
else:
    if target_config.exists():
        target_config.unlink()

print()
print("端到端测试完成")
