"""Adjust the generated Capacitor Android project: permissions, version number and app icon.

Usage: python3 patch_android.py <android project dir> <build number>
"""
import os, re, sys
from PIL import Image, ImageDraw

root, build = sys.argv[1], int(sys.argv[2])
app = os.path.join(root, "app")
main = os.path.join(app, "src", "main")

# --- permissions and the apps we need to talk to (speech, camera)
mf = os.path.join(main, "AndroidManifest.xml")
s = open(mf).read()
extra = """
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-feature android:name="android.hardware.location.gps" android:required="false" />
    <uses-feature android:name="android.hardware.camera" android:required="false" />
    <uses-feature android:name="android.hardware.microphone" android:required="false" />
    <queries>
        <intent><action android:name="android.speech.RecognitionService" /></intent>
        <intent><action android:name="android.speech.action.RECOGNIZE_SPEECH" /></intent>
        <intent><action android:name="android.media.action.IMAGE_CAPTURE" /></intent>
    </queries>
"""
if "RECORD_AUDIO" not in s:
    s = s.replace("<application", extra + "\n    <application", 1)
open(mf, "w").write(s)

# --- version number (each build must be higher so Android accepts it as an update)
bg = os.path.join(app, "build.gradle")
g = open(bg).read()
g = re.sub(r"versionCode\s+\d+", f"versionCode {build}", g)
g = re.sub(r'versionName\s+"[^"]*"', f'versionName "1.0.{build}"', g)
open(bg, "w").write(g)

# --- icon: navy background, yellow map pin, white dotted trail
def draw_icon(size, transparent=False, scale=1.0):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0) if transparent else (22, 50, 79, 255))
    d = ImageDraw.Draw(im)
    s_ = size * scale; off = (size - s_) / 2
    cx, cy, r = off + s_ * 0.5, off + s_ * 0.42, s_ * 0.2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#f2b33d")
    d.polygon([(cx - r * 0.82, cy + r * 0.55), (cx + r * 0.82, cy + r * 0.55), (cx, cy + r * 2.0)], fill="#f2b33d")
    d.ellipse([cx - r * 0.42, cy - r * 0.42, cx + r * 0.42, cy + r * 0.42], fill="#16324f")
    for k in range(4):
        x = off + s_ * 0.22 + k * s_ * 0.07; y = off + s_ * 0.84 - k * s_ * 0.02; rr = s_ * 0.018
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill="#ffffff")
    return im

res = os.path.join(main, "res")
for dens, px in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
    folder = os.path.join(res, f"mipmap-{dens}"); os.makedirs(folder, exist_ok=True)
    big = draw_icon(px * 4).resize((px, px), Image.LANCZOS)
    big.save(os.path.join(folder, "ic_launcher.png"))
    round_ = Image.new("RGBA", (px, px), (0, 0, 0, 0)); mask = Image.new("L", (px, px), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, px - 1, px - 1], fill=255); round_.paste(big, (0, 0), mask)
    round_.save(os.path.join(folder, "ic_launcher_round.png"))
    fg = int(px * 108 / 48)   # adaptive icon foreground canvas is 108dp; keep the art inside the middle 66dp
    draw_icon(fg * 4, transparent=True, scale=0.6).resize((fg, fg), Image.LANCZOS).save(os.path.join(folder, "ic_launcher_foreground.png"))

anydpi = os.path.join(res, "mipmap-anydpi-v26"); os.makedirs(anydpi, exist_ok=True)
xml = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/hunt_icon_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
"""
for n in ("ic_launcher.xml", "ic_launcher_round.xml"):
    open(os.path.join(anydpi, n), "w").write(xml)
os.makedirs(os.path.join(res, "values"), exist_ok=True)
open(os.path.join(res, "values", "hunt_colors.xml"), "w").write(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="hunt_icon_background">#16324F</color>\n</resources>\n')
print("patched: permissions, version", build, "and icons")
