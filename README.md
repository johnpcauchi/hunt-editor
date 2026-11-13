# Hunt Editor

A small web app for walking a treasure-hunt route on a tablet or phone and updating it as you go:
live map with your location, pins with GPS coordinates, status per clue, voice typing, and photos.

Hunt content (clues, answers, photos) is stored here only in locked form (`hunt.enc.json`, AES-GCM with a password-derived key).
The app asks for the password once per device, then keeps itself up to date.
Data is kept in the browser's on-device storage; use **Save backup** in the menu to keep a copy.

Built with [Leaflet](https://leafletjs.com). Map data © OpenStreetMap contributors; imagery © Esri.
