"""Lock a hunt file with a password so it can sit on the public website.

Usage: python3 encrypt_hunt.py <hunt.json> <out hunt.enc.json> <password> [salt_b64]
Format: gzip(JSON) encrypted with AES-256-GCM; key from PBKDF2-HMAC-SHA256.
Keep the same salt between builds so devices that are already unlocked keep working.
"""
import base64, gzip, json, os, sys
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

src, out, password = sys.argv[1], sys.argv[2], sys.argv[3]
salt = base64.b64decode(sys.argv[4]) if len(sys.argv) > 4 else os.urandom(16)
ITER = 310000

hunt = json.load(open(src))
raw = gzip.compress(json.dumps(hunt, ensure_ascii=False).encode("utf-8"), 9)
key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITER, 32)
iv = os.urandom(12)
ct = AESGCM(key).encrypt(iv, raw, None)
b64 = lambda b: base64.b64encode(b).decode()
json.dump({
    "format": "hunt-editor-enc/1",
    "title": hunt.get("title", "Treasure hunt"),
    "builtAt": hunt.get("builtAt"),
    "kdf": {"name": "PBKDF2", "hash": "SHA-256", "iterations": ITER, "salt": b64(salt)},
    "cipher": {"name": "AES-GCM", "iv": b64(iv)},
    "data": b64(ct),
}, open(out, "w"))
print("wrote", out, os.path.getsize(out), "bytes; salt", b64(salt), "builtAt", hunt.get("builtAt"))
