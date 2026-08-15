"""星黎音频 - 全局快捷键管理。

基于 `keyboard` 库 (已在 requirements 中)。
注意:
  * 全局键盘钩子在某些机器上需要管理员权限;
  * 同名快捷键重复注册会被忽略, 不会抛错;
  * 回调应短小, 复杂工作放回主线程 (通过 Qt Signal/Slot 调度)。
"""
from __future__ import annotations

from typing import Callable, Iterable

import keyboard  # type: ignore[import-untyped]


class HotkeyManager:
    """注册/注销 全局快捷键。"""

    def __init__(self) -> None:
        self._registered: dict[str, Callable[[], None]] = {}

    # ------------------------------------------------------------------ public
    def register(self, hotkey: str, callback: Callable[[], None]) -> bool:
        """注册一个全局快捷键。重复同名会被覆盖。"""
        if not hotkey:
            return False
        norm = self._normalize(hotkey)
        self.unregister(norm)
        try:
            keyboard.add_hotkey(norm, callback, suppress=False)
            self._registered[norm] = callback
            return True
        except Exception as e:
            print(f"[Hotkey] 注册失败 {hotkey!r}: {e}")
            return False

    def unregister(self, hotkey: str) -> None:
        norm = self._normalize(hotkey)
        if not norm:
            return
        try:
            keyboard.remove_hotkey(norm)
        except (KeyError, ValueError):
            pass
        self._registered.pop(norm, None)

    def unregister_all(self) -> None:
        for hk in list(self._registered.keys()):
            self.unregister(hk)

    def is_registered(self, hotkey: str) -> bool:
        return self._normalize(hotkey) in self._registered

    def registered(self) -> list[str]:
        return list(self._registered.keys())

    @staticmethod
    def _normalize(hotkey: str) -> str:
        """把 'Ctrl + Alt + 1' / 'ctrl+alt+1' 统一为 'ctrl+alt+1'。

        keyboard 库用小写 + '+' 分隔, 顺序 ctrl/alt/shift/win 在前, key 在后。
        """
        if not hotkey:
            return ""
        parts = [p.strip().lower() for p in hotkey.replace(" ", "").split("+") if p.strip()]
        mod_order = ["ctrl", "alt", "shift", "windows", "win"]
        mods = [p for p in parts if p in mod_order]
        keys = [p for p in parts if p not in mod_order]
        return "+".join(mods + keys)

    @staticmethod
    def normalize(hotkey: str) -> str:
        return HotkeyManager._normalize(hotkey)


# ---------------------------------------------------------------------------
# 用于 UI 显示的格式化
# ---------------------------------------------------------------------------
def format_for_display(hotkey: str) -> str:
    """把 'ctrl+alt+1' 格式化为更友好的 'Ctrl + Alt + 1'。"""
    if not hotkey:
        return ""
    parts = [p.strip() for p in hotkey.split("+") if p.strip()]
    pretty = []
    for p in parts:
        pl = p.lower()
        if pl in ("ctrl", "control"):
            pretty.append("Ctrl")
        elif pl in ("alt",):
            pretty.append("Alt")
        elif pl in ("shift",):
            pretty.append("Shift")
        elif pl in ("win", "windows", "super"):
            pretty.append("Win")
        else:
            pretty.append(p.upper() if len(p) == 1 else p.capitalize())
    return " + ".join(pretty)


def detect_conflicts(pairs: Iterable[dict]) -> list[tuple[int, int, str]]:
    """检查 pairs 之间是否有相同快捷键。返回 (i, j, hotkey) 列表。"""
    seen: dict[str, int] = {}
    conflicts: list[tuple[int, int, str]] = []
    for idx, p in enumerate(pairs):
        hk = (p.get("hotkey") or "").strip()
        if not hk:
            continue
        if hk in seen:
            conflicts.append((seen[hk], idx, hk))
        else:
            seen[hk] = idx
    return conflicts
