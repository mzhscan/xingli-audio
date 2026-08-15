"""星黎音频 - 配置管理。

配置文件: 与可执行文件同目录的 config.json (便携运行, 不写注册表/系统目录)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _default_pairs() -> list[dict[str, Any]]:
    """软件首次启动时, 默认给用户一对空快捷键 + 空设备。"""
    return [
        {"hotkey": "", "device_id": "", "device_name": ""}
    ]


DEFAULT_CONFIG: dict[str, Any] = {
    # 关闭按钮行为: "minimize" 最小化到托盘; "exit" 退出程序
    "close_behavior": "minimize",
    # 切换设备时是否弹出系统通知
    "notify_on_switch": True,
    # 启动时是否最小化到托盘
    "start_minimized": False,
    # 是否开机自启 (在 Windows 启动时自动启动并最小化)
    "auto_start": False,
    # 快捷键 -> 设备 映射列表
    "hotkey_device_pairs": _default_pairs(),
}


class Config:
    """JSON 持久化配置。"""

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            # 便携运行: 配置放在 exe 同目录 (而不是用户的 %APPDATA%)
            if getattr(sys, "frozen", False):
                base = Path(sys.executable).resolve().parent
            else:
                base = Path(__file__).resolve().parent.parent
            path = base / "config.json"
        self.path = Path(path)
        self.data: dict[str, Any] = self._load()

    # ------------------------------------------------------------------ load/save
    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"[Config] 读取失败, 使用默认配置: {e}")
            return json.loads(json.dumps(DEFAULT_CONFIG))

        # 合并默认值, 保证向下兼容
        merged = json.loads(json.dumps(DEFAULT_CONFIG))
        if isinstance(raw, dict):
            for k, v in raw.items():
                merged[k] = v
        # 确保至少有一对
        if not isinstance(merged.get("hotkey_device_pairs"), list) or not merged["hotkey_device_pairs"]:
            merged["hotkey_device_pairs"] = _default_pairs()
        # 规范化每个 pair 字段
        norm: list[dict[str, Any]] = []
        for item in merged["hotkey_device_pairs"]:
            if not isinstance(item, dict):
                continue
            norm.append({
                "hotkey": str(item.get("hotkey", "") or ""),
                "device_id": str(item.get("device_id", "") or ""),
                "device_name": str(item.get("device_name", "") or ""),
            })
        merged["hotkey_device_pairs"] = norm
        return merged

    def save(self) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True
        except OSError as e:
            print(f"[Config] 保存失败: {e}")
            return False

    # ------------------------------------------------------------------ accessors
    @property
    def close_behavior(self) -> str:
        return self.data.get("close_behavior", "minimize")

    @close_behavior.setter
    def close_behavior(self, value: str) -> None:
        self.data["close_behavior"] = value

    @property
    def notify_on_switch(self) -> bool:
        return bool(self.data.get("notify_on_switch", True))

    @notify_on_switch.setter
    def notify_on_switch(self, value: bool) -> None:
        self.data["notify_on_switch"] = bool(value)

    @property
    def start_minimized(self) -> bool:
        return bool(self.data.get("start_minimized", False))

    @start_minimized.setter
    def start_minimized(self, value: bool) -> None:
        self.data["start_minimized"] = bool(value)

    @property
    def auto_start(self) -> bool:
        return bool(self.data.get("auto_start", False))

    @auto_start.setter
    def auto_start(self, value: bool) -> None:
        self.data["auto_start"] = bool(value)

    @property
    def pairs(self) -> list[dict[str, Any]]:
        return list(self.data.get("hotkey_device_pairs", []))

    @pairs.setter
    def pairs(self, value: list[dict[str, Any]]) -> None:
        self.data["hotkey_device_pairs"] = value

    def get_path_display(self) -> str:
        """用于 UI 提示, 配置文件位置。"""
        return str(self.path)
