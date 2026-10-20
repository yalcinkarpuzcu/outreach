"""Performans Yönetimi — ilişkiler ve hesaplanan alanlar. Spec build'den SONRA çalışır:

    python3 apps/performans_fix_primary.py
    python3 apps/performans_computed.py

1. Üst-alt ilişkiler: ters bağlantı (association) üst listede açılır, Workiom'un alt listede
   oluşturduğu eş alan yeniden adlandırılır (1:N için allowMultiple = False).
2. İK uygulamasına "Performans Form Türü" alanı (Özlük Bilgileri → Form Türleri).
3. Lookup → formül → rollup / sayım → (rollup'a bağlı) formül.

Formül yazımı: {{Alan}} → _F_<id> · {{Alan=Seçenek}} → seçim karşılaştırması.
İdempotent: aynı adlı alan varsa atlanır.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from wk import client  # noqa: E402
from workiom.client import WorkiomAPIError  # noqa: E402

c = client()
SF = next((ROOT / "state").glob("performans*.json"))
ST = json.loads(SF.read_text())
REG = {ln: ld["id"] for ln, ld in ST["lists"].items()}
IK_APP = "9b672737-2465-4c5e-b41a-8a3db4f91d9b"
REG["Özlük Bilgileri"] = "cc279e0f-af5a-4ff8-986f-a31793432ddf"
REG["Organizasyon"] = "a045d821-d480-433d-b32d-0bae28de0689"
LIST_BY_ID = {v: k for k, v in REG.items()}
FAILED: list[str] = []
_F: dict[str, list[dict]] = {}


def fields(lst, refresh=False):
    if refresh or lst not in _F:
        r = c.get("/api/services/app/Fields/GetAll", {"listId": REG[lst]})
        _F[lst] = r.get("items", r) if isinstance(r, dict) else r
    return _F[lst]


def fld(lst, name):
    for refresh in (False, True):
        for f in fields(lst, refresh):
            if f["name"] == name:
                return f
    raise KeyError(f"{lst}.{name}")


def exists(lst, name):
    return any(f["name"] == name for f in fields(lst, True))


def log(msg, kind, lst, name):
    print(f"  {msg:<8s} {kind:<9s} {lst} · {name}")


def create(lst, body, kind):
    if exists(lst, body["name"]):
        log("exists", kind, lst, body["name"])
        return None
    try:
        r = c.create_field(REG[lst], {"isVisible": True, "isRequired": False, **body})
        _F.pop(lst, None)
        log("created", kind, lst, body["name"])
        return r
    except WorkiomAPIError as e:
        FAILED.append(f"{kind} {lst}.{body['name']}: {e.message} {e.details[:200]}")
        log("FAILED", kind, lst, body["name"])
        print("           ", e.message, e.details[:300])
        return None


# ─── 1. üst-alt ilişkiler ─────────────────────────────────────────────────────
def relation(parent, backlink, child, twin, twin_multiple=False):
    """parent.backlink (çoklu, ters bağlantı) ↔ child.twin (tekli ya da çoklu)."""
    if exists(child, twin) and exists(parent, backlink):
        log("exists", "relation", child, twin)
        return
    r = create(parent, {"name": backlink, "dataType": 5, "linkedListId": REG[child],
                        "isAssociation": True, "hasAssociatedLinkedField": True,
                        "allowMultiple": True}, "backlink")
    if not r:
        return
    twin_id = r["linkedFieldId"]
    tw = next(f for f in fields(child, True) if f["id"] == twin_id)
    body = {**tw, "name": twin, "allowMultiple": twin_multiple, "description": None}
    c.put("/api/services/app/Fields/Update", body, {"listId": REG[child], "id": twin_id})
    _F.pop(child, None)
    log("renamed", "twin", child, twin)


def plain_link(lst, name, target, multiple=False, app_id=None):
    body = {"name": name, "dataType": 5, "linkedListId": REG[target], "allowMultiple": multiple}
    if app_id:
        body["linkedAppId"] = app_id
    create(lst, body, "link")


# ─── 3. hesaplanan alanlar ────────────────────────────────────────────────────
def _opt(lst, fname, label):
    f = fld(lst, fname)
    for o in f.get("staticListValues", []):
        if o["label"] == label:
            return o["id"].replace("-", "z")
    raise KeyError(f"seçenek {lst}.{fname}={label}")


def compile_expr(lst, expr):
    def rep(m):
        tok = m.group(1)
        if "=" in tok:
            fname, label = tok.split("=", 1)
            fid = fld(lst, fname)["id"]
            return f"_F_{fid} = _F_{fid}_V_{_opt(lst, fname, label)}"
        return f"_F_{fld(lst, tok)['id']}"
    return re.sub(r"\{\{(.+?)\}\}", rep, expr)


def formula(lst, name, expr, fallback=None):
    try:
        body = {"name": name, "dataType": 1, "isComputed": True,
                "expression": compile_expr(lst, expr)}
    except KeyError as e:
        FAILED.append(f"formula {lst}.{name}: {e}")
        log("SKIP", "formula", lst, name)
        return
    if create(lst, body, "formula") is None and fallback and not exists(lst, name):
        FAILED.pop()
        create(lst, {**body, "expression": compile_expr(lst, fallback)}, "formula*")


def lookup(lst, name, via, src_field):
    try:
        link = fld(lst, via)
        tgt = LIST_BY_ID[link["linkedListId"]]
        src = fld(tgt, src_field)
    except KeyError as e:
        FAILED.append(f"lookup {lst}.{name}: {e}")
        log("SKIP", "lookup", lst, name)
        return
    create(lst, {"name": name, "dataType": src["dataType"], "isLookup": True,
                 "linkedFieldId": src["id"], "lookupFieldId": link["id"]}, "lookup")


SUM, AVG, CNT = 0, 1, 4


def rollup(parent, name, backlink, child, value_field, summary=SUM):
    try:
        bl, vf = fld(parent, backlink), fld(child, value_field)
    except KeyError as e:
        FAILED.append(f"rollup {parent}.{name}: {e}")
        log("SKIP", "rollup", parent, name)
        return
    create(parent, {"name": name, "dataType": 1, "isRollup": True, "linkedListId": REG[child],
                    "linkedFieldId": vf["id"], "rollupFieldId": bl["id"],
                    "rollupSummaryType": summary}, "rollup")


def count(parent, name, backlink):
    try:
        bl = fld(parent, backlink)
    except KeyError as e:
        FAILED.append(f"count {parent}.{name}: {e}")
        return
    create(parent, {"name": name, "dataType": 12, "countLocalLinkedFieldId": bl["id"]}, "count")


def z(f):
    return "Coalesce({{%s}}, 0)" % f


if __name__ == "__main__":
    K, H, YD = "Performans Karneleri", "KPI Hedefleri", "Yetkinlik Değerlendirmeleri"
    O, KR, CI, D = "Objective'ler", "Key Result'lar", "Check-in'ler", "Dönemler"

    print("\n▶ İlişkiler")
    relation(K, "KPI Hedefleri", H, "Karne")
    relation(K, "Yetkinlik Değerlendirmeleri", YD, "Karne")
    relation(K, "OKR'lar", O, "Karne")
    relation(O, "Key Result'lar", KR, "Objective")
    relation(O, "Alt Objective'ler", O, "Üst Objective")
    relation(KR, "Check-in'ler", CI, "Key Result")
    relation(H, "İyileştiren OKR'lar", O, "İyileştirdiği KPI")
    relation(H, "Beslediği KR'lar", KR, "Kaynak KPI")
    relation(D, "Karneler", K, "Dönem")
    relation(D, "Objective'ler", O, "Dönem")
    relation(D, "Çeyrekler", D, "Yıl")
    relation("Form Türleri", "Yetkinlikler", "Yetkinlikler", "Form Türleri", twin_multiple=True)

    print("\n▶ İK · Özlük Bilgileri")
    plain_link("Özlük Bilgileri", "Performans Form Türü", "Form Türleri",
               app_id=ST["app_id"])

    print("\n▶ Lookup'lar")
    lookup(K, "Birim", "Çalışan", "Organizasyon Birimi")
    lookup(K, "Çalışan Hesabı", "Çalışan", "Workiom Hesabı")
    lookup(K, "Yönetici Hesabı", "Çalışan", "Birim Yöneticisi")
    lookup(K, "İK Form Türü", "Çalışan", "Performans Form Türü")
    lookup(K, "Operasyonel Oranı", "Form Türü", "Operasyonel Oranı")
    lookup(K, "Proje Oranı", "Form Türü", "Proje Oranı")
    lookup(K, "Kurumsal Oranı", "Form Türü", "Kurumsal Oranı")
    lookup(K, "Yetkinlik Oranı", "Form Türü", "Yetkinlik Oranı")
    lookup(H, "Tür Kodu", "Hedef Türü", "Kod")
    lookup(H, "Çalışan", "Karne", "Çalışan")
    lookup(H, "Dönem", "Karne", "Dönem")
    lookup(YD, "Tanım", "Yetkinlik", "Tanım / Davranış Göstergeleri")
    # yetki filtreleri için ("Kendim" filtresi kullanıcı alanında çalışır)
    for lst in (H, YD):
        lookup(lst, "Karne Sahibi", "Karne", "Çalışan (kullanıcı)")
        lookup(lst, "Karne Yöneticisi", "Karne", "Yönetici (kullanıcı)")
    lookup(O, "Yıl", "Dönem", "Yıl")
    lookup(O, "Departman Yöneticisi", "Departman", "Birim Yöneticisi Hesabı")
    lookup(O, "Dönem Başlangıç", "Dönem", "Başlangıç")
    lookup(O, "Dönem Bitiş", "Dönem", "Bitiş")
    lookup(KR, "Dönem", "Objective", "Dönem")
    lookup(KR, "Objective Sahibi", "Objective", "Sahip")
    lookup(KR, "Kaynak KPI Gerçekleşen", "Kaynak KPI", "Gerçekleşen")
    lookup(CI, "KR Sahibi", "Key Result", "Sahip")
    lookup(CI, "Objective", "Key Result", "Objective")

    print("\n▶ Formüller (satır düzeyi)")
    formula("Form Türleri", "Toplam Oran",
            f"{z('Operasyonel Oranı')} + {z('Proje Oranı')} + {z('Kurumsal Oranı')} + {z('Yetkinlik Oranı')}")
    # Workiom formülünde bölme sonucu 3 ondalığa yuvarlanır (540 / 590 → 0,915). Hassasiyet için
    # oran 100.000 ile ölçeklenir (P = oran × 100.000) ve eşikler bu ölçekte yazılır.
    P = (f"If({{{{Hedef Yönelimi=Azalan}}}}, If({z('Gerçekleşen')} = 0, 0, {z('Hedeflenen')} * 100000 / {{{{Gerçekleşen}}}}), "
         f"If({z('Hedeflenen')} = 0, 0, {z('Gerçekleşen')} * 100000 / {{{{Hedeflenen}}}}))")
    formula(H, "Gerçekleşme (%)", f"({P}) / 1000")
    formula(H, "Hedef Puanı",
            f"If(({P}) < 80000, 0, If(({P}) <= 100000, 60 + (({P}) - 80000) / 500, "
            f"If(({P}) < 120000, 100 + (({P}) - 100000) / 1000, 120)))")
    formula(H, "Ağırlıklı Skor", f"{z('Hedef Puanı')} * {z('Hedef Ağırlığı (%)')} / 100")
    for kod, ad in ((1, "Op"), (2, "Proje"), (3, "Kurumsal")):
        formula(H, f"{ad} Katkısı", f"If({z('Tür Kodu')} = {kod}, {z('Ağırlıklı Skor')}, 0)")
        formula(H, f"{ad} Ağırlık Göstergesi", f"If({z('Tür Kodu')} = {kod}, {z('Hedef Ağırlığı (%)')}, 0)")
    formula(YD, "Puan (0–100)", f"If({z('Puan (1–5)')} = 0, 0, ({{{{Puan (1–5)}}}} - 1) * 25)")
    G = f"({z('Güncel Değer')} - {z('Başlangıç Değeri')}) / ({z('Hedef Değer')} - {z('Başlangıç Değeri')})"
    formula(KR, "İlerleme",
            f"Round(If({z('Hedef Değer')} = {z('Başlangıç Değeri')}, "
            f"If({z('Güncel Değer')} = {z('Hedef Değer')}, 1, 0), "
            f"If({G} < 0, 0, If({G} > 1, 1, {G}))), 3)")
    formula(KR, "Check-in Gecikti",
            "If(isBlank({{Son Check-in Tarihi}}), 1, If(SubtractDate(Today(), {{Son Check-in Tarihi}}) > 7, 1, 0))",
            fallback="If(SubtractDate(Today(), {{Son Check-in Tarihi}}) > 7, 1, 0)")

    print("\n▶ Rollup / sayım")
    count(K, "Hedef Sayısı", "KPI Hedefleri")
    rollup(K, "Operasyonel Skor", "KPI Hedefleri", H, "Op Katkısı")
    rollup(K, "Proje Skoru", "KPI Hedefleri", H, "Proje Katkısı")
    rollup(K, "Kurumsal Skor", "KPI Hedefleri", H, "Kurumsal Katkısı")
    rollup(K, "Op. Ağırlık Toplamı", "KPI Hedefleri", H, "Op Ağırlık Göstergesi")
    rollup(K, "Proje Ağırlık Toplamı", "KPI Hedefleri", H, "Proje Ağırlık Göstergesi")
    rollup(K, "Kurumsal Ağırlık Toplamı", "KPI Hedefleri", H, "Kurumsal Ağırlık Göstergesi")
    rollup(K, "Yetkinlik Skoru", "Yetkinlik Değerlendirmeleri", YD, "Puan (0–100)", AVG)
    count(K, "OKR Sayısı", "OKR'lar")
    rollup(K, "OKR Ortalaması", "OKR'lar", O, "Kapanış Puanı", AVG)
    count(O, "KR Sayısı", "Key Result'lar")
    count(O, "Hizalanan OKR Sayısı", "Alt Objective'ler")
    rollup(O, "İlerleme", "Key Result'lar", KR, "İlerleme", AVG)
    rollup(O, "Ortalama Güven", "Key Result'lar", KR, "Güven (1–10)", AVG)
    count(KR, "Check-in Sayısı", "Check-in'ler")
    count(H, "İyileştiren OKR Sayısı", "İyileştiren OKR'lar")

    print("\n▶ Formüller (rollup'a bağlı)")
    # Renk, çeyreğin geçen süresine göre beklenen ilerlemeyle kıyaslanır (OKR-04).
    formula(O, "Beklenen İlerleme",
            "Round(If(SubtractDate({{Dönem Bitiş}}, {{Dönem Başlangıç}}) <= 0, 0, "
            "If(SubtractDate(Today(), {{Dönem Başlangıç}}) < 0, 0, "
            "If(SubtractDate({{Dönem Bitiş}}, Today()) < 0, 1, "
            "SubtractDate(Today(), {{Dönem Başlangıç}}) / SubtractDate({{Dönem Bitiş}}, {{Dönem Başlangıç}})))), 3)")
    formula(O, "İlerleme Farkı", f"Round({z('İlerleme')} - {z('Beklenen İlerleme')}, 3)")
    formula(K, "Ağırlık Hatası",
            f"If({z('Op. Ağırlık Toplamı')} = 100, 0, 1) + If({z('Proje Ağırlık Toplamı')} = 100, 0, 1)"
            f" + If({z('Kurumsal Ağırlık Toplamı')} = 100, 0, 1)")
    formula(K, "KPI Skoru",
            f"Round({z('Operasyonel Skor')} * {z('Operasyonel Oranı')} / 100 + {z('Proje Skoru')} * "
            f"{z('Proje Oranı')} / 100 + {z('Kurumsal Skor')} * {z('Kurumsal Oranı')} / 100, 2)")
    formula(K, "Toplam Puan",
            f"Round({z('KPI Skoru')} + {z('Yetkinlik Skoru')} * {z('Yetkinlik Oranı')} / 100, 2)")

    print("\n" + ("✅ Hatasız" if not FAILED else "⚠️  Hatalar:\n  " + "\n  ".join(FAILED)))
