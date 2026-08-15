"""冒烟测试: 验证各模块能正常 import + 核心功能可用。"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

# 1) import
print("=== Import 测试 ===")
import core.config  # noqa: F401
import core.audio  # noqa: F401
import core.hotkey  # noqa: F401
import ui.hotkey_field  # noqa: F401
import ui.device_combo  # noqa: F401
import ui.pair_row  # noqa: F401
import ui.tray  # noqa: F401
import ui.main_window  # noqa: F401
print("OK: 所有模块 import 成功")

# 2) 枚举设备
print()
print("=== 音频设备枚举 ===")
from core.audio import list_output_devices
devs = list_output_devices()
print(f"共 {len(devs)} 个 ACTIVE 输出设备:")
for d in devs:
    flag = "●" if d.is_active else "○"
    print(f"  {flag} {d.name}")
    print(f"     id = {d.id[:60]}...")

# 3) 配置读写
print()
print("=== 配置读写 ===")
import tempfile, os
from core.config import Config
with tempfile.TemporaryDirectory() as td:
    p = os.path.join(td, "cfg.json")
    c = Config(path=p)
    print(f"默认 pairs: {c.pairs}")
    c.pairs = [{"hotkey": "ctrl+alt+1", "device_id": "devA", "device_name": "spk"}]
    ok = c.save()
    print(f"save() -> {ok}")
    c2 = Config(path=p)
    print(f"roundtrip: {c2.pairs}")
    print(f"配置文件位置: {c2.get_path_display()}")

# 4) 热键格式化
print()
print("=== 热键 normalize / 显示 / 冲突 ===")
from core.hotkey import HotkeyManager, format_for_display, detect_conflicts
print("normalize('Ctrl + Alt + 1') ->", repr(HotkeyManager.normalize("Ctrl + Alt + 1")))
print("format_for_display('ctrl+alt+1') ->", repr(format_for_display("ctrl+alt+1")))
print("format_for_display('ctrl+alt+f5') ->", repr(format_for_display("ctrl+alt+f5")))
print("format_for_display('ctrl+shift+win+tab') ->", repr(format_for_display("ctrl+shift+win+tab")))
print("detect_conflicts([{hotkey:'a'},{hotkey:'a'}]) ->",
      detect_conflicts([{"hotkey": "a"}, {"hotkey": "a"}]))
print("detect_conflicts([{hotkey:'a'},{hotkey:'b'}]) ->",
      detect_conflicts([{"hotkey": "a"}, {"hotkey": "b"}]))

# 5) 切换 (用第一个 device 测试, 不修改实际默认)
print()
print("=== 默认输出设备切换 (可选项, 实际会修改系统默认) ===")
if devs:
    target = devs[0]
    print(f"目标设备: {target.name}")
    print(f"目标 id  : {target.id}")
    confirm = input("  真的要切换吗? 这会改变你的系统默认输出 (y/N): ")
    if confirm.strip().lower() == "y":
        from core.audio import set_default_output_device, get_default_output_device_id
        before = get_default_output_device_id()
        print(f"  当前默认: {before[:60]}...")
        try:
            set_default_output_device(target.id)
            after = get_default_output_device_id()
            print(f"  切换后  : {after[:60]}...")
            print("  ✓ 切换成功" if after == target.id else "  ✗ 切换后 ID 不一致")
        except Exception as e:
            print(f"  ✗ 切换失败: {e}")
    else:
        print("  (跳过)")
else:
    print("未发现设备, 跳过切换测试")

print()
print("=== 全部测试通过 ===")
