"""App 2 durum akışı + kilometre taşı testi.  FARMATEK_APP=2 API_KEY=... python akis_testi2.py <proje_id> [hazirla|kilit|kt]"""
import sys, time
from zincir_testi2 import *

def gorevler_wbs(pid):
    return {int(g.get("WBS No") or 0): g for g in proje_kayitlari(G, pid)}

def durum(gid, label):
    c.put(f"{API}/Data/UpdatePartial", {str(fid(G, "Durum")): label}, {"listId": list_id(G), "id": gid})

def bekle(fn, aciklama, sure=95):
    t0 = time.time()
    while time.time() - t0 < sure:
        r = fn()
        if r: print(f"  ✅ {aciklama} ({int(time.time()-t0)} sn)", flush=True); return r
        time.sleep(5)
    print(f"  ❌ {aciklama} ({sure} sn içinde olmadı)", flush=True)

d = lambda g: (g.get("Durum") or {}).get("label")

if __name__ == "__main__":
    pid, adim = sys.argv[1], sys.argv[2]
    if adim == "hazirla":
        me = {"id": "158776"}
        for g in proje_kayitlari(G, pid):
            c.put(f"{API}/Data/UpdatePartial", {str(fid(G, "Sorumlu")): me, str(fid(G, "Onaylayıcı")): me}, {"listId": list_id(G), "id": g["_id"]})
        print("sorumlu/onaylayıcı → Yalçın")
    if adim == "kilit":
        gs = gorevler_wbs(pid)
        print("1) Öncülü açık WBS 3 başlatılıyor")
        durum(gs[3]["_id"], "Devam Ediyor")
        bekle(lambda: d(gorevler_wbs(pid)[3]) == "Başlamadı", "kilit: WBS 3 Başlamadı'ya geri alındı")
    if adim == "kt":
        gs = gorevler_wbs(pid)
        print("2) WBS 2 (Proje Duyurusu) tamamlanıyor")
        durum(gs[2]["_id"], "Tamamlandı")
        kt = lambda: next(k for k in proje_kayitlari(KT, pid) if k["Kilometre Taşı"] == "Proje Başlatıldı")
        r = bekle(lambda: (kt().get("KT Durumu") or {}).get("label") == "Ulaşıldı" and kt(), "KT 'Proje Başlatıldı' → Ulaşıldı")
        if r: print("     gerçekleşen tarih:", r.get("Gerçekleşen Tarih"))
        bekle(lambda: all(d(gorevler_wbs(pid)[n]) == "Başlayabilir" for n in (3, 4, 5, 6, 7, 8, 11)), "ardıllar 3–8, 11 Başlayabilir")
