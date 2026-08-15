"""深入调试冲突检测。"""
import os, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
PROJECT = Path(__file__).resolve().parent.parent if False else None  # trick
from pathlib import Path
PROJECT = Path(r"C:\Users\mzh_m\Documents\minimax\星黎音频")
sys.path.insert(0, str(PROJECT))

import tempfile
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
app.setStyle("Fusion")

from core.config import Config
from core.hotkey import detect_conflicts
from ui.main_window import MainWindow

with tempfile.TemporaryDirectory() as td:
    cfg = Config(path=str(Path(td) / "cfg.json"))
    win = MainWindow(config=cfg, icon_path=PROJECT / "assets" / "icon.ico")

    # 创建两个 row
    btn_add = win._add_btn
    btn_add.click()
    print(f"rows: {len(win._pending_rows)}")
    row0 = win._pending_rows[0]
    row1 = win._pending_rows[1]

    # 设置相同 hotkey
    print("--- set row0 hotkey=ctrl+alt+1 ---")
    row0.set_data("ctrl+alt+1", "DEV-FAKE", "spk")
    print(f"  row0.hotkey() = {row0.hotkey()!r}")
    print(f"  row0.device_id() = {row0.device_id()!r}")

    print("--- set row1 hotkey=ctrl+alt+1 ---")
    row1.set_data("ctrl+alt+1", "DEV-FAKE", "spk")
    print(f"  row1.hotkey() = {row1.hotkey()!r}")

    # 检查冲突
    pairs = win._collect_pairs()
    print(f"pairs: {pairs}")
    conflicts = detect_conflicts(pairs)
    print(f"conflicts: {conflicts}")

    # 检查 label
    print(f"conflict label visible: {win._conflict_label.isVisible()}")
    print(f"conflict label text: {win._conflict_label.text()!r}")
