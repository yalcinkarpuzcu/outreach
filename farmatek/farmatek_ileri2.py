"""
Ar-Ge Proje Yönetimi 2 — builder'ın kapsamadığı ileri kurulum (model 2: Fazlar / Kilometre Taşları ayrı).

  FARMATEK_APP=2 API_KEY=... python farmatek_ileri2.py yapi|gorunum|otomasyon|yetki

İlk app'in (farmatek_ileri.py) otomasyon DSL'i ve görünüm yardımcıları yeniden kullanılır.
"""
from __future__ import annotations

import os
import sys

assert os.environ.get("FARMATEK_APP") == "2", "FARMATEK_APP=2 ile çalıştırın"

from farmatek_ileri import (  # noqa: E402  (aynı DSL, wk durumu app 2'yi gösterir)
    G, K, P, _status, ensure_view, _drop_view, _filter_link, _filter_bool, _filter_opt, _widget,
    ref, is_, src, src_id, val, formula, m, find, flt, create, update, cond, notify_field, approval,
    ensure_automation, t_created, t_updated, GANTT, KUTUPHANE_DURUMLARI, _liste_izni, EKIP_DUZENLER)
from wk import *  # noqa: E402,F401,F403

FZ, FK, KT, KTK = "Fazlar", "Faz Kütüphanesi", "Kilometre Taşları", "Kilometre Taşı Kütüphanesi"

YENI_ADLAR = {
    K: {"Summary": "Görev Adı", "Description": "Açıklama", "Assignee": "Varsayılan Sorumlu", "Due date": "Bitiş", "Status": "Durum"},
    P: {"Summary": "Proje Adı", "Description": "Proje Açıklaması", "Assignee": "Proje Yöneticisi", "Due date": "Hedef Bitiş", "Status": "Durum"},
    G: {"Summary": "Görev Adı", "Description": "Açıklama", "Assignee": "Sorumlu", "Due date": "Bitiş", "Status": "Durum"},
    "Departmanlar": {"Name": "Departman"}, "Proje Şablonları": {"Name": "Şablon"},
    FK: {"Name": "Faz"}, KTK: {"Name": "Kilometre Taşı"}, FZ: {"Name": "Faz"}, KT: {"Name": "Kilometre Taşı"},
    "Onay Geçmişi": {"Name": "Başlık"}, "Baseline Arşivi": {"Name": "Başlık"},
}
GIZLE = {K: ["Parent Task", "Subtasks"], P: ["Parent Task", "Subtasks"], G: ["Parent Task", "Subtasks"]}   # alt görev yok
START = {K: "Başlangıç", P: "Başlangıç Tarihi", G: "Başlangıç"}
PLAN_DURUMLARI = ["Bekliyor", "Fazlar Oluşturuldu", "Görevler Oluşturuldu", "Öncüller Bağlandı", "Hazır"]


def yapi():
    print("── TASK başlangıç eşlemesi")
    for ln, fname in START.items():
        L = c.get(f"{API}/Lists/Get", {"id": list_id(ln)})
        sid = fid(ln, fname)
        if L.get("startDateFieldId") != sid:
            body = {k: v for k, v in L.items() if k not in ("views", "defaultView", "fields")}
            body["startDateFieldId"] = sid
            c.put(f"{API}/Lists/Update", body, {"id": list_id(ln)})
            print(f"  ✅ {ln}.startDateFieldId = {fname}")

    print("── sistem alanı adları")
    for ln, ren in YENI_ADLAR.items():
        fm = fmap(ln)
        for old, new in ren.items():
            if old in fm and new not in fm:
                update_field(ln, fm[old], name=new)
                print(f"  ✅ {ln}: {old} → {new}")
    print("── üst/alt görev alanlarını gizle (model 2'de alt görev yok)")
    for ln, names in GIZLE.items():
        fm = fmap(ln)
        for n in names:
            if n in fm and fm[n].get("isVisible") is not False:
                update_field(ln, fm[n], isVisible=False)
                print(f"  ✅ {ln}.{n} gizlendi")

    print("── kütüphane durumları + plan durumu seçenekleri")
    _status(K, KUTUPHANE_DURUMLARI, "Yayında")
    pd = fmap(P)["Plan Durumu"]
    if [v["label"] for v in pd["staticListValues"]] != PLAN_DURUMLARI:
        renk = ["#8ed6ff", "#4e86f7", "#f5c044", "#7942e3", "#5bd77e"]
        mevcut = {v["label"]: v for v in pd["staticListValues"]}
        vals = [{**mevcut.get(lb, {"id": new_uuid()}), "label": lb, "color": renk[i], "order": i} for i, lb in enumerate(PLAN_DURUMLARI)]
        update_field(P, pd, staticListValues=vals)
        print("  ✅ Plan Durumu seçenekleri")

    print("── native bağımlılık alanları")
    for ln in (K, G):
        ensure_field(ln, {"name": "Öncüller", "dataType": 21, "linkedListId": list_id(ln), "allowMultiple": True})

    print("── formüller")
    fk, fg, fz, fkt = fmap(K), fmap(G), fmap(FZ), fmap(KT)
    ensure_field(K, {"name": "Süre (gün)", "dataType": 1, "isComputed": True,
                     "expression": f"SubtractDate(_F_{fk['Bitiş']['id']}, _F_{fk['Başlangıç']['id']})"})
    ensure_field(K, {"name": "Başlangıç Ofseti (gün)", "dataType": 1, "isComputed": True,
                     "expression": f"SubtractDate(_F_{fk['Başlangıç']['id']}, _F_{fk['Referans Tarih']['id']})"})
    ensure_field(G, {"name": "Süre (gün)", "dataType": 1, "isComputed": True,
                     "expression": f"SubtractDate(_F_{fg['Bitiş']['id']}, _F_{fg['Başlangıç']['id']})"})
    ensure_field(G, {"name": "Sapma (gün)", "dataType": 1, "isComputed": True,
                     "expression": f"If(IsBlank(_F_{fg['Baseline Bitiş']['id']}), 0, "
                                   f"SubtractDate(_F_{fg['Bitiş']['id']}, _F_{fg['Baseline Bitiş']['id']}))"})
    ensure_field(FZ, {"name": "Süre (gün)", "dataType": 1, "isComputed": True,
                      "expression": f"SubtractDate(_F_{fz['Bitiş']['id']}, _F_{fz['Başlangıç']['id']})"})
    ensure_field(KT, {"name": "Sapma (gün)", "dataType": 1, "isComputed": True,
                      "expression": f"If(IsBlank(_F_{fkt['Baseline Tarih']['id']}), 0, "
                                    f"SubtractDate(_F_{fkt['Hedef Tarih']['id']}, _F_{fkt['Baseline Tarih']['id']}))"})

    print("── lookup'lar")
    fp = fmap(P)
    ensure_field(G, {"name": "Proje Yöneticisi", "dataType": 6, "isLookup": True,
                     "lookupFieldId": fg["Proje"]["id"], "linkedFieldId": fp["Proje Yöneticisi"]["id"]})
    ensure_field(KT, {"name": "Proje Yöneticisi", "dataType": 6, "isLookup": True,
                      "lookupFieldId": fkt["Proje"]["id"], "linkedFieldId": fp["Proje Yöneticisi"]["id"]})
    ensure_field(P, {"name": "Şablon Süresi", "dataType": 1, "isLookup": True,
                     "lookupFieldId": fp["Şablon"]["id"], "linkedFieldId": fid("Proje Şablonları", "Toplam Süre (gün)")})

    print("── rollup: açık öncül / açık bağlı görev")
    ensure_field(G, {"name": "Öncül Sayısı", "dataType": 1, "isRollup": True, "linkedListId": list_id(G),
                     "linkedFieldId": fg["Kapalı"]["id"], "rollupFieldId": fg["Öncül Kayıtları"]["id"], "rollupSummaryType": 4})
    ensure_field(G, {"name": "Kapanan Öncül", "dataType": 1, "isRollup": True, "linkedListId": list_id(G),
                     "linkedFieldId": fg["Kapalı"]["id"], "rollupFieldId": fg["Öncül Kayıtları"]["id"], "rollupSummaryType": 0})
    fg = fmap(G)
    ensure_field(G, {"name": "Açık Öncül Sayısı", "dataType": 1, "isComputed": True,
                     "expression": f"_F_{fg['Öncül Sayısı']['id']} - _F_{fg['Kapanan Öncül']['id']}"})
    ensure_field(KT, {"name": "Bağlı Görev Sayısı", "dataType": 1, "isRollup": True, "linkedListId": list_id(G),
                      "linkedFieldId": fg["Kapalı"]["id"], "rollupFieldId": fkt["Bağlı Görevler"]["id"], "rollupSummaryType": 4})
    ensure_field(KT, {"name": "Kapanan Bağlı Görev", "dataType": 1, "isRollup": True, "linkedListId": list_id(G),
                      "linkedFieldId": fg["Kapalı"]["id"], "rollupFieldId": fkt["Bağlı Görevler"]["id"], "rollupSummaryType": 0})
    fkt = fmap(KT)
    ensure_field(KT, {"name": "Açık Bağlı Görev", "dataType": 1, "isComputed": True,
                      "expression": f"_F_{fkt['Bağlı Görev Sayısı']['id']} - _F_{fkt['Kapanan Bağlı Görev']['id']}"})


# ───────────────────────────────────────────────────────────── görünümler
G_COLS = ["Görev Adı", "WBS No", "Faz", "Durum", "Sorumlu", "Başlangıç", "Bitiş", "Süre (gün)", "% Tamamlanma",
          "Proje", "Sorumlu Departman", "Öncüller", "Sapma (gün)"]
K_COLS = ["Görev Adı", "WBS No", "Faz", "Sorumlu Departman", "Başlangıç", "Bitiş", "Süre (gün)", "Başlangıç Ofseti (gün)",
          "Öncüller", "Kilometre Taşları", "Onay Gerekli", "Şablonlar", "Varsayım"]
P_COLS = ["Proje Adı", "Proje Kodu", "Durum", "Proje Yöneticisi", "Şablon", "Başlangıç Tarihi", "Hedef Bitiş", "Ürün / Molekül", "Baseline No"]
FZ_COLS = ["Faz", "Sıra", "Proje", "Başlangıç", "Bitiş", "Süre (gün)", "Baseline Bitiş"]
KT_COLS = ["Kilometre Taşı", "Proje", "Faz", "Hedef Tarih", "KT Durumu", "Gerçekleşen Tarih", "Bağlı Görevler", "Açık Bağlı Görev", "Sapma (gün)", "Kritik"]


def gorunum():
    from farmatek_seed import records
    print("── Görev Kütüphanesi")
    sab = {r[str(fid("Proje Şablonları", "Şablon"))]: r["_id"] for r in records("Proje Şablonları")}
    for s in sab:
        ensure_view(K, f"{s} Şablonu (Gantt)", 12, field="Öncüller", color="Faz", columns=K_COLS,
                    filters=[_filter_link(K, "Şablonlar", sab[s], s)], gantt=GANTT, default=(s == "Yeni Ürün"))
    ensure_view(K, "Kütüphane Tablosu", 0, columns=K_COLS)
    for n in ("Board", "Calendar", "List"):
        _drop_view(K, n)
    print("── Projeler")
    ensure_view(P, "Portföy Gantt", 12, color="Durum", columns=P_COLS,
                gantt={**GANTT, "dependencyShifting": "none", "dateViewType": "Quarter"}, default=True)
    ensure_view(P, "Durum Panosu", 1, field="Durum", color="Durum", columns=P_COLS, rename_from="Board")
    ensure_view(P, "Tüm Projeler", 0, columns=P_COLS)
    for n in ("Calendar", "List"):
        _drop_view(P, n)
    print("── Görevler")
    ensure_view(G, "Proje Planı (Gantt)", 12, field="Öncüller", color="Durum", columns=G_COLS, gantt=GANTT, default=True)
    ensure_view(G, "Durum Panosu", 1, field="Durum", color="Durum", columns=G_COLS, rename_from="Board")
    ensure_view(G, "Takvim", 3, field="Bitiş", color="Durum", columns=G_COLS, rename_from="Calendar")
    ensure_view(G, "Tüm Görevler", 0, columns=G_COLS + ["Onay Durumu", "Gerçekleşen Başlangıç", "Gerçekleşen Bitiş", "Baseline Bitiş", "Gecikmede"])
    ensure_view(G, "Geciken Görevler", 0, columns=G_COLS, filters=[_filter_bool(G, "Gecikmede")])
    ensure_view(G, "Onay Bekleyenler", 0, columns=G_COLS + ["Onaylayıcı"], filters=[_filter_opt(G, "Durum", "Onay Bekliyor")])
    ensure_view(G, "Baseline vs Plan", 0, columns=["Görev Adı", "Proje", "Faz", "Baseline Başlangıç", "Başlangıç", "Baseline Bitiş", "Bitiş", "Sapma (gün)", "Durum"])
    _drop_view(G, "List")
    print("── Fazlar / Kilometre Taşları")
    ensure_view(FZ, "Tüm Fazlar", 0, columns=FZ_COLS)
    ensure_view(KT, "Tüm Kilometre Taşları", 0, columns=KT_COLS)
    ensure_view(KT, "Kritik Kilometre Taşları", 0, columns=KT_COLS, filters=[_filter_bool(KT, "Kritik")])
    print("── Raporlar")
    _widget("Aktif Projeler", P, 0, summary=0, icon="fal fa-flask", filters=[_filter_opt(P, "Durum", "Devam Ediyor")])
    _widget("Görevler – Duruma Göre", G, 1, group="Durum", icon="fal fa-tasks")
    _widget("Görevler – Projeye Göre", G, 1, group="Proje", icon="fal fa-folder-open")
    _widget("Projeler – Duruma Göre", P, 2, group="Durum", icon="fal fa-chart-pie")
    _widget("Kilometre Taşları", KT, 4, icon="fal fa-flag",
            fields_=["Kilometre Taşı", "Proje", "Faz", "Hedef Tarih", "KT Durumu", "Sapma (gün)"])
    _widget("Geciken Görev Listesi", G, 4, icon="fal fa-exclamation-triangle", filters=[_filter_bool(G, "Gecikmede")],
            fields_=["Görev Adı", "Proje", "Faz", "Sorumlu", "Bitiş", "Durum", "Sapma (gün)"])
    _widget("Projeler – Özet", P, 4, icon="fal fa-table",
            fields_=["Proje Adı", "Durum", "Proje Yöneticisi", "Başlangıç Tarihi", "Hedef Bitiş", "Baseline No"])


# ───────────────────────────────────────────────────────────── otomasyonlar
AKTIF = ("Devam Ediyor", "Onay Bekliyor", "Tamamlandı")


def _plan(label):
    return update([m(P, "Plan Durumu", val(opt(P, "Plan Durumu", label)))])


def otomasyon():
    start = ref(P, "Başlangıç Tarihi")
    proje = lambda: flt(G, "Proje", src_id())  # noqa: E731

    # A1 — proje oluşturulunca: fazlar
    Lf = new_uuid()
    ensure_automation("A1 · Proje oluşturulunca fazları oluştur", t_created(P), [
        cond(f"IsNotBlank({ref(P, 'Şablon')}) and IsNotBlank({start})", then=[
            update([m(P, "Durum", val(opt(P, "Durum", "Planlanıyor"))),
                    m(P, "Plan Durumu", val(opt(P, "Plan Durumu", "Bekliyor"))),
                    m(P, "Hedef Bitiş", formula(f"{start} + {ref(P, 'Şablon Süresi')}"))]),
            find(FK, [flt(FK, "Şablonlar", src(P, "Şablon"), op=1)], id=Lf, sort="Sıra", count=50, actions=[
                create(FZ, [m(FZ, "Faz", src(FK, "Faz", Lf)), m(FZ, "Sıra", src(FK, "Sıra", Lf)),
                            m(FZ, "Proje", src_id()), m(FZ, "Faz Şablonu", src_id(Lf)),
                            m(FZ, "Başlangıç", formula(f"{start} + {ref(FK, 'Başlangıç Ofseti (gün)', Lf)}")),
                            m(FZ, "Bitiş", formula(f"{start} + {ref(FK, 'Başlangıç Ofseti (gün)', Lf)} + {ref(FK, 'Süre (gün)', Lf)}"))])]),
            _plan("Fazlar Oluşturuldu"),
        ])])

    # A1b — görevler (her biri projedeki karşılık gelen faza bağlı)
    L, X = new_uuid(), new_uuid()
    ensure_automation("A1b · Görevleri oluştur ve fazlara bağla", t_updated(P, "Plan Durumu"), [
        cond(is_(P, "Plan Durumu", "Fazlar Oluşturuldu"), then=[
            find(K, [flt(K, "Şablonlar", src(P, "Şablon"), op=1)], id=L, sort="WBS No", actions=[
                find(FZ, [flt(FZ, "Proje", src_id()), flt(FZ, "Faz Şablonu", src(K, "Faz", L))], id=X, count=1, actions=[
                    create(G, [
                        m(G, "Görev Adı", src(K, "Görev Adı", L)), m(G, "WBS No", src(K, "WBS No", L)),
                        m(G, "Proje", src_id()), m(G, "Faz", src_id(X)), m(G, "Şablon Öğesi", src_id(L)),
                        m(G, "Sorumlu Departman", src(K, "Sorumlu Departman", L)),
                        m(G, "Sorumlu", src(K, "Varsayılan Sorumlu", L)), m(G, "Onaylayıcı", src(K, "Departman Onaylayıcı", L)),
                        m(G, "Onay Gerekli", src(K, "Onay Gerekli", L)), m(G, "Açıklama", src(K, "Kabul Kriteri", L)),
                        m(G, "Başlangıç", formula(f"{start} + {ref(K, 'Başlangıç Ofseti (gün)', L)}")),
                        m(G, "Bitiş", formula(f"{start} + {ref(K, 'Başlangıç Ofseti (gün)', L)} + {ref(K, 'Süre (gün)', L)}")),
                        m(G, "Kapalı", val(0)), m(G, "% Tamamlanma", val(0)), m(G, "Durum", val(opt(G, "Durum", "Başlamadı"))),
                    ])])]),
            _plan("Görevler Oluşturuldu"),
        ])])

    # A2 — öncüller (yalnızca bu projenin görevleri arasında)
    T, S2, Y = new_uuid(), new_uuid(), new_uuid()
    ensure_automation("A2 · Öncülleri bağla", t_updated(P, "Plan Durumu"), [
        cond(is_(P, "Plan Durumu", "Görevler Oluşturuldu"), then=[
            find(G, [proje()], id=T, actions=[
                find(K, [flt(K, "Öncüller", src(G, "Şablon Öğesi", T), op=1)], id=S2, count=20, actions=[
                    find(G, [proje(), flt(G, "Şablon Öğesi", src_id(S2))], id=Y, count=1, actions=[
                        update([m(G, "Öncüller", src_id(T), append=True)], aid=Y),
                        update([m(G, "Öncül Kayıtları", src_id(T), append=True)], aid=Y)])])]),
            _plan("Öncüller Bağlandı"),
        ])])

    # A2b — kilometre taşları + bağlı görevler, plan hazır
    Lk, Yk, Mk, Sk, Gk = (new_uuid() for _ in range(5))
    ensure_automation("A2b · Kilometre taşlarını oluştur ve görevlere bağla", t_updated(P, "Plan Durumu"), [
        cond(is_(P, "Plan Durumu", "Öncüller Bağlandı"), then=[
            find(KTK, [flt(KTK, "Şablonlar", src(P, "Şablon"), op=1)], id=Lk, count=50, actions=[
                find(FZ, [flt(FZ, "Proje", src_id()), flt(FZ, "Faz Şablonu", src(KTK, "Faz", Lk))], id=Yk, count=1, actions=[
                    create(KT, [m(KT, "Kilometre Taşı", src(KTK, "Kilometre Taşı", Lk)), m(KT, "Proje", src_id()),
                                m(KT, "Faz", src_id(Yk)), m(KT, "KT Şablonu", src_id(Lk)), m(KT, "Kritik", src(KTK, "Kritik", Lk)),
                                m(KT, "Hedef Tarih", formula(f"{start} + {ref(KTK, 'Gün Ofseti', Lk)}")),
                                m(KT, "KT Durumu", val(opt(KT, "KT Durumu", "Bekleniyor")))])])]),
            find(KT, [flt(KT, "Proje", src_id())], id=Mk, count=50, actions=[
                find(K, [flt(K, "Kilometre Taşları", src(KT, "KT Şablonu", Mk), op=1)], id=Sk, count=20, actions=[
                    find(G, [proje(), flt(G, "Şablon Öğesi", src_id(Sk))], id=Gk, count=1, actions=[
                        update([m(KT, "Bağlı Görevler", src_id(Gk), append=True)], aid=Mk)])])]),
            _plan("Hazır"),
            notify_field(P, "Proje Yöneticisi", f"Proje planı hazır: {ref(P, 'Proje Adı')}. Fazlar, görevler, öncüller ve kilometre taşları oluşturuldu."),
        ])])

    # A3–A6 — görev durum akışı (öncül kilidi, onay, kapanış, ardıllar)
    ONAY = "Onay Geçmişi"
    gecmis = lambda karar: create(ONAY, [  # noqa: E731
        m(ONAY, "Başlık", formula(f"Concat(\"{karar}: \", {ref(G, 'Görev Adı')})")),
        m(ONAY, "Karar", val(opt(ONAY, "Karar", karar))), m(ONAY, "Onaylayan", src(G, "Onaylayıcı")),
        m(ONAY, "Tarih", formula("Today()")), m(ONAY, "Görev", src_id()), m(ONAY, "Proje", src(G, "Proje"))])
    Yd = new_uuid()
    kilitli = f"({' or '.join(is_(G, 'Durum', d) for d in AKTIF)}) and {ref(G, 'Açık Öncül Sayısı')} > 0"
    ensure_automation("A3-A6 · Görev durum akışı (öncül kilidi, onay, kapanış)", t_updated(G, "Durum"), [cond(kilitli, then=[
        update([m(G, "Durum", val(opt(G, "Durum", "Başlamadı")))]),
        notify_field(G, "Sorumlu", f"⛔ {ref(G, 'Görev Adı')}: öncül görevler tamamlanmadan başlatılamaz/tamamlanamaz. "
                                   f"Açık öncül sayısı: {ref(G, 'Açık Öncül Sayısı')}"),
    ], else_=[
        cond(is_(G, "Durum", "Devam Ediyor"), then=[
            cond(f"IsBlank({ref(G, 'Gerçekleşen Başlangıç')})", then=[update([m(G, "Gerçekleşen Başlangıç", formula("Today()"))])]),
            update([m(G, "Kapalı", val(0))])]),
        cond(is_(G, "Durum", "Onay Bekliyor"), then=[
            cond(f"{ref(G, 'Onay Gerekli')} = true", then=[
                update([m(G, "Onay Durumu", val(opt(G, "Onay Durumu", "Bekliyor")))]),
                approval("Görev onayı", f"{ref(G, 'Görev Adı')} · {ref(G, 'Proje')} — tamamlandı olarak onaya sunuldu.",
                         f"{fid(G, 'Onaylayıcı')}_A_{ZERO}",
                         on_approve=[update([m(G, "Onay Durumu", val(opt(G, "Onay Durumu", "Onaylandı"))),
                                             m(G, "Durum", val(opt(G, "Durum", "Tamamlandı")))]), gecmis("Onaylandı")],
                         on_reject=[update([m(G, "Onay Durumu", val(opt(G, "Onay Durumu", "Reddedildi"))),
                                            m(G, "Durum", val(opt(G, "Durum", "Revizyon Gerekli")))]), gecmis("Reddedildi"),
                                    notify_field(G, "Sorumlu", f"↩️ {ref(G, 'Görev Adı')} reddedildi, revizyon gerekiyor.")]),
            ], else_=[update([m(G, "Durum", val(opt(G, "Durum", "Tamamlandı")))])])]),
        cond(is_(G, "Durum", "Tamamlandı"), then=[
            cond(f"{ref(G, 'Onay Gerekli')} = true and not({is_(G, 'Onay Durumu', 'Onaylandı')})",
                 then=[update([m(G, "Durum", val(opt(G, "Durum", "Onay Bekliyor")))])],
                 else_=[update([m(G, "Kapalı", val(1)), m(G, "% Tamamlanma", val(100)), m(G, "Gerçekleşen Bitiş", formula("Today()"))]),
                        find(G, [flt(G, "Öncül Kayıtları", src_id(), op=1)], id=Yd, actions=[
                            cond(f"{is_(G, 'Durum', 'Başlamadı', Yd)} and {ref(G, 'Açık Öncül Sayısı', Yd)} = 0", then=[
                                update([m(G, "Durum", val(opt(G, "Durum", "Başlayabilir")))], aid=Yd),
                                notify_field(G, "Sorumlu", f"▶️ {ref(G, 'Görev Adı', Yd)} başlayabilir: tüm öncülleri tamamlandı.", aid=Yd)])])])]),
        cond(is_(G, "Durum", "İptal"), then=[update([m(G, "Kapalı", val(1))])]),
        cond(f"{is_(G, 'Durum', 'Revizyon Gerekli')} or {is_(G, 'Durum', 'Beklemede')} or "
             f"{is_(G, 'Durum', 'Başlamadı')} or {is_(G, 'Durum', 'Başlayabilir')}", then=[update([m(G, "Kapalı", val(0))])]),
    ])])

    ensure_automation("A6b · Öncülleri kapanan görevi Başlayabilir yap", t_updated(G, "Kapanan Öncül"), [
        cond(f"{is_(G, 'Durum', 'Başlamadı')} and {ref(G, 'Açık Öncül Sayısı')} = 0 and {ref(G, 'Öncül Sayısı')} > 0", then=[
            update([m(G, "Durum", val(opt(G, "Durum", "Başlayabilir")))]),
            notify_field(G, "Sorumlu", f"▶️ {ref(G, 'Görev Adı')} başlayabilir: tüm öncülleri tamamlandı.")])])

    # A-KT — bağlı görevlerin hepsi kapanınca kilometre taşına ulaşıldı
    ensure_automation("A-KT · Kilometre taşına ulaşıldı", t_updated(KT, "Kapanan Bağlı Görev"), [
        cond(f"{ref(KT, 'Bağlı Görev Sayısı')} > 0 and {ref(KT, 'Açık Bağlı Görev')} = 0 and not({is_(KT, 'KT Durumu', 'Ulaşıldı')})", then=[
            update([m(KT, "KT Durumu", val(opt(KT, "KT Durumu", "Ulaşıldı"))), m(KT, "Gerçekleşen Tarih", formula("Today()"))]),
            notify_field(KT, "Proje Yöneticisi", f"🏁 Kilometre taşına ulaşıldı: {ref(KT, 'Kilometre Taşı')} · {ref(KT, 'Proje')}")],
            else_=[cond(f"{ref(KT, 'Açık Bağlı Görev')} > 0 and {is_(KT, 'KT Durumu', 'Ulaşıldı')}", then=[
                update([m(KT, "KT Durumu", val(opt(KT, "KT Durumu", "Bekleniyor")))])])])])

    # A7–A8 — her sabah: geciken görev ve kilometre taşları, 3 gün kala hatırlatma
    Z, Zk = new_uuid(), new_uuid()
    ensure_automation("A7-A8 · Günlük gecikme ve yaklaşan bitiş kontrolü", {"type": 3, "cronExpression": "0 6 * * *"}, [
        find(G, [flt(G, "Kapalı", val(0), op=3)], id=Z, count=1000, actions=[
            cond(f"{ref(G, 'Bitiş', Z)} < Today() and not({ref(G, 'Gecikmede', Z)} = true)", then=[
                update([m(G, "Gecikmede", val(True))], aid=Z),
                notify_field(G, "Sorumlu", f"⏰ Gecikme: {ref(G, 'Görev Adı', Z)} — bitiş {ref(G, 'Bitiş', Z)}", aid=Z),
                notify_field(G, "Proje Yöneticisi", f"⏰ Geciken görev: {ref(G, 'Görev Adı', Z)} · {ref(G, 'Proje', Z)}", aid=Z)]),
            cond(f"SubtractDate({ref(G, 'Bitiş', Z)}, Today()) = 3", then=[
                notify_field(G, "Sorumlu", f"📅 3 gün kaldı: {ref(G, 'Görev Adı', Z)}", aid=Z),
                notify_field(G, "Proje Yöneticisi", f"📅 3 gün kaldı: {ref(G, 'Görev Adı', Z)} · {ref(G, 'Proje', Z)}", aid=Z)])]),
        find(KT, [flt(KT, "KT Durumu", val(opt(KT, "KT Durumu", "Bekleniyor")), op=3)], id=Zk, count=500, actions=[
            cond(f"{ref(KT, 'Hedef Tarih', Zk)} < Today()", then=[
                update([m(KT, "KT Durumu", val(opt(KT, "KT Durumu", "Gecikti")))], aid=Zk),
                notify_field(KT, "Proje Yöneticisi", f"⚠️ Kilometre taşı gecikti: {ref(KT, 'Kilometre Taşı', Zk)} · {ref(KT, 'Proje', Zk)}", aid=Zk)])]),
    ])
    ensure_automation("A8b · Bitiş güncellenince gecikme bayrağını yeniden değerlendir", t_updated(G, "Bitiş"), [
        cond(f"{ref(G, 'Bitiş')} >= Today()", then=[update([m(G, "Gecikmede", val(False))])])])

    # A9 — baseline (görev + faz + kilometre taşı)
    BA, Tb, Fb, Kb = "Baseline Arşivi", new_uuid(), new_uuid(), new_uuid()
    yeni_no = f"If(IsBlank({ref(P, 'Baseline No')}), 1, {ref(P, 'Baseline No')} + 1)"
    ensure_automation("A9 · Baseline al", t_updated(P, "Durum"), [cond(is_(P, "Durum", "Plan Onaylandı (Baseline)"), then=[
        find(G, [flt(G, "Proje", src_id())], id=Tb, actions=[
            update([m(G, "Baseline Başlangıç", src(G, "Başlangıç", Tb)), m(G, "Baseline Bitiş", src(G, "Bitiş", Tb))], aid=Tb),
            create(BA, [m(BA, "Başlık", formula(f"Concat(\"BL\", {yeni_no}, \" · \", {ref(G, 'Görev Adı', Tb)})")),
                        m(BA, "Baseline No", formula(yeni_no)), m(BA, "Baseline Tarihi", formula("Today()")),
                        m(BA, "Planlanan Başlangıç", src(G, "Başlangıç", Tb)), m(BA, "Planlanan Bitiş", src(G, "Bitiş", Tb)),
                        m(BA, "Proje", src_id()), m(BA, "Görev", src_id(Tb))])]),
        find(FZ, [flt(FZ, "Proje", src_id())], id=Fb, count=50, actions=[
            update([m(FZ, "Baseline Başlangıç", src(FZ, "Başlangıç", Fb)), m(FZ, "Baseline Bitiş", src(FZ, "Bitiş", Fb))], aid=Fb)]),
        find(KT, [flt(KT, "Proje", src_id())], id=Kb, count=50, actions=[
            update([m(KT, "Baseline Tarih", src(KT, "Hedef Tarih", Kb))], aid=Kb)]),
        update([m(P, "Baseline No", formula(yeni_no)), m(P, "Baseline Tarihi", formula("Today()")),
                m(P, "Durum", val(opt(P, "Durum", "Devam Ediyor")))]),
        notify_field(P, "Proje Yöneticisi", f"📌 Baseline alındı: {ref(P, 'Proje Adı')}"),
    ])])


# ───────────────────────────────────────────────────────────── roller (mevcut rollere app 2 eklenir)
def _rol_ekle(ad, app_izni):
    roller = c.get(f"{API}/Role/GetRoles", {})
    roller = roller["items"] if isinstance(roller, dict) else roller
    r = next(x for x in roller if x.get("displayName") == ad)
    e = c.get(f"{API}/Role/GetRoleForEdit", {"Id": r["id"]})
    tree = e["permissionTree"]
    tree["apps"] = [a for a in tree["apps"] if a["appId"] != APP_ID] + [app_izni]
    body = {"role": {"id": r["id"], "displayName": ad}, "teamUsersChanged": False, "roleUserIds": e.get("roleUserIds") or [],
            "teamPermissionTreeChanged": True,
            "permissionTree": {k: tree.get(k) for k in ("inviteMembers", "createApp", "createDashbaord", "createInterface", "useAIMila",
                                                        "apps", "dashboards", "interfaces", "adminUserIds")},
            "teamAdminUserIdsChanged": False, "adminUserIds": []}
    c.post(f"{API}/Role/CreateOrUpdateRole", body)
    print(f"  ✅ rol: {ad} ← {APP_NAME}")


def yetki():
    ref_ = ("Departmanlar", "Proje Şablonları")
    _rol_ekle("Ar-Ge · Proje Yöneticisi", {
        "appId": APP_ID, "accessLevel": 1, "reportsAccess": 1, "formsAccess": 1,
        "listsPermissions": [_liste_izni(P, erisim=2), _liste_izni(G, erisim=2), _liste_izni(FZ, erisim=2), _liste_izni(KT, erisim=2),
                             _liste_izni("Onay Geçmişi"), _liste_izni("Baseline Arşivi"),
                             _liste_izni(K), _liste_izni(FK), _liste_izni(KTK), *[_liste_izni(x) for x in ref_]],
        "listWithPreventViewCreationAccess": []})
    _rol_ekle("Ar-Ge · Ekip Üyesi", {
        "appId": APP_ID, "accessLevel": 1, "reportsAccess": 1, "formsAccess": 0,
        "listsPermissions": [_liste_izni(P), _liste_izni(G, duzenlenebilir=EKIP_DUZENLER), _liste_izni(FZ), _liste_izni(KT),
                             _liste_izni("Onay Geçmişi"), _liste_izni("Baseline Arşivi"), *[_liste_izni(x) for x in ref_]],
        "listWithPreventViewCreationAccess": []})
    _rol_ekle("Ar-Ge · Yönetim (İzleyici)", {
        "appId": APP_ID, "accessLevel": 2, "reportsAccess": 1, "formsAccess": 0, "listsPermissions": [], "listWithPreventViewCreationAccess": []})


if __name__ == "__main__":
    {"yapi": yapi, "gorunum": gorunum, "otomasyon": otomasyon, "yetki": yetki}[sys.argv[1]]()
