"""星黎音频 - 程序入口。

* 便携运行: 不写注册表, 配置保存在 exe 同目录 config.json
* 单实例: 通过文件锁防止重复启动 (Windows msvcrt 锁文件)
* 系统托盘: 启动即创建, 关闭按钮行为由用户在 UI 中配置
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QLockFile, QStandardPaths, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from core.config import Config
from ui.main_window import MainWindow
from ui.tray import TrayController


APP_NAME = "星黎音频"
APP_ORG = "MiniMax"
APP_VERSION = "1.0.0"


def _icon_path() -> Path:
    """定位图标路径。PyInstaller --onefile 解包到 sys._MEIPASS。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = Path(base) / "assets" / "icon.ico"
        if p.exists():
            return p
    # 源码运行
    return Path(__file__).resolve().parent / "assets" / "icon.ico"


def _tray_png_path() -> Path:
    """托盘图标使用较小的 PNG, 32x32, 视觉更干净。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = Path(base) / "assets" / "icon_32.png"
        if p.exists():
            return p
    return Path(__file__).resolve().parent / "assets" / "icon_32.png"


def _acquire_single_instance(app: QApplication) -> bool:
    """基于 QLockFile 的轻量单实例锁。"""
    lock_dir = Path(QStandardPaths.writableLocation(QStandardPaths.TempLocation))
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "xingli_audio.lock"
    lock = QLockFile(str(lock_path))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(
            None, APP_NAME, "星黎音频 已在运行, 请查看任务栏托盘。"
        )
        return False
    return True


def main() -> int:
    # DPI 缩放: Windows 11 默认开启 PerMonitorV2
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setApplicationName(APP_NAME)
    QApplication.setApplicationDisplayName(APP_NAME)
    QApplication.setApplicationVersion(APP_VERSION)
    QApplication.setOrganizationName(APP_ORG)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 全局默认字体: 微软雅黑优先 (你机器有 msyh.ttc), 再回退
    f = QFont("Microsoft YaHei", 9)
    f.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(f)

    # 单实例
    if not _acquire_single_instance(app):
        return 1

    # 必须有系统托盘
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None, APP_NAME, "未检测到系统托盘, 程序无法在后台运行, 将直接退出。"
        )
        return 2

    # 全局异常钩子: 弹窗而不是直接闪退
    def excepthook(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(text, file=sys.stderr)
        try:
            QMessageBox.critical(None, f"{APP_NAME} - 出现未处理异常", text)
        except Exception:
            pass
    sys.excepthook = excepthook

    # 配置
    config = Config()
    # 开机自启场景: 通过 --minimized 参数进入时不显示主窗口
    if "--minimized" in sys.argv:
        config.start_minimized = True

    # 主窗口
    icon = _icon_path()
    win = MainWindow(config=config, icon_path=icon)

    # 是否启动时最小化
    if not config.start_minimized:
        win.show()
    else:
        # 仅托盘
        win.hide()
        win._tray.notify(APP_NAME, "已启动, 右键托盘图标可打开主窗口。", 2000)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
