"""
Ar-Ge Proje Yönetimi 2 — kütüphane seed'i (model 2: faz / kilometre taşı ayrı, görevlerde yalnızca görev).

  FARMATEK_APP=2 API_KEY=... python farmatek_seed2.py kutuphane

İsim bazlı idempotent (upsert). Kaynak: sablon_veri.model2().
"""
from __future__ import annotations

import os
import sys

assert os.environ.get("FARMATEK_APP") == "2", "FARMATEK_APP=2 ile çalıştırın"

from wk import *  # noqa: E402,F401,F403
from farmatek_seed import upsert, user, users, link, DEPT_KISI, DEPT_KOD, YALCIN  # noqa: E402
from sablon_veri import DEPARTMANLAR, REFERANS_TARIH, model2, tarih  # noqa: E402

K, FK, KTK = "Görev Kütüphanesi", "Faz Kütüphanesi", "Kilometre Taşı Kütüphanesi"


def kutuphane():
    M = model2()
    F = lambda ln, n: str(fid(ln, n))  # noqa: E731

    print("── Departmanlar")
    dept = {}
    for d in DEPARTMANLAR:
        yon, ony, ekip = DEPT_KISI[d]
        dept[d] = upsert("Departmanlar", "Departman", d, {
            F("Departmanlar", "Kod"): DEPT_KOD[d], F("Departmanlar", "Departman Yöneticisi"): user(yon),
            F("Departmanlar", "Onaylayıcı"): user(ony), F("Departmanlar", "Ekip Üyeleri"): users(ekip)})
    print(f"  ✅ {len(dept)} departman")

    print("── Proje Şablonları")
    aciklama = {"Yeni Ürün": "Yeni jenerik ürün geliştirme: API seçimi → formülasyon → validasyon → BE → ruhsat.",
                "Alternatif Kaynak": "Ruhsatlı ürün için alternatif API kaynağı: DMF ve referans ürün temini adımları yok."}
    son = {g["no"]: g["e"] for g in M["gorevler"]}
    sab = {}
    for s, nolar in M["sablonlar"].items():
        sab[s] = upsert("Proje Şablonları", "Şablon", s, {
            F("Proje Şablonları", "Açıklama"): aciklama[s], F("Proje Şablonları", "Aktif"): True,
            F("Proje Şablonları", "Toplam Süre (gün)"): max(son[n] for n in nolar)})
        print(f"  ✅ {s}")
    def sablonlari(nolar):
        return link(*[sab[s] for s, ns in M["sablonlar"].items() if any(n in ns for n in nolar)])

    print("── Faz Kütüphanesi")
    faz = {}
    for f in M["fazlar"]:
        nolar = [g["no"] for g in M["gorevler"] if g["faz"] == f["kod"]]
        faz[f["kod"]] = upsert(FK, "Faz", f["ad"], {
            F(FK, "Sıra"): f["sira"], F(FK, "Başlangıç Ofseti (gün)"): f["s"], F(FK, "Süre (gün)"): f["e"] - f["s"],
            F(FK, "Şablonlar"): sablonlari(nolar)})
    print(f"  ✅ {len(faz)} faz")

    print("── Kilometre Taşı Kütüphanesi")
    kt = {}
    for k in M["kt"]:
        kt[k["kod"]] = upsert(KTK, "Kilometre Taşı", k["ad"], {
            F(KTK, "Gün Ofseti"): k["gun"], F(KTK, "Kritik"): k["kritik"], F(KTK, "Faz"): link(faz[k["faz"]]),
            F(KTK, "Şablonlar"): sablonlari(k["bagli"]),
            F(KTK, "Açıklama"): "Bağlı görevlerin tamamı kapandığında ulaşılır."})
    print(f"  ✅ {len(kt)} kilometre taşı")

    print("── Görev Kütüphanesi")
    fk = fmap(K)
    yayinda = next(o["id"] for o in fk["Durum"]["staticListValues"] if o["label"] == "Yayında")
    ref = REFERANS_TARIH.isoformat()
    gid = {}
    for g in M["gorevler"]:
        kts = [kt[k["kod"]] for k in M["kt"] if g["no"] in k["bagli"]]
        gid[g["no"]] = upsert(K, "Görev Adı", g["ad"], {
            F(K, "WBS No"): g["no"], F(K, "Başlangıç"): tarih(g["s"]), F(K, "Bitiş"): tarih(g["e"]),
            F(K, "Referans Tarih"): ref, F(K, "Onay Gerekli"): g["onay"], F(K, "Varsayım"): g["vars"],
            F(K, "Durum"): yayinda, F(K, "Faz"): link(faz[g["faz"]]), F(K, "Kilometre Taşları"): link(*kts),
            F(K, "Şablonlar"): link(*[sab[s] for s, ns in M["sablonlar"].items() if g["no"] in ns]),
            F(K, "Sorumlu Departman"): link(dept[g["dep"]]), F(K, "Varsayılan Sorumlu"): user(DEPT_KISI[g["dep"]][0]),
        })
    print(f"  ✅ {len(gid)} görev")
    for g in M["gorevler"]:
        c.put(f"{API}/Data/UpdatePartial", {F(K, "Öncüller"): [{"_id": gid[p], "dependencyType": 1} for p in g["onc"]]},
              {"listId": list_id(K), "id": gid[g["no"]]})
    print("  ✅ öncüller (FS)")


if __name__ == "__main__":
    {"kutuphane": kutuphane}[sys.argv[1]]()
