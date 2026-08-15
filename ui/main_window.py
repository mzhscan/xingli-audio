"""星黎音频 - 主窗口。

设计目标: Win11 美学 (圆角 / 浅色背景 / Segoe UI 字体 / 强调色按钮)。
"""
from __future__ import annotations

import sys
import winreg
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QLabel,
    QLayout, QMainWindow, QPushButton, QRadioButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from core.audio import (
    AudioDevice, AudioSwitchError, get_default_output_device_id,
    list_output_devices, set_default_output_device,
)
from core.auto_start import set_enabled as set_auto_start
from core.config import Config
from core.hotkey import detect_conflicts, format_for_display, HotkeyManager
from ui.card import Card
from ui.msgbox import show_info, show_warn, show_error
from ui.pair_row import PairRow
from ui.tray import TrayController


# ---------------------------------------------------------------------------
# 主题探测
# ---------------------------------------------------------------------------
def _is_windows_dark_mode() -> bool:
    if sys.platform != "win32":
        return False
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return int(value) == 0
    except OSError:
        return False


def _windows_accent_color() -> QColor:
    if sys.platform != "win32":
        return QColor("#0078D4")
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM"
        )
        value, _ = winreg.QueryValueEx(key, "AccentColor")
        bgr = int(value) & 0xFFFFFF
        return QColor((bgr >> 16) & 0xFF, (bgr >> 8) & 0xFF, bgr & 0xFF)
    except OSError:
        return QColor("#0078D4")


# ---------------------------------------------------------------------------
# QSS
# ---------------------------------------------------------------------------
def _font_stack() -> str:
    """字体优先级: 微软雅黑 (中文 + 英文) 优先, 再回退。"""
    return ('"Microsoft YaHei", "Microsoft YaHei UI", "Segoe UI", '
            '"PingFang SC", "Hiragino Sans GB", sans-serif')


def build_stylesheet(dark: bool, accent: QColor) -> str:
    accent_hex = accent.name().upper()
    accent_hover = accent.lighter(110).name().upper()
    accent_pressed = accent.darker(115).name().upper()
    accent_soft = accent.lighter(190).name().upper()
    accent_border = accent.lighter(140).name().upper()

    if dark:
        bg = "#202020"
        card_bg = "#2B2B2B"
        card_border = "#383838"
        text = "#F1F1F1"
        text_secondary = "#B5B5B5"
        subtle = "#9A9A9A"
        divider = "#3A3A3A"
        input_bg = "#323232"
        input_border = "#4A4A4A"
        btn_bg = "#383838"
        btn_hover = "#444444"
        btn_pressed = "#2E2E2E"
        danger = "#FF6B6B"
        conflict = "#FF6B6B"
        toggle_off = "#5A5A5A"
    else:
        bg = "#F3F3F3"
        card_bg = "#FFFFFF"
        card_border = "#E8E8E8"
        text = "#1C1C1C"
        text_secondary = "#3F3F3F"
        subtle = "#707070"
        divider = "#EDEDED"
        input_bg = "#FFFFFF"
        input_border = "#D5D5D5"
        btn_bg = "#FFFFFF"
        btn_hover = "#F5F5F5"
        btn_pressed = "#E8E8E8"
        danger = "#C42B1C"
        conflict = "#C42B1C"
        toggle_off = "#999999"

    family = _font_stack()

    return f"""
    /* === 全局 === */
    QMainWindow, QWidget#central {{
        background-color: {bg};
        color: {text};
        font-family: {family};
        font-size: 13px;
        font-weight: 400;
    }}
    QWidget#appHeader {{
        background-color: {bg};
    }}
    QWidget#actionBar {{
        background-color: {card_bg};
        border-top: 1px solid {card_border};
        border-bottom: 1px solid {card_border};
    }}
    QLabel {{
        color: {text};
        background: transparent;
    }}
    QLabel#appTitle {{
        font-size: 22px;
        font-weight: 600;
        letter-spacing: 0.2px;
        color: {text};
        padding: 0 0 2px 0;
    }}
    QLabel#appSubtitle {{
        font-size: 12px;
        font-weight: 400;
        color: {subtle};
        padding: 0;
    }}
    QLabel#cardTitle {{
        font-size: 14px;
        font-weight: 600;
        color: {text};
        padding: 0 0 2px 0;
    }}
    QLabel#sectionLabel {{
        font-size: 12px;
        font-weight: 600;
        color: {subtle};
        letter-spacing: 0.3px;
        padding: 6px 0 2px 0;
    }}
    QLabel#conflictLabel {{
        color: {conflict};
        font-size: 12px;
        padding: 4px 0 0 0;
    }}
    QLabel#footerHint {{
        color: {subtle};
        font-size: 11px;
    }}

    /* === 卡片 === */
    QFrame#card {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 10px;
    }}
    QFrame#cardSeparator {{
        background: {divider};
        max-height: 1px;
        min-height: 1px;
        border: none;
        margin: 4px 0;
    }}

    /* === 单选 / 多选 === */
    QRadioButton, QCheckBox {{
        color: {text};
        spacing: 12px;          /* 拉大 indicator 和文字的距离 */
        padding: 2px 0;
        min-height: 22px;       /* 整个控件高度, 防止被压缩 */
    }}
    QRadioButton::indicator, QCheckBox::indicator {{
        width: 18px;
        height: 18px;
    }}
    QRadioButton::indicator {{
        border-radius: 9px;
        border: 2px solid {toggle_off};
        background: {input_bg};
    }}
    QRadioButton::indicator:hover {{
        border-color: {accent_hex};
    }}
    /* 选中: 2px 细边 + 径向渐变做内点 (Win11 风格) */
    QRadioButton::indicator:checked {{
        border: 2px solid {accent_hex};
        background: qradialgradient(
            cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
            stop:0.0 {accent_hex},
            stop:0.35 {accent_hex},
            stop:0.4 {input_bg},
            stop:1.0 {input_bg}
        );
    }}
    QCheckBox::indicator {{
        border-radius: 4px;
        border: 1.5px solid {toggle_off};
        background: {input_bg};
    }}
    QCheckBox::indicator:hover {{
        border-color: {accent_hex};
    }}
    QCheckBox::indicator:checked {{
        background: {accent_hex};
        border-color: {accent_hex};
        image: none;
    }}

    /* === 输入框 === */
    QLineEdit, QComboBox {{
        background-color: {input_bg};
        color: {text};
        border: 1px solid {input_border};
        border-radius: 6px;
        padding: 6px 10px;
        selection-background-color: {accent_hex};
        selection-color: #FFFFFF;
        min-height: 18px;
    }}
    QLineEdit:hover, QComboBox:hover {{
        border-color: {accent_border};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 2px solid {accent_hex};
        padding: 5px 9px;
    }}
    QLineEdit[recording="true"] {{
        border: 2px solid {accent_hex};
        background-color: {accent_soft};
        padding: 5px 9px;
    }}
    QLineEdit[conflict="true"] {{
        border: 2px solid {conflict};
        padding: 5px 9px;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {card_bg};
        color: {text};
        border: 1px solid {card_border};
        border-radius: 6px;
        padding: 4px;
        selection-background-color: {accent_hex};
        selection-color: #FFFFFF;
        outline: 0;
    }}

    /* === 按钮 === */
    QPushButton {{
        background-color: {btn_bg};
        color: {text};
        border: 1px solid {card_border};
        border-radius: 6px;
        padding: 7px 18px;
        min-width: 76px;
        min-height: 22px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {btn_hover};
        border-color: {accent_border};
    }}
    QPushButton:pressed {{
        background-color: {btn_pressed};
    }}
    QPushButton:disabled {{
        color: {subtle};
        background-color: {card_bg};
    }}
    QPushButton#primaryBtn {{
        background-color: {accent_hex};
        color: #FFFFFF;
        border: 1px solid {accent_hex};
        font-weight: 600;
    }}
    QPushButton#primaryBtn:hover {{
        background-color: {accent_hover};
        border-color: {accent_hover};
    }}
    QPushButton#primaryBtn:pressed {{
        background-color: {accent_pressed};
        border-color: {accent_pressed};
    }}
    QPushButton#removeRowBtn {{
        background-color: transparent;
        color: {subtle};
        border: 1px solid transparent;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        min-width: 0;
        padding: 4px 0;
    }}
    QPushButton#removeRowBtn:hover {{
        background-color: {danger};
        color: #FFFFFF;
        border-color: {danger};
    }}
    QPushButton#addRowBtn {{
        background-color: {accent_hex};
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-weight: 600;
    }}
    QPushButton#addRowBtn:hover {{
        background-color: {accent_hover};
    }}
    QPushButton#addRowBtn:pressed {{
        background-color: {accent_pressed};
    }}
    QPushButton#refreshBtn {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 6px;
        font-size: 16px;
    }}
    QPushButton#refreshBtn:hover {{
        background-color: {btn_hover};
    }}

    /* === 滚动区 === */
    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {subtle};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {accent_hex};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* === Tooltip === */
    QToolTip {{
        background-color: {card_bg};
        color: {text};
        border: 1px solid {card_border};
        border-radius: 4px;
        padding: 4px 6px;
    }}
    """


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    exitRequested = Signal()
    minimizedToTray = Signal()

    def __init__(self, config: Config, icon_path: Path, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._icon_path = icon_path
        self._hotkey_manager = HotkeyManager()

        self._pending_rows: list[PairRow] = []
        self._closing = False

        self._dark = _is_windows_dark_mode()
        self._accent = _windows_accent_color()
        self.setStyleSheet(build_stylesheet(self._dark, self._accent))

        self.setWindowTitle("星黎音频")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(QSize(640, 560))
        self.resize(QSize(760, 620))
        # 关键: QMainWindow 默认 SetDefaultConstraint 会把 sizeHint 锁成 minimum,
        # 导致加行后窗口无法扩大。关掉。
        self.layout().setSizeConstraint(QLayout.SetNoConstraint)

        # 全局字体: 微软雅黑优先 (主窗口上 QSS 已设, 这里只设一个保险默认)
        base_font = QFont()
        for fam in ("Microsoft YaHei", "Microsoft YaHei UI", "Segoe UI"):
            base_font.setFamily(fam)
            break
        base_font.setPointSize(9)
        base_font.setWeight(QFont.Normal)
        base_font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(base_font)

        self._setup_ui()
        self._load_into_ui()

        # 托盘
        self._tray = TrayController(self._icon_path, QApplication.instance(), self)
        self._tray.showRequested.connect(self._show_from_tray)
        self._tray.quitRequested.connect(self._real_exit)

        QTimer.singleShot(300, self._apply_hotkeys)

    # ------------------------------------------------------------------ UI
    def _setup_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # === 标题区 (固定, 不滚动) ===
        header = QWidget()
        header.setObjectName("appHeader")
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(28, 20, 28, 12)
        header_lay.setSpacing(2)
        title = QLabel("星黎音频")
        title.setObjectName("appTitle")
        subtitle = QLabel("用快捷键在多个输出设备之间一键切换。")
        subtitle.setObjectName("appSubtitle")
        header_lay.addWidget(title)
        header_lay.addWidget(subtitle)
        root.addWidget(header)

        # === 中间可滚动区域 (现在不用 ScrollArea, 让窗口跟着行数扩展) ===
        scroll_body = QWidget()
        scroll_lay = QVBoxLayout(scroll_body)
        scroll_lay.setContentsMargins(28, 4, 28, 8)
        scroll_lay.setSpacing(10)
        # scroll_body 不设 stretch, 让它按内容高度走
        root.addWidget(scroll_body)

        # === 启动与关闭 ===
        card_start = Card("启动与关闭")
        self._cb_auto_start = QCheckBox("开机自动启动 (登录 Windows 时自动启动, 默认最小化到任务栏)")
        self._cb_auto_start.setChecked(self._config.auto_start)
        self._cb_auto_start.toggled.connect(self._on_auto_start_toggled)
        card_start.contentLayout().addWidget(self._cb_auto_start)

        sep = QFrame()
        sep.setObjectName("cardSeparator")
        sep.setFrameShape(QFrame.HLine)
        card_start.contentLayout().addWidget(sep)

        lbl_close = QLabel("关闭按钮")
        lbl_close.setObjectName("sectionLabel")
        card_start.contentLayout().addWidget(lbl_close)
        self._rb_minimize = QRadioButton("最小化到任务栏运行")
        self._rb_exit = QRadioButton("退出程序")
        self._rb_minimize.setChecked(self._config.close_behavior == "minimize")
        self._rb_exit.setChecked(self._config.close_behavior == "exit")
        # 显式分组: 保证同组内互斥 (避免父 widget 自动分组失效)
        self._close_group = QButtonGroup(self)
        self._close_group.setExclusive(True)
        self._close_group.addButton(self._rb_minimize)
        self._close_group.addButton(self._rb_exit)
        close_row = QHBoxLayout()
        close_row.setSpacing(16)
        close_row.addWidget(self._rb_minimize)
        close_row.addWidget(self._rb_exit)
        close_row.addStretch(1)
        card_start.contentLayout().addLayout(close_row)
        scroll_lay.addWidget(card_start)

        # === 快捷键 + 设备 ===
        card_pairs = Card("快捷键 + 输出设备")
        header2 = QHBoxLayout()
        header2.setSpacing(8)
        h1 = QLabel("快捷键")
        h1.setObjectName("sectionLabel")
        h1.setMinimumWidth(200)
        h2 = QLabel("输出设备")
        h2.setObjectName("sectionLabel")
        h3 = QLabel("")
        h3.setMinimumWidth(34)
        header2.addWidget(h1, 0)
        header2.addWidget(h2, 1)
        header2.addWidget(h3, 0)
        card_pairs.contentLayout().addLayout(header2)

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(8)
        card_pairs.contentLayout().addWidget(self._rows_container)

        add_row = QHBoxLayout()
        add_row.setContentsMargins(0, 4, 0, 0)
        self._add_btn = QPushButton("+  添加新的快捷键")
        self._add_btn.setObjectName("addRowBtn")
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.clicked.connect(lambda: self._add_row())
        add_row.addStretch(1)
        add_row.addWidget(self._add_btn)
        card_pairs.contentLayout().addLayout(add_row)

        self._conflict_label = QLabel("")
        self._conflict_label.setObjectName("conflictLabel")
        self._conflict_label.setVisible(False)
        card_pairs.contentLayout().addWidget(self._conflict_label)

        scroll_lay.addWidget(card_pairs)

        # === 切换时 (紧凑横向行, 不用完整 Card) ===
        notify_row_outer = QHBoxLayout()
        notify_row_outer.setContentsMargins(0, 0, 0, 0)
        notify_row_outer.setSpacing(0)
        lbl_notify = QLabel("切换时")
        lbl_notify.setObjectName("sectionLabel")
        lbl_notify.setMinimumWidth(60)
        notify_row_outer.addWidget(lbl_notify)
        self._rb_notify = QRadioButton("弹出系统通知")
        self._rb_silent = QRadioButton("静默切换")
        self._rb_notify.setChecked(self._config.notify_on_switch)
        self._rb_silent.setChecked(not self._config.notify_on_switch)
        # 显式分组: 保证同组内互斥
        self._notify_group = QButtonGroup(self)
        self._notify_group.setExclusive(True)
        self._notify_group.addButton(self._rb_notify)
        self._notify_group.addButton(self._rb_silent)
        notify_row_outer.addSpacing(8)
        notify_row_outer.addWidget(self._rb_notify)
        notify_row_outer.addSpacing(16)
        notify_row_outer.addWidget(self._rb_silent)
        notify_row_outer.addStretch(1)
        scroll_lay.addLayout(notify_row_outer)

        # === 动作按钮 (固定, 不滚动) ===
        action_bar = QWidget()
        action_bar.setObjectName("actionBar")
        action_lay = QHBoxLayout(action_bar)
        action_lay.setContentsMargins(28, 12, 28, 4)
        action_lay.setSpacing(8)

        self._btn_save = QPushButton("保  存")
        self._btn_save.setCursor(Qt.PointingHandCursor)
        self._btn_save.clicked.connect(self._on_save)

        # 默认主按钮: 保存并最小化
        self._btn_save_min = QPushButton("保存并最小化")
        self._btn_save_min.setObjectName("primaryBtn")
        self._btn_save_min.setCursor(Qt.PointingHandCursor)
        self._btn_save_min.setDefault(True)
        self._btn_save_min.setAutoDefault(True)
        self._btn_save_min.clicked.connect(self._on_save_min)

        action_lay.addWidget(self._btn_save)
        action_lay.addWidget(self._btn_save_min)
        action_lay.addStretch(1)
        root.addWidget(action_bar)

        # === 底部: 配置文件路径 (固定) ===
        footer = QLabel(f"配置文件: {self._config.get_path_display()}")
        footer.setObjectName("footerHint")
        footer.setWordWrap(True)
        footer_wrap = QWidget()
        footer_lay = QVBoxLayout(footer_wrap)
        footer_lay.setContentsMargins(28, 0, 28, 10)
        footer_lay.setSpacing(0)
        footer_lay.addWidget(footer)
        root.addWidget(footer_wrap)

    # ------------------------------------------------------------------ 数据
    def _load_into_ui(self) -> None:
        self._clear_rows()
        pairs = self._config.pairs
        if not pairs:
            pairs = [{"hotkey": "", "device_id": "", "device_name": ""}]

        for _ in pairs:
            self._add_row()
        self._update_remove_btn_visibility()

        for r in self._pending_rows:
            r.refresh_devices()

        for r, p in zip(self._pending_rows, pairs):
            r.set_data(
                p.get("hotkey", "") or "",
                p.get("device_id", "") or "",
                p.get("device_name", "") or "",
            )

        self._update_conflict_label()

    def _clear_rows(self) -> None:
        for row in self._pending_rows:
            self._rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._pending_rows.clear()

    def _add_row(self, hotkey: str = "", device_id: str = "",
                 device_name: str = "") -> PairRow:
        row = PairRow(self._rows_container)
        row.removeRequested.connect(self._on_remove_row)
        row.dataChanged.connect(self._on_row_data_changed)
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)
        self._pending_rows.append(row)
        self._update_remove_btn_visibility()
        if hotkey or device_id or device_name:
            row.set_data(hotkey, device_id, device_name)
        # 加一行后, 让窗口跟着内容自然扩大 (向下扩展)
        self._adjust_window_height()
        return row

    def _on_remove_row(self, row: PairRow) -> None:
        if len(self._pending_rows) <= 1:
            show_info(
                self, "提示",
                "至少需要保留一行。如需清空, 请直接清空该行的快捷键与设备。"
            )
            return
        self._pending_rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()
        self._update_remove_btn_visibility()
        self._update_conflict_label()
        # 减一行后, 窗口缩小
        self._adjust_window_height()

    def _adjust_window_height(self) -> None:
        """让窗口高度跟 PairRow 数量走, 简单可靠。"""
        target_w = 760
        fixed = 70 + 195 + 50 + 54 + 21 + 60
        per_row = 46
        n_rows = max(1, len(self._pending_rows))
        rows_h = per_row * n_rows
        card_pairs_padding = 80
        cw_needed = fixed + card_pairs_padding + rows_h
        # 标题栏估算
        frame_h = 32
        new_h = cw_needed + frame_h
        # 硬上限 1100 (7-8 行足够), 不受屏幕大小影响
        new_h = min(new_h, 1100)
        new_h = max(new_h, self.minimumHeight())
        if new_h != self.height() or self.width() != target_w:
            self.resize(target_w, new_h)
            QApplication.processEvents()

    def _on_row_data_changed(self) -> None:
        self._update_conflict_label()

    def _update_remove_btn_visibility(self) -> None:
        visible = len(self._pending_rows) > 1
        for r in self._pending_rows:
            r.set_remove_visible(visible)

    # ------------------------------------------------------------------ 冲突
    def _collect_pairs(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for r in self._pending_rows:
            out.append({
                "hotkey": r.hotkey().strip(),
                "device_id": r.device_id().strip(),
                "device_name": r.device_name().strip(),
            })
        return out

    def _update_conflict_label(self) -> None:
        pairs = self._collect_pairs()
        conflicts = detect_conflicts(pairs)
        for r in self._pending_rows:
            r.highlight_conflict(False)
        conflict_indices = {i for i, _j, _h in conflicts}
        conflict_indices |= {j for _i, j, _h in conflicts}
        for idx, r in enumerate(self._pending_rows):
            if idx in conflict_indices:
                r.highlight_conflict(True)
        if conflicts:
            txt = "快捷键冲突: " + ", ".join(
                f"第{max(i, j)+1}行 ({format_for_display(h)})"
                for i, j, h in conflicts
            )
            self._conflict_label.setText(txt)
            self._conflict_label.setVisible(True)
        else:
            self._conflict_label.setVisible(False)

    # ------------------------------------------------------------------ 动作
    def _validate(self) -> tuple[bool, str]:
        pairs = self._collect_pairs()
        if not any(p["hotkey"] for p in pairs):
            return False, "请至少配置一个快捷键。"
        if not any(p["device_id"] for p in pairs):
            return False, "请至少选择一个输出设备。"
        if detect_conflicts(pairs):
            return False, "存在重复的快捷键, 请修改后再保存。"
        for i, p in enumerate(pairs):
            if (p["hotkey"] and not p["device_id"]) or (p["device_id"] and not p["hotkey"]):
                return False, f"第 {i+1} 行: 快捷键与设备需同时填写。"
        return True, ""

    def _gather_config_from_ui(self) -> dict[str, Any]:
        return {
            "close_behavior": "minimize" if self._rb_minimize.isChecked() else "exit",
            "notify_on_switch": self._rb_notify.isChecked(),
            "start_minimized": self._config.start_minimized,
            "auto_start": self._cb_auto_start.isChecked(),
            "hotkey_device_pairs": self._collect_pairs(),
        }

    def _on_save(self) -> None:
        ok, msg = self._validate()
        if not ok:
            show_warn(self, "无法保存", msg)
            return
        self._config.data = self._gather_config_from_ui()
        if self._config.save():
            self._apply_hotkeys()
            show_info(self, "已保存", "配置已保存并已激活。")
        else:
            show_error(self, "保存失败", "无法写入配置文件, 请检查权限。")

    def _on_save_min(self) -> None:
        ok, msg = self._validate()
        if not ok:
            show_warn(self, "无法保存", msg)
            return
        self._config.data = self._gather_config_from_ui()
        if self._config.save():
            self._apply_hotkeys()
            self._hide_to_tray()
        else:
            show_error(self, "保存失败", "无法写入配置文件, 请检查权限。")

    def _on_auto_start_toggled(self, checked: bool) -> None:
        ok, err = set_auto_start(checked)
        if not ok:
            show_warn(self, "开机自启", err or "无法修改开机自启设置。")
            # 还原 checkbox
            self._cb_auto_start.blockSignals(True)
            self._cb_auto_start.setChecked(not checked)
            self._cb_auto_start.blockSignals(False)
            return
        # 同步到 config
        self._config.auto_start = checked

    # ------------------------------------------------------------------ 热键
    def _apply_hotkeys(self) -> None:
        self._hotkey_manager.unregister_all()
        for p in self._config.pairs:
            hk = (p.get("hotkey") or "").strip()
            dev_id = (p.get("device_id") or "").strip()
            dev_name = (p.get("device_name") or "").strip()
            if not hk or not dev_id:
                continue
            self._hotkey_manager.register(hk, lambda d=dev_id, n=dev_name: self._on_hotkey(d, n))

    def _on_hotkey(self, device_id: str, device_name: str) -> None:
        try:
            set_default_output_device(device_id)
        except AudioSwitchError as e:
            show_error(self, "切换失败", str(e))
            return
        if self._config.notify_on_switch:
            self._tray.notify("星黎音频", f"已切换到: {device_name}", 2000)

    # ------------------------------------------------------------------ 关闭
    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        if self._config.close_behavior == "exit":
            self._real_exit()
            event.accept()
        else:
            self._hide_to_tray()
            event.ignore()

    def _hide_to_tray(self) -> None:
        self.hide()
        self._tray.notify(
            "星黎音频",
            "已最小化到任务栏, 右键托盘图标可退出。",
            2000,
        )

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _real_exit(self) -> None:
        self._closing = True
        self._hotkey_manager.unregister_all()
        self._tray.hide()
        self.exitRequested.emit()
        self.close()

    def get_hotkey_manager(self) -> HotkeyManager:
        return self._hotkey_manager
