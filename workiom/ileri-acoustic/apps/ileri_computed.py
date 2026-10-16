"""
İleri Acoustic — hesaplanan alanlar (formül, lookup, toplam/rollup, sayım).
5 uygulama build edildikten SONRA çalıştırılır (state/ dosyalarındaki ID'leri kullanır):

    python3 apps/ileri_computed.py

İdempotent: aynı adlı alan listede varsa atlanır.

Formül yazımı:
    {{Alan}}             → _F_<id>
    {{Alan=Seçenek}}     → _F_<id>_V_<seçenek uuid z-format>  (SELECT karşılaştırması)
Filtreli toplam / sayım (API'de rollup filtresi yok) → çocuk listede 0/1 veya 0/değer
"gösterge" formülü + üst listede SUM rollup.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from workiom.client import WorkiomClient, WorkiomAPIError  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
KEY = (ROOT / ".env").read_text().split("=", 1)[1].strip()
c = WorkiomClient(KEY)

REG: dict[str, str] = {}
for sf in (ROOT / "state").glob("*.json"):
    d = json.loads(sf.read_text())
    for ln, ld in d.get("lists", {}).items():
        REG[ln] = ld["id"]

_FIELDS: dict[str, list[dict]] = {}
FAILED: list[str] = []


def fields(lst: str, refresh=False) -> list[dict]:
    if refresh or lst not in _FIELDS:
        _FIELDS[lst] = c.get_all_fields(REG[lst])
    return _FIELDS[lst]


def fld(lst: str, name: str) -> dict:
    for f in fields(lst):
        if f["name"] == name:
            return f
    for f in fields(lst, refresh=True):
        if f["name"] == name:
            return f
    raise KeyError(f"{lst}.{name}")


def exists(lst, name):
    return any(f["name"] == name for f in fields(lst, refresh=True))


def _opt(lst, fname, label):
    f = fld(lst, fname)
    src = f
    # lookup of a select → options live on the source field
    if not f.get("staticListValues") and f.get("linkedFieldId") and f.get("lookupFieldId"):
        hop = next(x for x in fields(lst) if x["id"] == f["lookupFieldId"])
        tgt_list = next(n for n, i in REG.items() if i == hop["linkedListId"])
        src = next(x for x in fields(tgt_list) if x["id"] == f["linkedFieldId"])
    for o in src.get("staticListValues", []):
        if o["label"] == label:
            return o["id"].replace("-", "z")
    raise KeyError(f"option {lst}.{fname}={label}")


def compile_expr(lst, expr):
    def rep(m):
        tok = m.group(1)
        if "=" in tok:
            fname, label = tok.split("=", 1)
            fid = fld(lst, fname)["id"]
            return f"_F_{fid} = _F_{fid}_V_{_opt(lst, fname, label)}"
        return f"_F_{fld(lst, tok)['id']}"
    return re.sub(r"\{\{(.+?)\}\}", rep, expr)


def log(kind, lst, name, msg):
    print(f"  {msg:<8s} {kind:<8s} {lst} · {name}")


def create(lst, body, kind):
    name = body["name"]
    if exists(lst, name):
        log(kind, lst, name, "exists")
        return
    try:
        r = c.create_field(REG[lst], {**body, "isVisible": True, "isRequired": False})
        _FIELDS.pop(lst, None)
        log(kind, lst, name, "created")
        return r
    except WorkiomAPIError as e:
        FAILED.append(f"{kind} {lst}.{name}: {e.message} {e.details}")
        log(kind, lst, name, "FAILED")
        print("           ", e.message, e.details[:200])


def formula(lst, name, expr, dtype=1, fallback=None):
    try:
        compiled = compile_expr(lst, expr)
    except KeyError as e:
        print(f"           compile error {e}; fallback")
        compiled = compile_expr(lst, fallback) if fallback else None
        if not compiled:
            FAILED.append(f"formula {lst}.{name}: {e}")
            return
    r = create(lst, {"name": name, "dataType": dtype, "isComputed": True, "expression": compiled},
               "formula")
    if r is None and fallback and not exists(lst, name):
        FAILED.pop()
        create(lst, {"name": name, "dataType": dtype, "isComputed": True,
                     "expression": compile_expr(lst, fallback)}, "formula*")


def _lookup(lst, name, via, src_field):
    link = fld(lst, via)
    tgt = next(n for n, i in REG.items() if i == link["linkedListId"])
    src = fld(tgt, src_field)
    create(lst, {"name": name, "dataType": src["dataType"], "isLookup": True,
                 "linkedFieldId": src["id"], "lookupFieldId": link["id"]}, "lookup")


SUM, AVG, MIN, MAX, CNT, FIRST, LAST = 0, 1, 2, 3, 4, 5, 6


def _rollup(parent, name, backlink, child, value_field, summary=SUM, dtype=1):
    bl = fld(parent, backlink)
    vf = fld(child, value_field)
    create(parent, {"name": name, "dataType": dtype, "isRollup": True,
                    "linkedListId": REG[child], "linkedFieldId": vf["id"],
                    "rollupFieldId": bl["id"], "rollupSummaryType": summary}, "rollup")


def _count(parent, name, backlink):
    create(parent, {"name": name, "dataType": 12,
                    "countLocalLinkedFieldId": fld(parent, backlink)["id"]}, "count")


def _safe(fn):
    def w(*a, **k):
        try:
            return fn(*a, **k)
        except KeyError as e:
            FAILED.append(f"{fn.__name__} {a[:2]}: eksik {e}")
            print(f"  SKIP     {a[0]} · {a[1]} (eksik {e})")
    return w


lookup, rollup, count = _safe(_lookup), _safe(_rollup), _safe(_count)

C = "Coalesce({{%s}}, 0)"


def z(f):
    return C % f


# ═══ A3 · Duvar Kalemleri ═══════════════════════════════════════════════════
print("\n▶ A3 Teknik Hesaplama")
D = "Duvar Kalemleri"
formula(D, "m²", f"Round({z('Uzunluk L (cm)')} * {z('Yükseklik H (cm)')} * {z('Sistem Adedi')} / 10000, 2)")
formula(D, "Panel Yüksekliği (cm)", f"If({z('Yükseklik H (cm)')} > 5, {{{{Yükseklik H (cm)}}}} - 5, 0)")
formula(D, "Panel Genişliği (cm)", z("Standart Panel Genişliği (cm)"))
formula(D, "Standart Panel Adedi",
        f"If({z('Standart Panel Genişliği (cm)')} > 0, "
        f"Round({z('Uzunluk L (cm)')} / {{{{Standart Panel Genişliği (cm)}}}} + 0.4999, 0), 0)")
formula(D, "Toplam Panel Adedi",
        f"({z('Standart Panel Adedi')} + {z('Teleskopik Panel')}) * {z('Sistem Adedi')}")
formula(D, "Teleskopik Panel Toplamı", f"{z('Teleskopik Panel')} * {z('Sistem Adedi')}")
formula(D, "Toplam Kapı Adedi",
        f"({z('Tek Kanat Kapı Adedi')} + {z('Çift Kanat Kapı Adedi')} + {z('İnce Kapı TK Adedi')}"
        f" + {z('İnce Kapı ÇK Adedi')}) * {z('Sistem Adedi')}")
formula(D, "Birim Fiyat", z("m² Birim Fiyatı"))
formula(D, "Kalem Tutarı",
        f"Round({z('m²')} * {z('Birim Fiyat')} + {z('Toplam Kapı Adedi')} * {z('Kapı Birim Fiyatı')}"
        f" + {z('Teleskopik Panel Toplamı')} * {z('Teleskopik Panel Birim Fiyatı')}, 2)")

# ═══ A3 · Reçete Kalemleri ══════════════════════════════════════════════════
R = "Reçete Kalemleri"
lookup(R, "Toplam Panel Adedi", "Duvar Kalemi", "Toplam Panel Adedi")
lookup(R, "Panel Yüksekliği (cm)", "Duvar Kalemi", "Panel Yüksekliği (cm)")
lookup(R, "Panel Genişliği (cm)", "Duvar Kalemi", "Panel Genişliği (cm)")
lookup(R, "Uzunluk L (cm)", "Duvar Kalemi", "Uzunluk L (cm)")
lookup(R, "Sistem Adedi", "Duvar Kalemi", "Sistem Adedi")
formula(R, "Adet",
        f"If({{{{Kaynak=Şablon}}}}, {z('Toplam Panel Adedi')} * {z('Adet Çarpanı')}"
        f" + {z('Adet Sabiti')} * {z('Sistem Adedi')}, 0)")
formula(R, "Kesim Ölçüsü (cm)",
        f"If({{{{Ölçü Bazı=Yükseklik}}}}, {z('Panel Yüksekliği (cm)')} + {z('Ölçü Farkı (cm)')}, "
        f"If({{{{Ölçü Bazı=Genişlik}}}}, {z('Panel Genişliği (cm)')} + {z('Ölçü Farkı (cm)')}, "
        f"If({{{{Ölçü Bazı=Uzunluk}}}}, {z('Uzunluk L (cm)')} + {z('Ölçü Farkı (cm)')}, 0)))",
        fallback=f"{z('Panel Yüksekliği (cm)')} + {z('Ölçü Farkı (cm)')}")
formula(R, "Toplam İhtiyaç",
        f"If({{{{Kaynak=Manuel Düzeltme}}}}, {z('Manuel Miktar')}, "
        f"If({{{{Birim=Metre}}}}, Round({z('Adet')} * {z('Kesim Ölçüsü (cm)')} / 100, 2), {z('Adet')}))",
        fallback=f"If({{{{Kaynak=Manuel Düzeltme}}}}, {z('Manuel Miktar')}, {z('Adet')})")

# ═══ Otomatik numaraların formül kopyaları (otomasyon döngülerinde otomatik numara okunamıyor) ═══
formula("Teklif Revizyonları", "Kayıt No (sayı)", "{{Kayıt No}}")
formula("Talepler", "Talep No (sayı)", "{{Talep No}}")

# ═══ A2 · Teklif Revizyonları ═══════════════════════════════════════════════
print("\n▶ A2 Proje & Teklif")
TR = "Teklif Revizyonları"
count(TR, "Duvar Kalemi Sayısı", "Duvar Kalemleri")
rollup(TR, "Toplam Panel", "Duvar Kalemleri", D, "Toplam Panel Adedi")
rollup(TR, "Toplam Teleskop", "Duvar Kalemleri", D, "Teleskopik Panel Toplamı")
rollup(TR, "Toplam Kapı", "Duvar Kalemleri", D, "Toplam Kapı Adedi")
rollup(TR, "Toplam m²", "Duvar Kalemleri", D, "m²")
rollup(TR, "Ara Toplam", "Duvar Kalemleri", D, "Kalem Tutarı")
formula(TR, "Teklif Tutarı",
        f"Round({z('Ara Toplam')} * (1 - {z('İskonto (%)')} / 100) + {z('Nakliye Bedeli')}"
        f" + {z('Montaj Bedeli')} + {z('Ambalaj Bedeli')}, 2)")

# ═══ A2 · Teklifler ═════════════════════════════════════════════════════════
T = "Teklifler"
count(T, "Revizyon Sayısı", "Revizyonlar")
lookup(T, "Geçerli Gönderilen Tutar", "Geçerli Revizyon", "Gönderilen Tutar")
lookup(T, "Geçerli Revizyon Tutarı", "Geçerli Revizyon", "Teklif Tutarı")
lookup(T, "Para Birimi", "Geçerli Revizyon", "Para Birimi")
lookup(T, "Geçerli Toplam Panel", "Geçerli Revizyon", "Toplam Panel")
lookup(T, "Geçerli Toplam m²", "Geçerli Revizyon", "Toplam m²")
formula(T, "Geçerli Tutar",
        f"If({z('Geçerli Gönderilen Tutar')} > 0, {{{{Geçerli Gönderilen Tutar}}}}, "
        f"{z('Geçerli Revizyon Tutarı')})")
KAYIP = "({{Teklif Durumu=Kaybedildi}} or {{Teklif Durumu=İptal}})"
formula(T, "Aktif Tutar (gösterge)", f"If({KAYIP}, 0, {z('Geçerli Tutar')})")
formula(T, "Aktif Panel (gösterge)", f"If({KAYIP}, 0, {z('Geçerli Toplam Panel')})")
formula(T, "Aktif m² (gösterge)", f"If({KAYIP}, 0, {z('Geçerli Toplam m²')})")
formula(T, "Açık (gösterge)",
        "If({{Teklif Durumu=Hazırlanıyor}} or {{Teklif Durumu=Gönderildi}} or "
        "{{Teklif Durumu=Revizyonda}}, 1, 0)")
formula(T, "Kazanıldı (gösterge)", "If({{Teklif Durumu=Kazanıldı}}, 1, 0)")
formula(T, "Kazanılan Tutar (gösterge)", f"If({{{{Teklif Durumu=Kazanıldı}}}}, {z('Geçerli Tutar')}, 0)")
# Tarih rollup'ı API'de yok → düz tarih alanı, PRJ-08 her takipte günceller
create(T, {"name": "Son Takip Tarihi", "dataType": 2}, "field")

# ═══ A4 · İş Emirleri / Üretim Planları ═════════════════════════════════════
print("\n▶ A4 Planlama & Üretim")
IE = "İş Emirleri"
ACIK = "({{Durum=Bekliyor}} or {{Durum=Hazır}} or {{Durum=Devam Ediyor}})"
formula(IE, "Açık (gösterge)", f"If({ACIK}, 1, 0)")
formula(IE, "Açık Hazırlık (gösterge)", f"If({ACIK} and {{{{Aşama Grubu=Hazırlık}}}}, 1, 0)",
        fallback=f"If({ACIK} and {z('İstasyon Sırası')} <= 6, 1, 0)")
formula(IE, "Açık Toplama (gösterge)", f"If({ACIK} and {{{{Aşama Grubu=Toplama}}}}, 1, 0)",
        fallback=f"If({ACIK} and {z('İstasyon Sırası')} = 7, 1, 0)")

UP = "Üretim Planları"
lookup(UP, "Toplam Panel", "Esas Revizyon", "Toplam Panel")
lookup(UP, "Toplam Teleskop", "Esas Revizyon", "Toplam Teleskop")
lookup(UP, "Toplam Kapı", "Esas Revizyon", "Toplam Kapı")
formula(UP, "İş Günü Sayısı",
        "If(IsBlank({{Başlangıç Tarihi}}) or IsBlank({{Hedef Bitiş Tarihi}}), 0, "
        "Round((SubtractDate({{Hedef Bitiş Tarihi}}, {{Başlangıç Tarihi}}) + 1) * 5 / 7, 0))")
formula(UP, "Tamamlanma (%)",
        f"If({z('Toplam Panel')} + {z('Toplam Kapı')} = 0, 0, "
        f"Round(({z('Biten Panel')} + {z('Biten Kapı')}) / ({{{{Toplam Panel}}}} + {z('Toplam Kapı')}) * 100, 0))")
rollup(UP, "Açık İş Emri Sayısı", "İş Emirleri", IE, "Açık (gösterge)")
rollup(UP, "Açık Hazırlık İş Emri", "İş Emirleri", IE, "Açık Hazırlık (gösterge)")
rollup(UP, "Açık Toplama İş Emri", "İş Emirleri", IE, "Açık Toplama (gösterge)")
count(UP, "Malzeme İhtiyacı Sayısı", "Malzeme İhtiyaçları")
KAPALI = "({{Durum=Montaj Tamamlandı}} or {{Durum=Montaj Yok}})"
formula(UP, "Açık Plan (gösterge)", f"If({KAPALI}, 0, 1)")
formula(UP, "Termin Durumu",
        f"If({KAPALI} or IsBlank({{{{Hedef Bitiş Tarihi}}}}), '', "
        f"If(Today() > {{{{Hedef Bitiş Tarihi}}}}, 'Gecikti', "
        f"If(SubtractDate({{{{Hedef Bitiş Tarihi}}}}, Today()) <= 2 and {z('Tamamlanma (%)')} < 80, "
        f"'Riskli', 'Zamanında')))", dtype=0)

# ═══ A2 · Sözleşmeler / Projeler / A1 Firmalar ══════════════════════════════
print("\n▶ A2 / A1 toplamlar")
SZ = "Sözleşmeler"
rollup(SZ, "Açık Üretim Planı Sayısı", "Üretim Planları", UP, "Açık Plan (gösterge)")

P = "Projeler"
rollup(P, "Geçerli Teklif Tutarı", "Teklifler", T, "Aktif Tutar (gösterge)")
rollup(P, "Toplam Panel", "Teklifler", T, "Aktif Panel (gösterge)")
rollup(P, "Toplam m²", "Teklifler", T, "Aktif m² (gösterge)")
rollup(P, "Açık Teklif Sayısı", "Teklifler", T, "Açık (gösterge)")
rollup(P, "Kazanılan Teklif Sayısı", "Teklifler", T, "Kazanıldı (gösterge)")
rollup(P, "Kazanılan Tutar", "Teklifler", T, "Kazanılan Tutar (gösterge)")
rollup(P, "Açık Üretim Planı Sayısı", "Sözleşmeler", SZ, "Açık Üretim Planı Sayısı")
# Seçim rollup'ı API'de yok → seçim alanı, PRJ-05 geçerli teklifin para birimini yazar
create(P, {"name": "Para Birimi", "dataType": 4, "defaultValue": None,
           "staticListValues": [{"id": u, "label": l, "color": col, "order": i} for i, (u, l, col) in
                                enumerate([(str(__import__("uuid").uuid4()), "USD", "#5bd77e"),
                                           (str(__import__("uuid").uuid4()), "EUR", "#f5c044"),
                                           (str(__import__("uuid").uuid4()), "TL", "#ea346f")])]},
       "field")

FI = "Firmalar"
rollup(FI, "Toplam Teklif Tutarı", "Projeler", P, "Geçerli Teklif Tutarı")
rollup(FI, "Kazanılan Tutar", "Projeler", P, "Kazanılan Tutar")

TA = "Talepler"
formula(TA, "İlk Yanıt Süresi (saat)",
        "If(IsBlank({{İlk Yanıt Tarihi}}) or IsBlank({{Talep Tarihi}}), 0, "
        "Round(SubtractDate({{İlk Yanıt Tarihi}}, {{Talep Tarihi}}) * 24, 1))")

# ═══ A5 · Satınalma & Stok ══════════════════════════════════════════════════
print("\n▶ A5 Satınalma & Stok")
SH = "Stok Hareketleri"
formula(SH, "İşaretli Miktar",
        f"If({{{{Hareket Türü=Çıkış}}}}, 0 - {z('Miktar')}, {z('Miktar')})")
MI = "Malzeme İhtiyaçları"
formula(MI, "Açık Miktar (gösterge)", f"If({{{{Durum=Açık}}}}, {z('İhtiyaç Miktarı')}, 0)")
ST = "Satınalma Talepleri"
formula(ST, "Açık Sipariş (gösterge)",
        f"If({{{{Durum=Onaylandı}}}} or {{{{Durum=Sipariş Verildi}}}}, {z('Miktar')}, 0)")
formula(ST, "Bekleyen Talep (gösterge)",
        f"If({{{{Durum=Talep}}}} or {{{{Durum=Teklif}}}} or {{{{Durum=Onay Bekliyor}}}}, {z('Miktar')}, 0)")
M = "Malzemeler"
rollup(M, "Stok Bakiyesi", "Stok Hareketleri", SH, "İşaretli Miktar")
rollup(M, "Rezerve Miktar", "Malzeme İhtiyaçları", MI, "Açık Miktar (gösterge)")
rollup(M, "Açık Sipariş Miktarı", "Satınalma Talepleri", ST, "Açık Sipariş (gösterge)")
rollup(M, "Bekleyen Talep Miktarı", "Satınalma Talepleri", ST, "Bekleyen Talep (gösterge)")
formula(M, "Serbest Stok", f"{z('Stok Bakiyesi')} - {z('Rezerve Miktar')}")
formula(M, "Net Durum",
        f"{z('Stok Bakiyesi')} + {z('Açık Sipariş Miktarı')} + {z('Bekleyen Talep Miktarı')}"
        f" - {z('Rezerve Miktar')}")
formula(M, "Kritik mi", f"If({z('Minimum Stok')} > 0 and {z('Stok Bakiyesi')} < {{{{Minimum Stok}}}}, 1, 0)")
lookup(MI, "Mevcut Stok", "Malzeme", "Stok Bakiyesi")
lookup(MI, "Net Durum", "Malzeme", "Net Durum")

print("\n" + ("✅ Tüm hesaplanan alanlar hazır." if not FAILED else "⚠️  Hatalı alanlar:"))
for f in FAILED:
    print("   ", f)
