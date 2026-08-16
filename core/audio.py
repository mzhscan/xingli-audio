"""星黎音频 - Windows 输出设备枚举与切换。

实现要点:
  * 枚举: IMMDeviceEnumerator.EnumAudioEndpoints (直接 COM, 不走高层 utils)
  * 切换默认设备: IPolicyConfig::SetDefaultEndpoint (eConsole/eMultimedia/eCommunications 三种 role)
  * 设备热插拔监听: pycaw.MMNotificationClient (outgoing COM 接口)
"""
from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from typing import Optional

if sys.platform != "win32":
    raise RuntimeError("星黎音频仅支持 Windows 平台。")

import comtypes  # noqa: E402
from ctypes import HRESULT, c_int, c_void_p, c_wchar_p  # noqa: E402
from comtypes import COMMETHOD, GUID, IUnknown  # noqa: E402
from PySide6.QtCore import QObject, Q_ARG, QMetaObject, Qt, Signal  # noqa: E402

# pycaw 底层 COM 接口
from pycaw.pycaw import (  # noqa: E402
    EDataFlow, ERole, IMMDeviceEnumerator, IPropertyStore, PROPERTYKEY,
)


# ---------------------------------------------------------------------------
# 常量 (Windows SDK)
# ---------------------------------------------------------------------------
# CLSID_MMDeviceEnumerator
_CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
# CLSID_PolicyConfigClient
_CLSID_PolicyConfigClient = GUID("{870AF99C-171D-4F9E-AF0D-E63DF40C2BC9}")
# PKEY_Device_FriendlyName: fmtid + pid=14
_PKEY_Device_FriendlyName = PROPERTYKEY(
    fmtid=GUID("{A45C254E-DF1C-4EFD-8020-67D146A850E0}"),
    pid=14,
)


# ---------------------------------------------------------------------------
# IPolicyConfig COM 接口
#
# 注意: IPolicyConfig 继承自 IUnknown (3 个方法), 自身有 12 个方法。
# SetDefaultEndpoint 在 vtable 的索引 13, 必须按顺序声明 0~13 才能让
# comtypes 用正确的偏移去调用。下方 0~12 用 c_void_p 填位, 13 是我们关心的。
# ---------------------------------------------------------------------------
class IPolicyConfig(IUnknown):
    _iid_ = GUID("{F8679F50-850A-41CF-9C72-430F290290C8}")
    _methods_ = [
        # 3: GetMixFormat(LPCWSTR, WAVEFORMATEX**)
        COMMETHOD([], HRESULT, "GetMixFormat",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in", "out"], c_void_p, "ppFormat")),
        # 4: GetDeviceFormat(LPCWSTR, BOOL, WAVEFORMATEX**)
        COMMETHOD([], HRESULT, "GetDeviceFormat",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in"], c_int, "bConfig"),
                  (["in", "out"], c_void_p, "ppFormat")),
        # 5: ResetDeviceFormat(LPCWSTR)
        COMMETHOD([], HRESULT, "ResetDeviceFormat",
                  (["in"], c_void_p, "pwstrDeviceId")),
        # 6: SetDeviceFormat(LPCWSTR, WAVEFORMATEX*, WAVEFORMATEX*)
        COMMETHOD([], HRESULT, "SetDeviceFormat",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in"], c_void_p, "pConfig"),
                  (["in"], c_void_p, "pFormat")),
        # 7: GetProcessingPeriod(LPCWSTR, BOOL, REFERENCE_TIME*, REFERENCE_TIME*)
        COMMETHOD([], HRESULT, "GetProcessingPeriod",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in"], c_int, "bConfigDefault"),
                  (["in", "out"], c_void_p, "hnsDefaultPeriod"),
                  (["in", "out"], c_void_p, "hnsMinimumPeriod")),
        # 8: SetProcessingPeriod(LPCWSTR, REFERENCE_TIME)
        COMMETHOD([], HRESULT, "SetProcessingPeriod",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in"], c_void_p, "hnsPeriod")),
        # 9: GetShareMode(LPCWSTR, DeviceShareMode*)
        COMMETHOD([], HRESULT, "GetShareMode",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["out"], c_void_p, "pMode")),
        # 10: SetShareMode(LPCWSTR, DeviceShareMode)
        COMMETHOD([], HRESULT, "SetShareMode",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in"], c_void_p, "pMode")),
        # 11: GetPropertyValue(LPCWSTR, const PROPERTYKEY, PROPVARIANT*)
        COMMETHOD([], HRESULT, "GetPropertyValue",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in"], c_void_p, "pKey"),
                  (["out"], c_void_p, "pValue")),
        # 12: SetPropertyValue(LPCWSTR, const PROPERTYKEY, const PROPVARIANT*)
        COMMETHOD([], HRESULT, "SetPropertyValue",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in"], c_void_p, "pKey"),
                  (["in"], c_void_p, "pValue")),
        # 13: SetDefaultEndpoint(LPCWSTR, ERole)  <-- 我们要用的
        COMMETHOD([], HRESULT, "SetDefaultEndpoint",
                  (["in"], c_wchar_p, "pwstrDeviceId"),
                  (["in"], c_int, "bConfig")),  # 0=eConsole, 1=eMultimedia, 2=eCommunications
        # 14: SetEndpointVisibility(LPCWSTR, BOOL)
        COMMETHOD([], HRESULT, "SetEndpointVisibility",
                  (["in"], c_void_p, "pwstrDeviceId"),
                  (["in"], c_int, "bVisible")),
    ]


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AudioDevice:
    id: str           # IMMDevice.GetId() 返回的端点 ID
    name: str         # FriendlyName
    is_active: bool   # 是否处于 ACTIVE 状态


# ---------------------------------------------------------------------------
# COM 初始化
# ---------------------------------------------------------------------------
_com_lock = threading.Lock()
_com_initialized = False


def _ensure_com() -> None:
    global _com_initialized
    with _com_lock:
        if _com_initialized:
            return
        try:
            comtypes.CoInitialize()
        except OSError:
            pass
        _com_initialized = True


# ---------------------------------------------------------------------------
# 设备枚举
# ---------------------------------------------------------------------------
def list_output_devices() -> list[AudioDevice]:
    """列出当前系统所有 ACTIVE 状态的输出 (渲染) 设备。

    用 IMMDeviceEnumerator.EnumAudioEndpoints(eRender, ACTIVE) 直接拿到
    仅渲染设备 (排除麦克风等输入设备)。
    """
    _ensure_com()
    out: list[AudioDevice] = []
    try:
        enumerator = comtypes.CoCreateInstance(
            _CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER,
        )
    except Exception as e:
        print(f"[Audio] 创建设备枚举器失败: {e}")
        return []

    # ACTIVE = 1
    try:
        collection = enumerator.EnumAudioEndpoints(
            EDataFlow.eRender.value, 1
        )
    except Exception as e:
        print(f"[Audio] 枚举端点失败: {e}")
        return []

    try:
        for i in range(collection.GetCount()):
            try:
                dev = collection.Item(i)
            except Exception:
                continue
            try:
                dev_id = dev.GetId()
                name = _get_friendly_name(dev) or dev_id
                out.append(AudioDevice(id=dev_id, name=name, is_active=True))
            except Exception as e:  # pragma: no cover
                print(f"[Audio] 读取端点属性失败: {e}")
    finally:
        try:
            collection.Release()
        except Exception:  # pragma: no cover
            pass

    return out


def _get_friendly_name(device) -> str:
    """从 IMMDevice 读 PKEY_Device_FriendlyName。"""
    try:
        store = device.OpenPropertyStore(0)  # STGM_READ
    except Exception:
        return ""
    try:
        try:
            store = store.QueryInterface(IPropertyStore)
        except Exception:
            pass
        try:
            val = store.GetValue(_PKEY_Device_FriendlyName)
        except Exception:
            return ""
        # PROPVARIANT 需要调 GetValue() 取真实字符串
        try:
            return str(val.GetValue())
        except Exception:
            pass
        if hasattr(val, "value"):
            try:
                return str(val.value)
            except Exception:
                pass
        return str(val)
    finally:
        try:
            store.Release()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 切换默认输出设备
# ---------------------------------------------------------------------------
class AudioSwitchError(RuntimeError):
    """切换默认设备失败。"""


def set_default_output_device(device_id: str) -> None:
    """把指定端点设为系统默认输出设备 (eConsole + eMultimedia + eCommunications)。"""
    if not device_id:
        raise AudioSwitchError("设备 ID 为空。")
    _ensure_com()
    try:
        policy = comtypes.CoCreateInstance(
            _CLSID_PolicyConfigClient,
            interface=IPolicyConfig,
            clsctx=comtypes.CLSCTX_INPROC_SERVER,
        )
    except Exception as e:
        raise AudioSwitchError(f"无法创建 IPolicyConfig: {e}") from e

    last_err: Optional[Exception] = None
    for role in (0, 1, 2):  # eConsole, eMultimedia, eCommunications
        try:
            policy.SetDefaultEndpoint(device_id, role)
        except Exception as e:
            last_err = e
    if last_err is not None:
        # 即使部分 role 失败, 至少 Console 角色通常成功
        print(f"[Audio] SetDefaultEndpoint 异常: {last_err}")


def get_default_output_device_id() -> str:
    """获取当前默认输出设备 (eConsole) 的 ID。"""
    _ensure_com()
    try:
        enumerator = comtypes.CoCreateInstance(
            _CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER,
        )
        dev = enumerator.GetDefaultAudioEndpoint(
            EDataFlow.eRender.value, ERole.eConsole.value
        )
        try:
            return dev.GetId()
        finally:
            try:
                dev.Release()
            except Exception:
                pass
    except Exception:  # pragma: no cover
        return ""


# ---------------------------------------------------------------------------
# 设备热插拔监听: IMMNotificationClient
#
# Windows 设备插/拔/启用/禁用/默认设备变化 都会通过这个 COM 回调通知。
# 我们继承 pycaw 已有的 MMNotificationClient (它已正确设置了 _com_interfaces_,
# 可以作为 outgoing interface 的 coclass 实例), 然后通过 PySide6 Signal
# 跨线程 marshal 到 Qt 主线程。
# ---------------------------------------------------------------------------
from pycaw.callbacks import MMNotificationClient  # noqa: E402

# Reason 常量 (DeviceCombo 收到信号后可以按需区分, 这里统一发一个简单信号)
DEVICE_CHANGE_REASON_DEFAULT = "default"
DEVICE_CHANGE_REASON_ADDED = "added"
DEVICE_CHANGE_REASON_REMOVED = "removed"
DEVICE_CHANGE_REASON_STATE = "state"


class _NotificationSink(MMNotificationClient):
    """COM 回调接收器: Windows 在自己的线程触发回调, 我们通过 DeviceNotifier
    的 Qt Signal 跨线程 marshal 到主线程 (Qt AutoConnection 自动 Queue)。
    """

    def __init__(self, notifier: "DeviceNotifier") -> None:
        super().__init__()
        self._notifier = notifier

    # ---- pycaw 的 MMNotificationClient 把 5 个 COM 回调映射到 pythonic 的 on_* ----
    def on_default_device_changed(self, flow, flow_id, role, role_id, default_device_id):
        # 只关心 render (输出) 设备
        if flow_id == 0:  # EDataFlow.eRender
            self._notifier._post_change(DEVICE_CHANGE_REASON_DEFAULT)

    def on_device_added(self, added_device_id):
        self._notifier._post_change(DEVICE_CHANGE_REASON_ADDED)

    def on_device_removed(self, removed_device_id):
        self._notifier._post_change(DEVICE_CHANGE_REASON_REMOVED)

    def on_device_state_changed(self, device_id, new_state, new_state_id):
        self._notifier._post_change(DEVICE_CHANGE_REASON_STATE)

    def on_property_value_changed(self, device_id, property_struct, fmtid, pid):
        # 改名 / 设备属性变化, 也触发刷新
        self._notifier._post_change(DEVICE_CHANGE_REASON_STATE)


class DeviceNotifier(QObject):
    """监听音频设备热插拔 / 状态变化, 发出 Qt 信号让 UI 刷新。

    用法:
        notifier = DeviceNotifier()
        notifier.deviceChanged.connect(some_slot)
        notifier.start()    # 注册 COM 回调
        ...
        notifier.stop()     # 取消注册 (进程退出时不必显式调用)
    """

    # reason: 字符串常量之一 (DEVICE_CHANGE_REASON_*)
    deviceChanged = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._enumerator = None  # type: ignore[var-annotated]
        self._sink = None  # type: ignore[var-annotated]
        self._registered = False

    def start(self) -> bool:
        """注册 COM 回调, 开始监听设备变化。失败 (e.g. 权限) 返回 False。"""
        _ensure_com()
        try:
            enumerator = comtypes.CoCreateInstance(
                _CLSID_MMDeviceEnumerator,
                IMMDeviceEnumerator,
                comtypes.CLSCTX_INPROC_SERVER,
            )
            sink = _NotificationSink(self)
            enumerator.RegisterEndpointNotificationCallback(sink)
            self._enumerator = enumerator
            self._sink = sink
            self._registered = True
            return True
        except Exception as e:
            print(f"[DeviceNotifier] 注册失败: {e}")
            self._enumerator = None
            self._sink = None
            self._registered = False
            return False

    def stop(self) -> None:
        """取消注册, 不再监听。"""
        if not self._registered:
            return
        try:
            if self._enumerator is not None and self._sink is not None:
                self._enumerator.UnregisterEndpointNotificationCallback(self._sink)
        except Exception as e:
            print(f"[DeviceNotifier] 注销失败: {e}")
        finally:
            self._enumerator = None
            self._sink = None
            self._registered = False

    def _post_change(self, reason: str) -> None:
        """COM 线程触发, 通过 QMetaObject.invokeMethod 跨线程 emit。
        绝对不能在 COM 线程直接 self.signal.emit(): Qt 不允许在非
        所属线程 emit, 会 crash (0xC0000005)。QueuedConnection 会把
        emit 排到 DeviceNotifier 所属的线程 (创建时所在 = 主线程) 再执行。
        """
        try:
            QMetaObject.invokeMethod(
                self,
                "deviceChanged",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, reason),
            )
        except Exception as e:
            print(f"[DeviceNotifier] invokeMethod 失败: {e}")
