"""输出设备下拉框。

* 启动时从 pycaw 拉取一次设备列表
* 提供 refresh() 方法重新拉取 (新插入的耳机/拔掉的设备)
* 设备用 device_id 标识, 显示 name
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from core.audio import list_output_devices


class DeviceComboBox(QWidget):
    """带刷新按钮的设备下拉框。"""

    deviceChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._combo = QComboBox(self)
        self._combo.setMinimumWidth(240)
        self._refresh_btn = QPushButton("⟳", self)
        self._refresh_btn.setFixedWidth(34)
        self._refresh_btn.setToolTip("刷新设备列表")
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self.refresh)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._combo, 1)
        layout.addWidget(self._refresh_btn, 0)

        self._combo.currentIndexChanged.connect(self._on_change)
        self._placeholder_text = "— 请选择输出设备 —"

    # ------------------------------------------------------------------ API
    def device_id(self) -> str:
        return self._combo.currentData() or ""

    def device_name(self) -> str:
        return self._combo.currentText()

    def set_device(self, device_id: str) -> None:
        idx = self._combo.findData(device_id)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)
        else:
            self._combo.setCurrentIndex(0)

    def refresh(self) -> None:
        previous = self.device_id()
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem(self._placeholder_text, "")
        try:
            devices = list_output_devices()
        except Exception as e:  # pragma: no cover
            print(f"[DeviceCombo] 枚举失败: {e}")
            devices = []
        for d in devices:
            label = d.name
            if not d.is_active:
                label = f"{d.name}  (未激活)"
            self._combo.addItem(label, d.id)
        self._combo.blockSignals(False)
        if previous:
            self.set_device(previous)

    def _on_change(self, _idx: int) -> None:
        self.deviceChanged.emit()
