#!/usr/bin/env bash
# Runs inside the Android emulator job: install the app, give it permissions, open it and try its features.
set -u
APP=mt.johncauchi.hunteditor
OUT=ci-out
mkdir -p "$OUT"
adb wait-for-device
adb shell wm size 1600x2560 || true
adb shell wm density 320 || true
if ! adb install -r HuntEditor.apk > "$OUT/install.txt" 2>&1; then
  echo "::error::Installing the app in the emulator failed: $(tail -3 "$OUT/install.txt" | tr '\n' ' ')"; exit 1
fi
echo "::notice::App installed in the Android 15 emulator"
for p in ACCESS_FINE_LOCATION ACCESS_COARSE_LOCATION RECORD_AUDIO CAMERA; do adb shell pm grant $APP android.permission.$p || true; done
adb emu geo fix 14.5225 35.8872 || true
adb shell monkey -p $APP -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1
sleep 30
adb emu geo fix 14.5226 35.8873 || true
adb exec-out screencap -p > "$OUT/1-launch.png"
pip install --quiet websocket-client
python3 android-app/devtools_test.py "$APP" "$OUT" || echo "::warning::The in-app feature test did not finish"
adb exec-out screencap -p > "$OUT/4-final.png"
adb shell ls -la /sdcard/Documents/HuntEditor /sdcard/Documents/HuntEditor/exports > "$OUT/documents-folder.txt" 2>&1 || true
adb logcat -d > "$OUT/logcat-full.txt" 2>&1 || true
grep -E "Capacitor|chromium|AndroidRuntime|FATAL" "$OUT/logcat-full.txt" | tail -400 > "$OUT/logcat.txt" || true
rm -f "$OUT/logcat-full.txt"
exit 0
