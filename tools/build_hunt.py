"""Build the hunt data file (clues, answers, points, reference photos) from the old Word/Excel files."""
import base64, io, json, re, sys
import docx, openpyxl
from PIL import Image, ImageOps

SRC = "/mnt/user-data/uploads/Treasure hunt/"
MEDIA = "/home/claude/hunt/src/media/"
OUT = sys.argv[1]


def clean_block(s):
    """Tidy a multi-line cell: strip each line, collapse runs of blank lines to one."""
    lines = [l.strip() for l in s.replace("\r", "").split("\n")]
    out, blank = [], False
    for l in lines:
        if not l:
            if out and not blank:
                out.append("")
            blank = True
        else:
            out.append(l)
            blank = False
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def clean_answer(s):
    lines = [l.strip().rstrip(",").strip() for l in s.split("\n")]
    return "\n".join(l for l in lines if l)


def clean_points(s):
    s = re.sub(r"\s+", " ", s.replace("\n", " ")).strip()
    s = re.sub(r"\s*,\s*", ", ", s)
    return s


def thumb(path, maxside=900, q=68):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((maxside, maxside))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


items, refphotos = [], {}


def add(**kw):
    kw.setdefault("flags", [])
    kw.setdefault("notes", "")
    kw.setdefault("status", "unchecked")
    kw.setdefault("lat", None)
    kw.setdefault("lng", None)
    kw.setdefault("acc", None)
    kw.setdefault("refPhoto", None)
    items.append(kw)


# ---- Clues from the Word files
for fname, section, code in [("Birgu Clues updated.docx", "Birgu", "B"),
                             ("Cospicua Clues updated.docx", "Cospicua", "C")]:
    t = docx.Document(SRC + fname).tables[0]
    for r in t.rows[2:]:
        c = [x.text for x in r.cells]
        n = int(c[0].strip())
        flags = []
        pts = clean_points(c[3])
        if not pts:
            pts = "10"
            flags.append("Points were blank in the Word file; 10 taken from the old spreadsheet.")
        add(id=f"{code}-clue-{n:02d}", type="clue", section=section, number=n,
            text=clean_block(c[1]), answer=clean_answer(c[2]), points=pts, flags=flags)

# ---- Senglea clues (Senglea Clues.docx, added Nov 2026)
wb = openpyxl.load_workbook(SRC + "POINT SYSTEM ThreeCities.xlsx")
t = docx.Document(SRC + "Senglea Clues.docx").tables[0]
for r in t.rows[2:]:
    c = [x.text for x in r.cells]
    n = int(c[0].strip())
    flags = []
    pts = clean_points(c[3])
    if not pts:
        pts = "10"
        flags.append("Points were blank in the Word file; 10 taken from the old spreadsheet.")
    add(id=f"S-clue-{n:02d}", type="clue", section="Senglea", number=n,
        text=clean_block(c[1]), answer=clean_answer(c[2]), points=pts, flags=flags)

# ---- Pictures ("spot this object") from Pictures with Answers.docx
t = docx.Document(SRC + "Pictures with Answers.docx").tables[0]
section, n = None, 0
pics = []
for r in t.rows[1:]:
    q, a = r.cells[0].text.strip(), r.cells[1].text.strip()
    if q.upper() in ("BIRGU", "COSPICUA", "SENGLEA"):
        section, n = q.title(), 0
        continue
    n += 1
    pics.append((section, n, q, a))

# The photo sheet is the reference for numbering. In the question list, questions 15 and 18
# were the other way round (photo 15 is the Gretna Green sign), so renumber those two.
renumber = {("Birgu", 15): 18, ("Birgu", 18): 15}
for section, n0, q, a in pics:
    code = section[0]
    pid = f"{code}-pic-{n0:02d}"          # the ID stays with the question, so field notes and pins follow it
    n = renumber.get((section, n0), n0)    # the number shown matches the photo sheet
    if section == "Birgu":
        f = f"image{n}.jpeg"
        overall = n
    else:
        f = f"cosp-{n-1:03d}.jpg"
        overall = 18 + n
    refphotos[pid] = thumb(MEDIA + f)
    add(id=pid, type="picture", section=section, number=n, text=q, answer=a, points="10",
        refPhoto=pid, sheetNo=overall)

# Senglea pictures: answers only, from the old spreadsheet
ws = wb["Pictures"]
for row in ws.iter_rows(min_row=30, max_row=34):
    n, ans = row[0].value, row[1].value
    if n is None:
        continue
    k = int(n) - 25
    add(id=f"S-pic-{k:02d}", type="picture", section="Senglea", number=k, text="", answer=str(ans).strip(),
        points="10", flags=["No Senglea photo sheet or questions were in the folder. Only this answer survives, from the old spreadsheet. Take a new photo and write the question."])

# ---- Photo challenges
d = docx.Document(SRC + "Photo-taking.docx")
paras = [p.text.strip() for p in d.paragraphs if p.text.strip()]
for i, p in enumerate(paras[1:], start=1):
    sec = "Cospicua" if "Cospicua" in p else "Anywhere"
    add(id=f"P-photo-{i:02d}", type="photo", section=sec, number=i, text=p, answer="", points="20")

# ---- Intro text
intro = "\n".join(p.text.strip() for p in docx.Document(SRC + "The Clues intro.docx").paragraphs if p.text.strip())

import time, os
order = {"clue": 0, "picture": 1, "photo": 2}
secs = ["Birgu", "Cospicua", "Senglea", "Anywhere"]
items.sort(key=lambda i: (order[i["type"]], secs.index(i["section"]), i["number"]))
for it in items:
    it["orig"] = {"text": it["text"], "answer": it["answer"], "points": it["points"]}
# Items that differ from the previous hunt file get a timestamp, so that loading this file on a device
# that already has the old one replaces them (the app keeps whichever copy of an item is newest).
PREV = sys.argv[2] if len(sys.argv) > 2 else None
built = int(time.time() * 1000)
changed = []
if PREV and os.path.exists(PREV):
    prev = {i["id"]: i for i in json.load(open(PREV))["items"]}
    keys = ("type", "section", "number", "text", "answer", "points", "refPhoto", "flags")
    for it in items:
        old = prev.get(it["id"])
        if old is None or any(old.get(k) != it.get(k) for k in keys):
            it["updatedAt"] = built
            changed.append(it["id"])
        elif old.get("updatedAt"):
            it["updatedAt"] = old["updatedAt"]
print("changed vs previous file:", len(changed), changed)

hunt = {
    "format": "hunt-editor/1",
    "builtAt": built,
    "title": "Three Cities Treasure Hunt",
    "intro": intro,
    "sections": [
        {"name": "Birgu", "code": "B", "label": "Section A", "bonus": 50},
        {"name": "Cospicua", "code": "C", "label": "Section B", "bonus": 50},
        {"name": "Senglea", "code": "S", "label": "Section C", "bonus": 80},
        {"name": "Anywhere", "code": "P", "label": "Photo tasks", "bonus": None},
    ],
    "items": items,
    "refPhotos": refphotos,
}
json.dump(hunt, open(OUT, "w"), ensure_ascii=False)
from collections import Counter
print(Counter((i["section"], i["type"]) for i in items))
print("items", len(items), "photos", len(refphotos))
