"""6.7 Roller ve Yetkiler — 6 rol, uygulama bazlı erişim seviyesi.
Erişim: 0=Yok, 2=Okuma, 3=İçerik düzenleyici, 4=Sahip.
Demo: tüm rollere tenant sahibi eklenir (bildirimler görülebilsin); gerçek kullanıcılar
S1 yanıtıyla rollere atanır. Kayıt bazlı kısıtlar (kendi portföyü, kendi istasyonu) arayüzden."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workiom.client import WorkiomClient, WorkiomAPIError
c = WorkiomClient((ROOT / ".env").read_text().split("=", 1)[1].strip())

APPS = {}
for sf in (ROOT / "state").glob("*.json"):
    d = json.loads(sf.read_text()); APPS[d["app_name"]] = d["app_id"]
CRM, PRJ, HSP, URT, STN = "CRM", "Proje & Teklif", "Teknik Hesaplama", "Planlama & Üretim", "Satınalma & Stok"

ROLES = {
    "Yönetici":               {CRM: 4, PRJ: 4, HSP: 4, URT: 4, STN: 4},
    "Satış Temsilcisi":       {CRM: 3, PRJ: 3, HSP: 3, URT: 2},
    "İmalat Planlama":        {CRM: 3, PRJ: 2, HSP: 3, URT: 3, STN: 3},
    "Satınalma":              {CRM: 3, PRJ: 2, STN: 3},
    "İmalat Şefi / Operatör": {CRM: 3, HSP: 2, URT: 3},
    "Montaj Ekibi":           {CRM: 3, URT: 3},
}
OWNER = c.get("/api/services/app/Session/GetCurrentLoginInformations")["user"]["id"]
existing = {r["displayName"]: r["id"] for r in c.get("/api/services/app/Role/GetRoles")["items"]}
out = {}
for name, access in ROLES.items():
    body = {"role": {"displayName": name, **({"id": existing[name]} if name in existing else {})},
            "teamUsersChanged": True, "roleUserIds": [OWNER],
            "teamPermissionTreeChanged": True,
            "permissionTree": {"inviteMembers": False, "createApp": False, "createDashbaord": False,
                               "useAIMila": True,
                               "apps": [{"appId": APPS[a], "accessLevel": lvl, "reportsAccess": 1,
                                         "formsAccess": 1, "listsPermissions": [],
                                         "listWithPreventViewCreationAccess": []}
                                        for a, lvl in access.items()],
                               "dashboards": [], "adminUserIds": []},
            "teamAdminUserIdsChanged": False, "adminUserIds": []}
    try:
        c.post("/api/services/app/Role/CreateOrUpdateRole", body)
        print(f"  ✅ rol: {name}")
    except WorkiomAPIError as e:
        print(f"  ⚠️  rol {name}: {e.message} {e.details[:200]}")
roles = {r["displayName"]: r["id"] for r in c.get("/api/services/app/Role/GetRoles")["items"]}
(ROOT / "roles.json").write_text(json.dumps({k: roles[k] for k in ROLES if k in roles},
                                                      ensure_ascii=False, indent=1))
print(json.dumps({k: roles.get(k) for k in ROLES}, ensure_ascii=False))
