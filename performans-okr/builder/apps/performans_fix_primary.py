"""Her listenin otomatik birincil alanını (Ad / Başlık) spec'teki ad alanıyla birleştirir:
birincil alan yeniden adlandırılır, spec'in oluşturduğu kopya metin alanı silinir. İdempotent."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from wk import client

PRIMARY = {"Dönemler": "Dönem Adı", "Form Türleri": "Form Türü", "Hedef Türleri": "Hedef Türü",
           "Yetkinlikler": "Yetkinlik", "Performans Karneleri": "Karne", "KPI Hedefleri": "Hedef",
           "Yetkinlik Değerlendirmeleri": "Değerlendirme", "Objective'ler": "Objective",
           "Key Result'lar": "Key Result", "Check-in'ler": "Check-in"}

c = client()
sf = next((ROOT / "state").glob("performans*.json"))
st = json.loads(sf.read_text())
for ln, name in PRIMARY.items():
    lid = st["lists"][ln]["id"]
    fs = c.get("/api/services/app/Fields/GetAll", {"listId": lid, "withSystemFields": "true"})
    fs = fs.get("items", fs) if isinstance(fs, dict) else fs
    prim = next(f for f in fs if f.get("isPrimary"))
    dup = next((f for f in fs if f["name"] == name and not f.get("isPrimary")), None)
    if dup:
        c.delete("/api/services/app/Fields/Delete", {"listId": lid, "id": dup["id"]})
    if prim["name"] != name:
        body = {**prim, "name": name, "isRequired": False, "isVisible": True}
        c.put("/api/services/app/Fields/Update", body, {"listId": lid, "id": prim["id"]})
    st["lists"][ln].setdefault("fields", {})[name] = prim["id"]
    print(f"  {ln}: birincil = {name} ({prim['id']})" + (" · kopya silindi" if dup else ""))
sf.write_text(json.dumps(st, ensure_ascii=False, indent=2))
