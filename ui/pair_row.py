"""单行: 快捷键 + 设备下拉 + 删除按钮。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ui.device_combo import DeviceComboBox
from ui.hotkey_field import HotkeyField


class PairRow(QWidget):
    """一行: 快捷键输入 | 设备下拉 | 删除按钮。"""

    removeRequested = Signal(object)        # 发出自己
    dataChanged = Signal()                  # 任何字段变化

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # 第 1 列: 快捷键输入
        self.hotkey_field = HotkeyField(self)
        # 第 2 列: 设备下拉
        self.device_combo = DeviceComboBox(self)
        # 第 3 列: 删除
        self.remove_btn = QPushButton("✕", self)
        self.remove_btn.setFixedWidth(34)
        self.remove_btn.setToolTip("删除这一行")
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setObjectName("removeRowBtn")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.hotkey_field, 0)
        layout.addWidget(self.device_combo, 1)
        layout.addWidget(self.remove_btn, 0)

        # 内部信号转发
        self.hotkey_field.hotkeyChanged.connect(self.dataChanged)
        self.device_combo.deviceChanged.connect(self.dataChanged)
        self.remove_btn.clicked.connect(lambda: self.removeRequested.emit(self))

        # 默认焦点链
        self.setTabOrder(self.hotkey_field, self.device_combo._combo)
        self.setTabOrder(self.device_combo._combo, self.remove_btn)

    # ------------------------------------------------------------------ API
    def hotkey(self) -> str:
        return self.hotkey_field.hotkey()

    def device_id(self) -> str:
        return self.device_combo.device_id()

    def device_name(self) -> str:
        return self.device_combo.device_name()

    def set_data(self, hotkey: str, device_id: str, device_name: str) -> None:
        self.hotkey_field.blockSignals(True)
        self.device_combo.blockSignals(True)
        try:
            self.hotkey_field.set_hotkey(hotkey or "")
            self.device_combo.set_device(device_id or "")
        finally:
            self.hotkey_field.blockSignals(False)
            self.device_combo.blockSignals(False)
        # blockSignals 期间子控件的信号被吞了, 这里手动通知一次
        self.dataChanged.emit()

    def refresh_devices(self) -> None:
        self.device_combo.refresh()

    def set_remove_visible(self, visible: bool) -> None:
        self.remove_btn.setVisible(visible)

    def highlight_conflict(self, conflict: bool) -> None:
        self.hotkey_field.setProperty("conflict", conflict)
        self.hotkey_field.style().unpolish(self.hotkey_field)
        self.hotkey_field.style().polish(self.hotkey_field)
