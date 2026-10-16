"""73 otomasyonu tetikleyici listenin uygulamasında kurar (idempotent: aynı ad varsa atlar).
Kullanım: python3 apps/ileri_build_automations.py [KOD_ÖNEKİ ...]"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workiom.client import WorkiomClient
from workiom.state import AppState
from workiom.multi_automation import MultiAppAutomationBuilder
from apps.ileri_automations import BY_APP

c = WorkiomClient((ROOT / ".env").read_text().split("=", 1)[1].strip())
roles = json.loads((ROOT / "roles.json").read_text())
only = sys.argv[1:]

# liste → uygulama (tetikleyicinin bulunduğu uygulama)
list_app = {}
for sf in (ROOT / "state").glob("*.json"):
    d = json.loads(sf.read_text())
    for ln in d.get("lists", {}):
        list_app[ln] = d["app_name"]

by_target: dict[str, list] = {}
for app, autos in BY_APP.items():
    for a in autos:
        if only and not any(a["name"].startswith(p) for p in only):
            continue
        lst = a["trigger"].get("list")
        by_target.setdefault(list_app[lst] if lst else app, []).append(a)

total = 0
for app, autos in by_target.items():
    st = AppState(app)
    print(f"\n⚡ {app} — {len(autos)} otomasyon")
    ab = MultiAppAutomationBuilder(c, st, role_ids=roles)
    ab.build_all(st.app_id, autos)
    total += len(autos)
print(f"\nToplam: {total}")
