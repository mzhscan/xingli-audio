"""无头测试: 启动 QApplication + 主窗口, 模拟点击几个按钮, 然后退出。
   验证 UI 没有崩溃、关键路径都通。"""
import os
import sys
from pathlib import Path

# 强制使用 offscreen 平台 (无显示器也能跑)
os.environ["QT_QPA_PLATFORM"] = "offscreen"

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from core.config import Config
from core.hotkey import HotkeyManager
from ui.main_window import MainWindow
from ui.pair_row import PairRow

print("[1/5] 启动 QApplication ...")
app = QApplication(sys.argv)
app.setStyle("Fusion")

print("[2/5] 加载配置 (使用临时文件) ...")
import tempfile
with tempfile.TemporaryDirectory() as td:
    cfg = Config(path=str(Path(td) / "cfg.json"))
    print(f"  默认 pairs: {cfg.pairs}")

    print("[3/5] 创建主窗口 ...")
    icon = PROJECT / "assets" / "icon.ico"
    win = MainWindow(config=cfg, icon_path=icon)
    print(f"  标题: {win.windowTitle()}")
    print(f"  最小尺寸: {win.minimumSize().width()}x{win.minimumSize().height()}")
    print(f"  实际尺寸: {win.size().width()}x{win.size().height()}")
    print(f"  默认行数: {len(win._pending_rows)}")

    # 1) 添加一行
    print("[4/5] 模拟操作: 添加一行 / 设置快捷键 / 选择设备 ...")
    btn_add = win._add_btn
    btn_add.click()
    print(f"  添加后行数: {len(win._pending_rows)}")
    assert len(win._pending_rows) == 2

    # 在第一行设置快捷键
    row0 = win._pending_rows[0]
    row0.set_data("ctrl+alt+1", "DEV-FAKE-ID", "扬声器 (测试)")
    print(f"  row0 hotkey = {row0.hotkey()}, device = {row0.device_name()}")

    # 第二行也设置一个
    row1 = win._pending_rows[1]
    row1.set_data("ctrl+alt+2", "DEV-FAKE-ID-2", "耳机 (测试)")
    print(f"  row1 hotkey = {row1.hotkey()}, device = {row1.device_name()}")

    # 冲突检测: 把第一行也改成 ctrl+alt+2
    row0.set_data("ctrl+alt+2", "DEV-FAKE-ID", "扬声器 (测试)")
    print(f"  冲突提示文本: {win._conflict_label.text()!r}")
    assert "冲突" in win._conflict_label.text(), "应该出现冲突提示"
    assert not win._conflict_label.isHidden(), "冲突时 label 应该被设置可见"

    # 取消冲突
    row0.set_data("ctrl+alt+1", "DEV-FAKE-ID", "扬声器 (测试)")
    print(f"  冲突已解决, 提示文本: {win._conflict_label.text()!r}")
    assert win._conflict_label.isHidden(), "解决冲突后 label 应该被设置隐藏"

    # 模拟 4 个动作按钮
    print("[5/5] 模拟动作按钮 (只触发 closeEvent, 不真弹窗) ...")
    # 拦截 QMessageBox 以免阻塞
    from PySide6.QtWidgets import QMessageBox
    QMessageBox.information = staticmethod(lambda *a, **k: 0)
    QMessageBox.warning = staticmethod(lambda *a, **k: 0)
    QMessageBox.critical = staticmethod(lambda *a, **k: 0)

    # 收集 pairs
    pairs = win._collect_pairs()
    print(f"  收集到的 pairs: {pairs}")
    assert len(pairs) == 2

    # 触发保存
    win._btn_save.click()
    print("  save() 已触发 (被拦截, 不会真弹窗)")

    # 触发 _apply_hotkeys (不真的注册, 看代码路径)
    hkm = win.get_hotkey_manager()
    print(f"  HotkeyManager 准备就绪, 已注册: {hkm.registered()}")

    # 关闭窗口
    win.close()
    print("  close() 已调用")

    print()
    print("UI 启动测试通过")

print("Done.")
