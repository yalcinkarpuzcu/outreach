"""
Proje Yönetimi (app 2) — baseline katmanı: Proje → Baseline'lar → Baseline Kalemleri.

  FARMATEK_APP=2 API_KEY=... python farmatek_baseline2.py yapi      # liste + alanlar
  FARMATEK_APP=2 API_KEY=... python farmatek_baseline2.py tasima    # mevcut kalemleri BL kayıtlarına bağla (otomasyondan ÖNCE)
  FARMATEK_APP=2 API_KEY=... python farmatek_baseline2.py otomasyon # A9 yeniden: BL kaydı + kalemler (görev / faz / KT)

Not: bir otomasyon çalıştırmasında yalnızca ilk "kayıt bul" döngüsü çalışır → görev, faz ve KT kalemleri
Baseline kaydı oluşunca tetiklenen üç ayrı otomasyonla yazılır.
"""
from __future__ import annotations

import json
import os
import sys

assert os.environ.get("FARMATEK_APP") == "2", "FARMATEK_APP=2 ile çalıştırın"

from wk import *  # noqa: E402,F401,F403
from wk import _FIELDS  # noqa: E402
from farmatek_ileri import (  # noqa: E402
    ref, is_, src, src_id, val, formula, m, find, flt, create, update, cond, notify_field, ensure_automation, t_created, t_updated)

P, G, FZ, KT = "Projeler", "Görevler", "Fazlar", "Kilometre Taşları"
BL, KAL, ESKI = "Baseline'lar", "Baseline Kalemleri", "Baseline Arşivi"
TURLER = ["Görev", "Faz", "Kilometre Taşı"]


def _state_save(s):
    json.dump(s, open(STATE_PATH, "w"), ensure_ascii=False, indent=2)


def _register(name, lid):
    s = state()
    flds = c.get(f"{API}/Fields/GetAll", {"listId": lid, "withSystemFields": "true"})["items"]
    s["lists"].setdefault(name, {"views": {}, "forms": {}, "layouts": {}})
    s["lists"][name]["id"] = lid
    s["lists"][name]["fields"] = {f["name"]: f["id"] for f in flds}
    _state_save(s)
    _FIELDS.pop(name, None)


def yapi():
    s = state()
    # 1) Baseline Arşivi → Baseline Kalemleri (ad değişikliği; kimlik aynı)
    if ESKI in s["lists"] and KAL not in s["lists"]:
        lid = s["lists"][ESKI]["id"]
        L = c.get(f"{API}/Lists/Get", {"id": lid})
        body = {k: v for k, v in L.items() if k not in ("views", "defaultView", "fields")}
        body["name"] = KAL
        c.put(f"{API}/Lists/Update", body, {"id": lid})
        s["lists"][KAL] = s["lists"].pop(ESKI)
        _state_save(s)
        print(f"  ✅ liste adı: {ESKI} → {KAL}")
    # 2) Baseline'lar listesi
    if BL not in state()["lists"]:
        r = c.create_list(APP_ID, BL, icon="far fa-layer-group", folder_id=state()["folders"]["Proje Yönetimi"], list_type=0)
        _register(BL, r["id"])
        print(f"  ✅ liste: {BL} ({r['id']})")
    prim = next(f for f in fields(BL) if f["name"] in ("Name", "Baseline"))
    if prim["name"] != "Baseline":
        update_field(BL, prim, name="Baseline")
    ensure_field(BL, {"name": "Proje", "dataType": 5, "linkedAppId": APP_ID, "linkedListId": list_id(P), "allowMultiple": False})
    ensure_field(BL, {"name": "Baseline No", "dataType": 1})
    ensure_field(BL, {"name": "Baseline Tarihi", "dataType": 2})
    ensure_field(BL, {"name": "Alan", "dataType": 6})
    ensure_field(BL, {"name": "Gerekçe", "dataType": 0, "enableFormatting": True})
    # 3) Projeler: baseline gerekçesi (baseline alınırken doldurulur, BL kaydına kopyalanıp temizlenir)
    ensure_field(P, {"name": "Baseline Gerekçesi", "dataType": 0, "enableFormatting": True})
    # 4) kalem alanları
    ensure_field(KAL, {"name": "Baseline", "dataType": 5, "linkedAppId": APP_ID, "linkedListId": list_id(BL), "allowMultiple": False})
    if "Tür" not in fmap(KAL):
        ensure_field(KAL, {"name": "Tür", "dataType": 4, "defaultValue": None,
                           "staticListValues": [{"id": new_uuid(), "label": t, "color": col, "order": i}
                                                for i, (t, col) in enumerate(zip(TURLER, ["#4d7ae0", "#2e3d4c", "#eb6834"]))]})
    ensure_field(KAL, {"name": "Faz", "dataType": 5, "linkedAppId": APP_ID, "linkedListId": list_id(FZ), "allowMultiple": False})
    ensure_field(KAL, {"name": "Kilometre Taşı", "dataType": 5, "linkedAppId": APP_ID, "linkedListId": list_id(KT), "allowMultiple": False})
    fk = fmap(KAL)
    ensure_field(KAL, {"name": "Güncel Bitiş (Görev)", "dataType": 2, "isLookup": True, "lookupFieldId": fk["Görev"]["id"], "linkedFieldId": fid(G, "Bitiş")})
    ensure_field(KAL, {"name": "Güncel Bitiş (Faz)", "dataType": 2, "isLookup": True, "lookupFieldId": fk["Faz"]["id"], "linkedFieldId": fid(FZ, "Bitiş")})
    ensure_field(KAL, {"name": "Güncel Tarih (KT)", "dataType": 2, "isLookup": True, "lookupFieldId": fk["Kilometre Taşı"]["id"], "linkedFieldId": fid(KT, "Hedef Tarih")})
    fk = fmap(KAL)
    g, f_, k, pb = (fk[n]["id"] for n in ("Güncel Bitiş (Görev)", "Güncel Bitiş (Faz)", "Güncel Tarih (KT)", "Planlanan Bitiş"))
    ensure_field(KAL, {"name": "Sapma (gün)", "dataType": 1, "isComputed": True,
                       "expression": f"If(IsNotBlank(_F_{g}), SubtractDate(_F_{g}, _F_{pb}), If(IsNotBlank(_F_{f_}), SubtractDate(_F_{f_}, _F_{pb}), "
                                     f"If(IsNotBlank(_F_{k}), SubtractDate(_F_{k}, _F_{pb}), 0)))"})
    kn = fmap(KAL).get("Kayıt No")
    if kn and kn.get("isVisible"):
        update_field(KAL, kn, isVisible=False)
    # durum kaydı
    for ln in (BL, KAL, P):
        _register(ln, list_id(ln))
    print("  ✅ yapı tamam:", {ln: len(state()["lists"][ln]["fields"]) for ln in (BL, KAL)})


def _all(ln):
    return c.post(f"{API}/Data/All", {"listId": list_id(ln), "maxResultCount": 1000, "skipCount": 0})["items"]


def tasima():
    F = lambda ln, n: str(fid(ln, n))  # noqa: E731
    kal = _all(KAL)
    bl = _all(BL)
    yalcin = c.get(f"{API}/User/GetUsers", {"MaxResultCount": 200})
    yalcin = next((u for u in (yalcin.get("items") if isinstance(yalcin, dict) else yalcin) if u.get("id") == 158776), None)
    gruplar = {}
    for r in kal:
        pid = (r.get(F(KAL, "Proje")) or [{}])[0].get("_id")
        no = int(r.get(F(KAL, "Baseline No")) or 0)
        if pid and no:
            gruplar.setdefault((pid, no), []).append(r)
    projeler = {p["_id"]: p for p in _all(P)}
    for (pid, no), rs in sorted(gruplar.items(), key=lambda x: x[0][1]):
        var = next((b for b in bl if (b.get(F(BL, "Proje")) or [{}])[0].get("_id") == pid and int(b.get(F(BL, "Baseline No")) or 0) == no), None)
        ad = projeler[pid][F(P, "Proje Adı")]
        if not var:
            body = {F(BL, "Baseline"): f"{ad} · BL{no}", F(BL, "Proje"): [pid], F(BL, "Baseline No"): no,
                    F(BL, "Baseline Tarihi"): rs[0].get(F(KAL, "Baseline Tarihi")),
                    F(BL, "Gerekçe"): "İlk plan onayı" if no == 1 else "Yeniden plan onayı (test)"}
            if yalcin:
                body[F(BL, "Alan")] = yalcin["emailAddress"]
            var = c.post(f"{API}/Data/Create", body, {"listId": list_id(BL)})
            print(f"  ✅ {ad} · BL{no}")
        bid = var.get("_id") or var.get("id")
        n = 0
        for r in rs:
            if not r.get(F(KAL, "Baseline")):
                c.put(f"{API}/Data/UpdatePartial", {F(KAL, "Baseline"): [bid], F(KAL, "Tür"): "Görev"}, {"listId": list_id(KAL), "id": r["_id"]})
                n += 1
        print(f"     {n} görev kalemi bağlandı")
        # son baseline için faz ve KT kalemleri (kayıtlardaki güncel baseline alanlarından)
        if no == max(x[1] for x in gruplar if x[0] == pid) and not any(
                (k.get(F(KAL, "Tür")) or {}).get("label") in ("Faz", "Kilometre Taşı") and (k.get(F(KAL, "Baseline")) or [{}])[0].get("_id") == bid for k in _all(KAL)):
            for f in _all(FZ):
                if (f.get(F(FZ, "Proje")) or [{}])[0].get("_id") == pid and f.get(F(FZ, "Baseline Başlangıç")):
                    c.post(f"{API}/Data/Create", {F(KAL, "Başlık" if "Başlık" in fmap(KAL) else "Name"): f"BL{no} · {f[F(FZ, 'Faz')]}",
                        F(KAL, "Baseline"): [bid], F(KAL, "Tür"): "Faz", F(KAL, "Faz"): [f["_id"]], F(KAL, "Proje"): [pid], F(KAL, "Baseline No"): no,
                        F(KAL, "Baseline Tarihi"): rs[0].get(F(KAL, "Baseline Tarihi")),
                        F(KAL, "Planlanan Başlangıç"): f[F(FZ, "Baseline Başlangıç")], F(KAL, "Planlanan Bitiş"): f[F(FZ, "Baseline Bitiş")]}, {"listId": list_id(KAL)})
            for k in _all(KT):
                if (k.get(F(KT, "Proje")) or [{}])[0].get("_id") == pid and k.get(F(KT, "Baseline Tarih")):
                    c.post(f"{API}/Data/Create", {F(KAL, "Başlık" if "Başlık" in fmap(KAL) else "Name"): f"BL{no} · {k[F(KT, 'Kilometre Taşı')]}",
                        F(KAL, "Baseline"): [bid], F(KAL, "Tür"): "Kilometre Taşı", F(KAL, "Kilometre Taşı"): [k["_id"]], F(KAL, "Proje"): [pid], F(KAL, "Baseline No"): no,
                        F(KAL, "Baseline Tarihi"): rs[0].get(F(KAL, "Baseline Tarihi")),
                        F(KAL, "Planlanan Başlangıç"): k[F(KT, "Baseline Tarih")], F(KAL, "Planlanan Bitiş"): k[F(KT, "Baseline Tarih")]}, {"listId": list_id(KAL)})
            print("     faz ve kilometre taşı kalemleri eklendi")


def otomasyon():
    yeni_no = f"If(IsBlank({ref(P, 'Baseline No')}), 1, {ref(P, 'Baseline No')} + 1)"
    # A9 — proje "Plan Onaylandı (Baseline)" olunca: Baseline kaydı + proje sayacı
    ensure_automation("A9 · Baseline al", t_updated(P, "Durum"), [cond(is_(P, "Durum", "Plan Onaylandı (Baseline)"), then=[
        create(BL, [m(BL, "Baseline", formula(f"Concat({ref(P, 'Proje Adı')}, \" · BL\", {yeni_no})")),
                    m(BL, "Proje", src_id()), m(BL, "Baseline No", formula(yeni_no)), m(BL, "Baseline Tarihi", formula("Today()")),
                    m(BL, "Alan", src(P, "Last Modifier")), m(BL, "Gerekçe", src(P, "Baseline Gerekçesi"))]),
        update([m(P, "Baseline No", formula(yeni_no)), m(P, "Baseline Tarihi", formula("Today()")),
                m(P, "Durum", val(opt(P, "Durum", "Devam Ediyor"))), m(P, "Baseline Gerekçesi", formula('""'))]),
        notify_field(P, "Proje Yöneticisi", f"📌 Baseline alındı: {ref(P, 'Proje Adı')} · BL{yeni_no}"),
    ])])
    pk = "Başlık" if "Başlık" in fmap(KAL) else "Name"
    kal = lambda tur, ad, aid, bas, bit, extra: create(KAL, [  # noqa: E731
        m(KAL, pk, formula(f"Concat(\"BL\", {ref(BL, 'Baseline No')}, \" · \", {ad})")),
        m(KAL, "Baseline", src_id()), m(KAL, "Tür", val(opt(KAL, "Tür", tur))), m(KAL, "Proje", src(BL, "Proje")),
        m(KAL, "Baseline No", src(BL, "Baseline No")), m(KAL, "Baseline Tarihi", src(BL, "Baseline Tarihi")),
        m(KAL, "Planlanan Başlangıç", bas), m(KAL, "Planlanan Bitiş", bit), *extra])
    Tb, Fb, Kb = new_uuid(), new_uuid(), new_uuid()
    ensure_automation("A9b · Baseline kalemleri — görevler", t_created(BL), [
        find(G, [flt(G, "Proje", src(BL, "Proje"))], id=Tb, actions=[
            update([m(G, "Baseline Başlangıç", src(G, "Başlangıç", Tb)), m(G, "Baseline Bitiş", src(G, "Bitiş", Tb))], aid=Tb),
            kal("Görev", ref(G, "Görev Adı", Tb), Tb, src(G, "Başlangıç", Tb), src(G, "Bitiş", Tb), [m(KAL, "Görev", src_id(Tb))])])])
    ensure_automation("A9c · Baseline kalemleri — fazlar", t_created(BL), [
        find(FZ, [flt(FZ, "Proje", src(BL, "Proje"))], id=Fb, count=50, actions=[
            update([m(FZ, "Baseline Başlangıç", src(FZ, "Başlangıç", Fb)), m(FZ, "Baseline Bitiş", src(FZ, "Bitiş", Fb))], aid=Fb),
            kal("Faz", ref(FZ, "Faz", Fb), Fb, src(FZ, "Başlangıç", Fb), src(FZ, "Bitiş", Fb), [m(KAL, "Faz", src_id(Fb))])])])
    ensure_automation("A9d · Baseline kalemleri — kilometre taşları", t_created(BL), [
        find(KT, [flt(KT, "Proje", src(BL, "Proje"))], id=Kb, count=50, actions=[
            update([m(KT, "Baseline Tarih", src(KT, "Hedef Tarih", Kb))], aid=Kb),
            kal("Kilometre Taşı", ref(KT, "Kilometre Taşı", Kb), Kb, src(KT, "Hedef Tarih", Kb), src(KT, "Hedef Tarih", Kb), [m(KAL, "Kilometre Taşı", src_id(Kb))])])])
    # eski faz/KT baseline otomasyonları (Baseline No tetikli) artık gereksiz
    r = c.get(f"{API}/Automation/GetAll", {"appId": APP_ID})
    for a in (r["items"] if isinstance(r, dict) else r):
        if a["name"] in ("A9b · Faz baseline", "A9c · Kilometre taşı baseline"):
            c.delete(f"{API}/Automation/Delete", {"automationId": a["id"]})
            print("  🗑", a["name"])


if __name__ == "__main__" and sys.argv[1] != "gorunum":
    {"yapi": yapi, "tasima": tasima, "otomasyon": otomasyon}[sys.argv[1]]()


def gorunum():
    from farmatek_ileri import ensure_view
    vs = {v["name"]: v for v in views(BL)}
    ensure_view(BL, "Tüm Baseline'lar", 0, columns=["Baseline", "Proje", "Baseline No", "Baseline Tarihi", "Alan", "Gerekçe"],
                default=True, rename_from=next((n for n in vs if n not in ("Tüm Baseline'lar",)), None))
    ensure_view(KAL, "Tüm Kalemler", 0, columns=["Başlık", "Baseline", "Tür", "Proje", "Planlanan Başlangıç", "Planlanan Bitiş",
                                                 "Güncel Bitiş (Görev)", "Güncel Bitiş (Faz)", "Güncel Tarih (KT)", "Sapma (gün)"],
                default=True, rename_from="Tüm Baseline Kayıtları")


if __name__ == "__main__" and sys.argv[1] == "gorunum":
    gorunum()
