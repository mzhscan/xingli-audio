"""生成 512x512 高清 PNG + 多尺寸 .ico 图标。"""
from PIL import Image
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SOURCE = ASSETS / "xingliaudio_source.png"


def main():
    if not SOURCE.exists():
        raise SystemExit(f"找不到源图标: {SOURCE}")

    img = Image.open(SOURCE).convert("RGBA")
    print(f"源图尺寸: {img.size}")

    # 1) 512x512 高清 PNG
    img_512 = img.resize((512, 512), Image.LANCZOS)
    img_512.save(ASSETS / "icon_512.png", format="PNG", optimize=True)
    print(f"已保存: icon_512.png ({img_512.size})")

    # 2) 多尺寸 .ico (Windows 资源管理器 / 任务栏 / 标题栏)
    #    包含 16/24/32/48/64/128/256 多种尺寸
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48),
                 (64, 64), (128, 128), (256, 256)]
    base_for_ico = img.resize((256, 256), Image.LANCZOS)
    base_for_ico.save(
        ASSETS / "icon.ico",
        format="ICO",
        sizes=ico_sizes,
        append_images=[img.resize(s, Image.LANCZOS) for s in ico_sizes],
    )
    print(f"已保存: icon.ico (含 {len(ico_sizes)+1} 个尺寸)")

    # 3) 托盘用 32x32 PNG（如果需要透明背景小图）
    img_32 = img.resize((32, 32), Image.LANCZOS)
    img_32.save(ASSETS / "icon_32.png", format="PNG", optimize=True)
    print("已保存: icon_32.png")

    # 4) 复制一个 512x512 主图标 (PyInstaller 资源用)
    img_512.save(ASSETS / "icon_512_for_exe.ico", format="ICO",
                 sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("已保存: icon_512_for_exe.ico (PyInstaller 备用)")


if __name__ == "__main__":
    main()
