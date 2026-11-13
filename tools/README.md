# Rebuilding the hunt

1. `build_hunt.py <out.json> [previous.json]` reads the Word files in the Treasure hunt folder
   (Birgu, Cospicua and Senglea clue sheets, Pictures with Answers, Photo-taking, Photos Birgu.docx,
   Photos Cospicua.pdf) and writes the hunt file. Items that differ from the previous file get a new
   timestamp, so devices pick up the change. Paths at the top of the script point at the staged folder.
2. `encrypt_hunt.py <hunt.json> ../hunt.enc.json <password> aBPGXSHyr8xG2TSSmspYKg==` locks it for the website.
   Always reuse this salt, or every device will have to type the password again.
3. Commit and push to both `main` and `gh-pages`. Devices update the next time the app opens online.

The password is not stored here. Ask John for it.
