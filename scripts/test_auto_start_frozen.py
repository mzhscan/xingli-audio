"""模拟 frozen 模式, 验证 auto_start 真的能写/清注册表。

⚠ 这会真实修改注册表, 完成后会清理。
"""
import sys
from pathlib import Path
PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

# 模拟 frozen 模式: 用真实 exe 路径
real_exe = PROJECT / "dist" / "星黎音频.exe"
if not real_exe.exists():
    print(f"!! 找不到 {real_exe}, 请先 build")
    sys.exit(1)

import core.auto_start as A
# 把 sys.frozen 临时设成 True, 让 _exe_command() 返回真实 exe 路径
sys.frozen = True
A.sys.frozen = True
# 重新指向真实 exe
A.sys.executable = str(real_exe)

print(f"将写入: {A._exe_command()}")
print()

print("=== 写入注册表 ===")
ok, err = A.set_enabled(True)
print(f"  set_enabled(True) -> ok={ok}, err={err!r}")
print(f"  is_enabled() = {A.is_enabled()}")
print(f"  current_command() = {A.current_command()!r}")

print()
print("=== 清理注册表 ===")
ok, err = A.set_enabled(False)
print(f"  set_enabled(False) -> ok={ok}, err={err!r}")
print(f"  is_enabled() = {A.is_enabled()}")
print(f"  current_command() = {A.current_command()!r}")

print()
print("完成")
