"""Görev durum akışının uçtan uca testi (A3–A6): öncül kilidi, kapanış, ardılları açma, onay.

  API_KEY=... python akis_testi.py <proje_id>

Test projesinde Sorumlu/Onaylayıcı önceden API kullanıcısına çevrilmiş olmalı (bildirim başkasına gitmesin).
"""
import sys
import time

from farmatek_ileri import *  # noqa: F401,F403
from dogrula import gorevler

DUR, ONAY = None, None


def by_wbs(pid):
    return {int(g.get("WBS No") or 0): g for g in gorevler(pid)}


def durum_yaz(gid, label):
    c.put(f"{API}/Data/UpdatePartial", {str(fid(G, "Durum")): opt(G, "Durum", label)},
          {"listId": list_id(G), "id": gid})


def bekle(pid, kosul, aciklama, sure=120):
    t0 = time.time()
    while time.time() - t0 < sure:
        gs = by_wbs(pid)
        if kosul(gs):
            print(f"  ✅ {aciklama} ({int(time.time() - t0)} sn)")
            return gs
        time.sleep(6)
    print(f"  ❌ {aciklama} — {sure} sn içinde gerçekleşmedi")
    return by_wbs(pid)


def d(g):
    return (g.get("Durum") or {}).get("label")


def main(pid):
    gs = by_wbs(pid)
    print("1) Öncülü açık görevi başlatma denemesi (WBS 2, öncül 1 açık)")
    durum_yaz(gs[2]["_id"], "Devam Ediyor")
    bekle(pid, lambda g: d(g[2]) == "Başlamadı", "WBS 2 kilit nedeniyle 'Başlamadı'ya geri alındı")

    print("2) Kilometre taşı WBS 1 tamamlanır → ardılı WBS 2 'Başlayabilir' olmalı")
    durum_yaz(gs[1]["_id"], "Tamamlandı")
    gs = bekle(pid, lambda g: d(g[2]) == "Başlayabilir", "WBS 2 Başlayabilir")
    print(f"     WBS 1 Kapalı={gs[1].get('Kapalı')} %={gs[1].get('% Tamamlanma')} "
          f"Gerçekleşen Bitiş={gs[1].get('Gerçekleşen Bitiş')}")

    print("3) WBS 2 başlar ve tamamlanır → 3–8 ve 11 'Başlayabilir'")
    durum_yaz(gs[2]["_id"], "Devam Ediyor")
    gs = bekle(pid, lambda g: d(g[2]) == "Devam Ediyor" and g[2].get("Gerçekleşen Başlangıç"),
               "WBS 2 Devam Ediyor + Gerçekleşen Başlangıç dolu")
    durum_yaz(gs[2]["_id"], "Tamamlandı")
    bekle(pid, lambda g: all(d(g[n]) == "Başlayabilir" for n in (3, 4, 5, 6, 7, 8, 11)),
          "WBS 3–8, 11 Başlayabilir", sure=180)

    print("4) Onay gerekli WBS 3: doğrudan 'Tamamlandı' → 'Onay Bekliyor'a çevrilmeli + onay talebi")
    gs = by_wbs(pid)
    durum_yaz(gs[3]["_id"], "Tamamlandı")
    gs = bekle(pid, lambda g: d(g[3]) == "Onay Bekliyor" and
               (g[3].get("Onay Durumu") or {}).get("label") == "Bekliyor", "WBS 3 Onay Bekliyor")

    r = c.post(f"{API}/Data/All", {"listId": list_id(G), "maxResultCount": 100, "skipCount": 0,
                                   "includeApprovalRequest": True})
    rec = next(x for x in r["items"] if x["_id"] == gs[3]["_id"])
    print("     onay alanları:", {k: v for k, v in rec.items() if "pprov" in k})
    return rec


def onay_talebi(gid):
    r = c.post(f"{API}/Data/All", {"listId": list_id(G), "maxResultCount": 200, "skipCount": 0,
                                   "includeApprovalRequest": True})
    rec = next(x for x in r["items"] if x["_id"] == gid)
    return (rec.get("approvalRequest") or {}).get("requestId")


def onay_testi(pid):
    gs = by_wbs(pid)
    g3 = gs[3]["_id"]
    print("5) WBS 3 yeniden onaya: Devam Ediyor → Onay Bekliyor")
    durum_yaz(g3, "Devam Ediyor")
    bekle(pid, lambda g: d(g[3]) == "Devam Ediyor", "WBS 3 Devam Ediyor")
    durum_yaz(g3, "Onay Bekliyor")
    bekle(pid, lambda g: (g[3].get("Onay Durumu") or {}).get("label") == "Bekliyor", "onay talebi açıldı")
    time.sleep(3)
    rid = onay_talebi(g3)
    print("     talep:", rid)
    c.post(f"{API}/AutomationApprovalRequest/Reject", None, {"approvalRequestId": rid,
                                                            "message": "Rapor eksik, ek analiz ekleyin"})
    bekle(pid, lambda g: d(g[3]) == "Revizyon Gerekli", "RED → Revizyon Gerekli")
    print("6) Revizyon sonrası tekrar onaya → ONAY")
    durum_yaz(g3, "Onay Bekliyor")
    bekle(pid, lambda g: (g[3].get("Onay Durumu") or {}).get("label") == "Bekliyor", "yeni onay talebi")
    time.sleep(3)
    rid = onay_talebi(g3)
    c.post(f"{API}/AutomationApprovalRequest/Approve", None, {"approvalRequestId": rid})
    bekle(pid, lambda g: d(g[3]) == "Tamamlandı" and g[3].get("Kapalı") == 1, "ONAY → Tamamlandı, Kapalı=1")
    bekle(pid, lambda g: all(d(g[n]) == "Başlayabilir" for n in (9, 10, 12, 13, 14)),
          "ardıllar 9,10,12,13,14 Başlayabilir", sure=150)
    from farmatek_seed import records
    fo = {str(f["id"]): f["name"] for f in fields("Onay Geçmişi")}
    for r in records("Onay Geçmişi"):
        x = {fo.get(k, k): v for k, v in r.items()}
        print("     Onay Geçmişi:", x.get("Başlık"), (x.get("Karar") or {}).get("label"),
              (x.get("Onaylayan") or {}).get("fullname"), x.get("Tarih"))


if __name__ == "__main__":
    main(sys.argv[1])
    onay_testi(sys.argv[1])
