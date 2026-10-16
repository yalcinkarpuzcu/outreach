"""
İleri Acoustic — ana veri (seed). Otomasyonlardan ÖNCE çalıştırılır.
Birincil alan değerine göre upsert: aynı ad varsa atlanır.
LINK değerleri hedef listenin birincil alan değeriyle verilir.

Not: Sistem fiyatları, panel genişliği ve reçete şablonu katsayıları G12 (formül envanteri)
teyidine kadar DEMO değerlerdir.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workiom.client import WorkiomClient  # noqa: E402

c = WorkiomClient((ROOT / ".env").read_text().split("=", 1)[1].strip())
OWNER = str(c.get("/api/services/app/Session/GetCurrentLoginInformations")["user"]["id"])

REG = {}
for sf in (ROOT / "state").glob("*.json"):
    for ln, ld in json.loads(sf.read_text()).get("lists", {}).items():
        REG[ln] = ld["id"]

_F, _REC = {}, {}


def fields(lst):
    if lst not in _F:
        _F[lst] = {f["name"]: f for f in c.get_all_fields(REG[lst])}
    return _F[lst]


def primary(lst):
    return next(f for f in fields(lst).values() if f.get("isPrimary"))


def records(lst):
    if lst not in _REC:
        pid = str(primary(lst)["id"])
        _REC[lst] = {r.get(pid): r["_id"] for r in c.get_all_records(REG[lst])}
    return _REC[lst]


def value(lst, fname, v):
    f = fields(lst)[fname]
    dt = f["dataType"]
    if dt in (4, 17):  # select / multiselect
        opts = {o["label"]: o["id"] for o in f.get("staticListValues", [])}
        return [opts[x] for x in v] if dt == 17 else opts[v]
    if dt == 5:  # link
        tgt = next(n for n, i in REG.items() if i == f["linkedListId"])
        vals = v if isinstance(v, list) else [v]
        return [{"_id": records(tgt)[x]} for x in vals]
    if dt == 6:
        return {"id": OWNER} if v == "OWNER" else v
    return v


def seed(lst, rows):
    pname = primary(lst)["name"]
    made = 0
    for row in rows:
        if row[pname] in records(lst):
            continue
        payload = {str(fields(lst)[k]["id"]): value(lst, k, v) for k, v in row.items()}
        rid = c.create_record(REG[lst], payload)
        records(lst)[row[pname]] = rid
        made += 1
    print(f"  🌱 {lst:<22s} +{made} (toplam {len(rows)})")


# ─── A4 · İstasyonlar (başlangıç kayıtları, G15'te teyit) ───────────────────
seed("İstasyonlar", [
    {"İstasyon Adı": n, "Sıra": i, "Aşama Grubu": g, "Aktif mi": True, "Sorumlu": "OWNER"}
    for i, (n, g) in enumerate([
        ("Alüminyum Kesim/İşleme", "Hazırlık"), ("Alüminyum Boya", "Hazırlık"), ("Ray Boya", "Hazırlık"),
        ("Ahşap/Yüzey", "Hazırlık"), ("Cam İşleri", "Hazırlık"), ("Mekanik", "Hazırlık"),
        ("Toplama", "Toplama"), ("Paketleme", "Paketleme")], start=1)])

# ─── A3 · Sistemler ─────────────────────────────────────────────────────────
seed("Sistemler", [
    {"Sistem Adı": n, "Sistem Ailesi": fam, "Standart Panel Genişliği (cm)": w, "Kalınlık (mm)": t,
     "m² Birim Fiyatı": m2, "Kapı Birim Fiyatı": kapi, "Teleskopik Panel Birim Fiyatı": tel, "Aktif mi": True}
    for n, fam, w, t, m2, kapi, tel in [
        ("PANELITE", "Hareketli Panel", 100, 100, 185, 650, 240),
        ("PANSMART", "Hareketli Panel", 110, 105, 210, 700, 260),
        ("PANPLUS", "Hareketli Panel", 120, 110, 235, 750, 280),
        ("PANSLIM 80", "Hareketli Panel", 100, 80, 160, 600, 220),
        ("PANSLIDE WOOD", "Hareketli Panel", 90, 85, 175, 620, 230),
        ("EPART-DOORSON", "Kapı", 90, 50, 140, 550, 0)]])

# ─── A5 · Tedarikçiler / Malzemeler ─────────────────────────────────────────
seed("Tedarikçiler", [
    {"Firma Adı": "Demir Alüminyum A.Ş.", "Yetkili": "Satış Birimi",
     "Tedarik Ettiği Kategoriler": ["Profil", "Ray"]},
    {"Firma Adı": "Kale Ahşap Panel Ltd.", "Yetkili": "Satış Birimi",
     "Tedarik Ettiği Kategoriler": ["Plaka", "Yüzey"]},
    {"Firma Adı": "Akustik Yalıtım San.", "Yetkili": "Satış Birimi",
     "Tedarik Ettiği Kategoriler": ["Aksesuar", "Makara", "Boya", "Ambalaj"]},
])
M = [
    ("AL-YK-01", "Yan Kapak Profili", "Profil", "Metre", True, 21, 300, "Demir Alüminyum A.Ş."),
    ("AL-UP-01", "U Profil", "Profil", "Metre", True, 21, 300, "Demir Alüminyum A.Ş."),
    ("AL-GP-01", "Giyotin Profili", "Profil", "Metre", True, 21, 200, "Demir Alüminyum A.Ş."),
    ("AL-GB-01", "Giyotin Borusu", "Profil", "Metre", False, 10, 150, "Demir Alüminyum A.Ş."),
    ("RAY-R1", "R1 Ray", "Ray", "Metre", True, 30, 100, "Demir Alüminyum A.Ş."),
    ("MAK-M1", "M1 Makara", "Makara", "Adet", False, 14, 200, "Akustik Yalıtım San."),
    ("MDF-KE-A319", "MDF Lam KE A319", "Plaka", "Plaka", False, 7, 40, "Kale Ahşap Panel Ltd."),
    ("YAL-TY-50", "Taşyünü 50 mm", "Aksesuar", "m²", False, 7, 150, "Akustik Yalıtım San."),
    ("BOYA-9016", "Fırın Boya RAL 9016 Mat", "Boya", "Kg", False, 5, 50, "Akustik Yalıtım San."),
    ("AMB-KK", "Kenar Karton", "Ambalaj", "Adet", False, 3, 300, "Akustik Yalıtım San."),
]
seed("Malzemeler", [
    {"Malzeme Adı": ad, "Malzeme Kodu": kod, "Kategori": kat, "Birim": birim, "Özel Üretim mi": ozel,
     "Tedarik Süresi (gün)": sure, "Minimum Stok": mn, "Varsayılan Tedarikçi": ted}
    for kod, ad, kat, birim, ozel, sure, mn, ted in M])

# Açılış stoku (Sayım Düzeltme) — STN-13 gibi otomasyonlar kurulmadan önce
seed("Stok Hareketleri", [
    {"Açıklama": f"Açılış sayımı – {ad}", "Malzeme": ad, "Hareket Türü": "Sayım Düzeltme",
     "Miktar": mn * 2 if i % 3 else mn // 2, "Tarih": "2026-10-16T00:00:00Z", "Yapan": "OWNER"}
    for i, (kod, ad, kat, birim, ozel, sure, mn, ted) in enumerate(M)])

# ─── A3 · Reçete Şablonu (PANELITE – G12 teyidine kadar demo katsayılar) ─────
R = [  # kod, liste türü, malzeme, istasyon, çarpan, sabit, ölçü bazı, fark, adet kuralı, ölçü kuralı
    ("PNL-AL-YANKAPAK", "Alüminyum Kesim", "Yan Kapak Profili", "Alüminyum Kesim/İşleme", 2, 0,
     "Yükseklik", -2, "Toplam Panel Adedi × 2", "Panel Yüksekliği − 2"),
    ("PNL-AL-UPROFIL", "Alüminyum Kesim", "U Profil", "Alüminyum Kesim/İşleme", 2, 0,
     "Genişlik", -1, "Toplam Panel Adedi × 2", "Panel Genişliği − 1"),
    ("PNL-AL-GIYOTIN", "Alüminyum Kesim", "Giyotin Profili", "Alüminyum Kesim/İşleme", 1, 0,
     "Genişlik", 0, "Toplam Panel Adedi × 1", "Panel Genişliği"),
    ("PNL-GB-BORU", "Giyotin Borusu", "Giyotin Borusu", "Alüminyum Kesim/İşleme", 1, 0,
     "Genişlik", -4, "Toplam Panel Adedi × 1", "Panel Genişliği − 4"),
    ("PNL-AHS-MDF", "Ahşap Kesim", "MDF Lam KE A319", "Ahşap/Yüzey", 2, 0,
     "Yükseklik", -6, "Toplam Panel Adedi × 2 (iki yüz)", "Panel Yüksekliği − 6"),
    ("PNL-AKS-TASYUNU", "Aksesuar", "Taşyünü 50 mm", "Mekanik", 1, 0, "Yok", 0,
     "Toplam Panel Adedi × 1", "–"),
    ("PNL-BOYA-AL", "Boya", "Fırın Boya RAL 9016 Mat", "Alüminyum Boya", 0.4, 0, "Yok", 0,
     "Toplam Panel Adedi × 0,4 kg", "–"),
    ("PNL-RAY-R1", "Alüminyum Kesim", "R1 Ray", "Ray Boya", 0, 1, "Uzunluk", 10,
     "Duvar başına 1 × Sistem Adedi", "Uzunluk L + 10"),
    ("PNL-MAKARA", "Aksesuar", "M1 Makara", "Mekanik", 2, 0, "Yok", 0, "Toplam Panel Adedi × 2", "–"),
    ("PNL-AMB-KARTON", "Ambalaj", "Kenar Karton", "Paketleme", 1, 0, "Yok", 0, "Toplam Panel Adedi × 1", "–"),
]
seed("Reçete Şablonu", [
    {"Şablon Kodu": kod, "Sistem": "PANELITE", "Liste Türü": lt, "Malzeme": mlz, "İstasyon": ist,
     "Adet Çarpanı": carp, "Adet Sabiti": sabit, "Ölçü Bazı": baz, "Ölçü Farkı (cm)": fark,
     "Adet Kuralı": akural, "Ölçü Kuralı": okural, "Sıra": i, "Aktif mi": True}
    for i, (kod, lt, mlz, ist, carp, sabit, baz, fark, akural, okural) in enumerate(R, start=1)])

# ─── A3 · Hesap Parametreleri ───────────────────────────────────────────────
seed("Hesap Parametreleri", [
    {"Parametre": p, "Parametre Kodu": k, "Değer": v, "Para Birimi": pb, "Birim": b,
     "Geçerlilik Tarihi": "2026-12-31T00:00:00Z"}
    for p, k, v, pb, b in [
        ("Nakliye bedeli (yurt içi)", "FYT-NAKLIYE", 500, "TL", "sabit"),
        ("Ekspertiz bedeli", "FYT-EKSPERTIZ", 600, "TL", "sabit"),
        ("Ambalaj fiyatı (panel başı)", "FYT-AMBALAJ", 4, "USD", "adet"),
        ("Ray R1 metre fiyatı", "FYT-RAY-R1", 25, "USD", "m"),
        ("Montaj bedeli (m²)", "FYT-MONTAJ-M2", 12, "USD", "m²"),
    ]])

# ─── A1 · Demo firmalar ve kişiler ──────────────────────────────────────────
seed("Firmalar", [
    {"Firma Adı": "DEMO Grand Otel İzmir", "Müşteri Tipi": "Yurt İçi", "Ülke": "Türkiye", "Şehir": "İzmir",
     "Firma Türü": "Son Kullanıcı", "Sektör": "Otel", "Müşteri Durumu": "Aday", "Satış Temsilcisi": "OWNER"},
    {"Firma Adı": "DEMO Accra Conference Centre", "Müşteri Tipi": "Yurt Dışı", "Ülke": "Gana",
     "Firma Türü": "Müteahhit", "Sektör": "Kongre / Etkinlik", "Müşteri Durumu": "Aday",
     "Satış Temsilcisi": "OWNER"},
])
seed("Kişiler", [
    {"Ad Soyad": "DEMO Ayşe Yılmaz", "Firma": "DEMO Grand Otel İzmir", "Unvan / Rol": "Satın Alma Müdürü",
     "Telefon": "+905320000001", "E-posta": "ayse.demo@example.com", "Dil": "TR"},
    {"Ad Soyad": "DEMO Kwame Mensah", "Firma": "DEMO Accra Conference Centre", "Unvan / Rol": "Architect",
     "Telefon": "+233200000001", "E-posta": "kwame.demo@example.com", "Dil": "EN"},
])
print("✅ Seed tamam")
