"""
Farmatek Ar-Ge — referans verisi + görev kütüphanesi seed'i (farmatek_ileri.py yapi'dan SONRA).

  API_KEY=... python farmatek_seed.py kutuphane   # departman, şablon, 6 faz + 38 kalem (tarih, öncül, hiyerarşi)

İsim bazlı idempotent: var olan kayıt güncellenir, tekrar oluşturulmaz.
"""
from __future__ import annotations

import sys

from wk import *  # noqa: F401,F403
from sablon_veri import (DEPARTMANLAR, FAZLAR, GOREVLER, SABLONLAR, REFERANS_TARIH,
                         hesapla, faz_araliklari, tarih)

# Demo kullanıcıları — yalnızca Workiom ekibi (müşteri kullanıcılarına bildirim gitmesin)
YALCIN, UGUR, DENIZ, GOZDE = 158776, 160380, 160378, 160155
DEPT_KISI = {   # departman: (yönetici, onaylayıcı, ekip)
    "Proje Yönetimi":            (YALCIN, YALCIN, [YALCIN]),
    "Formülasyon Geliştirme":    (DENIZ,  UGUR,   [DENIZ]),
    "Analitik Metot Geliştirme": (GOZDE,  UGUR,   [GOZDE]),
    "Ruhsat":                    (UGUR,   YALCIN, [UGUR]),
    "Kalite Güvence":            (UGUR,   UGUR,   [UGUR]),
}
DEPT_KOD = {"Proje Yönetimi": "PM", "Formülasyon Geliştirme": "FOR", "Analitik Metot Geliştirme": "ANA",
            "Ruhsat": "RUH", "Kalite Güvence": "KG"}


def user(uid):
    return {"id": str(uid)}


def users(uids):
    return [user(u) for u in uids]


def link(*ids):
    return [{"_id": i} for i in ids]


def records(list_name):
    out, skip = [], 0
    while True:
        r = c.post(f"{API}/Data/All", {"listId": list_id(list_name), "maxResultCount": 500, "skipCount": skip})
        out += r["items"]
        if len(out) >= r["totalCount"] or not r["items"]:
            return out
        skip += 500


def upsert(list_name, key_field, key, payload):
    """key_field adına göre bul → güncelle, yoksa oluştur. _id döner."""
    kid = str(fid(list_name, key_field))
    cache = _cache.setdefault(list_name, {r.get(kid): r["_id"] for r in records(list_name)})
    payload = {kid: key, **payload}
    if key in cache:
        c.put(f"{API}/Data/UpdatePartial", payload, {"listId": list_id(list_name), "id": cache[key]})
        return cache[key]
    rid = c.post(f"{API}/Data/Create", payload, {"listId": list_id(list_name)})["_id"]
    cache[key] = rid
    return rid


_cache: dict = {}


def kutuphane():
    fd, fs, fk = fmap("Departmanlar"), fmap("Proje Şablonları"), fmap("Görev Kütüphanesi")
    F = lambda fm, n: str(fm[n]["id"])  # noqa: E731

    print("── Departmanlar")
    dept = {}
    for d in DEPARTMANLAR:
        yon, ony, ekip = DEPT_KISI[d]
        dept[d] = upsert("Departmanlar", "Departman", d, {
            F(fd, "Kod"): DEPT_KOD[d], F(fd, "Departman Yöneticisi"): user(yon),
            F(fd, "Onaylayıcı"): user(ony), F(fd, "Ekip Üyeleri"): users(ekip)})
        print(f"  ✅ {d}")

    print("── Proje Şablonları")
    sab = {}
    aciklama = {"Yeni Ürün": "Yeni jenerik ürün geliştirme: API seçimi → formülasyon → validasyon → BE → ruhsat.",
                "Alternatif Kaynak": "Ruhsatlı ürün için alternatif API kaynağı: DMF ve referans ürün temini adımları yok."}
    for s in SABLONLAR:
        sab[s] = upsert("Proje Şablonları", "Şablon", s, {
            F(fs, "Açıklama"): aciklama[s], F(fs, "Aktif"): True,
            F(fs, "Toplam Süre (gün)"): max(e for _, e in hesapla(SABLONLAR[s]).values())})
        print(f"  ✅ {s}")

    adlar = [f[1] for f in FAZLAR] + [g[2] for g in GOREVLER]
    assert len(adlar) == len(set(adlar)), "kütüphane adları benzersiz olmalı (upsert anahtarı)"
    tum = sorted({n for ns in SABLONLAR.values() for n in ns})
    ofs = hesapla(tum)
    faz_ofs = faz_araliklari(tum, ofs)
    tur = {o["label"]: o["id"] for o in fk["Tür"]["staticListValues"]}
    yayinda = next(o["id"] for o in fk["Durum"]["staticListValues"] if o["label"] == "Yayında")
    ref = REFERANS_TARIH.isoformat()

    print("── Fazlar")
    faz_id = {}
    for kod, ad, sira in FAZLAR:
        s, e = faz_ofs[kod]
        sablonlar = [sab[t] for t, ns in SABLONLAR.items()
                     if any(g[0] in ns for g in GOREVLER if g[1] == kod)]
        faz_id[kod] = upsert("Görev Kütüphanesi", "Görev Adı", ad, {
            F(fk, "WBS No"): sira * 100, F(fk, "Tür"): tur["Faz"],
            F(fk, "Başlangıç"): tarih(s), F(fk, "Bitiş"): tarih(e), F(fk, "Referans Tarih"): ref,
            F(fk, "Durum"): yayinda, F(fk, "Şablonlar"): link(*sablonlar),
            F(fk, "Kilometre Taşı"): False, F(fk, "Onay Gerekli"): False, F(fk, "Varsayım"): False,
            F(fk, "Sorumlu Departman"): [], F(fk, "Üst Öğe"): [], F(fk, "Öncüller"): [],
            F(fk, "Varsayılan Sorumlu"): user(YALCIN),
        })
        print(f"  ✅ {ad}")

    print("── Görevler")
    gid = {}
    for no, faz, ad, sure, onc, dep, kt, onay, vars_ in GOREVLER:
        s, e = ofs[no]
        sablonlar = [sab[t] for t, ns in SABLONLAR.items() if no in ns]
        gid[no] = upsert("Görev Kütüphanesi", "Görev Adı", ad, {
            F(fk, "WBS No"): no, F(fk, "Tür"): tur["Kilometre Taşı" if kt else "Görev"],
            F(fk, "Başlangıç"): tarih(s), F(fk, "Bitiş"): tarih(e), F(fk, "Referans Tarih"): ref,
            F(fk, "Kilometre Taşı"): kt, F(fk, "Onay Gerekli"): onay, F(fk, "Varsayım"): vars_,
            F(fk, "Durum"): yayinda, F(fk, "Şablonlar"): link(*sablonlar),
            F(fk, "Sorumlu Departman"): link(dept[dep]), F(fk, "Üst Öğe"): link(faz_id[faz]),
            F(fk, "Varsayılan Sorumlu"): user(DEPT_KISI[dep][0]),
        })
    print(f"  ✅ {len(gid)} kalem")

    print("── Öncüller (native bağımlılık, FS)")
    for no, faz, ad, sure, onc, *_ in GOREVLER:
        c.put(f"{API}/Data/UpdatePartial",
              {F(fk, "Öncüller"): [{"_id": gid[p], "dependencyType": 1} for p in onc]},
              {"listId": list_id("Görev Kütüphanesi"), "id": gid[no]})
    print("  ✅ öncüller yazıldı")


if __name__ == "__main__":
    {"kutuphane": kutuphane}[sys.argv[1]]()
