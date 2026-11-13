"""Drive the installed app inside the emulator through Chrome DevTools and check its features.

Usage: python3 devtools_test.py <package> <output dir>
Writes <output dir>/report.json and screenshots, and prints a GitHub notice per check.
Uses a small made-up hunt, never the real clues.
"""
import json, subprocess, sys, time, urllib.request
import websocket

app, out = sys.argv[1], sys.argv[2]
report = {}

def adb(*a):
    return subprocess.run(["adb", *a], capture_output=True, text=True).stdout.strip()

def shot(name):
    with open(f"{out}/{name}.png", "wb") as f:
        f.write(subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True).stdout)

pid = ""
for _ in range(20):
    pid = adb("shell", "pidof", app)
    if pid: break
    time.sleep(2)
socks = [l.split("@")[-1] for l in adb("shell", "cat", "/proc/net/unix").splitlines() if "webview_devtools_remote" in l]
sock = next((s for s in socks if s.endswith("_" + pid)), socks[0] if socks else None)
if not sock:
    print("::error::No WebView debugging socket found"); sys.exit(1)
subprocess.run(["adb", "forward", "tcp:9222", "localabstract:" + sock], check=True)
pages = []
for _ in range(15):
    try:
        pages = [p for p in json.load(urllib.request.urlopen("http://127.0.0.1:9222/json")) if p.get("type") == "page"]
        if pages: break
    except Exception:
        pass
    time.sleep(2)
ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"], timeout=90, suppress_origin=True)
msg_id = 0

def ev(expr, timeout=60):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate",
                        "params": {"expression": expr, "awaitPromise": True, "returnByValue": True, "timeout": timeout * 1000}}))
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == msg_id:
            r = m.get("result", {})
            if "exceptionDetails" in r:
                return "EXCEPTION: " + json.dumps(r["exceptionDetails"].get("exception", {}).get("description") or r["exceptionDetails"])[:500]
            return r.get("result", {}).get("value")

def check(name, expr, timeout=60):
    try:
        v = ev(expr, timeout)
    except Exception as e:
        v = "ERROR: " + str(e)
    report[name] = v
    print(f"::notice title={name}::{str(v)[:900]}")
    return v

check("platform", "JSON.stringify({native:NATIVE, fs:!!FS, geo:!!GEO, speech:!!SPEECH, share:!!SHARE, register:!!REGISTER, welcome:!!document.querySelector('#wLoad'), mapButton:document.querySelector('#layerBtn').textContent, offlineMap:!!layers.offline, size:[innerWidth,innerHeight]})")

hunt = {"format": "hunt-editor/1", "title": "CI test hunt", "intro": "Test", "builtAt": 1,
        "sections": [{"name": "Birgu", "code": "B", "label": "Section A"}, {"name": "Cospicua", "code": "C", "label": "Section B"},
                     {"name": "Senglea", "code": "S", "label": "Section C"}, {"name": "Anywhere", "code": "P", "label": "Photo tasks"}],
        "items": [{"id": "B-clue-01", "type": "clue", "section": "Birgu", "number": 1, "text": "Test clue one\nSecond line", "answer": "Alpha", "points": "10"},
                  {"id": "S-clue-01", "type": "clue", "section": "Senglea", "number": 1, "text": "Test clue two", "answer": "Beta", "points": "10"}],
        "refPhotos": {}}
for it in hunt["items"]:
    it["orig"] = {"text": it["text"], "answer": it["answer"], "points": it["points"]}
check("load hunt", f"importData({json.dumps(hunt)}, 'ci-test', {{quiet:true}}).then(() => liveItems().length + ' items loaded')")
check("location", "new Promise(r => setTimeout(() => r(JSON.stringify(S.me || 'no fix yet') + ' | chip: ' + document.querySelector('#locChip').textContent), 12000))", 30)
check("open item + pin + edit", """(async () => { openItem('B-clue-01', false);
  const it = S.items.get('B-clue-01'); const c = S.me || map.getCenter(); setPin(it, c.lat, c.lng, S.me ? S.me.acc : null, 'me');
  it.status = 'ok'; it.notes = 'checked in CI'; touch(it, 0); renderDetail(); await new Promise(r => setTimeout(r, 800));
  return JSON.stringify({status: it.status, lat: it.lat, notes: it.notes}); })()""")
shot("2-item-open")
check("save version", "saveVersion('manual', {quiet:true}).then(v => v.name + ' -> ' + v.where + ' (' + v.text.length + ' chars)')")
check("auto version", "(async () => { S.meta.lastChange = now(); S.meta.lastAutoVersion = 0; S.meta.lastBackup = 0; await autoVersion(); return (S.meta.versions || []).map(v => v.name).join(', '); })()")
check("list versions", "listTabletVersions().then(f => JSON.stringify(f.map(x => [x.name, x.dir, x.size])))")
check("read back version", """(async () => { const f = (await listTabletVersions()).find(x => !/-auto/.test(x.name));
  const r = await FS.readFile({path: 'HuntEditor/' + f.name, directory: f.dir, encoding: 'utf8'});
  const d = JSON.parse(r.data); const it = d.items.find(i => i.id === 'B-clue-01');
  return f.name + ': ' + d.items.length + ' items, B1 status=' + it.status + ', notes=' + it.notes + ', pinned=' + (it.lat != null); })()""")
check("csv export file", "writeTabletFile('ci-test.csv', 'a,b\\n1,2', 'exports').then(r => JSON.stringify({where: r.where, dir: r.dir}))")
check("speech recogniser", "SPEECH.available().then(r => JSON.stringify(r)).catch(e => 'ERR ' + (e.message || e))")
check("offline map", "setLayer('offline').then(() => new Promise(r => setTimeout(() => r('layer=' + S.layer + ', drawn tiles=' + document.querySelectorAll('.leaflet-tile-loaded, canvas.leaflet-tile').length), 6000)))", 30)
ev("closeDetail(); map.setView([35.8885, 14.5195], 16); 'ok'")
time.sleep(5)
shot("3-offline-map")
check("upload button without settings", "(async () => { await updateCloudChip(); return 'cloud chip visible=' + (document.querySelector('#cloudChip').style.display !== 'none'); })()")
check("menu opens", "(() => { menu(); const n = document.querySelectorAll('#modalBox .menu button').length; closeModal(); return n + ' menu items'; })()")
check("js errors so far", "JSON.stringify(window.__errs || [])")
json.dump(report, open(f"{out}/report.json", "w"), indent=2)
print("done")
