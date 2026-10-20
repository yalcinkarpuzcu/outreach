"""Performans Yönetimi — referans verisi + demo verisi (İK dahil).

    python3 apps/performans_seed.py            # hepsi
    python3 apps/performans_seed.py ref ik     # yalnızca seçilen adımlar

Adımlar: ref (dönem, form türü, hedef türü, yetkinlik) · ik (İK'ya demo çalışan, birim yöneticileri,
form türü) · karne (2025 tamamlanmış + 2026 aktif karneler, KPI hedefleri, yetkinlik puanları) ·
okr (2026-Ç3 kapanmış + 2026-Ç4 aktif OKR'lar, KR'lar, check-in'ler) · post (performans grubu,
renk, kapanış puanı — otomasyonların yapacağı işi demo veride bir kez yapar).

Bildirim gitmemesi için tüm kullanıcı alanlarında yalnızca tenant sahibi (Yalçın) kullanılır.
2025'te üç çalışana Excel'deki A / B / C örnekleri birebir girilir: KPI Skoru 63,10 / 85,91 / 70,05.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from wk import client  # noqa: E402

c = client()
API = "/api/services/app"
ST = json.loads(next((ROOT / "state").glob("performans*.json")).read_text())
REG = {ln: ld["id"] for ln, ld in ST["lists"].items()}
REG["Özlük Bilgileri"] = "cc279e0f-af5a-4ff8-986f-a31793432ddf"
REG["Organizasyon"] = "a045d821-d480-433d-b32d-0bae28de0689"
REG["Cinsiyet"] = "8953ae1d-26a4-4931-b415-55bdf95b6bc7"
YALCIN = 161668
rnd = random.Random(42)

_F: dict[str, list] = {}


def fields(lst):
    if lst not in _F:
        r = c.get(f"{API}/Fields/GetAll", {"listId": REG[lst]})
        _F[lst] = r.get("items", r) if isinstance(r, dict) else r
    return _F[lst]


def F(lst, name):
    for f in fields(lst):
        if f["name"] == name:
            return str(f["id"])
    raise KeyError(f"{lst}.{name}")


def O(lst, fname, label):
    f = next(x for x in fields(lst) if x["name"] == fname)
    return next(o["id"] for o in f["staticListValues"] if o["label"] == label)


def STATUS(lst, label):
    f = next(x for x in fields(lst) if x["dataType"] == 16)
    return str(f["id"]), next(o["id"] for o in f["staticListValues"] if o["label"] == label)


def user(uid=YALCIN):
    return {"id": str(uid)}


def link(*ids):
    return [{"_id": i} for i in ids if i]


def records(lst):
    out, skip = [], 0
    while True:
        r = c.post(f"{API}/Data/All", {"listId": REG[lst], "maxResultCount": 500, "skipCount": skip})
        out += r["items"]
        if len(out) >= r["totalCount"] or not r["items"]:
            return out
        skip += 500


def payload(lst, vals: dict):
    """{'Alan adı': değer} → {field_id: değer}; seçim alanında etiket verilirse id'ye çevrilir."""
    out = {}
    for k, v in vals.items():
        if v is None:
            continue
        f = next(x for x in fields(lst) if x["name"] == k)
        if f["dataType"] in (4, 16) and isinstance(v, str):
            v = next(o["id"] for o in f["staticListValues"] if o["label"] == v)
        out[str(f["id"])] = v
    return out


def _retry(fn):
    from workiom.client import WorkiomAPIError
    for i in range(4):
        try:
            return fn()
        except WorkiomAPIError as e:
            if "curl" not in e.message or i == 3:
                raise
            import time
            time.sleep(3 * (i + 1))


def create(lst, vals):
    return _retry(lambda: c.post(f"{API}/Data/Create", payload(lst, vals), {"listId": REG[lst]})["_id"])


def update(lst, rid, vals):
    _retry(lambda: c.put(f"{API}/Data/UpdatePartial", payload(lst, vals), {"listId": REG[lst], "id": rid}))


_UP: dict[str, dict] = {}


def upsert(lst, key_field, key, vals):
    kid = F(lst, key_field)
    if lst not in _UP:
        _UP[lst] = {r.get(kid): r["_id"] for r in records(lst)}
    if key in _UP[lst]:
        update(lst, _UP[lst][key], vals)
        return _UP[lst][key]
    rid = create(lst, {key_field: key, **vals})
    _UP[lst][key] = rid
    return rid


def d(s):
    return s if isinstance(s, str) else s.isoformat()


# ═══ ref ════════════════════════════════════════════════════════════════════
FORM = {"Yönetici ve Uzman": (50, 30, 10, 10), "Müdür": (45, 25, 20, 10),
        "GM, Başkan, Direktör": (35, 25, 30, 10)}
YETKINLIK = [  # ad, tanım, form türleri
    ("Sonuç Odaklılık", "Hedefleri sahiplenir, engellere rağmen sonuca ulaşır.", list(FORM)),
    ("Müşteri Odaklılık", "İç ve dış müşteri ihtiyacını anlar, beklentinin ötesine geçer.", list(FORM)),
    ("Takım Çalışması", "Bilgi paylaşır, ortak hedef için birimler arası iş birliği yapar.", list(FORM)),
    ("İletişim", "Açık, zamanında ve hedef kitleye uygun iletişim kurar.", list(FORM)),
    ("Problem Çözme", "Kök nedeni bulur, veriye dayalı çözüm üretir.", ["Yönetici ve Uzman", "Müdür"]),
    ("Liderlik ve Ekip Geliştirme", "Ekibine yön verir, geri bildirimle geliştirir.", ["Müdür", "GM, Başkan, Direktör"]),
    ("Stratejik Düşünme", "Uzun vadeli hedefleri bugünün kararlarına bağlar.", ["GM, Başkan, Direktör"]),
    ("OKR Davranışı", "İddialı hedef alır, check-in'leri düzenli girer, riskleri erken bildirir.", list(FORM)),
]
DONEMLER = [  # ad, tür, başlangıç, bitiş, son giriş, durum, yıl
    ("2025", "Yıl", "2025-01-01", "2025-12-31", "2025-01-31", "Kapalı", None),
    ("2026", "Yıl", "2026-01-01", "2026-12-31", "2026-01-31", "Aktif", None),
    ("2027", "Yıl", "2027-01-01", "2027-12-31", "2027-01-31", "Planlama", None),
    ("2026-Ç1", "Çeyrek", "2026-01-01", "2026-03-31", "2026-01-14", "Kapalı", "2026"),
    ("2026-Ç2", "Çeyrek", "2026-04-01", "2026-06-30", "2026-04-14", "Kapalı", "2026"),
    ("2026-Ç3", "Çeyrek", "2026-07-01", "2026-09-30", "2026-07-14", "Kapalı", "2026"),
    ("2026-Ç4", "Çeyrek", "2026-10-01", "2026-12-31", "2026-10-14", "Aktif", "2026"),
    ("2027-Ç1", "Çeyrek", "2027-01-01", "2027-03-31", "2027-01-14", "Planlama", "2027"),
]
ID: dict[str, dict[str, str]] = {"donem": {}, "form": {}, "tur": {}, "yet": {}}


def step_ref():
    print("▶ ref")
    for ad, (op, pr, ku, ye) in FORM.items():
        ID["form"][ad] = upsert("Form Türleri", "Form Türü", ad, {
            "Operasyonel Oranı": op, "Proje Oranı": pr, "Kurumsal Oranı": ku, "Yetkinlik Oranı": ye})
    for i, (ad, aciklama) in enumerate([("Operasyonel Hedef", "Sürdürülen işin performansı"),
                                         ("Proje Hedefi", "Dönem içinde tamamlanacak proje / iyileştirme"),
                                         ("Kurumsal Hedef", "Şirket geneli ortak hedef")], 1):
        ID["tur"][ad] = upsert("Hedef Türleri", "Hedef Türü", ad, {"Kod": i, "Açıklama": aciklama})
    for i, (ad, tanim, formlar) in enumerate(YETKINLIK, 1):
        ID["yet"][ad] = upsert("Yetkinlikler", "Yetkinlik", ad, {
            "Tanım / Davranış Göstergeleri": tanim, "Aktif": 1, "Sıra": i,
            "Form Türleri": link(*[ID["form"][f] for f in formlar])})
    for ad, tur, bas, bit, son, durum, yil in DONEMLER:
        ID["donem"][ad] = upsert("Dönemler", "Dönem Adı", ad, {
            "Tür": tur, "Tür Kodu": 1 if tur == "Yıl" else 2, "Başlangıç": bas, "Bitiş": bit,
            "Hedef Giriş Son Tarihi": son, "Durum": durum,
            "Yıl": link(ID["donem"].get(yil)) if yil else None})


# ═══ ik ═════════════════════════════════════════════════════════════════════
YONETICI_BIRIMLERI = ["CEO", "CTO", "CFO", "Yazılım Müdürü", "İK Müdürü", "Operasyon Müdürü",
                      "Müşteri Hizmetleri Müdürü", "Proje Yöneticisi"]


def form_of(birim):
    if birim in ("CEO", "CTO", "CFO"):
        return "GM, Başkan, Direktör"
    if "Müdür" in birim or birim == "Proje Yöneticisi":
        return "Müdür"
    return "Yönetici ve Uzman"


AILE = {  # birim → hedef ailesi + departman (OKR) birimi
    "CEO": ("yonetim", "CEO"), "CTO": ("yonetim", "CTO"), "CFO": ("finans", "CFO"),
    "Yazılım Müdürü": ("yazilim", "Yazılım Müdürü"), "Yazılım Müdür Yardımcısı": ("yazilim", "Yazılım Müdürü"),
    "Yazılım Geliştirici": ("yazilim", "Yazılım Müdürü"), "Yazılım Uzmanı": ("yazilim", "Yazılım Müdürü"),
    "İK Müdürü": ("ik", "İK Müdürü"), "İK Müdür Yardımcısı": ("ik", "İK Müdürü"), "İK Uzmanı": ("ik", "İK Müdürü"),
    "Operasyon Müdürü": ("operasyon", "Operasyon Müdürü"), "Operasyon Uzmanı": ("operasyon", "Operasyon Müdürü"),
    "Müşteri Hizmetleri Müdürü": ("musteri", "Müşteri Hizmetleri Müdürü"),
    "Müşteri Temsilcisi": ("musteri", "Müşteri Hizmetleri Müdürü"),
    "Proje Yöneticisi": ("proje", "Proje Yöneticisi"), "Proje Uzmanı": ("proje", "Proje Yöneticisi"),
    "Finans Uzmanı": ("finans", "CFO"),
}
YENI_CALISANLAR = [  # ad, soyad, birim, işe başlama, eğitim
    ("Selin", "Aydın", "CEO", "2015-03-02", "Yüksek Lisans"),
    ("Kerem", "Yıldız", "CTO", "2017-09-11", "Yüksek Lisans"),
    ("Defne", "Arslan", "CFO", "2018-01-15", "Yüksek Lisans"),
    ("Murat", "Koç", "Yazılım Müdürü", "2019-04-01", "Lisans"),
    ("Ece", "Şahin", "Yazılım Müdür Yardımcısı", "2020-06-15", "Lisans"),
    ("Burak", "Çelik", "Yazılım Geliştirici", "2021-02-01", "Lisans"),
    ("Zeynep", "Öztürk", "Yazılım Geliştirici", "2022-08-22", "Lisans"),
    ("Emre", "Kaya", "Yazılım Geliştirici", "2023-03-13", "Lisans"),
    ("İrem", "Demir", "Yazılım Geliştirici", "2024-09-02", "Lisans"),
    ("Can", "Polat", "Yazılım Uzmanı", "2020-11-16", "Lisans"),
    ("Deniz", "Erdoğan", "Yazılım Uzmanı", "2022-01-10", "Yüksek Lisans"),
    ("Gülşen", "Yılmaz", "İK Müdürü", "2016-05-09", "Yüksek Lisans"),
    ("Onur", "Aksoy", "İK Müdür Yardımcısı", "2019-10-07", "Lisans"),
    ("Merve", "Kurt", "İK Uzmanı", "2021-07-19", "Lisans"),
    ("Tolga", "Özdemir", "İK Uzmanı", "2023-05-15", "Lisans"),
    ("Hakan", "Bulut", "Operasyon Müdürü", "2014-02-17", "Lisans"),
    ("Seda", "Güneş", "Operasyon Uzmanı", "2018-08-06", "Önlisans"),
    ("Okan", "Tekin", "Operasyon Uzmanı", "2020-03-23", "Lisans"),
    ("Pınar", "Acar", "Operasyon Uzmanı", "2022-10-03", "Önlisans"),
    ("Aylin", "Kılıç", "Müşteri Hizmetleri Müdürü", "2017-06-12", "Lisans"),
    ("Barış", "Doğan", "Müşteri Temsilcisi", "2021-04-05", "Önlisans"),
    ("Cansu", "Yavuz", "Müşteri Temsilcisi", "2022-02-14", "Lisans"),
    ("Furkan", "Özkan", "Müşteri Temsilcisi", "2023-09-18", "Lisans"),
    ("Gizem", "Karaca", "Müşteri Temsilcisi", "2024-01-08", "Lisans"),
    ("Serkan", "Uçar", "Proje Yöneticisi", "2016-11-21", "Yüksek Lisans"),
    ("Nazlı", "Ekinci", "Proje Yöneticisi", "2019-01-14", "Yüksek Lisans"),
    ("Volkan", "Sarı", "Proje Uzmanı", "2021-09-27", "Lisans"),
    ("Esra", "Turan", "Proje Uzmanı", "2023-06-05", "Lisans"),
    ("Kaan", "Aslan", "Finans Uzmanı", "2020-05-11", "Lisans"),
    ("Melis", "Ateş", "Finans Uzmanı", "2022-12-05", "Lisans"),
]
CALISAN: list[dict] = []   # {id, ad, birim, form, aile, dept}
BIRIM: dict[str, str] = {}


def step_ik():
    print("▶ ik")
    for r in records("Organizasyon"):
        BIRIM[r[F("Organizasyon", "Birim  Adı")]] = r["_id"]
        ad = r[F("Organizasyon", "Birim  Adı")]
        if ad in YONETICI_BIRIMLERI and not r.get(F("Organizasyon", "Birim Yöneticisi Hesabı")):
            update("Organizasyon", r["_id"], {"Birim Yöneticisi Hesabı": user()})
    aktif = "Aktif Çalışan"
    cins = {r.get("5980991"): r["_id"] for r in records("Cinsiyet")}   # Cinsiyet listesinin birincil alanı
    kadin = {"Selin", "Defne", "Ece", "Zeynep", "İrem", "Deniz", "Gülşen", "Merve", "Seda", "Pınar", "Aylin",
             "Cansu", "Gizem", "Nazlı", "Esra", "Melis"}
    sicil = 1001
    for ad, soyad, birim, bas, egitim in YENI_CALISANLAR:
        eposta = f"{ad.lower()}.{soyad.lower()}@example.com".translate(str.maketrans("çğıöşüİ", "cgiosui"))
        upsert("Özlük Bilgileri", "E-Posta Adresi", eposta, {
            "Ad": ad, "Soyad": soyad, "Organizasyon Birimi": link(BIRIM[birim]),
            "Fiili Görev Durumu": aktif, "İşe Başlama Tarihi": bas, "Eğitim Durumu": egitim,
            "Sicil No": sicil, "Doğum Tarihi": f"{rnd.randint(1972, 2000)}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}",
            "Birim Yöneticisi": user(), "Hedef İzin Tarihi": "2026-12-28",
            "Cinsiyet": link(cins.get("Kadın" if ad in kadin else "Erkek"))})
        sicil += 1
    # tüm aktif çalışanlar: form türü + yönetici
    for r in records("Özlük Bilgileri"):
        b = (r.get(F("Özlük Bilgileri", "Organizasyon Birimi")) or [{}])[0].get("label")
        if b not in AILE:
            continue
        form = form_of(b)
        update("Özlük Bilgileri", r["_id"], {"Performans Form Türü": link(ID["form"][form]),
                                              "Birim Yöneticisi": user()})
        CALISAN.append({"id": r["_id"], "ad": r[F("Özlük Bilgileri", "İsim")], "birim": b, "form": form,
                        "aile": AILE[b][0], "dept": AILE[b][1]})
    CALISAN.sort(key=lambda x: x["ad"])
    print(f"  {len(CALISAN)} aktif çalışan")


# ═══ karne ══════════════════════════════════════════════════════════════════
H = {  # aile → (operasyonel [(hedef, yönelim, birim, hedeflenen)], proje [...])
    "yazilim": ([("Sprint teslim oranı", "Artan", "%", 90), ("Üretim ortamı hata sayısı", "Azalan", "Adet", 24),
                 ("Kritik hata çözüm süresi", "Azalan", "Gün", 2), ("Kod gözden geçirme kapsamı", "Artan", "%", 95),
                 ("Otomatik test kapsamı", "Artan", "%", 70)],
                [("Yeni ödeme modülünün canlıya alınması", "Artan", "%", 100),
                 ("Mobil uygulama v2 yayını", "Artan", "%", 100)]),
    "ik": ([("Ortalama işe alım süresi", "Azalan", "Gün", 35), ("Kişi başı eğitim saati", "Artan", "Adet", 24),
            ("Çalışan bağlılık skoru", "Artan", "Puan", 75), ("Gönüllü ayrılma oranı", "Azalan", "%", 8),
            ("Bordro hata sayısı", "Azalan", "Adet", 6)],
           [("Performans sisteminin dijitalleşmesi", "Artan", "%", 100),
            ("Yetenek havuzu programı", "Artan", "%", 100)]),
    "operasyon": ([("Zamanında teslimat oranı", "Artan", "%", 95), ("Birim üretim maliyeti", "Azalan", "TL/KG", 12.5),
                   ("Fire oranı", "Azalan", "%", 3), ("Enerji tüketimi", "Azalan", "KWH/M²", 42),
                   ("Üretim miktarı", "Artan", "Ton", 18000)],
                  [("Depo yerleşim optimizasyonu", "Artan", "%", 100),
                   ("Yalın üretim pilot hattı", "Artan", "%", 100)]),
    "musteri": ([("Müşteri memnuniyeti (CSAT)", "Artan", "Puan", 85), ("İlk temasta çözüm oranı", "Artan", "%", 75),
                 ("Ortalama yanıt süresi", "Azalan", "Dakika", 30), ("Şikayet sayısı", "Azalan", "Adet", 120),
                 ("Geri arama tamamlama oranı", "Artan", "%", 90)],
                [("CRM entegrasyonu", "Artan", "%", 100), ("Self servis bilgi bankası", "Artan", "%", 100)]),
    "proje": ([("Zamanında biten proje oranı", "Artan", "%", 85), ("Bütçe sapması", "Azalan", "%", 5),
               ("Müşteri kabul oranı", "Artan", "%", 95), ("Değişiklik talebi çevrim süresi", "Azalan", "Gün", 10)],
              [("PMO süreç standardı", "Artan", "%", 100), ("Proje portföy panosu", "Artan", "%", 100)]),
    "finans": ([("Ay sonu kapanış süresi", "Azalan", "Gün", 5), ("Tahsilat süresi (DSO)", "Azalan", "Gün", 55),
                ("Bütçe tahmin doğruluğu", "Artan", "%", 95), ("Fatura hata oranı", "Azalan", "%", 1)],
               [("ERP finans modülü geçişi", "Artan", "%", 100), ("Nakit akış tahmin modeli", "Artan", "%", 100)]),
    "yonetim": ([("Konsolide ciro", "Artan", "Tutar", 850000000), ("FAVÖK marjı", "Artan", "%", 18),
                 ("Nakit dönüşüm süresi", "Azalan", "Gün", 60), ("Çalışan bağlılık skoru", "Artan", "Puan", 75)],
                [("Yeni pazar girişi", "Artan", "%", 100), ("Dijital dönüşüm yol haritası", "Artan", "%", 100)]),
}
KURUMSAL = {"2025": ("Şirket ciro hedefi", "Artan", "Tutar", 720000000),
            "2026": ("Şirket ciro hedefi", "Artan", "Tutar", 850000000)}
AGIRLIK = [[40, 30, 30], [30, 25, 25, 20], [25, 25, 20, 15, 15], [35, 35, 30]]

# Excel örnekleri (hedef türü, hedef, yönelim, ağırlık, hedeflenen, birim, gerçekleşen)
EXCEL = {
    "A": [("Proje Hedefi", "X", "Artan", 40, 5, "Tutar", 3), ("Operasyonel Hedef", "X", "Artan", 10, 10000, "Ton", 11000),
          ("Proje Hedefi", "X", "Azalan", 60, 90, "Adet", 70), ("Operasyonel Hedef", "X", "Azalan", 10, 5, "Gün", 8),
          ("Operasyonel Hedef", "X", "Azalan", 5, 29, "Dakika", 20), ("Operasyonel Hedef", "X", "Artan", 5, 0.9, "KWH/M²", 1),
          ("Operasyonel Hedef", "X", "Azalan", 30, 3939, "Tutar", 3900), ("Operasyonel Hedef", "X", "Azalan", 25, 222, "Ton", 299),
          ("Operasyonel Hedef", "X", "Azalan", 10, 1000000, "Adet", 985000), ("Operasyonel Hedef", "X", "Artan", 5, 5, "Gün", 1),
          ("Kurumsal Hedef", "X", "Artan", 100, 100, "Dakika", 100)],
    "B": [("Operasyonel Hedef", "X", "Azalan", 25, 90, "KWH/M²", 98), ("Proje Hedefi", "X", "Azalan", 100, 85, "Tutar", 80),
          ("Operasyonel Hedef", "X", "Azalan", 25, 100, "Ton", 100), ("Operasyonel Hedef", "X", "Artan", 50, 590, "Adet", 540),
          ("Kurumsal Hedef", "X", "Artan", 100, 100, "Gün", 100)],
}
EXCEL["C"] = EXCEL["A"]
KARNE: dict[tuple, str] = {}           # (çalışan id, yıl) → karne id
KPI_IDX: dict[tuple, str] = {}         # (dept, hedef adı) → 2026 KPI hedefi id (yöneticinin)


def _gercek(h, yon, ratio):
    g = h * ratio if yon == "Artan" else h / ratio
    return round(g, 2) if h < 100 else round(g)


def _karne(cal, yil, durum, hedefler, kilit):
    kid = upsert("Performans Karneleri", "Karne", f"{yil} – {cal['ad']}", {
        "Çalışan": link(cal["id"]), "Dönem": link(ID["donem"][yil]), "Form Türü": link(ID["form"][cal["form"]]),
        "Yönetici (kullanıcı)": user(), "Durum": durum,
        "Onay Tarihi": f"{yil}-01-{rnd.randint(20, 30)}" if durum not in ("Hedef Belirleme", "Yönetici Onayında") else None})
    KARNE[(cal["id"], yil)] = kid
    if kid in DOLU:                      # yeniden çalıştırmada hedefler tekrar oluşturulmaz
        return kid
    for tur, ad, yon, ag, hdf, birim, ger in hedefler:
        hid = create("KPI Hedefleri", {
            "Hedef": ad, "Hedef Türü": link(ID["tur"][tur]), "Hedef Yönelimi": yon, "Birim": birim,
            "Hedef Ağırlığı (%)": ag, "Hedeflenen": hdf, "Gerçekleşen": ger, "Kilitli": 1 if kilit else 0,
            "Karne": link(kid), "Son Güncelleme": "2026-10-15" if yil == "2026" and ger is not None else None})
        if yil == "2026" and cal["birim"] == cal["dept"]:
            KPI_IDX[(cal["dept"], ad)] = hid
    return kid


def _hedefler(cal, yil, ytd):
    op, pr = H[cal["aile"]]
    n = rnd.choice([3, 4, 4, 5]) if len(op) >= 5 else rnd.choice([3, 4])
    agr = next(a for a in AGIRLIK if len(a) == n) if n != 3 else rnd.choice([AGIRLIK[0], AGIRLIK[3]])
    out = []
    perf = rnd.gauss(1.0, 0.08)               # kişinin genel performans eğilimi
    for (ad, yon, birim, hdf), ag in zip(rnd.sample(op, n), agr):
        r = max(0.6, min(1.35, rnd.gauss(perf, 0.12)))
        out.append(("Operasyonel Hedef", ad, yon, ag, hdf, birim, _gercek(hdf, yon, r * ytd) if ytd else None))
    projeler = rnd.sample(pr, rnd.choice([1, 2]))
    for (ad, yon, birim, hdf), ag in zip(projeler, [100] if len(projeler) == 1 else [60, 40]):
        r = max(0.5, min(1.2, rnd.gauss(perf, 0.15)))
        out.append(("Proje Hedefi", ad, yon, ag, hdf, birim, round(min(120, hdf * r * ytd)) if ytd else None))
    ad, yon, birim, hdf = KURUMSAL[yil]
    out.append(("Kurumsal Hedef", ad, yon, 100, hdf, birim, round(hdf * (1.04 if yil == "2025" else 0.97) * ytd) if ytd else None))
    return out


DOLU: set[str] = set()


def step_karne():
    print("▶ karne")
    DOLU.update(k[0]["_id"] for r in records("KPI Hedefleri") if (k := r.get(F("KPI Hedefleri", "Karne"))))
    yd_var = {r.get(F("Yetkinlik Değerlendirmeleri", "Değerlendirme")) for r in records("Yetkinlik Değerlendirmeleri")}
    # 2025: 15 çalışan, tamamlanmış (3'ü Excel örneği)
    excel_kim = {
        "A": next(x for x in CALISAN if x["form"] == "Yönetici ve Uzman" and x["aile"] == "operasyon"),
        "B": next(x for x in CALISAN if x["form"] == "Müdür" and x["aile"] == "operasyon"),
        "C": next(x for x in CALISAN if x["form"] == "GM, Başkan, Direktör"),
    }
    secilen = list(excel_kim.values()) + [x for x in CALISAN if x not in excel_kim.values()][:12]
    for cal in secilen:
        ornek = next((k for k, v in excel_kim.items() if v is cal), None)
        hed = EXCEL[ornek] if ornek else _hedefler(cal, "2025", 1.0)
        kid = _karne(cal, "2025", "Tamamlandı", hed, True)
        for ad, _, formlar in YETKINLIK:
            if cal["form"] in formlar and f"{ad} – {cal['ad']} (2025)" not in yd_var:
                create("Yetkinlik Değerlendirmeleri", {
                    "Değerlendirme": f"{ad} – {cal['ad']} (2025)", "Karne": link(kid),
                    "Yetkinlik": link(ID["yet"][ad]), "Puan (1–5)": rnd.choice([3, 3, 4, 4, 4, 5, 2]),
                    "Değerlendiren": user()})
        print(f"  2025 · {cal['ad']}" + (f" (Excel {ornek})" if ornek else ""))
    # 2026: herkes; çoğu Aktif (Ekim itibarıyla ~%80 yıl gerçekleşmesi)
    durumlar = (["Hedef Belirleme"] * 2 + ["Yönetici Onayında"] * 3 + ["Aktif"] * 40)
    for i, cal in enumerate(sorted(CALISAN, key=lambda x: (x["birim"] != x["dept"], x["ad"]))):
        durum = "Aktif" if cal["birim"] == cal["dept"] else durumlar[i % len(durumlar)]
        aktif = durum == "Aktif"
        _karne(cal, "2026", durum, _hedefler(cal, "2026", 0.97 if aktif else 0), aktif)
    print(f"  2026 · {len(CALISAN)} karne")


# ═══ okr ════════════════════════════════════════════════════════════════════
SIRKET = {
    "2026-Ç3": [
        ("Müşteri deneyiminde sektör lideri olmak", "İddialı (Aspirational)",
         [("NPS'i 35'ten 50'ye çıkarmak", "Puan", 35, 50), ("Aylık şikayet sayısını 120'den 70'e indirmek", "Adet", 120, 70),
          ("İlk temasta çözüm oranını %65'ten %80'e çıkarmak", "%", 65, 80)]),
        ("Operasyonel verimlilikte sıçrama yapmak", "Zorunlu (Committed)",
         [("Birim maliyeti 13,2'den 12,0 TL/KG'ye indirmek", "TL/KG", 13.2, 12.0),
          ("Zamanında teslimatı %90'dan %96'ya çıkarmak", "%", 90, 96)]),
        ("Dijital ürünlerle büyümek", "İddialı (Aspirational)",
         [("Mobil aktif kullanıcıyı 20.000'den 45.000'e çıkarmak", "Adet", 20000, 45000),
          ("Yeni ödeme modülünü canlıya almak", None, 0, 1),
          ("Dijital kanal satış payını %15'ten %22'ye çıkarmak", "%", 15, 22)]),
    ],
    "2026-Ç4": [
        ("Müşteri sadakatini kalıcı hale getirmek", "İddialı (Aspirational)",
         [("Tekrar satın alma oranını %38'den %48'e çıkarmak", "%", 38, 48), ("NPS'i 45'ten 55'e çıkarmak", "Puan", 45, 55),
          ("Müşteri kaybını %9'dan %6'ya indirmek", "%", 9, 6)]),
        ("Kârlı büyüme", "Zorunlu (Committed)",
         [("Çeyrek cirosunu 210 milyon TL'ye taşımak", "Tutar", 185000000, 210000000),
          ("FAVÖK marjını %16'dan %18'e çıkarmak", "%", 16, 18)]),
        ("Yetenekleri elde tutmak ve geliştirmek", "İddialı (Aspirational)",
         [("Gönüllü ayrılmayı %10'dan %7'ye indirmek", "%", 10, 7),
          ("Kişi başı eğitimi 6 saatten 10 saate çıkarmak", "Adet", 6, 10),
          ("Kritik rollerde yedekleme planını tamamlamak", None, 0, 1)]),
    ],
}
DEPT_OKR = {  # dept → (üst şirket OKR sırası, objective, KPI adı (köprü), KR'lar [(ad, birim, baş, hedef, kpi?)])
    "Müşteri Hizmetleri Müdürü": (0, "Müşteriye ilk temasta çözüm sunmak", "İlk temasta çözüm oranı",
                                  [("İlk temasta çözüm oranını %70'ten %80'e çıkarmak", "%", 70, 80, True),
                                   ("Ortalama yanıt süresini 35 dk'dan 20 dk'ya indirmek", "Dakika", 35, 20, False),
                                   ("Self servis bilgi bankasında 150 makale yayınlamak", "Adet", 40, 150, False)]),
    "Operasyon Müdürü": (1, "Maliyet ve teslimatta yalın operasyon", "Birim üretim maliyeti",
                         [("Birim maliyeti 13,0'dan 12,0 TL/KG'ye indirmek", "TL/KG", 13.0, 12.0, True),
                          ("Fire oranını %3,5'ten %2,5'e indirmek", "%", 3.5, 2.5, False),
                          ("Yalın pilot hattını devreye almak", None, 0, 1, False)]),
    "Yazılım Müdürü": (2, "Güvenilir ve hızlı dijital ürün teslimatı", "Üretim ortamı hata sayısı",
                       [("Üretim hatalarını çeyrekte 12'den 5'e indirmek", "Adet", 12, 5, True),
                        ("Otomatik test kapsamını %55'ten %75'e çıkarmak", "%", 55, 75, False),
                        ("Mobil uygulama v2'yi yayınlamak", None, 0, 1, False)]),
    "İK Müdürü": (2, "Doğru yeteneği hızla kazanmak", "Ortalama işe alım süresi",
                  [("İşe alım süresini 42 günden 30 güne indirmek", "Gün", 42, 30, True),
                   ("Aday deneyim puanını 3,8'den 4,5'e çıkarmak", "Puan", 3.8, 4.5, False)]),
    "Proje Yöneticisi": (1, "Projeleri sözünde teslim etmek", "Zamanında biten proje oranı",
                         [("Zamanında biten proje oranını %75'ten %90'a çıkarmak", "%", 75, 90, True),
                          ("Bütçe sapmasını %8'den %4'e indirmek", "%", 8, 4, False)]),
    "CFO": (1, "Nakdi hızlandırmak", "Tahsilat süresi (DSO)",
            [("DSO'yu 62 günden 50 güne indirmek", "Gün", 62, 50, True),
             ("Ay sonu kapanışı 7 günden 4 güne indirmek", "Gün", 7, 4, False)]),
    "CTO": (2, "Ölçeklenebilir teknoloji altyapısı", None,
            [("Sistem erişilebilirliğini %99,5'ten %99,9'a çıkarmak", "%", 99.5, 99.9, False),
             ("Bulut maliyetini kullanıcı başına %20 düşürmek", "%", 0, 20, False)]),
}
KISI_OKR = [  # (birim adı eşleşmesi, objective, KR'lar)
    ("Müşteri Temsilcisi", "Çağrılarımı ilk temasta kapatmak",
     [("Kişisel ilk temasta çözüm oranımı %72'den %82'ye çıkarmak", "%", 72, 82),
      ("Bilgi bankasına 20 makale katkısı", "Adet", 0, 20)]),
    ("Müşteri Temsilcisi", "Şikayet çözüm süresini kısaltmak",
     [("Şikayet çözüm süresini 3 günden 1,5 güne indirmek", "Gün", 3, 1.5),
      ("Geri arama oranını %85'ten %95'e çıkarmak", "%", 85, 95)]),
    ("Operasyon Uzmanı", "Hat 2'de fireyi azaltmak",
     [("Hat 2 fire oranını %4'ten %2,8'e indirmek", "%", 4, 2.8), ("Kök neden analizlerini tamamlamak", None, 0, 1)]),
    ("Yazılım Geliştirici", "Ödeme modülünün kalitesini artırmak",
     [("Modül test kapsamını %50'den %80'e çıkarmak", "%", 50, 80), ("Açık kritik hata sayısını 6'dan 0'a indirmek", "Adet", 6, 0)]),
    ("Yazılım Geliştirici", "Mobil v2 performansını iyileştirmek",
     [("Açılış süresini 3,2 sn'den 1,8 sn'ye indirmek", "Skor", 3.2, 1.8), ("Çökme oranını %1,2'den %0,4'e indirmek", "%", 1.2, 0.4)]),
    ("İK Uzmanı", "İşe alım hunisini hızlandırmak",
     [("İlk görüşmeye kadar geçen süreyi 10 günden 5 güne indirmek", "Gün", 10, 5), ("Aday havuzuna 300 profil eklemek", "Adet", 0, 300)]),
    ("Proje Uzmanı", "Portföy görünürlüğünü artırmak",
     [("Tüm projelerin haftalık durum raporunu %100 girmek", "%", 60, 100), ("Proje portföy panosunu yayınlamak", None, 0, 1)]),
    ("Finans Uzmanı", "Tahsilatta gecikmeyi azaltmak",
     [("60 gün üstü alacakları 18 milyon TL'den 10 milyon TL'ye indirmek", "Tutar", 18000000, 10000000),
      ("Fatura hata oranını %1,5'ten %0,8'e indirmek", "%", 1.5, 0.8)]),
]


def _kr_ve_checkin(oid, ad, birim, bas, hedef, ceyrek, ilerleme, kpi=None, sahip_takip=0):
    tip = "Kilometre Taşı" if birim is None else "Metrik"
    kr = create("Key Result'lar", {
        "Key Result": ad, "Objective": link(oid), "Sahip": user(), "KR Tipi": tip, "Birim": birim,
        "Başlangıç Değeri": bas, "Hedef Değer": hedef, "Güncel Değer": bas, "Takipte": sahip_takip,
        "Kaynak KPI": link(kpi) if kpi else None})
    if ceyrek == "2026-Ç3":
        tarihler = [date(2026, 7, 13), date(2026, 8, 10), date(2026, 9, 7), date(2026, 9, 28)]
    else:
        tarihler = [date(2026, 10, 6), date(2026, 10, 13), date(2026, 10, 20)]
    guven = rnd.randint(6, 8)
    deger = bas
    for i, t in enumerate(tarihler, 1):
        p = ilerleme * i / len(tarihler)
        if tip == "Kilometre Taşı":
            deger = 1 if (p >= 0.95) else 0
        else:
            deger = bas + (hedef - bas) * p
            deger = round(deger, 2) if abs(hedef) < 1000 else round(deger)
        guven = max(2, min(10, guven + (1 if p > 0.25 * i else -1) + rnd.choice([-1, 0, 0, 1])))
        create("Check-in'ler", {
            "Check-in": f"{ad[:40]} – {t.isoformat()}", "Key Result": link(kr), "Tarih": t.isoformat(),
            "Yeni Değer": deger, "Güven (1–10)": guven, "Giren": user(),
            "Bu Hafta Yapılan": rnd.choice(["Haftalık aksiyonlar tamamlandı, veriler güncellendi.",
                                            "Ekip toplantısında sapmalar gözden geçirildi.",
                                            "Pilot uygulama sonuçları ölçüldü.",
                                            "Paydaşlarla ilerleme paylaşıldı."]),
            "Engel / İhtiyaç": "Diğer ekipten veri bekleniyor." if guven <= 4 else None})
    update("Key Result'lar", kr, {"Güncel Değer": deger, "Güven (1–10)": guven,
                                  "Son Check-in Tarihi": tarihler[-1].isoformat()})
    return kr


def _kpi_index():
    """2026 yönetici KPI hedefleri: (departman, hedef adı) → id (OKR köprüsü için)."""
    karne_cal = {r["_id"]: ((r.get(F("Performans Karneleri", "Çalışan")) or [{}])[0].get("_id"),
                            (r.get(F("Performans Karneleri", "Dönem")) or [{}])[0].get("label"))
                 for r in records("Performans Karneleri")}
    cal_by_id = {x["id"]: x for x in CALISAN}
    for r in records("KPI Hedefleri"):
        k = (r.get(F("KPI Hedefleri", "Karne")) or [{}])[0].get("_id")
        cid, yil = karne_cal.get(k, (None, None))
        cal = cal_by_id.get(cid)
        if yil == "2026" and cal and cal["birim"] == cal["dept"]:
            KPI_IDX[(cal["dept"], r[F("KPI Hedefleri", "Hedef")])] = r["_id"]


def step_okr():
    print("▶ okr")
    if not KPI_IDX:
        _kpi_index()
    birim_id = {r[F("Organizasyon", "Birim  Adı")]: r["_id"] for r in records("Organizasyon")}
    for ceyrek in ("2026-Ç3", "2026-Ç4"):
        kapali = ceyrek == "2026-Ç3"
        durum = "Kapandı" if kapali else "Aktif"
        takip = 0 if kapali else 1
        sirket_ids = []
        for ad, tur, krs in SIRKET[ceyrek]:
            oid = create("Objective'ler", {
                "Objective": ad, "Dönem": link(ID["donem"][ceyrek]), "Seviye": "Şirket", "Seviye Kodu": 1,
                "Sahip": user(), "Onaylayıcı": user(), "OKR Türü": tur,
                "Başarı Eşiği": 0.7 if tur.startswith("İddialı") else 1, "Durum": durum,
                "Açıklama / Neden": "Yönetim kurulunun yıllık stratejik önceliklerinden.",
                "Kapanış Tarihi": "2026-09-30" if kapali else None})
            sirket_ids.append(oid)
            for kad, birim, bas, hdf in krs:
                _kr_ve_checkin(oid, kad, birim, bas, hdf, ceyrek,
                               rnd.uniform(0.45, 1.05) if kapali else rnd.uniform(0.12, 0.35), sahip_takip=takip)
        dept_ids = {}
        for dept, (ust, ad, kpi_ad, krs) in DEPT_OKR.items():
            kpi = KPI_IDX.get((dept, kpi_ad)) if kpi_ad else None
            st = durum if kapali else ("Onayda" if dept == "CTO" else "Aktif")
            oid = create("Objective'ler", {
                "Objective": ad if not kapali else ad, "Dönem": link(ID["donem"][ceyrek]), "Seviye": "Departman",
                "Seviye Kodu": 2, "Departman": link(birim_id[dept]), "Sahip": user(), "Onaylayıcı": user(),
                "OKR Türü": "İddialı (Aspirational)", "Başarı Eşiği": 0.7, "Durum": st,
                "Üst Objective": link(sirket_ids[ust]), "İyileştirdiği KPI": link(kpi) if kpi else None,
                "Katkı Veren Departmanlar": link(birim_id["Proje Yöneticisi"]) if dept == "Yazılım Müdürü" else None,
                "Kapanış Tarihi": "2026-09-30" if kapali else None})
            dept_ids[dept] = oid
            for kad, birim, bas, hdf, kopru in krs:
                _kr_ve_checkin(oid, kad, birim, bas, hdf, ceyrek,
                               rnd.uniform(0.4, 1.05) if kapali else rnd.uniform(0.08, 0.38),
                               kpi=kpi if (kopru and kpi) else None, sahip_takip=0 if st != "Aktif" else 1)
        if kapali:
            continue
        # Ç4 kişisel OKR'lar
        kullanilan = set()
        for i, (birim, ad, krs) in enumerate(KISI_OKR):
            cal = next(x for x in CALISAN if x["birim"] == birim and x["id"] not in kullanilan)
            kullanilan.add(cal["id"])
            st = "Taslak" if i == 6 else ("Onayda" if i == 3 else "Aktif")
            oid = create("Objective'ler", {
                "Objective": ad, "Dönem": link(ID["donem"][ceyrek]), "Seviye": "Kişi", "Seviye Kodu": 3,
                "Departman": link(birim_id[cal["dept"]]), "Sahip": user(), "Sahip Çalışan": link(cal["id"]),
                "Onaylayıcı": user(), "OKR Türü": "İddialı (Aspirational)", "Başarı Eşiği": 0.7, "Durum": st,
                "Üst Objective": link(dept_ids.get(cal["dept"])),
                "Karne": link(KARNE.get((cal["id"], "2026")))})
            for kad, kb, bas, hdf in krs:
                _kr_ve_checkin(oid, kad, kb, bas, hdf, ceyrek, rnd.uniform(0.05, 0.4),
                               sahip_takip=1 if st == "Aktif" else 0)
        print(f"  {ceyrek} tamam")


# ═══ post ═══════════════════════════════════════════════════════════════════
def grup(p):
    return ("Beklentinin Çok Altında" if p < 60 else "Beklenenin Altında" if p < 90 else
            "Beklenen Performans" if p < 101 else "Beklentinin Üstünde" if p < 111 else "Beklentinin Çok Üstünde")


def step_post():
    print("▶ post")
    import time
    time.sleep(5)
    O_ = "Objective'ler"
    for r in records(O_):
        ilerleme = r.get(F(O_, "İlerleme")) or 0
        renk = "Yeşil" if ilerleme >= 0.7 else "Sarı" if ilerleme >= 0.4 else "Kırmızı"
        st = (r.get(F(O_, "Durum")) or {}).get("label")
        vals = {"Renk": renk}
        if st == "Kapandı":
            vals.update({"Kapanış Puanı": round(ilerleme, 2),
                         "Retro Notu": "Hedefin büyük kısmı tutturuldu; kalan KR'lar bir sonraki çeyreğe taşındı."
                         if ilerleme >= 0.7 else "Kaynak yetersizliği nedeniyle geride kalındı; hedef revize edilecek."})
        update(O_, r["_id"], vals)
    K = "Performans Karneleri"
    kalibre = 0
    for r in records(K):
        p = r.get(F(K, "Toplam Puan")) or 0
        st = (r.get(F(K, "Durum")) or {}).get("label")
        vals = {"Performans Grubu": grup(p)}
        if st == "Tamamlandı":
            g = grup(p)
            if kalibre < 2 and g == "Beklenenin Altında" and p > 80:
                vals.update({"Kalibre Grup": "Beklenen Performans",
                             "Kalibrasyon Notu": "Yıl içinde üstlendiği ek sorumluluk nedeniyle bir üst gruba alındı."})
                g = "Beklenen Performans"
                kalibre += 1
            vals["Final Performans Grubu"] = g
        update(K, r["_id"], vals)
    print("  grup / renk / kapanış puanı yazıldı")


if __name__ == "__main__":
    steps = sys.argv[1:] or ["ref", "ik", "karne", "okr", "post"]
    if steps == ["fix"]:
        steps = []
    if steps:
        step_ref()
    if any(s in steps for s in ("ik", "karne", "okr")):
        step_ik()
    if "karne" in steps:
        step_karne()
    if "okr" in steps:
        if not KARNE:
            for r in records("Performans Karneleri"):
                cal = (r.get(F("Performans Karneleri", "Çalışan")) or [{}])[0].get("_id")
                yil = (r.get(F("Performans Karneleri", "Dönem")) or [{}])[0].get("label")
                KARNE[(cal, yil)] = r["_id"]
        step_okr()
    if "post" in steps:
        step_post()


# ═══ fix (yeniden çalıştırılabilir düzeltme adımları) ══════════════════════════
def step_guven():
    """Güven skorunu ilerlemenin zamana göre beklenene oranından türetir (check-in + KR)."""
    print("▶ güven")
    KR_, CI_ = "Key Result'lar", "Check-in'ler"
    kr = {r["_id"]: r for r in records(KR_)}
    gruplar: dict[str, list] = {}
    for r in records(CI_):
        k = (r.get(F(CI_, "Key Result")) or [{}])[0].get("_id")
        gruplar.setdefault(k, []).append(r)
    for k, cis in gruplar.items():
        r = kr[k]
        b, h = r.get(F(KR_, "Başlangıç Değeri")) or 0, r.get(F(KR_, "Hedef Değer")) or 0
        cis.sort(key=lambda x: x[F(CI_, "Tarih")])
        g = 7
        for ci in cis:
            t = date.fromisoformat(ci[F(CI_, "Tarih")][:10])
            q0 = date(t.year, 10, 1) if t.month >= 10 else date(t.year, 7, 1)
            e = (t - q0).days / 91
            v = ci.get(F(CI_, "Yeni Değer")) or 0
            p = 0 if h == b else max(0, min(1, (v - b) / (h - b)))
            g = max(2, min(10, round(7 + (p - e) * 10 + rnd.choice([-1, 0, 0, 1]))))
            update(CI_, ci["_id"], {"Güven (1–10)": g,
                                    "Engel / İhtiyaç": "Diğer ekipten veri / kaynak bekleniyor." if g <= 4 else None})
        update(KR_, k, {"Güven (1–10)": g})
    print(f"  {len(gruplar)} KR güncellendi")


def step_renk():
    """Lookup'ları tazeler, rengi beklenen ilerlemeye göre yazar (OKR-04 ile aynı kural)."""
    print("▶ renk")
    O_ = "Objective'ler"
    for r in records(O_):
        update(O_, r["_id"], {"Dönem": r.get(F(O_, "Dönem"))})     # lookup'ı tazele
    import time
    time.sleep(5)
    for r in records(O_):
        st = (r.get(F(O_, "Durum")) or {}).get("label")
        il = r.get(F(O_, "İlerleme")) or 0
        if st == "Kapandı":
            renk = "Yeşil" if il >= 0.7 else "Sarı" if il >= 0.4 else "Kırmızı"
        else:
            fark = r.get(F(O_, "İlerleme Farkı")) or 0
            renk = "Yeşil" if fark >= -0.05 else "Sarı" if fark >= -0.15 else "Kırmızı"
        update(O_, r["_id"], {"Renk": renk})
    print("  renkler yazıldı")


if __name__ == "__main__" and "fix" in sys.argv[1:]:
    step_guven()
    step_renk()
