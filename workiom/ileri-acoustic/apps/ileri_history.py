"""Otomasyon geçmişi: python3 apps/ileri_history.py <Uygulama> [otomasyon_id] [n]"""
import sys, json; sys.path.insert(0, '.')
from apps.ileri_demo_lib import c
from workiom.state import AppState
st = AppState(sys.argv[1]); aid = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else None
n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
names = {a["id"]: a["name"] for a in c.get_all_automations(st.app_id)}
res = c.post("/api/services/app/AutomationHistory/GetAllPaged",
             {"sortByDateDescending": True, "skipCount": 0, "maxResultCount": n, "automationId": aid},
             params={"appId": st.app_id})
items = res.get("items", res) if isinstance(res, dict) else res
for h in items:
    print(names.get(h["automationId"]), h.get("status"), h.get("failureReason"))
    for l in (h.get("executionLog") or [])[:12]:
        print("    ", json.dumps(l, ensure_ascii=False)[:300])
