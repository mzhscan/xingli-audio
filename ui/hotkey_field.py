"""快捷键录制控件。

点击进入录制状态, 监听用户按下的下一个组合键, 结束后写回 _hotkey。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit

from core.hotkey import format_for_display


class HotkeyField(QLineEdit):
    """可录制的快捷键输入框 (外观类似只读 LineEdit)。"""

    # 当录制/清除完成时发射, 通知外部 (主窗口) 检查冲突
    hotkeyChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._recording = False
        self._hotkey: str = ""         # 内部小写格式: ctrl+alt+1
        self._placeholder_text = "点击此处, 然后按下快捷键…"
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setPlaceholderText(self._placeholder_text)
        self.setMinimumWidth(200)

    # ------------------------------------------------------------------ API
    def hotkey(self) -> str:
        return self._hotkey

    def set_hotkey(self, value: str) -> None:
        self._hotkey = (value or "").strip().lower()
        self._refresh_text()
        self.hotkeyChanged.emit()

    def clear_hotkey(self) -> None:
        self._hotkey = ""
        self._refresh_text()
        self.hotkeyChanged.emit()

    # ------------------------------------------------------------------ events
    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._begin_recording()
        super().mousePressEvent(event)

    def focusOutEvent(self, event) -> None:  # type: ignore[override]
        if self._recording:
            self._cancel_recording()
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if not self._recording:
            return super().keyPressEvent(event)

        key = event.key()
        if key in (Qt.Key_Escape,):
            self._cancel_recording()
            return

        # Backspace/Delete 清空
        if key in (Qt.Key_Backspace, Qt.Key_Delete):
            self._hotkey = ""
            self._refresh_text()
            self._end_recording()
            return

        # 必须至少有一个修饰键 + 一个普通键
        mods = event.modifiers()
        has_mod = bool(
            mods & (Qt.ControlModifier | Qt.AltModifier
                    | Qt.ShiftModifier | Qt.MetaModifier)
        )
        key_name = self._qt_key_to_name(key)
        if not key_name:
            return  # 忽略单独的修饰键 / 不可识别的键
        if not has_mod:
            # 允许单独功能键 (F1~F24) 不带修饰键
            if not key_name.lower().startswith("f") or not key_name[1:].isdigit():
                return

        mod_parts: list[str] = []
        if mods & Qt.ControlModifier:
            mod_parts.append("ctrl")
        if mods & Qt.AltModifier:
            mod_parts.append("alt")
        if mods & Qt.ShiftModifier:
            mod_parts.append("shift")
        if mods & Qt.MetaModifier:
            mod_parts.append("win")

        self._hotkey = "+".join(mod_parts + [key_name.lower()])
        self._refresh_text()
        self._end_recording()
        self.hotkeyChanged.emit()

    # ------------------------------------------------------------------ helpers
    def _begin_recording(self) -> None:
        self._recording = True
        self.setPlaceholderText("请按下快捷键 (Esc 取消, Delete 清空)…")
        self.setText("")
        self.setFocus(Qt.OtherFocusReason)
        # 视觉态在 QSS 中根据 _recording 调整 (通过 dynamic property)
        self.setProperty("recording", True)
        self.style().unpolish(self)
        self.style().polish(self)

    def _end_recording(self) -> None:
        self._recording = False
        self.setProperty("recording", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.clearFocus()
        self.setPlaceholderText(self._placeholder_text)
        self._refresh_text()

    def _cancel_recording(self) -> None:
        self._end_recording()
        self._refresh_text()

    def _refresh_text(self) -> None:
        self.setText(format_for_display(self._hotkey))

    @staticmethod
    def _qt_key_to_name(key: int) -> str | None:
        """Qt key -> keyboard 库能识别的名称。"""
        # 功能键 F1~F24
        if Qt.Key_F1 <= key <= Qt.Key_F24:
            return f"f{key - Qt.Key_F1 + 1}"
        # 字母
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key).lower()
        # 数字
        if Qt.Key_0 <= key <= Qt.Key_9:
            return str(key - Qt.Key_0)
        # 常用功能键
        table = {
            Qt.Key_Space: "space",
            Qt.Key_Tab: "tab",
            Qt.Key_Return: "enter",
            Qt.Key_Enter: "enter",
            Qt.Key_Backspace: "backspace",
            Qt.Key_Delete: "delete",
            Qt.Key_Insert: "insert",
            Qt.Key_Home: "home",
            Qt.Key_End: "end",
            Qt.Key_PageUp: "page up",
            Qt.Key_PageDown: "page down",
            Qt.Key_Up: "up",
            Qt.Key_Down: "down",
            Qt.Key_Left: "left",
            Qt.Key_Right: "right",
            Qt.Key_CapsLock: "caps lock",
            Qt.Key_NumLock: "num lock",
            Qt.Key_ScrollLock: "scroll lock",
            Qt.Key_Print: "print screen",
            Qt.Key_Pause: "pause",
            Qt.Key_Menu: "menu",
            Qt.Key_Minus: "-",
            Qt.Key_Equal: "=",
            Qt.Key_BracketLeft: "[",
            Qt.Key_BracketRight: "]",
            Qt.Key_Backslash: "\\",
            Qt.Key_Semicolon: ";",
            Qt.Key_Apostrophe: "'",
            Qt.Key_Comma: ",",
            Qt.Key_Period: ".",
            Qt.Key_Slash: "/",
            Qt.Key_QuoteLeft: "`",
        }
        return table.get(key)
