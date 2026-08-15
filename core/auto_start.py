"""星黎音频 - 开机自启 (写 Windows 用户级 Run 键, 不需管理员权限)。

注册表路径: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
键名:       XingLiAudio
值:         "C:\\path\\to\\星黎音频.exe" --minimized
"""
from __future__ import annotations

import sys
from pathlib import Path

if sys.platform != "win32":
    raise RuntimeError("auto_start 仅支持 Windows。")

import winreg

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "XingLiAudio"
_MINIMIZED_FLAG = "--minimized"


def _exe_command() -> str:
    """返回注册表里要写入的命令字符串。"""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        # 路径加引号, 即使有空格也安全
        return f'"{exe}" {_MINIMIZED_FLAG}'
    # 源码运行时不写入 (避免开发时把 .py 设成自启)
    return ""


def is_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY)
        try:
            value, _ = winreg.QueryValueEx(key, _APP_NAME)
            return bool(value)
        finally:
            key.Close()
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_enabled(enabled: bool) -> tuple[bool, str]:
    """开启/关闭自启。返回 (成功, 错误信息)。"""
    if not getattr(sys, "frozen", False):
        return False, "请先用 build.bat 打包成 exe 后再设置开机自启。"
    try:
        key = winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        try:
            if enabled:
                winreg.SetValueEx(
                    key, _APP_NAME, 0, winreg.REG_SZ, _exe_command()
                )
            else:
                try:
                    winreg.DeleteValue(key, _APP_NAME)
                except FileNotFoundError:
                    pass
        finally:
            key.Close()
        return True, ""
    except OSError as e:
        return False, f"无法写入注册表: {e}"


def current_command() -> str:
    """返回当前已注册的命令 (调试用)。"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY)
        try:
            value, _ = winreg.QueryValueEx(key, _APP_NAME)
            return str(value)
        finally:
            key.Close()
    except OSError:
        return ""
