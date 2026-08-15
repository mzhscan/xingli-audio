"""把所有输出设备写到 utf-8 文件, 验证名字。"""
import sys
from pathlib import Path
PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from core.audio import list_output_devices, set_default_output_device, get_default_output_device_id

devs = list_output_devices()
out_lines = [f"共 {len(devs)} 个 ACTIVE 输出设备:", ""]
for i, d in enumerate(devs):
    out_lines.append(f"  [{i}] {d.name}")
    out_lines.append(f"      id = {d.id}")

target = PROJECT / "scripts" / "_devices_dump.txt"
target.write_text("\n".join(out_lines), encoding="utf-8")
print(f"已写入: {target}")
print("--- 内容 ---")
print(target.read_text(encoding="utf-8"))
