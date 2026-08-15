"""截图: 把主窗口渲染成 PNG (offscreen), 用户可以预览 UI 效果。"""
import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from core.config import Config
from ui.main_window import MainWindow
from core.audio import list_output_devices

app = QApplication(sys.argv)
app.setStyle("Fusion")

# 用真实设备填充 (保证截图里有内容)
import tempfile
with tempfile.TemporaryDirectory() as td:
    cfg = Config(path=str(Path(td) / "cfg.json"))

    # 写入一些示例配置
    real_devs = list_output_devices()
    real_id_0 = real_devs[0].id if len(real_devs) > 0 else ""
    real_id_1 = real_devs[1].id if len(real_devs) > 1 else ""
    real_name_0 = real_devs[0].name if len(real_devs) > 0 else "扬声器"
    real_name_1 = real_devs[1].name if len(real_devs) > 1 else "耳机"

    cfg.pairs = [
        {"hotkey": "ctrl+alt+1", "device_id": real_id_0, "device_name": real_name_0},
        {"hotkey": "ctrl+alt+2", "device_id": real_id_1, "device_name": real_name_1},
        {"hotkey": "ctrl+alt+3", "device_id": "", "device_name": ""},
    ]
    cfg.save()

    cfg2 = Config(path=str(Path(td) / "cfg.json"))
    win = MainWindow(config=cfg2, icon_path=PROJECT / "assets" / "icon.ico")
    win.show()

    # 强制一次 layout
    QTimer.singleShot(50, lambda: None)
    app.processEvents()
    app.processEvents()
    app.processEvents()

    out = PROJECT / "scripts" / "_ui_screenshot.png"
    pix = win.grab()
    pix.save(str(out), "PNG")
    print(f"已保存: {out} ({pix.width()}x{pix.height()})")

    # 同时也保存一份深色模式截图
    win._dark = True
    from ui.main_window import build_stylesheet
    win.setStyleSheet(build_stylesheet(True, win._accent))
    app.processEvents()
    app.processEvents()
    out2 = PROJECT / "scripts" / "_ui_screenshot_dark.png"
    pix2 = win.grab()
    pix2.save(str(out2), "PNG")
    print(f"已保存: {out2} ({pix2.width()}x{pix2.height()})")
