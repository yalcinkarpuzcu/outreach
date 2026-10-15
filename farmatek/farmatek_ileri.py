"""
Farmatek Ar-Ge — builder'ın kapsamadığı ileri kurulum (workiom-builder build'inden SONRA çalışır).

  API_KEY=... python farmatek_ileri.py yapi        # TASK eşlemeleri, sistem alanı adları, durumlar, bağımlılık/formül/lookup/rollup
  API_KEY=... python farmatek_ileri.py gorunum     # Gantt, Kanban, Takvim görünümleri + sistem alanlı raporlar
  API_KEY=... python farmatek_ileri.py otomasyon   # A1–A9
  API_KEY=... python farmatek_ileri.py yetki       # validasyonlar + roller

Her faz tekrar çalıştırılabilir (isim bazlı idempotent).
"""
from __future__ import annotations

import sys

from wk import *  # noqa: F401,F403

G, K, P = "Görevler", "Görev Kütüphanesi", "Projeler"

GOREV_DURUMLARI = [
    ("Başlamadı",        "#8ed6ff", False),
    ("Başlayabilir",     "#4e86f7", False),
    ("Devam Ediyor",     "#f5c044", False),
    ("Onay Bekliyor",    "#7942e3", False),
    ("Revizyon Gerekli", "#ea346f", False),
    ("Beklemede",        "#ffa979", False),
    ("Tamamlandı",       "#5bd77e", True),
    ("İptal",            "#ff86c7", True),
]
PROJE_DURUMLARI = [
    ("Taslak",                      "#8ed6ff", False),
    ("Planlanıyor",                 "#4e86f7", False),
    ("Plan Onaylandı (Baseline)",   "#7942e3", False),
    ("Devam Ediyor",                "#f5c044", False),
    ("Beklemede",                   "#ffa979", False),
    ("Tamamlandı",                  "#5bd77e", True),
    ("İptal",                       "#ea346f", True),
]
KUTUPHANE_DURUMLARI = [
    ("Yayında", "#5bd77e", False),
    ("Taslak",  "#8ed6ff", False),
    ("Arşiv",   "#ea346f", True),
]

# sistem alanı → yeni ad
YENI_ADLAR = {
    K: {"Summary": "Görev Adı", "Description": "Açıklama", "Assignee": "Varsayılan Sorumlu",
        "Due date": "Bitiş", "Status": "Durum", "Parent Task": "Üst Öğe", "Subtasks": "Alt Öğeler"},
    P: {"Summary": "Proje Adı", "Description": "Proje Açıklaması", "Assignee": "Proje Yöneticisi",
        "Due date": "Hedef Bitiş", "Status": "Durum", "Parent Task": "Ana Program",
        "Subtasks": "Alt Projeler"},
    G: {"Summary": "Görev Adı", "Description": "Açıklama", "Assignee": "Sorumlu",
        "Due date": "Bitiş", "Status": "Durum", "Parent Task": "Üst Görev", "Subtasks": "Alt Görevler"},
    "Departmanlar": {"Name": "Departman"},
    "Proje Şablonları": {"Name": "Şablon"},
    "Onay Geçmişi": {"Name": "Başlık"},
    "Baseline Arşivi": {"Name": "Başlık"},
}
# builder'ın eklediği, birincil alanla çakışan kopyalar
SILINECEK = {"Departmanlar": ["Departman Adı"], "Proje Şablonları": ["Şablon Adı"], P: ["Açıklama"]}
START_FIELD = {K: "Başlangıç", P: "Başlangıç Tarihi", G: "Başlangıç"}


def _status(list_name, opts, default):
    f = next(f for f in fields(list_name) if f["dataType"] == 16)
    if [v["label"] for v in f["staticListValues"]] == [o[0] for o in opts]:
        print(f"  · {list_name} durumları mevcut"); return
    vals = [{"id": new_uuid(), "label": l, "color": col, "order": i, "isClosed": cl}
            for i, (l, col, cl) in enumerate(opts)]
    update_field(list_name, f, staticListValues=vals, defaultValue=default)
    print(f"  ✅ {list_name} durumları ({len(vals)})")


def yapi():
    print("── TASK başlangıç eşlemesi")
    for ln, fname in START_FIELD.items():
        L = c.get(f"{API}/Lists/Get", {"id": list_id(ln)})
        sid = fid(ln, fname)
        if L.get("startDateFieldId") != sid:
            body = {k: v for k, v in L.items() if k not in ("views", "defaultView", "fields")}
            body["startDateFieldId"] = sid
            c.put(f"{API}/Lists/Update", body, {"id": list_id(ln)})
            print(f"  ✅ {ln}.startDateFieldId = {fname}")
        else:
            print(f"  · {ln} başlangıç eşlemesi mevcut")

    print("── kopya alanları sil")
    for ln, names in SILINECEK.items():
        fm = fmap(ln)
        for n in names:
            if n in fm:
                c.delete(f"{API}/Fields/Delete", {"listId": list_id(ln), "id": fm[n]["id"]})
                print(f"  🗑  {ln}.{n}")

    print("── sistem alanı adları")
    for ln, ren in YENI_ADLAR.items():
        fm = fmap(ln)
        for old, new in ren.items():
            if old in fm and new not in fm:
                update_field(ln, fm[old], name=new)
                print(f"  ✅ {ln}: {old} → {new}")

    print("── durumlar")
    _status(G, GOREV_DURUMLARI, "Başlamadı")
    _status(P, PROJE_DURUMLARI, "Taslak")
    _status(K, KUTUPHANE_DURUMLARI, "Yayında")

    print("── native bağımlılık alanları (dataType 21)")
    for ln in (K, G):
        ensure_field(ln, {"name": "Öncüller", "dataType": 21, "linkedListId": list_id(ln),
                          "allowMultiple": True})

    print("── formüller")
    fk, fg = fmap(K), fmap(G)
    ensure_field(K, {"name": "Süre (gün)", "dataType": 1, "isComputed": True,
                     "expression": f"SubtractDate(_F_{fk['Bitiş']['id']}, _F_{fk['Başlangıç']['id']})"})
    ensure_field(K, {"name": "Başlangıç Ofseti (gün)", "dataType": 1, "isComputed": True,
                     "expression": f"SubtractDate(_F_{fk['Başlangıç']['id']}, _F_{fk['Referans Tarih']['id']})"})
    ensure_field(G, {"name": "Süre (gün)", "dataType": 1, "isComputed": True,
                     "expression": f"SubtractDate(_F_{fg['Bitiş']['id']}, _F_{fg['Başlangıç']['id']})"})
    ensure_field(G, {"name": "Sapma (gün)", "dataType": 1, "isComputed": True,
                     "expression": f"If(IsBlank(_F_{fg['Baseline Bitiş']['id']}), 0, "
                                   f"SubtractDate(_F_{fg['Bitiş']['id']}, _F_{fg['Baseline Bitiş']['id']}))"})

    print("── lookup'lar")
    fp = fmap(P)
    ensure_field(G, {"name": "Proje Yöneticisi", "dataType": 6, "isLookup": True,
                     "lookupFieldId": fg["Proje"]["id"], "linkedFieldId": fp["Proje Yöneticisi"]["id"]})
    ensure_field(G, {"name": "Şablon Üst Öğe", "dataType": 5, "isLookup": True,
                     "lookupFieldId": fg["Şablon Öğesi"]["id"], "linkedFieldId": fk["Üst Öğe"]["id"]})
    ensure_field(G, {"name": "Proje Başlangıcı", "dataType": 2, "isLookup": True,
                     "lookupFieldId": fg["Proje"]["id"], "linkedFieldId": fp["Başlangıç Tarihi"]["id"]})

    print("── şablon süresi")
    ensure_field("Proje Şablonları", {"name": "Toplam Süre (gün)", "dataType": 1})
    ensure_field(P, {"name": "Şablon Süresi", "dataType": 1, "isLookup": True,
                     "lookupFieldId": fp["Şablon"]["id"],
                     "linkedFieldId": fid("Proje Şablonları", "Toplam Süre (gün)")})

    print("── rollup: açık öncül sayısı")
    ensure_field(G, {"name": "Öncül Sayısı", "dataType": 1, "isRollup": True,
                     "linkedListId": list_id(G), "linkedFieldId": fg["Kapalı"]["id"],
                     "rollupFieldId": fg["Öncül Kayıtları"]["id"], "rollupSummaryType": 4})
    ensure_field(G, {"name": "Kapanan Öncül", "dataType": 1, "isRollup": True,
                     "linkedListId": list_id(G), "linkedFieldId": fg["Kapalı"]["id"],
                     "rollupFieldId": fg["Öncül Kayıtları"]["id"], "rollupSummaryType": 0})
    fg = fmap(G)
    ensure_field(G, {"name": "Açık Öncül Sayısı", "dataType": 1, "isComputed": True,
                     "expression": f"_F_{fg['Öncül Sayısı']['id']} - _F_{fg['Kapanan Öncül']['id']}"})


# ───────────────────────────────────────────────────────────── görünümler
def _filter_link(list_name, field, rec_id, label):
    return {"fieldId": fid(list_name, field), "operator": 3, "value": [{"_id": rec_id, "label": label}]}


def _filter_bool(list_name, field, val=True):
    return {"fieldId": fid(list_name, field), "operator": 0, "value": val}


def _filter_opt(list_name, field, label):
    return {"fieldId": fid(list_name, field), "operator": 3,
            "value": [{"label": label, "id": opt(list_name, field, label)}]}


def _columns(list_name, visible):
    fm = fmap(list_name)
    out = [{"fieldId": fm[n]["id"], "displayState": True, "width": 260 if i == 0 else 130}
           for i, n in enumerate(visible) if n in fm]
    out += [{"fieldId": f["id"], "displayState": False} for f in fm.values() if f["name"] not in visible]
    return out


def ensure_view(list_name, name, view_type, *, field=None, color=None, filters=(), columns=None,
                gantt=None, default=False, rename_from=None):
    lid = list_id(list_name)
    vs = {v["name"]: v for v in views(list_name)}
    if rename_from and rename_from in vs and name not in vs:
        old = vs.pop(rename_from)
        c.put(f"{API}/Views/Update", {**old, "name": name}, {"listId": lid, "id": old["id"]})
        print(f"  ✅ {list_name} / {rename_from} → {name}")
        vs[name] = {**old, "name": name}
    v = vs.get(name)
    if not v:
        body = {"name": name, "viewType": view_type, "listId": lid, "filters": list(filters),
                "filterCollectionOperator": 0, "groupingSorting": 0, "accessibility": 0, "roleIds": [],
                "conditionalColorFilters": []}
        if field:
            body["fieldId"] = fid(list_name, field)
        if color:
            body["colorFieldId"] = fid(list_name, color)
        v = c.post(f"{API}/Views/Create", body, {"listId": lid})
        print(f"  ✅ {list_name} / {name} oluşturuldu ({v['id']})")
    else:
        print(f"  · {list_name} / {name} mevcut ({v['id']})")
    st = {"fieldDisplayStateObjects": _columns(list_name, columns or []), "kanbanCardStateObjects": []}
    if gantt:
        st["ganttDisplayStateObject"] = gantt
    body = {"name": name, "viewType": view_type, "filters": list(filters), "filterCollectionOperator": 0,
            "groupingSorting": 0, "state": st, "order": v.get("order", 0), "accessibility": 0,
            "roleIds": [], "sourceViewId": v["id"], "conditionalColorFilters": []}
    if field:
        body["fieldId"] = fid(list_name, field)
    if color:
        body["colorFieldId"] = fid(list_name, color)
    c.put(f"{API}/Views/UpdateState", body, {"listId": lid, "id": v["id"]})
    if default:
        c.post(f"{API}/Views/SetDefault", {"id": v["id"]}, {"listId": lid})
    return v["id"]


GANTT = {"dateViewType": "Month", "dependencyShifting": "maintain_buffer_downstream", "showCriticalPath": True}
G_COLS = ["Görev Adı", "WBS No", "Durum", "Sorumlu", "Başlangıç", "Bitiş", "Süre (gün)", "% Tamamlanma",
          "Proje", "Sorumlu Departman", "Öncüller", "Sapma (gün)"]
K_COLS = ["Görev Adı", "WBS No", "Tür", "Sorumlu Departman", "Başlangıç", "Bitiş", "Süre (gün)",
          "Başlangıç Ofseti (gün)", "Öncüller", "Kilometre Taşı", "Onay Gerekli", "Şablonlar", "Varsayım"]
P_COLS = ["Proje Adı", "Proje Kodu", "Durum", "Proje Yöneticisi", "Şablon", "Başlangıç Tarihi",
          "Hedef Bitiş", "Ürün / Molekül", "Baseline No"]


def gorunum():
    from farmatek_seed import records
    print("── Görev Kütüphanesi")
    sab = {r[str(fid("Proje Şablonları", "Şablon"))]: r["_id"] for r in records("Proje Şablonları")}
    for s in ("Yeni Ürün", "Alternatif Kaynak"):
        ensure_view(K, f"{s} Şablonu (Gantt)", 12, field="Öncüller", color="Tür", columns=K_COLS,
                    filters=[_filter_link(K, "Şablonlar", sab[s], s)], gantt=GANTT,
                    default=(s == "Yeni Ürün"))
    ensure_view(K, "Kütüphane Tablosu", 0, columns=K_COLS)
    for n in ("Board", "Calendar", "List"):
        _drop_view(K, n)

    print("── Projeler")
    ensure_view(P, "Portföy Gantt", 12, field=None, color="Durum", columns=P_COLS,
                gantt={**GANTT, "dependencyShifting": "none", "dateViewType": "Quarter"}, default=True)
    ensure_view(P, "Durum Panosu", 1, field="Durum", color="Durum", columns=P_COLS, rename_from="Board")
    ensure_view(P, "Tüm Projeler", 0, columns=P_COLS)
    for n in ("Calendar", "List"):
        _drop_view(P, n)

    print("── Görevler")
    ensure_view(G, "Proje Planı (Gantt)", 12, field="Öncüller", color="Durum", columns=G_COLS,
                gantt=GANTT, default=True)
    ensure_view(G, "Kilometre Taşları (Gantt)", 12, field="Öncüller", color="Durum", columns=G_COLS,
                filters=[_filter_bool(G, "Kilometre Taşı")], gantt={**GANTT, "dateViewType": "Quarter"})
    ensure_view(G, "Durum Panosu", 1, field="Durum", color="Durum", columns=G_COLS, rename_from="Board")
    ensure_view(G, "Takvim", 3, field="Bitiş", color="Durum", columns=G_COLS, rename_from="Calendar")
    ensure_view(G, "Tüm Görevler", 0, columns=G_COLS + ["Onay Durumu", "Gerçekleşen Başlangıç",
                                                       "Gerçekleşen Bitiş", "Baseline Bitiş", "Gecikmede"])
    ensure_view(G, "Geciken Görevler", 0, columns=G_COLS, filters=[_filter_bool(G, "Gecikmede")])
    ensure_view(G, "Onay Bekleyenler", 0, columns=G_COLS + ["Onaylayıcı"],
                filters=[_filter_opt(G, "Durum", "Onay Bekliyor")])
    ensure_view(G, "Kilometre Taşları", 0, columns=G_COLS, filters=[_filter_bool(G, "Kilometre Taşı")])
    ensure_view(G, "Baseline vs Plan", 0, columns=["Görev Adı", "Proje", "Baseline Başlangıç", "Başlangıç",
                                                   "Baseline Bitiş", "Bitiş", "Sapma (gün)", "Durum"])
    _drop_view(G, "List")

    print("── Raporlar")
    raporlar()


def _drop_view(list_name, name):
    for v in views(list_name):
        if v["name"] == name and not v.get("isDefault"):
            c.delete(f"{API}/Views/Delete", {"id": v["id"], "listId": list_id(list_name)})
            print(f"  🗑  {list_name} / {name}")


def _widget(label, list_name, wtype, *, filters=(), group=None, fields_=(), summary=None, icon="fal fa-chart-bar"):
    body = {"appId": APP_ID, "label": label, "icon": icon, "listId": list_id(list_name), "viewId": None,
            "filters": list(filters), "filterCollectionOperator": 0, "summaryMode": summary,
            "widgetType": wtype, "fieldsIds": [fid(list_name, f) for f in fields_], "valueFieldId": [],
            "fieldAggregationType": 4, "groupingFieldId": fid(list_name, group) if group else None,
            "groupingDateFrequency": 2 if group else None, "isPin": True, "limit": 100, "limitSub": 100,
            "sortingType": 0, "sortingType2": 0, "xGroupOthers": True, "yGroupOthers": True}
    r = c.get(f"{API}/AppDashboard/GetAll", {"appId": APP_ID})
    ex = {w["label"]: w for w in (r["items"] if isinstance(r, dict) else r)}
    if label in ex:
        c.put(f"{API}/AppDashboard/Update", {**ex[label], **body}, {"appId": APP_ID, "id": ex[label]["id"]})
        print(f"  · {label} güncellendi")
    else:
        c.post(f"{API}/AppDashboard/Create", body, {"appId": APP_ID})
        print(f"  ✅ {label}")


def raporlar():
    _widget("Aktif Projeler", P, 0, summary=0, icon="fal fa-flask",
            filters=[_filter_opt(P, "Durum", "Devam Ediyor")])
    _widget("Açık Görevler (Devam Ediyor)", G, 0, summary=0, icon="fal fa-tasks",
            filters=[_filter_opt(G, "Durum", "Devam Ediyor")])
    _widget("Görevler – Duruma Göre", G, 1, group="Durum", icon="fal fa-tasks")
    _widget("Görevler – Projeye Göre", G, 1, group="Proje", icon="fal fa-folder-open")
    _widget("Projeler – Duruma Göre", P, 2, group="Durum", icon="fal fa-chart-pie")
    _widget("Kilometre Taşları", G, 4, icon="fal fa-flag", filters=[_filter_bool(G, "Kilometre Taşı")],
            fields_=["Görev Adı", "Proje", "Başlangıç", "Bitiş", "Durum", "Sapma (gün)"])
    _widget("Geciken Görev Listesi", G, 4, icon="fal fa-exclamation-triangle",
            filters=[_filter_bool(G, "Gecikmede")],
            fields_=["Görev Adı", "Proje", "Sorumlu", "Bitiş", "Durum", "Sapma (gün)"])
    _widget("Projeler – Özet", P, 4, icon="fal fa-table",
            fields_=["Proje Adı", "Durum", "Proje Yöneticisi", "Başlangıç Tarihi", "Hedef Bitiş", "Baseline No"])


# ───────────────────────────────────────────────────────────── otomasyon DSL (ham API şekli)
def ref(list_name, field, aid=ZERO):
    """formül/koşul referansı"""
    return f"_F_{fid(list_name, field)}_A_{z(aid)}"


def optref(list_name, field, label, aid=ZERO):
    return f"{ref(list_name, field, aid)}_V_{z(opt(list_name, field, label))}"


def is_(list_name, field, label, aid=ZERO):
    return f"{ref(list_name, field, aid)} = {optref(list_name, field, label, aid)}"


def src(list_name, field, aid=ZERO):
    return {"type": 0, "sourceField": f"{fid(list_name, field)}_A_{aid}"}


def src_id(aid=ZERO):
    return {"type": 0, "sourceField": f"_id_A_{aid}"}


def val(v):
    return {"type": 1, "value": v}


def formula(f):
    return {"type": 2, "formula": f}


def m(list_name, field, value, append=False):
    return {"fieldId": fid(list_name, field), "appendValue": append, "value": value}


def _base(t, **kw):
    return {"id": kw.pop("id", None) or new_uuid(), "type": t, "isEnabled": True,
            "successWithWarningsEnabled": False, "issues": [], **kw}


def find(list_name, filters, actions, *, sort=None, count=500, id=None, no_result=()):
    return _base(7, id=id, appId=APP_ID, listId=list_id(list_name), viewId=None,
                 sorting=f"{fid(list_name, sort)} ASC" if sort else None, recordsCount=count,
                 filters=filters, actions=actions, noResultActions=list(no_result))


def flt(list_name, field, value, op=3):
    """op: 1=Contains (çoklu link / bağımlılık), 3=Is (tekil eşitlik)"""
    return {"fieldId": fid(list_name, field), "value1Mapping": value, "value2Mapping": None, "operator": op}


def create(list_name, mappings):
    return _base(0, appId=APP_ID, listId=list_id(list_name), fieldValueMappings=mappings)


def update(mappings, aid=ZERO):
    return _base(1, recordsMapping={"type": 0, "actionId": aid}, fieldValueMappings=mappings)


def cond(expr, then=(), else_=()):
    return _base(2, condition=expr, showBasic=False, successActions=list(then), failedActions=list(else_))


def notify_field(list_name, field, message, aid=ZERO):
    return _base(3, user={"type": 1, "userField": f"{fid(list_name, field)}_A_{aid}"}, message=message)


def approval(title, subtitle, approver_src, on_approve, on_reject, reject_msg=True):
    return _base(10, title=title, subtitle=subtitle, approvals={"type": 1, "userField": approver_src},
                 timeoutInDays=None, isRejectionMessageRequired=reject_msg,
                 recordsMapping={"type": 0, "actionId": ZERO},
                 approveActions=list(on_approve), rejectActions=list(on_reject))


def ensure_automation(name, trigger, actions, active=True):
    r = c.get(f"{API}/Automation/GetAll", {"appId": APP_ID})
    for a in (r["items"] if isinstance(r, dict) else r):
        if a["name"] == name:
            c.delete(f"{API}/Automation/Delete", {"automationId": a["id"]})
    res = c.post(f"{API}/Automation/Create",
                 {"name": name, "isActive": active, "trigger": trigger, "actions": actions},
                 {"appId": APP_ID})
    print(f"  ✅ ⚡ {name} ({res['id']})")
    return res["id"]


def t_created(list_name):
    return {"type": 0, "listId": list_id(list_name)}


def t_updated(list_name, field):
    return {"type": 1, "listId": list_id(list_name), "fieldId": fid(list_name, field)}


AKTIF = ("Devam Ediyor", "Onay Bekliyor", "Tamamlandı")


def otomasyon():
    S_ = "Proje Şablonları"
    # A1 — proje oluşturulunca şablondaki kalemleri Görevler'e kopyala
    L = new_uuid()
    a1 = [cond(f"IsNotBlank({ref(P, 'Şablon')}) and IsNotBlank({ref(P, 'Başlangıç Tarihi')})", then=[
        update([m(P, "Durum", val(opt(P, "Durum", "Planlanıyor"))),
                m(P, "Plan Durumu", val(opt(P, "Plan Durumu", "Bekliyor"))),
                m(P, "Hedef Bitiş", formula(f"{ref(P, 'Başlangıç Tarihi')} + {ref(P, 'Şablon Süresi')}"))]),
        find(K, [flt(K, "Şablonlar", src(P, "Şablon"), op=1)], id=L, sort="WBS No", actions=[
            create(G, [
                m(G, "Görev Adı", src(K, "Görev Adı", L)),
                m(G, "WBS No", src(K, "WBS No", L)),
                m(G, "Tür", src(K, "Tür", L)),
                m(G, "Proje", src_id()),
                m(G, "Şablon Öğesi", src_id(L)),
                m(G, "Sorumlu Departman", src(K, "Sorumlu Departman", L)),
                m(G, "Sorumlu", src(K, "Varsayılan Sorumlu", L)),
                m(G, "Onaylayıcı", src(K, "Departman Onaylayıcı", L)),
                m(G, "Kilometre Taşı", src(K, "Kilometre Taşı", L)),
                m(G, "Onay Gerekli", src(K, "Onay Gerekli", L)),
                m(G, "Açıklama", src(K, "Kabul Kriteri", L)),
                m(G, "Başlangıç", formula(f"{ref(P, 'Başlangıç Tarihi')} + {ref(K, 'Başlangıç Ofseti (gün)', L)}")),
                m(G, "Bitiş", formula(f"{ref(P, 'Başlangıç Tarihi')} + {ref(K, 'Başlangıç Ofseti (gün)', L)}"
                                      f" + {ref(K, 'Süre (gün)', L)}")),
                m(G, "Kapalı", val(0)), m(G, "Gecikme Sayacı", val(0)), m(G, "% Tamamlanma", val(0)),
                m(G, "Durum", val(opt(G, "Durum", "Başlamadı"))),
            ])]),
        update([m(P, "Plan Durumu", val(opt(P, "Plan Durumu", "Görevler Oluşturuldu")))]),
    ])]
    ensure_automation("A1 · Proje oluşturulunca şablondan görevleri üret", t_created(P), a1)

    # A2 — hiyerarşi + öncülleri proje içinde (Proje + Şablon Öğesi ile) bağla
    T, X, S2, Y = new_uuid(), new_uuid(), new_uuid(), new_uuid()
    proje_filtre = lambda: flt(G, "Proje", src_id())  # noqa: E731
    a2 = [cond(is_(P, "Plan Durumu", "Görevler Oluşturuldu"), then=[
        find(G, [proje_filtre()], id=T, actions=[
            # üst öğe
            find(G, [proje_filtre(), flt(G, "Şablon Öğesi", src(G, "Şablon Üst Öğe", T))], id=X, count=1,
                 actions=[update([m(G, "Üst Görev", src_id(X))], aid=T)]),
            # ardılları: kütüphanede T'nin şablonunu öncül olarak tutan kalemler → projedeki karşılıkları
            find(K, [flt(K, "Öncüller", src(G, "Şablon Öğesi", T), op=1)], id=S2, actions=[
                find(G, [proje_filtre(), flt(G, "Şablon Öğesi", src_id(S2))], id=Y, count=1, actions=[
                    update([m(G, "Öncüller", src_id(T), append=True),
                            m(G, "Öncül Kayıtları", src_id(T), append=True)], aid=Y)])]),
        ]),
        update([m(P, "Plan Durumu", val(opt(P, "Plan Durumu", "Hazır")))]),
        notify_field(P, "Proje Yöneticisi",
                     f"Proje planı hazır: {ref(P, 'Proje Adı')}. Görevler, hiyerarşi ve öncüller oluşturuldu."),
    ])]
    ensure_automation("A2 · Görev hiyerarşisini ve öncülleri bağla", t_updated(P, "Plan Durumu"), a2)

    # A3–A6 — görev durum akışı (öncül kilidi, onay, kapanış, ardılları açma)
    ONAY = "Onay Geçmişi"
    gecmis = lambda karar: create(ONAY, [  # noqa: E731
        m(ONAY, "Başlık", formula(f"Concat(\"{karar}: \", {ref(G, 'Görev Adı')})")),
        m(ONAY, "Karar", val(opt(ONAY, "Karar", karar))),
        m(ONAY, "Onaylayan", src(G, "Onaylayıcı")),
        m(ONAY, "Tarih", formula("Today()")),
        m(ONAY, "Görev", src_id()),
        m(ONAY, "Proje", src(G, "Proje")),
    ])
    Yd = new_uuid()
    kilitli = (f"({' or '.join(is_(G, 'Durum', d) for d in AKTIF)}) and {ref(G, 'Açık Öncül Sayısı')} > 0")
    a3 = [cond(kilitli, then=[
        update([m(G, "Durum", val(opt(G, "Durum", "Başlamadı")))]),
        notify_field(G, "Sorumlu", f"⛔ {ref(G, 'Görev Adı')}: öncül görevler tamamlanmadan başlatılamaz/tamamlanamaz. "
                                   f"Açık öncül sayısı: {ref(G, 'Açık Öncül Sayısı')}"),
    ], else_=[
        cond(is_(G, "Durum", "Devam Ediyor"), then=[
            cond(f"IsBlank({ref(G, 'Gerçekleşen Başlangıç')})",
                 then=[update([m(G, "Gerçekleşen Başlangıç", formula("Today()"))])]),
            update([m(G, "Kapalı", val(0))]),
        ]),
        cond(is_(G, "Durum", "Onay Bekliyor"), then=[
            cond(f"{ref(G, 'Onay Gerekli')} = true", then=[
                update([m(G, "Onay Durumu", val(opt(G, "Onay Durumu", "Bekliyor")))]),
                approval("Görev onayı",
                         f"{ref(G, 'Görev Adı')} · {ref(G, 'Proje')} — tamamlandı olarak onaya sunuldu.",
                         f"{fid(G, 'Onaylayıcı')}_A_{ZERO}",
                         on_approve=[update([m(G, "Onay Durumu", val(opt(G, "Onay Durumu", "Onaylandı"))),
                                             m(G, "Durum", val(opt(G, "Durum", "Tamamlandı")))]),
                                     gecmis("Onaylandı")],
                         on_reject=[update([m(G, "Onay Durumu", val(opt(G, "Onay Durumu", "Reddedildi"))),
                                            m(G, "Durum", val(opt(G, "Durum", "Revizyon Gerekli")))]),
                                    gecmis("Reddedildi"),
                                    notify_field(G, "Sorumlu", f"↩️ {ref(G, 'Görev Adı')} reddedildi, "
                                                               f"revizyon gerekiyor. Onay notlarını kontrol edin.")]),
            ], else_=[update([m(G, "Durum", val(opt(G, "Durum", "Tamamlandı")))])]),
        ]),
        cond(is_(G, "Durum", "Tamamlandı"), then=[
            cond(f"{ref(G, 'Onay Gerekli')} = true and not({is_(G, 'Onay Durumu', 'Onaylandı')})", then=[
                update([m(G, "Durum", val(opt(G, "Durum", "Onay Bekliyor")))]),
            ], else_=[
                update([m(G, "Kapalı", val(1)), m(G, "% Tamamlanma", val(100)),
                        m(G, "Gerçekleşen Bitiş", formula("Today()"))]),
                find(G, [flt(G, "Öncül Kayıtları", src_id(), op=1)], id=Yd, actions=[
                    cond(f"{is_(G, 'Durum', 'Başlamadı', Yd)} and {ref(G, 'Açık Öncül Sayısı', Yd)} = 0", then=[
                        update([m(G, "Durum", val(opt(G, "Durum", "Başlayabilir")))], aid=Yd),
                        notify_field(G, "Sorumlu", f"▶️ {ref(G, 'Görev Adı', Yd)} başlayabilir: tüm öncülleri tamamlandı.",
                                     aid=Yd),
                    ])]),
            ]),
        ]),
        cond(is_(G, "Durum", "İptal"), then=[update([m(G, "Kapalı", val(1))])]),
        cond(f"{is_(G, 'Durum', 'Revizyon Gerekli')} or {is_(G, 'Durum', 'Beklemede')} or "
             f"{is_(G, 'Durum', 'Başlamadı')} or {is_(G, 'Durum', 'Başlayabilir')}",
             then=[update([m(G, "Kapalı", val(0))])]),
    ])]
    ensure_automation("A3-A6 · Görev durum akışı (öncül kilidi, onay, kapanış)", t_updated(G, "Durum"), a3)

    # A7/A8 — her sabah: geciken görevleri işaretle, 3 gün kalanlara hatırlatma
    Z = new_uuid()
    a7 = [find(G, [flt(G, "Kapalı", val(0), op=3)], id=Z, count=1000, actions=[
        cond(f"{ref(G, 'Bitiş', Z)} < Today() and not({ref(G, 'Gecikmede', Z)} = true)", then=[
            update([m(G, "Gecikmede", val(True)), m(G, "Gecikme Sayacı", val(1))], aid=Z),
            notify_field(G, "Sorumlu", f"⏰ Gecikme: {ref(G, 'Görev Adı', Z)} — bitiş {ref(G, 'Bitiş', Z)}", aid=Z),
            notify_field(G, "Proje Yöneticisi", f"⏰ Geciken görev: {ref(G, 'Görev Adı', Z)} · {ref(G, 'Proje', Z)} "
                                                f"(sorumlu: {ref(G, 'Sorumlu', Z)})", aid=Z),
        ]),
        cond(f"SubtractDate({ref(G, 'Bitiş', Z)}, Today()) = 3", then=[
            notify_field(G, "Sorumlu", f"📅 3 gün kaldı: {ref(G, 'Görev Adı', Z)} — bitiş {ref(G, 'Bitiş', Z)}", aid=Z),
            notify_field(G, "Proje Yöneticisi", f"📅 3 gün kaldı: {ref(G, 'Görev Adı', Z)} · {ref(G, 'Proje', Z)}", aid=Z),
        ]),
    ])]
    ensure_automation("A7-A8 · Günlük gecikme ve yaklaşan bitiş kontrolü",
                      {"type": 3, "cronExpression": "0 6 * * *"}, a7)

    # A8b — bitiş ileri alınırsa gecikme bayrağını kaldır
    ensure_automation("A8b · Bitiş güncellenince gecikme bayrağını yeniden değerlendir", t_updated(G, "Bitiş"), [
        cond(f"{ref(G, 'Bitiş')} >= Today()", then=[
            update([m(G, "Gecikmede", val(False)), m(G, "Gecikme Sayacı", val(0))])])])

    # A9 — baseline
    BA, Tb = "Baseline Arşivi", new_uuid()
    yeni_no = f"If(IsBlank({ref(P, 'Baseline No')}), 1, {ref(P, 'Baseline No')} + 1)"
    a9 = [cond(is_(P, "Durum", "Plan Onaylandı (Baseline)"), then=[
        find(G, [flt(G, "Proje", src_id())], id=Tb, actions=[
            update([m(G, "Baseline Başlangıç", src(G, "Başlangıç", Tb)),
                    m(G, "Baseline Bitiş", src(G, "Bitiş", Tb))], aid=Tb),
            create(BA, [m(BA, "Başlık", formula(f"Concat(\"BL\", {yeni_no}, \" · \", {ref(G, 'Görev Adı', Tb)})")),
                        m(BA, "Baseline No", formula(yeni_no)),
                        m(BA, "Baseline Tarihi", formula("Today()")),
                        m(BA, "Planlanan Başlangıç", src(G, "Başlangıç", Tb)),
                        m(BA, "Planlanan Bitiş", src(G, "Bitiş", Tb)),
                        m(BA, "Proje", src_id()), m(BA, "Görev", src_id(Tb))]),
        ]),
        update([m(P, "Baseline No", formula(yeni_no)), m(P, "Baseline Tarihi", formula("Today()")),
                m(P, "Durum", val(opt(P, "Durum", "Devam Ediyor")))]),
        notify_field(P, "Proje Yöneticisi", f"📌 Baseline alındı: {ref(P, 'Proje Adı')}"),
    ])]
    ensure_automation("A9 · Baseline al", t_updated(P, "Durum"), a9)


if __name__ == "__main__":
    {"yapi": yapi, "gorunum": gorunum, "raporlar": raporlar, "otomasyon": otomasyon}[sys.argv[1]]()
