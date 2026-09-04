import os
import shutil
from pathlib import Path
from PIL import Image

src_img_path = r"C:\Users\jeskin alfred\.gemini\antigravity-ide\brain\0da4047a-4505-4d08-9180-a4cba227aa52\nexa_app_icon_1788539808478.jpg"
flutter_app_dir = Path(r"c:\Users\jeskin alfred\OneDrive\Desktop\nexa\frontend\nexa_app")
desktop_dir = Path(r"C:\Users\jeskin alfred\OneDrive\Desktop")

# 1. Ensure assets/icon directory
assets_icon_dir = flutter_app_dir / "assets" / "icon"
assets_icon_dir.mkdir(parents=True, exist_ok=True)

# 2. Open and convert source image to PNG
img = Image.open(src_img_path).convert("RGBA")

# Save master PNG to assets and Desktop
master_png = assets_icon_dir / "app_icon.png"
img.save(master_png, "PNG")
img.save(desktop_dir / "NEXA_App_Logo.png", "PNG")
print(f"Saved master logo to {master_png} and Desktop/NEXA_App_Logo.png")

# 3. Android Mipmap Icons
android_res_dir = flutter_app_dir / "android" / "app" / "src" / "main" / "res"
mipmap_sizes = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192
}

for folder, size in mipmap_sizes.items():
    target_dir = android_res_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Standard launcher icon
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(target_dir / "ic_launcher.png", "PNG")
    
    # Round launcher icon
    resized.save(target_dir / "ic_launcher_round.png", "PNG")
    print(f"Generated {folder}/ic_launcher.png ({size}x{size})")

# 4. Web Icons
web_dir = flutter_app_dir / "web"
web_icons_dir = web_dir / "icons"
web_icons_dir.mkdir(parents=True, exist_ok=True)

img.resize((16, 16), Image.Resampling.LANCZOS).save(web_dir / "favicon.png", "PNG")
img.resize((192, 192), Image.Resampling.LANCZOS).save(web_icons_dir / "Icon-192.png", "PNG")
img.resize((192, 192), Image.Resampling.LANCZOS).save(web_icons_dir / "Icon-maskable-192.png", "PNG")
img.resize((512, 512), Image.Resampling.LANCZOS).save(web_icons_dir / "Icon-512.png", "PNG")
img.resize((512, 512), Image.Resampling.LANCZOS).save(web_icons_dir / "Icon-maskable-512.png", "PNG")
print("Generated Web icons and favicon!")

# 5. Windows App Icon (.ico)
windows_res_dir = flutter_app_dir / "windows" / "runner" / "resources"
if windows_res_dir.exists():
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(windows_res_dir / "app_icon.ico", format="ICO", sizes=ico_sizes)
    print("Generated Windows runner app_icon.ico!")

print("\nAll icon assets successfully created and mapped!")
