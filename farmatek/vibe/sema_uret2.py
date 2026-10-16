"""proje-yonetimi vibe app'i için canlı şemadan schema.js üretir (FARMATEK_APP=2)."""
import json, os
os.environ["FARMATEK_APP"] = "2"
from wk import c, API, APP_ID, list_id, fields

KISA = {"P": "Projeler", "F": "Fazlar", "G": "Görevler", "K": "Kilometre Taşları", "O": "Onay Geçmişi",
        "B": "Baseline Kalemleri", "BL": "Baseline'lar", "D": "Departmanlar", "S": "Proje Şablonları", "GK": "Görev Kütüphanesi",
        "FK": "Faz Kütüphanesi", "KK": "Kilometre Taşı Kütüphanesi"}
out = {"APP": {"id": APP_ID, "name": "Proje Yönetimi"}}
for k, ln in KISA.items():
    fs = {}
    for f in fields(ln):
        if f.get("isSystemField") or f["name"] in ("Watchers",):
            continue
        d = {"id": f["id"], "t": f["dataType"]}
        if f.get("isRequired"): d["req"] = True
        if f.get("isPrimaryRecordName"): d["pri"] = True
        if f.get("isComputed") or f.get("isRollup") or f.get("isLookup") or f.get("isReadOnly"): d["ro"] = True
        if f.get("staticListValues"): d["opts"] = [o["label"] for o in f["staticListValues"]]
        if f.get("defaultValue"): d["def"] = f["defaultValue"]
        fs[f["name"]] = d
    out[k] = {"id": list_id(ln), "name": ln, "f": fs}
txt = (
    "/* Proje Yönetimi — canlı şema keşfinden üretildi (farmatek.workiom.com). Elle düzenlemeyin; sema_uret2.py ile yenileyin. */\n"
    "const SCHEMA = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
for d in ("proje-yonetimi", "proje-merkezi"):
    open(f"vibe/{d}/schema.js", "w").write(txt)
print({k: len(v["f"]) for k, v in out.items() if k != "APP"})
print(out["G"]["f"]["Öncüller"], out["G"]["f"]["Durum"]["id"], out["K"]["f"]["Bağlı Görevler"])
