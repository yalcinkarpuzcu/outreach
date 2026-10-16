"""Demo veri yardımcıları (seed ile aynı mantık + güncelleme/okuma)."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workiom.client import WorkiomClient
c = WorkiomClient((ROOT / ".env").read_text().split("=", 1)[1].strip())
OWNER = str(c.get("/api/services/app/Session/GetCurrentLoginInformations")["user"]["id"])
REG = {}
for sf in (ROOT / "state").glob("*.json"):
    for ln, ld in json.loads(sf.read_text()).get("lists", {}).items():
        REG[ln] = ld["id"]
_F = {}
def fields(l):
    if l not in _F: _F[l] = {f["name"]: f for f in c.get_all_fields(REG[l])}
    return _F[l]
def pid(l): return str(next(f for f in fields(l).values() if f.get("isPrimary"))["id"])
def recs(l): return c.get_all_records(REG[l])
def by_primary(l): p = pid(l); return {r.get(p): r["_id"] for r in recs(l)}
def val(l, k, v):
    f = fields(l)[k]; dt = f["dataType"]
    if dt in (4, 17):
        o = {x["label"]: x["id"] for x in f.get("staticListValues", [])}
        return [o[x] for x in v] if dt == 17 else o[v]
    if dt == 5:
        tgt = next(n for n, i in REG.items() if i == f["linkedListId"])
        if isinstance(v, str) and len(v) == 24 and all(ch in "0123456789abcdef" for ch in v):
            return [{"_id": v}]
        m = by_primary(tgt); vs = v if isinstance(v, list) else [v]
        return [{"_id": m[x]} for x in vs]
    if dt == 6: return {"id": OWNER} if v == "OWNER" else v
    return v
def payload(l, row): return {str(fields(l)[k]["id"]): val(l, k, v) for k, v in row.items()}
def create(l, row): return c.create_record(REG[l], payload(l, row))
def update(l, rid, row): return c.update_record(REG[l], rid, payload(l, row))
def get(l, r, k):
    v = r.get(str(fields(l)[k]["id"]))
    if isinstance(v, dict): return v.get("label") or v.get("fullname") or v.get("id")
    if isinstance(v, list): return [x.get("label") if isinstance(x, dict) else x for x in v]
    return v
def counts():
    return {l: len(recs(l)) for l in REG}
