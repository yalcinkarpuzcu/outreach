"""App 2: yeni proje → fazlar, görevler (faza bağlı), öncüller, kilometre taşları zincirini doğrular.
  FARMATEK_APP=2 API_KEY=... python zincir_testi2.py [olustur|kontrol <proje_id>]"""
import sys, time
from wk import *
from farmatek_seed import records

P, G, FZ, KT = "Projeler", "Görevler", "Fazlar", "Kilometre Taşları"


def olustur(ad="TEST – Zincir Doğrulama", sablon="Yeni Ürün", bas="2026-11-02"):
    sab = {x[str(fid("Proje Şablonları", "Şablon"))]: x["_id"] for x in records("Proje Şablonları")}
    rid = c.post(f"{API}/Data/Create", {str(fid(P, "Proje Adı")): ad, str(fid(P, "Başlangıç Tarihi")): bas,
                 str(fid(P, "Şablon")): [{"_id": sab[sablon]}], str(fid(P, "Proje Yöneticisi")): {"id": "158776"}}, {"listId": list_id(P)})["_id"]
    print("proje", rid, flush=True)
    return rid


def proje_kayitlari(ln, pid):
    fm = {str(f["id"]): f["name"] for f in fields(ln)}
    return [{fm.get(k, k): v for k, v in r.items()} for r in records(ln) if any(x["_id"] == pid for x in (r.get(str(fid(ln, "Proje"))) or []))]


def kontrol(pid, detay=False):
    p = c.get(f"{API}/Data/Get", {"listId": list_id(P), "id": pid})
    plan = (p.get(str(fid(P, "Plan Durumu"))) or {}).get("label")
    fz, gs, kts = proje_kayitlari(FZ, pid), proje_kayitlari(G, pid), proje_kayitlari(KT, pid)
    ids = {g["_id"] for g in gs}
    sizinti = sum(1 for g in gs for o in (g.get("Öncüller") or []) if o["_id"] not in ids)
    fz_ids = {f["_id"] for f in fz}
    yanlis_faz = sum(1 for g in gs if not g.get("Faz") or g["Faz"][0]["_id"] not in fz_ids)
    print(f"plan={plan} faz={len(fz)} görev={len(gs)} öncüllü={sum(1 for g in gs if g.get('Öncüller'))} "
          f"KT={len(kts)} bağlı-KT={sum(1 for k in kts if k.get('Bağlı Görevler'))} sızıntı={sizinti} fazsız/yanlış-faz={yanlis_faz}", flush=True)
    if detay:
        for f in sorted(fz, key=lambda x: x.get("Sıra") or 0):
            print(f"  FAZ {f['Faz']:<22} {(f.get('Başlangıç') or '')[:10]} → {(f.get('Bitiş') or '')[:10]}  görev={sum(1 for g in gs if g.get('Faz') and g['Faz'][0]['_id']==f['_id'])}")
        for k in kts:
            print(f"  KT  {k['Kilometre Taşı']:<24} hedef {(k.get('Hedef Tarih') or '')[:10]}  faz={[x['label'] for x in k.get('Faz') or []]}  bağlı={[x['label'][:16] for x in k.get('Bağlı Görevler') or []]}  açık={k.get('Açık Bağlı Görev')}")
    return plan, len(fz), len(gs), len(kts)


if __name__ == "__main__":
    if sys.argv[1] == "olustur":
        open("/tmp/claude-0/-home-user-outreach/c65e3a42-4be9-5780-8f1b-b4e75f33c0ab/scratchpad/test2", "w").write(olustur())
    else:
        kontrol(sys.argv[2], detay=len(sys.argv) > 3)
