"""Adı verilen kod önekiyle başlayan otomasyonları siler (yeniden kurmak için). Kullanım: ... KRN-04"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from wk import client
from workiom.state import AppState
c = client()
st = AppState("Performans Yönetimi")
r = c.get("/api/services/app/Automation/GetAll", {"appId": st.app_id})
for a in (r.get("items", r) if isinstance(r, dict) else r):
    if any(a["name"].startswith(p) for p in sys.argv[1:]):
        c.delete("/api/services/app/Automation/Delete", {"automationId": a["id"]})
        st._data.get("automations", {}).pop(a["name"], None) if hasattr(st, "_data") else None
        print("silindi", a["name"])
st.save()
