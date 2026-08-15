@echo off
REM 一键打包 星黎音频 -> dist\星黎音频.exe
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo [1/3] 生成图标...
python scripts\make_icon.py
if errorlevel 1 goto :fail

echo.
echo [2/3] 清理旧的 build / dist...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo.
echo [3/3] PyInstaller 打包...
pyinstaller build.spec --noconfirm
if errorlevel 1 goto :fail

echo.
echo ========================================
echo  打包完成: dist\星黎音频.exe
echo  双击即可运行, 不需安装。
echo ========================================
exit /b 0

:fail
echo.
echo 打包失败, 请查看上面的错误。
exit /b 1
