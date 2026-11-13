# Hunt Editor

A small app for walking a treasure-hunt route on a tablet or phone and updating it as you go:
map with your location, pins with coordinates, a status per clue, voice typing, photos,
timestamped saved versions, and upload of the latest version to a private GitHub repository.

- **Android app:** download `HuntEditor.apk` from the [Android app release](https://github.com/johnpcauchi/hunt-editor/releases/tag/android)
  and open it on the tablet. Built by `.github/workflows/android.yml` (Capacitor), tested in an Android 15 emulator.
- **In Chrome:** https://johnpcauchi.github.io/hunt-editor/

Hunt content (clues, answers, photos) is **not** stored here. It is loaded from a hunt file on the device,
and uploaded versions go to a separate private repository.

The app is signed with `android-app/hunt-editor.keystore` so that new builds install as updates over old ones.
It is a personal, side-loaded app; this key has no other use.

Built with [Leaflet](https://leafletjs.com) and [protomaps-leaflet](https://github.com/protomaps/protomaps-leaflet).
Map data © OpenStreetMap contributors (offline map via Protomaps); imagery © Esri.
