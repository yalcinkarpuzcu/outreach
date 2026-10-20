"""Performans Yönetimi — roller ve yetkiler (TASARIM.md bölüm 6).

    python3 apps/performans_roles.py

Rol başına: uygulama erişimi (1 = özel), liste erişimi, ekleme / silme / toplu güncelleme / export,
kayıt filtresi ("Kendim" = oturumdaki kullanıcı, kullanıcı alanında) ve alan izinleri
(0 = Görmez, 1 = Salt okunur, 2 = Düzenler). Belirtilmeyen alanlar listenin varsayılan iznini alır.
Koşullu yetki grupları (ör. Kilitli = 1 iken salt okunur) API'de kurulmadı → arayüzden (bkz. TASARIM.md).
Roller kullanıcısız oluşturulur; gerçek kullanıcılar arayüzden atanır.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from wk import client  # noqa: E402
from workiom.client import WorkiomAPIError  # noqa: E402

c = client()
ST = json.loads(next((ROOT / "state").glob("performans*.json")).read_text())
APP = ST["app_id"]
REG = {ln: ld["id"] for ln, ld in ST["lists"].items() if ld["id"] != "cc279e0f-af5a-4ff8-986f-a31793432ddf"}
_F: dict[str, list] = {}

GORMEZ, OKUR, DUZENLER = 0, 1, 2
KENDIM = [{"id": "-2", "label": "Kendim"}]


def fields(lst):
    if lst not in _F:
        r = c.get("/api/services/app/Fields/GetAll", {"listId": REG[lst], "withSystemFields": "true"})
        _F[lst] = r.get("items", r) if isinstance(r, dict) else r
    return _F[lst]


def fid(lst, name):
    return next(f["id"] for f in fields(lst) if f["name"] == name)


def liste(lst, varsayilan, ekle=False, sil=False, toplu=False, export=False, kendim=None, alan=None):
    """varsayilan: tüm alanlar için izin; alan: {ad: izin} istisnalar; kendim: kayıt filtresi alanı."""
    perms = {str(f["id"]): varsayilan for f in fields(lst)}
    for ad, izin in (alan or {}).items():
        perms[str(fid(lst, ad))] = izin
    filters = []
    if kendim:
        filters = [{"id": 0, "groupId": 0, "fieldId": fid(lst, kendim), "operator": 3, "collectionOperator": 0,
                    "value": KENDIM, "stringValue": json.dumps(KENDIM, ensure_ascii=False),
                    "value2": None, "stringValue2": ""}]
    return {"listId": REG[lst], "listAccess": 1, "createRecords": ekle, "deleteRecords": sil,
            "bulkUpdateRecords": toplu, "export": export, "import": False, "preventViewCreation": True,
            "filters": filters, "filtersCache": [], "fieldsPermissions": perms, "permissionGroups": []}


K, H, YD = "Performans Karneleri", "KPI Hedefleri", "Yetkinlik Değerlendirmeleri"
O, KR, CI = "Objective'ler", "Key Result'lar", "Check-in'ler"
TANIM = ["Dönemler", "Form Türleri", "Hedef Türleri", "Yetkinlikler"]
KALIBRASYON = {"Kalibre Grup": GORMEZ, "Kalibrasyon Notu": GORMEZ}
OKR_LISTELERI = lambda ekle_o: [  # noqa: E731
    liste(O, DUZENLER, ekle=ekle_o), liste(KR, DUZENLER, ekle=True), liste(CI, DUZENLER, ekle=True)]

ROLLER = {
    # İK / Performans Yöneticisi: uygulamanın sahibi (tüm listeler, kalibrasyon, tanımlar)
    "Performans – İK": None,
    "Performans – Üst Yönetim": [
        *[liste(t, OKUR) for t in TANIM],
        liste(K, OKUR, export=True), liste(H, OKUR, export=True), liste(YD, OKUR),
        *OKR_LISTELERI(True),
    ],
    "Performans – Yönetici": [
        *[liste(t, OKUR) for t in TANIM],
        liste(K, OKUR, kendim="Yönetici (kullanıcı)", export=True,
              alan={"Durum": DUZENLER, **KALIBRASYON}),
        liste(H, DUZENLER, ekle=True, sil=True, kendim="Karne Yöneticisi",
              alan={"Kilitli": OKUR, "Karne": OKUR}),
        liste(YD, OKUR, kendim="Karne Yöneticisi", alan={"Puan (1–5)": DUZENLER, "Açıklama": DUZENLER}),
        *OKR_LISTELERI(True),
    ],
    "Performans – Çalışan": [
        liste("Yetkinlikler", OKUR),
        liste(K, OKUR, kendim="Çalışan (kullanıcı)",
              alan={"Durum": DUZENLER, **KALIBRASYON, "Yetkinlik Skoru": GORMEZ}),
        liste(H, DUZENLER, ekle=True, kendim="Karne Sahibi",
              alan={"Kilitli": OKUR, "Karne": OKUR}),
        *OKR_LISTELERI(True),
    ],
}

if __name__ == "__main__":
    existing = {r["displayName"]: r["id"] for r in c.get("/api/services/app/Role/GetRoles")["items"]}
    for ad, listeler in ROLLER.items():
        app = {"appId": APP, "accessLevel": 4 if listeler is None else 1, "reportsAccess": 1,
               "formsAccess": 1, "listsPermissions": listeler or [], "listWithPreventViewCreationAccess": []}
        body = {"role": {"displayName": ad, **({"id": existing[ad]} if ad in existing else {})},
                "teamUsersChanged": False, "roleUserIds": [],
                "teamPermissionTreeChanged": True,
                "permissionTree": {"inviteMembers": False, "createApp": False, "createDashbaord": False,
                                   "useAIMila": True, "apps": [app], "dashboards": [], "adminUserIds": []},
                "teamAdminUserIdsChanged": False, "adminUserIds": []}
        try:
            c.post("/api/services/app/Role/CreateOrUpdateRole", body)
            print(f"  ✅ {ad}")
        except WorkiomAPIError as e:
            print(f"  ⚠️  {ad}: {e.message} {e.details[:300]}")
    roles = {r["displayName"]: r["id"] for r in c.get("/api/services/app/Role/GetRoles")["items"]}
    (ROOT / "roles.json").write_text(json.dumps({k: roles[k] for k in ROLLER if k in roles},
                                                ensure_ascii=False, indent=1))
    print(json.dumps({k: roles.get(k) for k in ROLLER}, ensure_ascii=False))
