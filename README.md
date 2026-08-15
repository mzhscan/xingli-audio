# 星黎音频 (XingLi Audio)

> 用快捷键在多个 Windows 输出音频设备之间一键切换。便携、绿色、开机自启。

![主界面](assets/icon_512.png)

## 特性

- **全局热键切换** — `Ctrl+Alt+1` 切到扬声器，`Ctrl+Alt+2` 切到耳机，按下立即生效
- **任意多对配置** — 需要几对就加几对，不限数量
- **开机自启** — 可选登录 Windows 时自动启动并最小化到任务栏
- **关闭策略** — 关闭按钮可选"最小化到托盘"或"退出程序"
- **切换通知** — 切换设备时弹出系统通知（可关闭成静默切换）
- **Win11 美学** — 自动跟随系统深色/浅色模式，自动读取系统强调色
- **便携单文件** — 打包成单个 .exe，无需安装，双击即用

## 截图

> 实际效果（运行 .exe 后），浅色/深色自适应：

| 浅色模式 | 深色模式 |
|----------|----------|
| 实际 exe 截图 1 | 实际 exe 截图 2 |

> 上面截图渲染于真实打包后的 exe，文字可能因系统 DPI 与字体回退而与你的机器略有差异。

## 快速开始

### 1. 下载

到 [Releases](../../releases) 页面下载最新的 `星黎音频.exe`（单文件，~46 MB）。

### 2. 首次运行

双击 `星黎音频.exe`，首次会显示一个空白配置：

- 点击快捷键输入框，按下你想用的组合键（例如 `Ctrl+Alt+1`）
- 在设备下拉里选择对应的输出设备
- 点 **"保存并最小化"** （推荐默认按钮）—— 软件会注册全局热键并最小化到任务栏

之后随时右键托盘图标可以：
- 打开主窗口
- 退出

### 3. 添加更多设备对

点 **"+ 添加新的快捷键"** 按钮，重复上面步骤。窗口会自动向下扩展以容纳新行。

## 使用

- **触发热键**：全局生效，**不需要**主窗口在前台
- **设备切换**：按下热键瞬间切换系统默认输出设备，同时（可选）弹出通知
- **配置位置**：与 .exe 同目录的 `config.json`（便携），删除后下次启动恢复默认
- **开机自启**：勾选后写入注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

## 开发

### 环境

- Python 3.10+ (开发用 3.14)
- Windows 10 / 11
- 依赖：[PySide6](https://doc.qt.io/qtforpython-6/)、[pycaw](https://github.com/AndreMiras/pycaw)、[comtypes](https://github.com/enthought/comtypes)、[keyboard](https://github.com/boppreh/keyboard)

### 从源码运行

```bash
pip install -r requirements.txt
python main.py
```

### 自行打包

```bash
build.bat
# 产物: dist\星黎音频.exe
```

`build.bat` 会自动重新生成图标（来自 `assets\xingliaudio_source.png` 缩到 512×512 + 多尺寸 .ico），然后用 PyInstaller 打成单文件。

## 工作原理

- **设备枚举**：`pycaw` 高层 API + `IMMDeviceEnumerator.EnumAudioEndpoints(eRender, ACTIVE)`，只列 ACTIVE 状态输出设备
- **切换默认设备**：通过 `IPolicyConfig::SetDefaultEndpoint` 调 COM 接口（一次设 `eConsole` / `eMultimedia` / `eCommunications` 三个 role，所以浏览器 / 通讯软件都跟着切）
- **全局热键**：`keyboard` 库的低层钩子，无须管理员权限
- **开机自启**：写 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`，值为 `"{exe}" --minimized`，主程序识别 `--minimized` 后直接进托盘

## 已知限制

- 仅支持 Windows（用了 pycaw + winreg + IPolicyConfig COM）
- 系统级热键，可能与其他软件冲突；冲突时可在 UI 里看到红色高亮
- 切设备时不会迁移正在播放的音频流（这是 Windows 行为，不是软件限制）

## 许可

MIT License.

## 致谢

- 图标素材由项目作者提供
- 音频切换实现参考了 [pycaw](https://github.com/AndreMiras/pycaw) 项目
- Win11 风格参考了微软官方设计规范
