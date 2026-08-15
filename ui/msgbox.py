"""自定义消息框: 中文不会截断, 圆角, 居中, 跟主窗口风格一致。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)


class _IconCircle(QWidget):
    """小圆图标: 不同级别显示不同颜色。"""

    COLORS = {
        "info": "#0078D4",
        "warn": "#D83B01",
        "error": "#C42B1C",
        "ok": "#107C10",
    }
    GLYPHS = {
        "info": "i",
        "warn": "!",
        "error": "✕",
        "ok": "✓",
    }

    def __init__(self, level: str, parent=None) -> None:
        super().__init__(parent)
        self._level = level if level in self.COLORS else "info"
        self.setFixedSize(28, 28)

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        color = QColor(self.COLORS[self._level])
        p.setBrush(color)
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 28, 28)
        p.setPen(QPen(QColor("#FFFFFF")))
        font = QFont()
        font.setBold(True)
        font.setPointSize(13)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter, self.GLYPHS[self._level])


class MsgBox(QDialog):
    """一个简洁的圆角消息框: 标题 + 正文 + 确定按钮。"""

    def __init__(self, parent, level: str, title: str, text: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self._build_ui(level, text)

    def _build_ui(self, level: str, text: str) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # 图标
        icon = _IconCircle(level, self)
        root.addWidget(icon, 0, Qt.AlignTop)

        # 文本
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(8)
        lbl_text = QLabel(text, self)
        lbl_text.setWordWrap(True)
        lbl_text.setMinimumWidth(280)
        # 允许自然换行
        font = lbl_text.font()
        font.setPointSize(10)
        lbl_text.setFont(font)
        text_col.addWidget(lbl_text)

        # 按钮行 (右对齐)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 4, 0, 0)
        btn_row.addStretch(1)
        btn_ok = QPushButton("确定", self)
        btn_ok.setObjectName("primaryBtn")
        btn_ok.setMinimumWidth(80)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        text_col.addLayout(btn_row)

        root.addLayout(text_col, 1)
        self.setMinimumWidth(360)
        self.adjustSize()


def show_info(parent, title: str, text: str) -> None:
    MsgBox(parent, "info", title, text).exec()


def show_warn(parent, title: str, text: str) -> None:
    MsgBox(parent, "warn", title, text).exec()


def show_error(parent, title: str, text: str) -> None:
    MsgBox(parent, "error", title, text).exec()
