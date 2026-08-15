"""系统托盘图标 + 菜单。

* 左键单击: 唤起/隐藏主窗口
* 右键菜单: 显示主窗口 / 退出
* 提供 showMessage() 用于切换设备时的系统通知
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class TrayController(QObject):
    showRequested = Signal()
    quitRequested = Signal()

    def __init__(self, icon_path: Path, app: QApplication, parent=None) -> None:
        super().__init__(parent)
        self._app = app

        icon = QIcon(str(icon_path)) if icon_path.exists() else app.windowIcon()
        self._tray = QSystemTrayIcon(icon, parent=parent)
        self._tray.setToolTip("星黎音频")

        menu = QMenu()
        self._act_show = QAction("显示主窗口", menu)
        self._act_show.triggered.connect(self.showRequested.emit)
        self._act_quit = QAction("退出", menu)
        self._act_quit.triggered.connect(self.quitRequested.emit)
        menu.addAction(self._act_show)
        menu.addSeparator()
        menu.addAction(self._act_quit)
        self._tray.setContextMenu(menu)

        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    # ------------------------------------------------------------------ API
    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def notify(self, title: str, message: str, msec: int = 2500) -> None:
        if not self._tray.supportsMessages():
            return
        self._tray.showMessage(title, message, QSystemTrayIcon.Information, msec)

    # ------------------------------------------------------------------ slot
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.showRequested.emit()
