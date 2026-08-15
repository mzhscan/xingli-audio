"""测试切换默认设备: 切到 device[1] 再切回 device[0]。"""
import sys
from pathlib import Path
PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from core.audio import (
    list_output_devices, set_default_output_device,
    get_default_output_device_id, AudioSwitchError,
)

devs = list_output_devices()
if len(devs) < 2:
    print("需要至少 2 个输出设备才能测试, 当前:", len(devs))
    sys.exit(0)

print(f"找到 {len(devs)} 个输出设备, 准备在 [0] 和 [1] 之间切换测试。")
print()

original_id = get_default_output_device_id()
print(f"当前默认: {[d for d in devs if d.id == original_id][0].name}")

# 切到 [1]
target = devs[1]
print(f"切换 -> [{target.name}]")
set_default_output_device(target.id)
new_id = get_default_output_device_id()
print(f"  新默认: {[d for d in devs if d.id == new_id][0].name if new_id else '<None>'}")
assert new_id == target.id, f"切换失败: expected {target.id}, got {new_id}"
print("  [OK] 切换到目标设备成功")

# 切回 [0]
back = devs[0]
print(f"切回 -> [{back.name}]")
set_default_output_device(back.id)
restored_id = get_default_output_device_id()
print(f"  新默认: {[d for d in devs if d.id == restored_id][0].name if restored_id else '<None>'}")
assert restored_id == back.id, f"切回失败: expected {back.id}, got {restored_id}"
print("  [OK] 切回原设备成功")

print()
print("切换功能正常")
