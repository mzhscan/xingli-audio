"""列出 Windows 已安装字体中与 Segoe / YaHei 相关的。"""
import subprocess
ps = r'''
$fonts = Get-ChildItem "C:\Windows\Fonts" -Filter "*.ttf" -ErrorAction SilentlyContinue
$fonts += Get-ChildItem "C:\Windows\Fonts" -Filter "*.ttc" -ErrorAction SilentlyContinue
$match = $fonts | Where-Object { $_.Name -match "segoe|yahei|msyh" -and $_.Name -notmatch "emoji|ui-bold|symbol|monotype" } | Select-Object Name
$match | ForEach-Object { $_.Name }
'''
out = subprocess.run(
    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
    capture_output=True, text=True, encoding="utf-8",
)
print(out.stdout)
print("---stderr---", out.stderr[:300])
