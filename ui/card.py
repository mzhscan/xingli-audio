"""Win11 风格的卡片容器。

替代 QGroupBox: QGroupBox 的 title 跟内容重叠是已知问题,
用 QFrame + 显式 QLabel 标题可以完全掌控间距。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class Card(QFrame):
    """一个圆角白底卡片, 顶部可选标题。"""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 14, 20, 14)
        self._layout.setSpacing(8)

        self._title: QLabel | None = None
        if title:
            self.setTitle(title)

    # ------------------------------------------------------------------ API
    def setTitle(self, text: str) -> None:
        if self._title is None:
            self._title = QLabel(text, self)
            self._title.setObjectName("cardTitle")
            self._layout.insertWidget(0, self._title)
        else:
            self._title.setText(text)

    def title(self) -> str:
        return self._title.text() if self._title else ""

    def contentLayout(self) -> QVBoxLayout:
        return self._layout
