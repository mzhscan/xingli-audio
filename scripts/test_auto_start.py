"""测试 auto_start 模块。"""
import sys
from pathlib import Path
PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from core import auto_start

print("=== 测试前状态 ===")
print(f"  is_enabled() = {auto_start.is_enabled()}")
print(f"  current_command() = {auto_start.current_command()!r}")

print()
print("=== 启用 auto_start ===")
ok, err = auto_start.set_enabled(True)
print(f"  set_enabled(True) -> ok={ok}, err={err!r}")
print(f"  is_enabled() = {auto_start.is_enabled()}")
print(f"  current_command() = {auto_start.current_command()!r}")

print()
print("=== 关闭 auto_start ===")
ok, err = auto_start.set_enabled(False)
print(f"  set_enabled(False) -> ok={ok}, err={err!r}")
print(f"  is_enabled() = {auto_start.is_enabled()}")
print(f"  current_command() = {auto_start.current_command()!r}")

print()
print("auto_start 测试完成")
