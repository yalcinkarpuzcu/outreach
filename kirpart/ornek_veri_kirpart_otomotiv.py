"""
Kırpart Tedarikçi Portalı — Kırpart Otomotiv POC örnek verileri
Build + upgrade + seed SONRASI çalıştır (skill klasöründen):

    python apps/ornek_veri_kirpart_otomotiv.py

Kayıtlar otomasyonları tetikleyecek sırada açılır (ör. denetim → cevaplar, PPAP talebi → dokümanlar).
Firma adları ve kişiler kurgusaldır. Kırpart tarafındaki tüm sorumlu/onaycı alanlarına
tenant'taki kullanıcı atanır (KIRPART_USER).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workiom.client import WorkiomClient, WorkiomAPIError
from workiom.state import AppState


def _api_key() -> str:
    if os.environ.get("API_KEY"):
        return os.environ["API_KEY"]
    for line in open(".env").read().splitlines():
        if line.startswith("API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("API_KEY yok")


c = WorkiomClient(_api_key())
st = AppState("Kırpart Tedarikçi Portalı")
U = int(os.environ.get("KIRPART_USER", "161933"))

LIST_BY_ID = {v["id"]: k for k, v in st.data["lists"].items()}
META: dict[str, dict] = {}
CACHE: dict[str, dict[str, str]] = {}
STATS = {"create": 0, "update": 0, "error": 0}


def retry(fn, *a):
    """Geçici ağ hatalarında (curl) tekrar dene."""
    for i in range(6):
        try:
            return fn(*a)
        except WorkiomAPIError as e:
            if "curl" not in e.message or i == 5:
                raise
            print(f"  … ağ hatası, tekrar deneniyor ({i + 1})", flush=True)
            time.sleep(5 * (i + 1))


def meta(lst):
    if lst not in META:
        META[lst] = {f["name"]: f for f in c.get_all_fields(st.get_list_id(lst))}
    return META[lst]


def conv(lst, name, v):
    f = meta(lst)[name]
    dt = f["dataType"]
    if v is None:
        return None
    if dt == 4:
        return {o["label"]: o["id"] for o in f["staticListValues"]}[v]
    if dt == 17:
        opts = {o["label"]: o["id"] for o in f["staticListValues"]}
        return [opts[x] for x in v]
    if dt == 5:
        tgt = LIST_BY_ID[f["linkedListId"]]
        keys = v if isinstance(v, list) else [v]
        return [{"_id": CACHE[tgt][k]} for k in keys]
    if dt == 6:
        return v
    if dt == 18:
        return v if isinstance(v, list) else [v]
    return v


def payload(lst, data):
    return {str(meta(lst)[k]["id"]): conv(lst, k, v) for k, v in data.items()}


def create(lst, key, data):
    try:
        rid = retry(c.create_record, st.get_list_id(lst), payload(lst, data))
        CACHE.setdefault(lst, {})[key] = rid
        STATS["create"] += 1
        return rid
    except (WorkiomAPIError, KeyError) as e:
        STATS["error"] += 1
        print(f"  ✗ {lst} / {key}: {getattr(e, 'message', e)} {getattr(e, 'details', '')[:160]}")


def update(lst, key, data):
    try:
        retry(c.update_record, st.get_list_id(lst), CACHE[lst][key], payload(lst, data))
        STATS["update"] += 1
    except (WorkiomAPIError, KeyError) as e:
        STATS["error"] += 1
        print(f"  ✗ güncelleme {lst} / {key}: {getattr(e, 'message', e)} {getattr(e, 'details', '')[:160]}")


def load_existing(lst, key_field):
    fid = str(meta(lst)[key_field]["id"])
    for r in c.get_all_records(st.get_list_id(lst)):
        if r.get(fid):
            CACHE.setdefault(lst, {})[r[fid]] = r["_id"]


def section(t):
    print(f"\n▶ {t}  (toplam: {STATS['create']} kayıt, {STATS['update']} güncelleme, {STATS['error']} hata)", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
section("Referans veriler yükleniyor")
load_existing("Denetim Tipleri", "Denetim Tipi")
load_existing("PPAP Belge Tipleri", "Belge Tipi")
load_existing("Denetim Soruları", "Soru Kodu")

# ─── Ek denetim soruları ─────────────────────────────────────────────────────
for kod, tip, bolum, soru, w in [
    ("ÜRN-01", "Ürün Denetimi", "Boyutsal", "Kritik ölçüler kontrol planındaki sıklıkta ölçülüyor mu?", 3),
    ("ÜRN-02", "Ürün Denetimi", "Görsel", "Görünüş standartlarına (çapak, çökme, renk) uygunluk sağlanıyor mu?", 2),
    ("ÜRN-03", "Ürün Denetimi", "Etiketleme", "Parça ve kasa etiketleri Kırpart etiket şartnamesine uygun mu?", 1),
    ("ÜRN-04", "Ürün Denetimi", "Fonksiyonel", "Montaj/fonksiyon testi kayıtları lot bazında tutuluyor mu?", 2),
    ("SİS-01", "Sistem Denetimi", "Yönetim", "IATF 16949 sertifikası geçerli ve kapsamı uygun mu?", 3),
    ("SİS-02", "Sistem Denetimi", "Tedarik", "Alt tedarikçi değerlendirme süreci tanımlı mı?", 2),
    ("SİS-03", "Sistem Denetimi", "İyileştirme", "Müşteri şikayetlerinde 8D metodu uygulanıyor mu?", 2),
    ("SİS-04", "Sistem Denetimi", "Acil Durum", "Tedarik sürekliliği için acil durum planı var mı?", 1),
]:
    if kod not in CACHE.get("Denetim Soruları", {}):
        create("Denetim Soruları", kod, {"Soru Kodu": kod, "Bölüm": bolum, "Soru": soru, "Maksimum Puan": 10,
                                          "Ağırlık": w, "Sıra": int(kod[-1]), "Aktif": True, "Denetim Tipi": tip})

# ═══════════════════════════════════════════════════════════════════════════════
section("Tedarikçiler")
TED = [
    # ad, kod, kısa, durum, ülke, şehir, ürün, yöntem, fiyat, vade, pb, ciro, kar, kredi, hedefler(ppm,otd,vaka,8d,den), puan, sınıf, kapasite
    ("Özmetal Pres ve Kalıp San. A.Ş.", "TED-1001", "Özmetal", "Aktif", "Türkiye", "Bursa", ["Metal İşleme"],
     ["Pres", "Talaşlı İmalat"], "Orta", 90, "TRY", 850_000_000, 59_500_000, 40_000_000, (150, 95, 2, 30, 80), 88.4, "A",
     "4 adet 400–800 ton pres hattı, 2 vardiya. Aylık ~1,2 milyon braket kapasitesi; %72 doluluk."),
    ("Nilüfer Plastik Enjeksiyon Ltd. Şti.", "TED-1002", "Nilüfer Plastik", "Aktif", "Türkiye", "Bursa",
     ["Plastik Enjeksiyon"], ["Enjeksiyon", "Montaj"], "Düşük", 75, "TRY", 420_000_000, 21_000_000, 15_000_000,
     (200, 95, 2, 30, 80), 76.2, "B", "18 enjeksiyon makinesi (80–650 ton), 3 vardiya. Montaj hattı 2 adet."),
    ("Anadolu Polimer Hammadde A.Ş.", "TED-1003", "Anadolu Polimer", "Aktif", "Türkiye", "Kocaeli",
     ["Plastik Hammadde"], ["Enjeksiyon"], "Orta", 60, "TRY", 1_250_000_000, 93_750_000, 60_000_000,
     (100, 98, 1, 20, 85), 91.0, "A", "Kompaund hattı 3 adet, yıllık 45.000 ton. Gebze deposu 2.000 ton stoklu."),
    ("Marmara Kauçuk Teknik San. Tic. A.Ş.", "TED-1004", "Marmara Kauçuk", "Aktif", "Türkiye", "İstanbul",
     ["Kauçuk"], ["Pres", "Montaj"], "Düşük", 90, "TRY", 210_000_000, 6_300_000, 8_000_000, (300, 92, 3, 30, 75),
     61.5, "C", "Ekstrüzyon hattı 2, kalıplama presi 12 adet. Haziran'dan beri %95 doluluk — kapasite riski."),
    ("Ege Ambalaj ve Koli San. A.Ş.", "TED-1005", "Ege Ambalaj", "Aktif", "Türkiye", "İzmir", ["Ambalaj"],
     ["Montaj"], "Düşük", 60, "TRY", 180_000_000, 10_800_000, 5_000_000, (500, 95, 3, 30, 70), 79.0, "B",
     "Oluklu mukavva hattı 2, KLT kasa yıkama hattı 1. Haftalık 40.000 koli."),
    ("Kessler Kunststofftechnik GmbH", "TED-1006", "Kessler", "Aktif", "Almanya", "Stuttgart",
     ["Plastik Enjeksiyon"], ["Enjeksiyon", "Boya-Kaplama"], "Yüksek", 60, "EUR", 64_000_000, 4_480_000,
     2_000_000, (50, 98, 1, 20, 90), 93.5, "A", "2K enjeksiyon ve soft-touch boya. Lead time 6 hafta (deniz)."),
    ("Ningbo Hengtai Precision Co., Ltd.", "TED-1007", "Ningbo Hengtai", "Aktif", "Çin", "Ningbo",
     ["Metal İşleme", "Elektronik"], ["Döküm", "Talaşlı İmalat"], "Düşük", 45, "USD", 38_000_000, 2_660_000,
     1_000_000, (250, 90, 2, 40, 75), 72.8, "B", "Alüminyum basınçlı döküm + CNC. Deniz yolu 45 gün."),
    ("Torino Elettromeccanica S.r.l.", "TED-1008", "Torino Elettro", "Aday", "İtalya", "Torino",
     ["Elektronik"], ["Montaj"], "Yüksek", 60, "EUR", 22_000_000, 1_540_000, None, (100, 95, 1, 30, 85), None,
     None, "Konnektör ve sensör muhafazası montajı. Ön değerlendirme aşamasında."),
]
for (ad, kod, kisa, durum, ulke, sehir, urun, yontem, fiyat, vade, pb, ciro, kar, kredi, hed, puan, sinif,
     kap) in TED:
    d = {"Tedarikçi Adı": ad, "Tedarikçi Kodu": kod, "Kısa Ad": kisa, "Durum": durum, "Ülke": ulke, "Şehir": sehir,
         "Adres": f"{sehir} OSB, {kisa} tesisleri", "Ürün Çeşit Kodu": urun, "Üretim Yöntemi": yontem,
         "Fiyat Segmenti": fiyat, "Vergi Dairesi": "Nilüfer" if ulke == "Türkiye" else "—",
         "Vergi No": f"{kod[-4:]}45{kod[-2:]}7812" if ulke == "Türkiye" else f"EU{kod[-4:]}", "Ödeme Vadesi (gün)": vade,
         "Para Birimi": pb, "Genel Kapasite Açıklaması": kap,
         "Satınalma Sorumlusu (Kırpart)": U, "Kalite Sorumlusu (Kırpart)": U, "Lojistik Sorumlusu (Kırpart)": U,
         "Finans Sorumlusu (Kırpart)": U, "Tedarikçi Portal Kullanıcıları": [U],
         "Son Yıl Ciro": ciro, "Son Yıl Net Kâr": kar, "Finansal Veri Yılı": "2025",
         "PPM Hedefi": hed[0], "Zamanında Teslim Hedefi %": hed[1], "Vaka Sayısı Hedefi (dönem)": hed[2],
         "8D Kapanış Hedefi (gün)": hed[3], "Min. Denetim Puanı %": hed[4]}
    if kredi:
        d["Kredi Limiti / Risk"] = kredi
    if puan:
        d["Güncel Performans Puanı"] = puan
        d["Performans Sınıfı"] = sinif
    create("Tedarikçiler", ad, d)
T = {t[2]: t[0] for t in TED}  # kısa ad → tedarikçi adı

# ═══════════════════════════════════════════════════════════════════════════════
section("Kontaklar & Portal Kullanıcıları")
KONTAK = [
    ("Murat Özkan", "Özmetal", "Genel Müdür", "TR", ["Kalite", "Lojistik", "Satınalma", "Finans"], True,
     ["Sipariş", "8D", "PPAP", "Mutabakat"]),
    ("Elif Şahin", "Özmetal", "Kalite Müdürü", "TR", ["Kalite"], False, ["8D", "PPAP", "Sertifika", "Denetim"]),
    ("Serkan Aydın", "Özmetal", "Sevkiyat Şefi", "TR", ["Lojistik"], False, ["Sipariş", "Sevkiyat"]),
    ("Hakan Yıldız", "Nilüfer Plastik", "Fabrika Müdürü", "TR", ["Kalite", "Lojistik", "Satınalma", "Finans"], True,
     ["Sipariş", "8D", "Maliyet"]),
    ("Zeynep Kara", "Nilüfer Plastik", "Kalite Mühendisi", "TR", ["Kalite"], False, ["8D", "PPAP", "Denetim"]),
    ("Burak Demir", "Anadolu Polimer", "Satış Müdürü", "TR", ["Lojistik", "Satınalma", "Finans"], True,
     ["Sipariş", "Sevkiyat", "Mutabakat"]),
    ("Selin Arslan", "Marmara Kauçuk", "Kalite Güvence Şefi", "TR", ["Kalite", "Lojistik", "Satınalma", "Finans"],
     True, ["8D", "Sipariş", "Maliyet"]),
    ("Okan Çelik", "Ege Ambalaj", "Müşteri Temsilcisi", "TR", ["Lojistik", "Satınalma", "Finans"], True,
     ["Sipariş", "Sevkiyat", "Mutabakat"]),
    ("Thomas Becker", "Kessler", "Key Account Manager", "EN", ["Kalite", "Lojistik", "Satınalma", "Finans"], True,
     ["Sipariş", "PPAP", "Sertifika"]),
    ("Anna Vogel", "Kessler", "Quality Engineer", "EN", ["Kalite"], False, ["8D", "PPAP", "Denetim"]),
    ("Li Wei", "Ningbo Hengtai", "Export Manager", "EN", ["Kalite", "Lojistik", "Satınalma", "Finans"], True,
     ["Sipariş", "Sevkiyat", "8D", "Sapma" if False else "PPAP"]),
    ("Marco Rossi", "Torino Elettro", "Sales Director", "EN", ["Kalite", "Satınalma"], True, ["PPAP", "Denetim"]),
]
for ad, ted, unvan, dil, dep, master, konu in KONTAK:
    mail = ad.lower().replace(" ", ".").translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU"))
    dom = ted.lower().split()[0].translate(str.maketrans("çğıöşü", "cgiosu"))
    create("Kontaklar & Portal Kullanıcıları", ad, {
        "Ad Soyad": ad, "Tedarikçi": T[ted], "Unvan": unvan, "E-posta": f"{mail}@{dom}.example",
        "Telefon": "+90 224 411 " + str(2000 + len(CACHE.get("Kontaklar & Portal Kullanıcıları", {}))),
        "Dil": dil, "Departman Yetkisi": dep, "Master Kullanıcı": master, "Otomatik E-posta Listesinde": True,
        "Bildirim Konuları": konu, "Aktif": True, **({"Workiom Kullanıcısı": U} if master else {})})

time.sleep(5)
for i, (ad, *_r) in enumerate(KONTAK):  # tedarikçinin eklediği kişiler Kırpart onayından geçmiş olsun
    update("Kontaklar & Portal Kullanıcıları", ad, {"Kırpart Onay Durumu": "Talep Edildi" if i == 4 else "Onaylandı"})

# ═══════════════════════════════════════════════════════════════════════════════
section("Malzemeler")
MALZ = [
    ("HM-PP-T20", "PP %20 Talk Dolgulu Granül", "PP 20% Talc Filled Compound", "Hammadde", "Kg", None, None, None),
    ("HM-ABS-01", "ABS Granül Siyah UV Stabilize", "ABS Black UV Stabilized", "Hammadde", "Kg", None, None, None),
    ("HM-PA6-GF30", "PA6 %30 Cam Elyaf Takviyeli Granül", "PA6 GF30", "Hammadde", "Kg", None, None, None),
    ("HM-EPDM-70", "EPDM Kauçuk Karışım 70 Shore A", "EPDM Compound 70 ShA", "Hammadde", "Kg", None, None, None),
    ("KRP-24101", "Kapı Paneli Bağlantı Braketi", "Door Panel Mounting Bracket", "Parça", "Adet", "ÇZ-24101", "C",
     "PRJ-LCV-24 Hafif Ticari"),
    ("KRP-24115", "Far Montaj Braketi Alüminyum", "Headlamp Mounting Bracket Alu", "Parça", "Adet", "ÇZ-24115", "B",
     "PRJ-SUV-25 SUV"),
    ("KRP-31020", "Torpido Kapağı Menteşesi", "Glovebox Lid Hinge", "Parça", "Adet", "ÇZ-31020", "D",
     "PRJ-LCV-24 Hafif Ticari"),
    ("KRP-31044", "Orta Konsol Havalandırma Izgarası", "Center Console Air Vent Grille", "Parça", "Adet",
     "ÇZ-31044", "A", "PRJ-SUV-25 SUV"),
    ("KRP-35210", "Ön Kapı Cam Fitili", "Front Door Glass Run Seal", "Parça", "Adet", "ÇZ-35210", "C",
     "PRJ-BUS-23 Otobüs"),
    ("KRP-40118", "Koltuk Ayar Kolu Soft-Touch", "Seat Adjust Lever Soft-Touch", "Parça", "Adet", "ÇZ-40118", "B",
     "PRJ-SUV-25 SUV"),
    ("KRP-60301", "Park Sensörü Konnektör Muhafazası", "Park Sensor Connector Housing", "Parça", "Adet",
     "ÇZ-60301", "A", "PRJ-SUV-25 SUV"),
    ("YM-24101", "Braket Sac Kesim Blankosu", "Bracket Sheet Blank", "Yarı Mamul", "Adet", "ÇZ-24101-B", "C",
     "PRJ-LCV-24 Hafif Ticari"),
    ("AMB-KLT-4314", "KLT Kasa 400x300x147", "KLT Box 4314", "Kasa-Ambalaj", "Adet", None, None, None),
    ("AMB-KLT-6429", "KLT Kasa 600x400x280", "KLT Box 6429", "Kasa-Ambalaj", "Adet", None, None, None),
    ("AMB-KOLI-64", "Oluklu Koli 600x400x300 Çift Dalga", "Corrugated Box 600x400", "Kasa-Ambalaj", "Adet", None,
     None, None),
]
for kod, ad, en, tip, birim, cz, rev, prj in MALZ:
    d = {"Malzeme Kodu": kod, "Malzeme Adı": ad, "Malzeme Adı (EN)": en, "Malzeme Tipi": tip, "Birim": birim,
         "Aktif": True, "PLM Kodu": "PLM-" + kod}
    if cz:
        d.update({"Çizim No": cz, "Revizyon": rev, "Proje / Müşteri": prj})
    create("Malzemeler", kod, d)

# ═══════════════════════════════════════════════════════════════════════════════
section("Tedarikçi–Malzeme Kartları")
KART = [  # ted, malzeme, ana, haftalık kap, lead, kutu, kutu içi, birim ağ, dara
    ("Özmetal", "KRP-24101", True, 30000, 14, "AMB-KLT-6429", 400, 0.085, 1.9),
    ("Özmetal", "YM-24101", True, 35000, 10, "AMB-KLT-6429", 500, 0.095, 1.9),
    ("Ningbo Hengtai", "KRP-24115", True, 12000, 60, "AMB-KOLI-64", 120, 0.21, 0.6),
    ("Özmetal", "KRP-24115", False, 5000, 21, "AMB-KLT-6429", 150, 0.21, 1.9),
    ("Nilüfer Plastik", "KRP-31020", True, 25000, 10, "AMB-KLT-4314", 250, 0.032, 0.9),
    ("Nilüfer Plastik", "KRP-31044", True, 18000, 12, "AMB-KLT-4314", 80, 0.115, 0.9),
    ("Kessler", "KRP-31044", False, 8000, 42, "AMB-KOLI-64", 100, 0.115, 0.6),
    ("Kessler", "KRP-40118", True, 10000, 42, "AMB-KOLI-64", 150, 0.07, 0.6),
    ("Marmara Kauçuk", "KRP-35210", True, 6000, 15, "AMB-KOLI-64", 50, 0.38, 0.6),
    ("Anadolu Polimer", "HM-PP-T20", True, 60000, 7, None, 25, 1, 0.2),
    ("Anadolu Polimer", "HM-ABS-01", True, 25000, 7, None, 25, 1, 0.2),
    ("Anadolu Polimer", "HM-PA6-GF30", True, 15000, 10, None, 25, 1, 0.2),
    ("Ningbo Hengtai", "KRP-60301", True, 20000, 55, "AMB-KOLI-64", 300, 0.018, 0.6),
    ("Ege Ambalaj", "AMB-KOLI-64", True, 40000, 5, None, 1, 0.65, 0),
]
for ted, mlz, ana, kap, lt, kutu, adet, bw, dara in KART:
    d = {"Kart Adı": f"{ted} – {mlz}", "Tedarikçi": T[ted], "Malzeme": mlz, "Ana Tedarikçi": ana,
         "Haftalık Kapasite": kap, "Lead Time (gün)": lt, "Kutu İçi Adet": adet, "Birim Ağırlık (kg)": bw,
         "Kutu Dara (kg)": dara, "Son Güncelleme": "2026-09-30",
         "Paketleme Açıklaması": "Kırpart etiket şartnamesi KRP-LOJ-007'ye göre etiketlenir; palet başı max 1.000 kg."}
    if kutu:
        d["Kutu / Kasa"] = kutu
    create("Tedarikçi–Malzeme Kartları", f"{ted} – {mlz}", d)

# ═══════════════════════════════════════════════════════════════════════════════
section("Siparişler ve sipariş kalemleri")
SIP = [  # no, yayın, tarih, ted, durum, not, kalemler[(satır, mlz, tarih, miktar)]
    ("SAS-2026-04512", "YAY-41", "2026-09-02", "Özmetal", "Kısmi Teyit", None,
     [(10, "KRP-24101", "2026-09-22", 24000), (20, "KRP-24101", "2026-10-20", 28000),
      (30, "YM-24101", "2026-10-27", 30000)]),
    ("SAS-2026-04530", "YAY-41", "2026-09-05", "Nilüfer Plastik", "Teyit Edildi", None,
     [(10, "KRP-31020", "2026-09-25", 20000), (20, "KRP-31044", "2026-10-16", 15000)]),
    ("SAS-2026-04588", "YAY-42", "2026-09-18", "Anadolu Polimer", "Teyit Edildi", None,
     [(10, "HM-PP-T20", "2026-10-03", 50000), (20, "HM-ABS-01", "2026-10-21", 20000)]),
    ("SAS-2026-04601", "YAY-42", "2026-09-21", "Marmara Kauçuk", "Teyit Bekliyor",
     "Müşteri talep artışı nedeniyle Kasım miktarı %20 artırıldı.",
     [(10, "KRP-35210", "2026-10-24", 5500), (20, "KRP-35210", "2026-11-14", 6600)]),
    ("SAS-2026-04622", "YAY-42", "2026-09-24", "Kessler", "Teyit Edildi", None,
     [(10, "KRP-40118", "2026-11-05", 9000)]),
    ("SAS-2026-04640", "YAY-43", "2026-09-29", "Ningbo Hengtai", "Kısmi Teyit", None,
     [(10, "KRP-24115", "2026-11-20", 11000), (20, "KRP-60301", "2026-11-28", 18000)]),
    ("SAS-2026-04677", "YAY-43", "2026-10-06", "Ege Ambalaj", "Açık", None,
     [(10, "AMB-KOLI-64", "2026-10-23", 12000)]),
]
for no, yay, tar, ted, durum, notu, kalemler in SIP:
    d = {"Sipariş No": no, "Yayın No": yay, "Sipariş Tarihi": tar, "Durum": durum, "Tedarikçi": T[ted]}
    if notu:
        d["Kırpart Notu"] = notu
    create("Siparişler", no, d)
    for satir, mlz, ist, mik in kalemler:
        create("Sipariş Kalemleri", f"{no}/{satir}", {
            "Kalem Kodu": f"{no}/{satir}", "Sipariş": no, "Satır No": satir, "Tedarikçi": T[ted], "Malzeme": mlz,
            "İstenen Teslim Tarihi": ist, "Sipariş Miktarı": mik})

time.sleep(5)
TEYIT = {  # kalem: (durum, miktar, tarih, kapasite, ihtiyaç, red gerekçesi, red açıklama)
    "SAS-2026-04512/10": ("Onaylandı", 24000, "2026-09-22", "Evet", None, None, None),
    "SAS-2026-04512/20": ("Onaylandı", 28000, "2026-10-20", "Evet", None, None, None),
    "SAS-2026-04512/30": ("Kısmi Onay", 22000, "2026-10-30", "Hayır",
                          "2. vardiya için ek operatör ve 1 adet progresif kalıp yedeği gerekiyor; 8.000 adet "
                          "Kasım ilk haftasına kayar.", None, None),
    "SAS-2026-04530/10": ("Onaylandı", 20000, "2026-09-25", "Evet", None, None, None),
    "SAS-2026-04530/20": ("Onaylandı", 15000, "2026-10-16", "Evet", None, None, None),
    "SAS-2026-04588/10": ("Onaylandı", 50000, "2026-10-03", "Evet", None, None, None),
    "SAS-2026-04588/20": ("Onaylandı", 20000, "2026-10-21", "Evet", None, None, None),
    "SAS-2026-04601/10": ("Onaylandı", 5500, "2026-10-24", "Evet", None, None, None),
    "SAS-2026-04622/10": ("Onaylandı", 9000, "2026-11-05", "Evet", None, None, None),
    "SAS-2026-04640/10": ("Onaylandı", 11000, "2026-11-20", "Evet", None, None, None),
    "SAS-2026-04640/20": ("Reddedildi", None, None, "Hayır", "Konnektör pimi için kalay kaplama alt tedarikçisi "
                          "yeni; numune onayı bekleniyor.", "Hammadde Yok",
                          "Alt tedarikçi kalay kaplama onayı Kasım sonu bekleniyor; termin 2026-12-15 öneriyoruz."),
}
for k, (dur, mik, tar, kap, iht, red, redacik) in TEYIT.items():
    d = {"Teyit Durumu": dur, "Mevcut Kapasite Yeterli mi?": kap}
    if mik:
        d["Teyit Edilen Miktar"] = mik
    if tar:
        d["Teyit Edilen Tarih"] = tar
    if iht:
        d["Neye İhtiyacın Var?"] = iht
    if red:
        d.update({"Red Gerekçesi": red, "Red Açıklaması": redacik})
    update("Sipariş Kalemleri", k, d)

# ═══════════════════════════════════════════════════════════════════════════════
section("Sevkiyatlar (ASN) ve sevkiyat kalemleri")
SEV = [  # irsaliye, ted, durum, plan, gerçek, varış, teslim, taşıyıcı, plaka, etiket, ambalaj, not, kalemler[(sip kalem, sevk, kabul, lot, kutu)]
    ("ÖZM-2026-118734", "Özmetal", "Teslim Alındı", "2026-09-19", "2026-09-19", "2026-09-19", "2026-09-19",
     "Özmetal Lojistik", "16 ÖZM 118", True, True, "Eksiksiz teslim alındı.",
     [("SAS-2026-04512/10", 24000, 24000, "L26-0919-A", 60)]),
    ("NLF-2026-55102", "Nilüfer Plastik", "Teslim Alındı", "2026-09-24", "2026-09-24", "2026-09-25", "2026-09-26",
     "Bursa Nakliyat", "16 BN 4410", False, True, "1 gün gecikme; 6 kasada etiket eksik, sevkiyat kabul edildi.",
     [("SAS-2026-04530/10", 20000, 19750, "NP-0924-07", 80)]),
    ("APH-2026-90871", "Anadolu Polimer", "Teslim Alındı", "2026-10-02", "2026-10-02", "2026-10-03", "2026-10-03",
     "Gebze Tank Lojistik", "41 GT 908", True, True, "Big-bag ambalaj sağlam.",
     [("SAS-2026-04588/10", 50000, 50000, "APP-26-1002", 2000)]),
    ("ÖZM-2026-119020", "Özmetal", "Teslim Alındı", "2026-10-09", "2026-10-09", "2026-10-09", "2026-10-13",
     "Özmetal Lojistik", "16 ÖZM 118", True, False, "Ara teslimat; KLT kasalarda 3 adet kırık kasa.",
     [("SAS-2026-04512/20", 12000, 12000, "L26-1009-B", 30)]),
    ("NLF-2026-55388", "Nilüfer Plastik", "Yolda", "2026-10-14", "2026-10-14", "2026-10-15", None,
     "Bursa Nakliyat", "16 BN 4412", False, False, None, [("SAS-2026-04530/20", 15000, None, "NP-1014-02", 188)]),
    ("KSL-DE-2026-3341", "Kessler", "Yolda", "2026-10-02", "2026-10-03", "2026-10-30", None,
     "Hapag Lloyd / Ekol", "DE-CONT-4471", False, False, None, [("SAS-2026-04622/10", 9000, None, "KS-2610-01", 60)]),
    ("ÖZM-2026-119305", "Özmetal", "Planlandı", "2026-10-17", None, "2026-10-17", None,
     "Özmetal Lojistik", None, False, False, None, [("SAS-2026-04512/20", 16000, None, "L26-1017-A", 40)]),
    ("APH-2026-91120", "Anadolu Polimer", "Planlandı", "2026-10-20", None, "2026-10-21", None,
     "Gebze Tank Lojistik", None, False, False, None, [("SAS-2026-04588/20", 20000, None, "APP-26-1020", 800)]),
]
for irs, ted, dur, plan, ger, var, tes, tas, plk, et, amb, notu, kalemler in SEV:
    d = {"İrsaliye No": irs, "Tedarikçi": T[ted], "Durum": dur, "Planlanan Sevk Tarihi": plan,
         "Tahmini Varış": var, "Taşıyıcı Firma": tas, "Etiketleme Uygun": et, "Ambalaj Uygun": amb}
    for k, v in (("Gerçek Sevk Tarihi", ger), ("Teslim Alma Tarihi", tes), ("Araç Plakası", plk), ("Kabul Notu", notu)):
        if v:
            d[k] = v
    create("Sevkiyatlar", irs, d)
    for skal, sevk, kabul, lot, kutu in kalemler:
        create("Sevkiyat Kalemleri", lot, {"Lot No": lot, "Sevkiyat": irs, "Sipariş Kalemi": skal,
                                           "Sevk Edilen Miktar": sevk, "Kutu Adedi": kutu})
time.sleep(20)  # tedarikçi kopyalama + rollup senkronu
for irs, *_rest in SEV:
    for skal, sevk, kabul, lot, kutu in _rest[-1]:
        if kabul:
            update("Sevkiyat Kalemleri", lot, {"Kabul Edilen Miktar": kabul})  # → 05b son irsaliye

# ═══════════════════════════════════════════════════════════════════════════════
section("Envanter bildirimleri")
for ted, mlz, mik, tar, notu in [
    ("Özmetal", "KRP-24101", 8400, "2026-10-10", "Mamul stok; 2 gün üretim emniyet stoğu."),
    ("Özmetal", "AMB-KLT-6429", 140, "2026-10-10", "Boş KLT ihtiyacı: 260 adet iade bekliyoruz."),
    ("Nilüfer Plastik", "KRP-31044", 3200, "2026-10-12", None),
    ("Nilüfer Plastik", "AMB-KLT-4314", 90, "2026-10-12", "Kasa sıkıntısı — sevkiyat için 300 boş kasa gerekli."),
    ("Anadolu Polimer", "HM-PP-T20", 185000, "2026-10-08", "Gebze deposu Kırpart'a ayrılmış konsinye stok."),
    ("Anadolu Polimer", "HM-ABS-01", 42000, "2026-10-08", None),
    ("Marmara Kauçuk", "HM-EPDM-70", 6800, "2026-10-11", "Karışım stoğu 1 haftalık; yeni parti 20 Ekim."),
    ("Kessler", "KRP-40118", 12500, "2026-10-01", "Stuttgart deposunda sevke hazır."),
]:
    create("Envanter Bildirimleri", f"{ted} {mlz} {tar}", {
        "Özet": f"{T[ted].split()[0]} – {mlz} stok bildirimi", "Tedarikçi": T[ted], "Malzeme": mlz,
        "Mevcut Miktar": mik, "Bildirim Tarihi": tar, **({"Not": notu} if notu else {})})

# ═══════════════════════════════════════════════════════════════════════════════
section("Cari mutabakatlar")
CARI = [
    ("Özmetal", "2026-09-30", "TRY", 18_450_000, 18_450_000, "Mutabık", None),
    ("Nilüfer Plastik", "2026-09-30", "TRY", 7_920_500, 8_064_200, "Mutabık Değil",
     "NLF-2026-55102 irsaliyesinde 250 adet fark ve 1 adet fiyat farkı faturası (FF-0912) Kırpart kayıtlarında yok."),
    ("Anadolu Polimer", "2026-09-30", "TRY", 31_200_000, 31_200_000, "Mutabık", None),
    ("Kessler", "2026-09-30", "EUR", 412_800, 398_300, "Çözüldü",
     "Kalitesizlik maliyeti yansıtması (KV kaydı) ile 14.500 EUR fark kapatıldı."),
    ("Marmara Kauçuk", "2026-09-30", "TRY", 3_480_000, None, "Gönderildi", None),
]
for ted, donem, pb, kb, tb, dur, acik in CARI:
    key = f"{ted} {donem}"
    d = {"Mutabakat Dönemi": f"{T[ted].split()[0]} – Eylül 2026", "Tedarikçi": T[ted], "Dönem Sonu": donem,
         "Para Birimi": pb, "Kırpart Bakiyesi": kb, "Finans Sorumlusu (Kırpart)": U}
    create("Cari Mutabakatlar", key, d)
time.sleep(5)
for ted, donem, pb, kb, tb, dur, acik in CARI:
    if dur != "Gönderildi":
        d = {"Tedarikçi Bakiyesi": tb, "Durum": dur}
        if acik:
            d["Fark Açıklaması"] = acik
        update("Cari Mutabakatlar", f"{ted} {donem}", d)

# ═══════════════════════════════════════════════════════════════════════════════
section("Kalite vakaları (uygunsuzluk, iade, 8D, kalitesizlik maliyeti)")
D8 = {
    "D1 Ekip": "Zeynep Kara (Kalite), Hakan Yıldız (Fabrika Md.), Enjeksiyon şefi, Kalıphane sorumlusu; Kırpart SQE.",
    "D2 Problem Tanımı": "KRP-31020 menteşe pim çapı 4,00 ±0,05 yerine 3,88–3,92 ölçüldü; montajda boşluk ve tıkırtı.",
    "D3 Geçici Önlem": "Hat ve depodaki 19.750 adet %100 ayıklandı; go/no-go mastarı ile sevkiyat öncesi kontrol.",
    "D4 Kök Neden": "Kalıp 2. gözde pim maçasının aşınması; ölçüm sıklığı vardiya başı 1 olduğundan geç tespit.",
    "D5 Kalıcı Önlem": "Maça yenilendi ve sertleştirildi (60 HRC); kritik ölçü SPC'ye alındı (saatlik 5'li numune).",
    "D6 Uygulama ve Doğrulama": "3 lot boyunca Cpk 1,67 üstü doğrulandı; Kırpart giriş kontrolünde 0 ret.",
    "D7 Tekrarı Önleme": "Kalıp bakım talimatına maça aşınma ölçümü eklendi; PFMEA ve kontrol planı revize edildi.",
    "D8 Kapanış": "Ekip teşekkür toplantısı yapıldı; ders çıkarılanlar diğer menteşe kalıplarına yaygınlaştırıldı.",
}
VAKA = [
    dict(key="KV-Menteşe pim çapı", ted="Nilüfer Plastik", mlz="KRP-31020", kaynak="GKK Parti Reddi (ERP)",
         ref="GKK-2026-0731", lot="NP-0924-07", sev="NP-0924-07", tespit="2026-09-26", kontrol=20000, hatali=250,
         kat="Boyutsal", tanim="Menteşe pim çapı tolerans altı (3,88–3,92 mm). Parti reddedildi.", iade="Tedarikçi Teslim Aldı",
         iade_irs="KRP-IADE-2026-0412", d8=True, d8dur="Kapandı", d8ter="2026-10-10", d8tam=True, kapanis="2026-10-08",
         maliyet={"Ayıklama Maliyeti": 18500, "Ek Nakliye Maliyeti": 4200}, mpb="TRY", mdur="Onaylandı",
         macik="2 kişi × 3 gün ayıklama + acil nakliye."),
    dict(key="KV-Braket çapak", ted="Özmetal", mlz="KRP-24101", kaynak="Hat İadesi (ERP)", ref="HAT-2026-1188",
         lot="L26-1009-B", sev="L26-1009-B", tespit="2026-10-13", kontrol=1200, hatali=36, kat="Görsel",
         tanim="Delik kenarlarında çapak; montaj hattında vida oturmuyor (36 adet hat iadesi).", iade="İade Edilecek",
         d8=True, d8dur="Tedarikçiye Gönderildi", d8ter="2026-11-12", maliyet={"Rework Maliyeti": 6400}, mpb="TRY",
         mdur="Tedarikçi Onayında", macik="Hat duruşu 25 dk + rework işçiliği."),
    dict(key="KV-Fitil sertlik", ted="Marmara Kauçuk", mlz="KRP-35210", kaynak="Müşteri Şikayeti (PLM)",
         ref="PLM-CC-2026-0088", lot="MK-0901-03", tespit="2026-09-15", kontrol=500, hatali=500, kat="Malzeme",
         tanim="Araç sahada cam fitilinde sertleşme ve çatlak; müşteri 0 km şikayeti.", iade="Sevk Edildi",
         iade_irs="KRP-IADE-2026-0398", d8=True, d8dur="Revizyon İstendi", d8ter="2026-10-15", d8tam=True,
         revnot="D4 kök neden yetersiz: vulkanizasyon sıcaklık kayıtları ve karışım reçetesi eklenmeli.",
         maliyet={"Ayıklama Maliyeti": 22000, "Ceza / Müşteri Yansıması": 145000, "Ek Nakliye Maliyeti": 9800},
         mpb="TRY", mdur="İtiraz", itiraz="Müşteri cezasının tamamı yansıtılmamalı; montaj hatası ihtimali de var.",
         macik="Müşteri yansıtma faturası CC-0088 + saha ayıklama."),
    dict(key="KV-Etiket eksik", ted="Nilüfer Plastik", mlz="KRP-31020", kaynak="Lojistik Uygunsuzluk",
         ref="LOJ-2026-0219", lot="NP-0924-07", tespit="2026-09-26", kontrol=80, hatali=6, kat="Ambalaj-Etiket",
         tanim="6 kasada parça etiketi yok; kasa etiketi ile malzeme kodu eşleşmiyor.", iade="İade Yok", d8=False,
         mdur="Maliyet Yok"),
    dict(key="KV-Döküm gözenek", ted="Ningbo Hengtai", mlz="KRP-24115", kaynak="GKK Parti Reddi (ERP)",
         ref="GKK-2026-0702", lot="NH-0815-11", tespit="2026-08-29", kontrol=2000, hatali=140, kat="Malzeme",
         tanim="Alüminyum braket döküm gözeneği; sızdırmazlık testinde 140 adet ret.", iade="Tedarikçi Teslim Aldı",
         d8=True, d8dur="Onaylandı", d8ter="2026-09-30", d8tam=True, maliyet={"Hurda Maliyeti": 3150,
         "Ek Nakliye Maliyeti": 1800}, mpb="USD", mdur="Faturalandı", macik="Hurda + hava kargo ile yedek parti."),
    dict(key="KV-Izgara renk", ted="Kessler", mlz="KRP-31044", kaynak="Manuel", ref="KRP-MAN-2026-031",
         lot="KS-2608-04", tespit="2026-10-07", kontrol=300, hatali=12, kat="Görsel",
         tanim="Soft-touch boyada renk tonu farkı (ΔE 1,8 > 1,0).", iade="İade Yok", d8=True, d8dur="Kırpart Onayında",
         d8ter="2026-11-07", mdur="Taslak", maliyet={"Ayıklama Maliyeti": 950}, mpb="EUR"),
]
for v in VAKA:
    d = {"Vaka Başlığı": f"{T[v['ted']].split()[0]} – {v['tanim'][:45]}", "Vaka Kaynağı": v["kaynak"],
         "ERP / PLM Referans No": v["ref"], "Tedarikçi": T[v["ted"]], "Malzeme": v["mlz"], "Lot No": v["lot"],
         "Tespit Tarihi": v["tespit"], "Kontrol Edilen Miktar": v["kontrol"], "Hatalı Miktar": v["hatali"],
         "Hata Kategorisi": v["kat"], "Hata Tanımı": v["tanim"], "İade Durumu": v["iade"]}
    if v.get("sev"):
        d["Sevkiyat Kalemi"] = v["sev"]
    if v.get("iade_irs"):
        d["İade İrsaliye No"] = v["iade_irs"]
    create("Kalite Vakaları", v["key"], d)
time.sleep(8)
for v in VAKA:
    d = {}
    if v["d8"]:
        d.update({"8D Gerekli": True, "8D Durumu": v["d8dur"], "8D Termin": v["d8ter"], "8D Onaylayan": U,
                  "Revizyon No": 1 if v.get("revnot") else 0})
        if v.get("d8tam"):
            d.update(D8 if v["mlz"] == "KRP-31020" else {k: f"{v['tanim'][:70]} — {k[3:]} çalışması tedarikçi "
                                                             f"tarafından girildi." for k in D8})
        if v.get("revnot"):
            d["Son Revizyon Notu"] = v["revnot"]
    if v.get("maliyet"):
        d.update(v["maliyet"])
        d["Maliyet Para Birimi"] = v["mpb"]
        d["Maliyet Açıklaması"] = v.get("macik", "")
    d["Maliyet Onay Durumu"] = v["mdur"]
    if v.get("itiraz"):
        d["Tedarikçi İtiraz Notu"] = v["itiraz"]
    update("Kalite Vakaları", v["key"], d)
time.sleep(5)
for v in VAKA:
    if v.get("kapanis"):
        update("Kalite Vakaları", v["key"], {"8D Kapanış Tarihi": v["kapanis"]})

# ═══════════════════════════════════════════════════════════════════════════════
section("Denetimler (cevap kayıtları otomasyonla açılır)")
DEN = [  # key, ted, tip, plan, gerçek, durum, puanlar(oran), bulgular
    ("DEN Özmetal Süreç 2026", "Özmetal", "Süreç Denetimi", "2026-03-18", "2026-03-18", "Yapıldı", 0.92, None),
    ("DEN Nilüfer Süreç 2026", "Nilüfer Plastik", "Süreç Denetimi", "2026-10-01", "2026-10-02", "Yapıldı", 0.74,
     "SÜR-01: Kontrol planı sahada güncel değil; SÜR-04: Lot izlenebilirliği kasa etiketinde kopuyor."),
    ("DEN Marmara Ürün 2026", "Marmara Kauçuk", "Ürün Denetimi", "2026-09-22", "2026-09-23", "Yapıldı", 0.61,
     "ÜRN-01: Kritik ölçü sıklığı yetersiz; ÜRN-04: Lot bazlı sertlik test kaydı yok."),
    ("DEN Kessler Sistem 2026", "Kessler", "Sistem Denetimi", "2026-06-10", "2026-06-11", "Yapıldı", 0.95, None),
    ("DEN Ningbo Süreç 2026", "Ningbo Hengtai", "Süreç Denetimi", "2026-11-17", None, "Planlandı", None, None),
    ("DEN Torino Ön Değ. 2026", "Torino Elettro", "Ön Değerlendirme", "2026-10-28", None, "Planlandı", None, None),
    ("DEN Ege Ürün 2026", "Ege Ambalaj", "Ürün Denetimi", "2026-10-29", None, "Planlandı", None, None),
]
for key, ted, tip, plan, ger, dur, oran, bulgu in DEN:
    create("Denetimler", key, {"Denetim Başlığı": key.replace("DEN ", "") + " Denetimi", "Tedarikçi": T[ted],
                               "Denetim Tipi": tip, "Planlanan Tarih": plan, "Durum": "Planlandı", "Denetçiler": [U]})
print("  … denetim cevaplarının otomasyonla açılması bekleniyor", flush=True)
time.sleep(40)
cv_meta = meta("Denetim Cevapları")
F = lambda n: str(cv_meta[n]["id"])
CEVAPLAR = c.get_all_records(st.get_list_id("Denetim Cevapları"))
for key, ted, tip, plan, ger, dur, oran, bulgu in DEN:
    if dur != "Yapıldı":
        continue
    den_id = CACHE["Denetimler"][key]
    rows = [r for r in CEVAPLAR if (r.get(F("Denetim")) or [{}])[0].get("_id") == den_id]
    for i, r in enumerate(sorted(rows, key=lambda r: r.get(F("Cevap")) or "")):
        kod = r.get(F("Cevap")) or ""
        puan = 10 if oran > 0.9 else round(10 * oran + (1 if i % 2 else -1))
        puan = max(0, min(10, puan))
        d = {"Verilen Puan": puan}
        if bulgu and kod and kod in bulgu:
            d.update({"Verilen Puan": 4, "Bulgu / Yorum": bulgu.split(kod + ": ")[1].split(";")[0],
                      "Aksiyon Gerekli": True})
        CACHE.setdefault("Denetim Cevapları", {})[r["_id"]] = r["_id"]
        update("Denetim Cevapları", r["_id"], d)
    update("Denetimler", key, {"Gerçekleşen Tarih": ger, "Durum": "Yapıldı",
                               **({"Genel Bulgular": bulgu} if bulgu else {"Genel Bulgular": "Majör bulgu yok."})})
print(f"  denetim cevabı güncellendi: {len(CACHE.get('Denetim Cevapları', {}))}")

# ═══════════════════════════════════════════════════════════════════════════════
section("PPAP talepleri (dokümanlar otomasyonla açılır)")
PPAP = [
    ("PPAP Kessler KRP-40118", "Kessler", "KRP-40118", "Seviye 3", "Yeni Parça", "2026-08-20", "2026-10-30"),
    ("PPAP Özmetal KRP-24101 Rev C", "Özmetal", "KRP-24101", "Seviye 2", "Mühendislik Değişikliği", "2026-09-10",
     "2026-10-10"),
    ("PPAP Ningbo KRP-60301", "Ningbo Hengtai", "KRP-60301", "Seviye 3", "Yeni Parça", "2026-10-05", "2026-12-01"),
    ("PPAP Nilüfer KRP-31020 Kalıp", "Nilüfer Plastik", "KRP-31020", "Seviye 1", "Kalıp Değişimi", "2026-10-09",
     "2026-10-31"),
]
for key, ted, mlz, sev, seb, tal, ter in PPAP:
    create("PPAP Talepleri", key, {"Talep Başlığı": key, "Tedarikçi": T[ted], "Malzeme": mlz, "PPAP Seviyesi": sev,
                                   "Sunum Sebebi": seb, "Termin": ter, "Kırpart Sorumlusu": U,
                                   "Notlar": f"{mlz} için {seb.lower()} kapsamında PPAP sunumu."})
print("  … PPAP dokümanlarının otomasyonla açılması bekleniyor", flush=True)
time.sleep(40)
dk_meta = meta("PPAP Dokümanları")
G = lambda n: str(dk_meta[n]["id"])
for r in c.get_all_records(st.get_list_id("PPAP Dokümanları")):
    talep = (r.get(G("PPAP Talebi")) or [{}])[0].get("_id")
    belge = r.get(G("Doküman")) or ""
    CACHE.setdefault("PPAP Dokümanları", {})[r["_id"]] = r["_id"]
    d = {"İnceleyen": U}
    if talep == CACHE["PPAP Talepleri"]["PPAP Özmetal KRP-24101 Rev C"]:
        d.update({"Durum": "Onaylandı", "Versiyon": 1, "Yükleme Tarihi": "2026-10-01",
                  "Tedarikçi Yanıtı": "Rev C çizimine göre hazırlandı."})
    elif talep == CACHE["PPAP Talepleri"]["PPAP Kessler KRP-40118"]:
        if belge in ("PFMEA", "Kontrol Planı"):
            d.update({"Durum": "Revizyon İstendi", "Versiyon": 1, "Yükleme Tarihi": "2026-10-06",
                      "İnceleme Notu": "Soft-touch boya prosesi adımları PFMEA'da eksik; kontrol planına ΔE ölçümü "
                                       "eklenmeli."})
        elif belge in ("MSA", "İlk Proses Çalışmaları"):
            d.update({"Durum": "Yüklendi", "Versiyon": 1, "Yükleme Tarihi": "2026-10-12"})
        elif belge in ("Numune Parça", "Akredite Lab. Dokümanları"):
            d.update({"Durum": "Bekliyor"})
        else:
            d.update({"Durum": "Onaylandı", "Versiyon": 1, "Yükleme Tarihi": "2026-10-03"})
    elif talep == CACHE["PPAP Talepleri"]["PPAP Nilüfer KRP-31020 Kalıp"] and belge.startswith("PSW"):
        d.update({"Durum": "İncelemede", "Versiyon": 1, "Yükleme Tarihi": "2026-10-13"})
    update("PPAP Dokümanları", r["_id"], d)
update("PPAP Talepleri", "PPAP Özmetal KRP-24101 Rev C", {"Durum": "Onaylandı"})
update("PPAP Talepleri", "PPAP Kessler KRP-40118", {"Durum": "Revizyon İstendi"})
update("PPAP Talepleri", "PPAP Nilüfer KRP-31020 Kalıp", {"Durum": "İncelemede"})

# ═══════════════════════════════════════════════════════════════════════════════
section("Sapma talepleri ve sapmalı lotlar")
SAP = [
    ("Sapma – Fitil ölçü toleransı", "Marmara Kauçuk", "KRP-35210", "Selin Arslan", "Boyutsal",
     "Fitil kesit genişliği 12,6 mm (spec 12,0 ±0,4).", "Ekstrüzyon kalıbı aşınması; yeni kalıp 5 hafta sonra.",
     "12,0 ±0,4 mm", "12,6 mm", 6000, "2026-10-01", "2026-11-15", "Montaj denemesinde sızdırmazlık sorunu yok.",
     "Onaylandı", "Montaj denemesi olumlu. Yalnızca PRJ-BUS-23 için, 6.000 adet ile sınırlı."),
    ("Sapma – Alternatif granül", "Nilüfer Plastik", "KRP-31044", "Zeynep Kara", "Malzeme",
     "ABS yerine ABS/PC karışım granül kullanımı.", "Ana granül tedarikinde 3 haftalık gecikme.", "ABS (HM-ABS-01)",
     "ABS/PC Bayblend eşdeğeri", 15000, "2026-10-15", "2026-11-30", "Mekanik değerler eşdeğer veya üstün.",
     "Kalite Onayında", None),
    ("Sapma – Kasa tipi değişikliği", "Özmetal", "KRP-24101", "Serkan Aydın", "Ambalaj",
     "KLT 6429 yerine geçici ahşap palet + koli.", "Boş KLT iadesi gecikiyor.", "KLT 6429", "Ahşap palet + koli",
     30000, "2026-10-14", "2026-10-31", "Hasar riski düşük; parça ara katmanlı.", "Proje Onayında", None),
    ("Sapma – Yüzey pürüzlülüğü", "Ningbo Hengtai", "KRP-24115", "Li Wei", "Proses",
     "Montaj yüzeyi Ra 3,2 yerine Ra 4,0.", "CNC takım değişimi.", "Ra ≤ 3,2", "Ra 4,0", 4000, "2026-09-01",
     "2026-09-30", "Fonksiyonel etkisi yok.", "Reddedildi", "Far ayar hassasiyetini etkileyebilir; kabul edilmedi."),
]
for (key, ted, mlz, talep_eden, tip, tanim, sebep, spec, gercek, mik, bas, bit, risk, dur, notu) in SAP:
    create("Sapma Talepleri", key, {"Sapma Konusu": key, "Tedarikçi": T[ted], "Malzeme": mlz,
                                    "Talep Eden": talep_eden, "Sapma Tipi": tip, "Sapma Tanımı": tanim,
                                    "Sebep": sebep, "Spesifikasyon Değeri": spec, "Gerçek Değer": gercek,
                                    "Talep Edilen Miktar": mik, "Geçerlilik Başlangıcı": bas,
                                    "Geçerlilik Bitişi": bit, "Risk Değerlendirmesi": risk})
time.sleep(10)
for (key, ted, mlz, *_r) in SAP:
    dur, notu = _r[-2], _r[-1]
    d = {"Durum": dur}
    if dur == "Proje Onayında":
        d["Proje Onaycısı"] = U
    if dur == "Onaylandı":
        d["Onay Tarihi"] = "2026-09-29"
    if notu:
        d["Onay / Red Notu"] = notu
    update("Sapma Talepleri", key, d)
time.sleep(8)
for lot, mik, sev_tar, sev in [("MK-1003-01", 2200, "2026-10-03", None), ("MK-1010-02", 1800, "2026-10-10", None)]:
    create("Sapmalı Lotlar", lot, {"Lot No": lot, "Sapma Talebi": "Sapma – Fitil ölçü toleransı", "Miktar": mik,
                                   "Sevk Tarihi": sev_tar, "Not": "Lot etiketine 'SAPMALI' ibaresi eklendi."})

# ═══════════════════════════════════════════════════════════════════════════════
section("Ziyaret & toplantılar")
ZIY = [
    ("Q3 Tedarikçi Performans Gözden Geçirme – Nilüfer", "Nilüfer Plastik", "Kırpart'ta Toplantı", "2026-10-06",
     ["Hakan Yıldız", "Zeynep Kara"],
     "Q3 PPM 312 (hedef 200). Menteşe 8D kapandı; etiketleme hataları tekrarlıyor. Kasa döngüsü iyileşmeli.",
     "Etiket kontrolü için sevkiyat öncesi ikinci onay; Kasım'da süreç denetimi takibi."),
    ("Özmetal Pres Hattı Ziyareti", "Özmetal", "Tedarikçi Ziyareti", "2026-09-17", ["Murat Özkan", "Serkan Aydın"],
     "Yeni 800 ton pres devreye alındı; Rev C braket kalıbı denemeleri izlendi. Çapak kontrolü görsel yapılıyor.",
     "Çapak için otomatik kamera kontrolü yatırımı değerlendirilecek."),
    ("Kessler PPAP Kick-off (Online)", "Kessler", "Online", "2026-08-25", ["Thomas Becker", "Anna Vogel"],
     "KRP-40118 PPAP Seviye 3 kapsamı ve soft-touch boya gereklilikleri konuşuldu.",
     "PFMEA ön taslağı 2 hafta içinde paylaşılacak."),
    ("Marmara Kauçuk Eskalasyon Toplantısı", "Marmara Kauçuk", "Kırpart'ta Toplantı", "2026-10-09", ["Selin Arslan"],
     "Müşteri şikayeti (fitil sertleşmesi) ve kapasite riski. 8D D4 yetersiz bulundu.",
     "Haftalık kalite toplantısı; kapasite artışı için 2. ekstrüzyon hattı planı istenecek."),
]
for konu, ted, tur, tar, kat, notlar, karar in ZIY:
    create("Ziyaret & Toplantılar", konu, {"Konu": konu, "Tedarikçi": T[ted], "Tür": tur, "Tarih": tar,
                                           "Gündem": "1) Performans KPI'ları 2) Açık kalite konuları 3) Kapasite ve "
                                                     "teslimat planı 4) Aksiyonlar",
                                           "Kırpart Katılımcıları": [U], "Tedarikçi Katılımcıları": kat,
                                           "Toplantı Notları": notlar, "Kararlar": karar})

# ═══════════════════════════════════════════════════════════════════════════════
section("Aksiyonlar")
AKS = [  # başlık, kaynak tipi, link alanı, link key, ted, tanım, tip, taraf, kişi, termin, durum, not
    ("Menteşe kalıbı maça yenileme", "8D", "Kalite Vakası", "KV-Menteşe pim çapı", "Nilüfer Plastik",
     "2. göz pim maçasını yenile ve sertleştir.", "Düzeltici", "Tedarikçi", "Zeynep Kara", "2026-10-05", "Kapandı",
     "Maça yenilendi, ölçüm raporu ektedir."),
    ("Kritik ölçü SPC'ye alınsın", "8D", "Kalite Vakası", "KV-Menteşe pim çapı", "Nilüfer Plastik",
     "Pim çapı saatlik SPC takibine alınsın.", "Önleyici", "Tedarikçi", "Zeynep Kara", "2026-10-10",
     "Doğrulama Bekliyor", "SPC kartları 3 lot boyunca dolduruldu."),
    ("Braket çapak giderme istasyonu", "8D", "Kalite Vakası", "KV-Braket çapak", "Özmetal",
     "Çapak alma istasyonu ve %100 görsel kontrol devreye alınsın.", "Düzeltici", "Tedarikçi", "Elif Şahin",
     "2026-10-24", "Devam Ediyor", None),
    ("Vulkanizasyon kayıtlarının paylaşılması", "8D", "Kalite Vakası", "KV-Fitil sertlik", "Marmara Kauçuk",
     "Son 3 ayın vulkanizasyon sıcaklık/süre kayıtlarını paylaş.", "Düzeltici", "Tedarikçi", "Selin Arslan",
     "2026-10-08", "Açık", None),
    ("Kasa etiket ikinci onay", "Ziyaret-Toplantı", "Ziyaret / Toplantı",
     "Q3 Tedarikçi Performans Gözden Geçirme – Nilüfer", "Nilüfer Plastik",
     "Sevkiyat öncesi etiket kontrolünde ikinci onay adımı.", "Önleyici", "Tedarikçi", "Hakan Yıldız",
     "2026-10-31", "Açık", None),
    ("2. ekstrüzyon hattı kapasite planı", "Ziyaret-Toplantı", "Ziyaret / Toplantı",
     "Marmara Kauçuk Eskalasyon Toplantısı", "Marmara Kauçuk", "Kapasite artışı için yatırım ve zaman planı.",
     "İyileştirme", "Tedarikçi", "Selin Arslan", "2026-11-15", "Açık", None),
    ("Kamera ile çapak kontrolü fizibilitesi", "Ziyaret-Toplantı", "Ziyaret / Toplantı",
     "Özmetal Pres Hattı Ziyareti", "Özmetal", "Otomatik görüntü işleme yatırımının fizibilitesi.", "İyileştirme",
     "Kırpart", None, "2026-11-30", "Devam Ediyor", None),
    ("Sapmalı lot izlenebilirliği", "Sapma", "Sapma Talebi", "Sapma – Fitil ölçü toleransı", "Marmara Kauçuk",
     "Sapmalı lotların montaj hattında ayrı stoklanması ve araç VIN eşleştirmesi.", "Önleyici", "Kırpart", None,
     "2026-10-20", "Devam Ediyor", None),
    ("Boya ΔE ölçümü kontrol planına", "Diğer", None, None, "Kessler",
     "Soft-touch boya renk ölçümü (ΔE) kontrol planına eklensin.", "Düzeltici", "Tedarikçi", "Anna Vogel",
     "2026-10-25", "Açık", None),
]
for (bas, kaynak, lf, lk_, ted, tanim, tip, taraf, kisi, ter, dur, notu) in AKS:
    d = {"Aksiyon Başlığı": bas, "Kaynak Tipi": kaynak, "Tedarikçi": T[ted], "Aksiyon Tanımı": tanim,
         "Aksiyon Tipi": tip, "Sorumlu Taraf": taraf, "Termin": ter, "Durum": "Açık", "Sorumlu Kişi (Kırpart)": U}
    if lf:
        d[lf] = lk_
    if kisi:
        d["Sorumlu Kişi (Tedarikçi)"] = kisi
    create("Aksiyonlar", bas, d)
time.sleep(10)
for (bas, *_r) in AKS:
    dur, notu = _r[-2], _r[-1]
    if dur != "Açık":
        d = {"Durum": dur}
        if notu:
            d["Tamamlanma Notu"] = notu
        if dur == "Kapandı":
            d["Doğrulayan"] = U
        update("Aksiyonlar", bas, d)

# ═══════════════════════════════════════════════════════════════════════════════
section("Belgeler (sertifika, sözleşme, şartname, rehber, finansal tablo)")
BEL = [  # ad, tür, tedarikçiler, standart, no, kuruluş, baş, bit, malzemeler, onay
    ("Özmetal IATF 16949 Sertifikası", "Kalite Sertifikası", ["Özmetal"], "IATF 16949", "IATF-0451288",
     "TÜV SÜD", "2024-11-20", "2027-11-19", None, "Onaylandı"),
    ("Nilüfer Plastik IATF 16949 Sertifikası", "Kalite Sertifikası", ["Nilüfer Plastik"], "IATF 16949",
     "IATF-0438821", "Bureau Veritas", "2023-12-01", "2026-11-30", None, "Onaylandı"),
    ("Marmara Kauçuk ISO 9001 Sertifikası", "Kalite Sertifikası", ["Marmara Kauçuk"], "ISO 9001", "Q-9001-77120",
     "TSE", "2023-10-01", "2026-10-31", None, "Onaylandı"),
    ("Ningbo Hengtai IATF 16949 Certificate", "Kalite Sertifikası", ["Ningbo Hengtai"], "IATF 16949",
     "IATF-0412290", "SGS", "2023-09-15", "2026-09-14", None, "Bekliyor"),
    ("Kessler ISO 14001 Zertifikat", "Kalite Sertifikası", ["Kessler"], "ISO 14001", "EMS-14001-3381", "DEKRA",
     "2025-03-01", "2028-02-28", None, "Onaylandı"),
    ("Anadolu Polimer IATF 16949 Sertifikası", "Kalite Sertifikası", ["Anadolu Polimer"], "IATF 16949",
     "IATF-0461102", "TÜV Rheinland", "2025-06-10", "2028-06-09", None, "Onaylandı"),
    ("Kırpart Genel Satınalma Sözleşmesi 2026 – Özmetal", "Satınalma Sözleşmesi", ["Özmetal"], None, "KRP-SAS-2026-11",
     None, "2026-01-01", "2026-12-31", None, None),
    ("Kırpart Kalite Güvence Sözleşmesi – Nilüfer Plastik", "Kalite Sözleşmesi", ["Nilüfer Plastik"], None,
     "KRP-KGS-2025-07", None, "2025-07-01", "2027-06-30", None, None),
    ("KRP-31044 Teknik Şartname Rev A", "Teknik Şartname", ["Nilüfer Plastik", "Kessler"], None, "TS-31044-A",
     None, None, None, ["KRP-31044"], None),
    ("KRP-24101 Çizim Rev C", "Çizim", ["Özmetal"], None, "ÇZ-24101-C", None, None, None, ["KRP-24101"], None),
    ("Tedarikçi Portalı Kullanım Kılavuzu v1.0", "Portal Kullanım Kılavuzu", [], None, "KRP-PRT-001", None, None,
     None, None, None),
    ("MRP Okuma Rehberi", "MRP Okuma Rehberi", [], None, "KRP-PRT-002", None, None, None, None, None),
    ("ASN Oluşturma Rehberi", "ASN Oluşturma Rehberi", [], None, "KRP-PRT-003", None, None, None, None, None),
    ("Özmetal 2025 Bilanço ve Gelir Tablosu", "Finansal Tablo", ["Özmetal"], None, None, None, None, None, None,
     "Onaylandı"),
    ("Marmara Kauçuk 2025 Bilanço ve Gelir Tablosu", "Finansal Tablo", ["Marmara Kauçuk"], None, None, None, None,
     None, None, "Bekliyor"),
]
for ad, tur, teds, std, no, kur, bas, bit, mlz, onay in BEL:
    d = {"Belge Adı": ad, "Belge Türü": tur, "Tedarikçiler": [T[t] for t in teds], "Kırpart Sorumlusu": U,
         "Portal Kullanıcıları": [U], "Dil": "TR+EN" if "Rehber" in ad or "Kılavuz" in ad else "TR", "Versiyon": "1"}
    for k, v in (("Sertifika Standardı", std), ("Belge No", no), ("Veren Kuruluş", kur),
                 ("Geçerlilik Başlangıcı", bas), ("Geçerlilik Bitişi", bit), ("Malzemeler", mlz)):
        if v:
            d[k] = v
    if tur == "Finansal Tablo":
        d["Finansal Yıl"] = "2025"
    create("Belgeler", ad, d)
time.sleep(8)
for ad, *_r in BEL:
    if _r[-1]:
        update("Belgeler", ad, {"Kırpart Onayı": _r[-1]})

# ═══════════════════════════════════════════════════════════════════════════════
section("Varlıklar (kalıp/ekipman) ve bakım & baskı kayıtları")
VAR = [  # demirbaş, ad, tip, ted, malz, kapsam, sahiplik, teslim, göz, ömür, periyot, durum
    ("KLP-31020-01", "Torpido Menteşesi Enjeksiyon Kalıbı 2 Gözlü", "Kalıp", "Nilüfer Plastik", ["KRP-31020"],
     "Outsource", "Kırpart", "2024-02-15", 2, 800000, 90, "Aktif"),
    ("KLP-31044-01", "Havalandırma Izgarası Kalıbı", "Kalıp", "Nilüfer Plastik", ["KRP-31044"], "Yeni Proje",
     "Müşteri", "2025-05-10", 1, 500000, 90, "Aktif"),
    ("KLP-24101-P1", "Kapı Braketi Progresif Pres Kalıbı", "Kalıp", "Özmetal", ["KRP-24101", "YM-24101"],
     "Outsource", "Kırpart", "2023-09-01", 1, 1500000, 60, "Aktif"),
    ("KLP-40118-01", "Koltuk Ayar Kolu 2K Kalıbı", "Kalıp", "Kessler", ["KRP-40118"], "Yeni Proje", "Kırpart",
     "2026-06-20", 2, 600000, 120, "Aktif"),
    ("KLP-35210-E1", "Cam Fitili Ekstrüzyon Kalıbı", "Kalıp", "Marmara Kauçuk", ["KRP-35210"], "Outsource",
     "Kırpart", "2022-04-11", 1, 300000, 60, "Revizyonda"),
    ("FKS-24115-01", "Far Braketi CNC Fikstürü", "Fikstür", "Ningbo Hengtai", ["KRP-24115"], "Yeni Proje",
     "Kırpart", "2025-11-05", 1, 200000, 180, "Aktif"),
    ("KA-31020-M1", "Menteşe Pim Go/No-Go Mastarı", "Kontrol Aparatı", "Nilüfer Plastik", ["KRP-31020"],
     "Outsource", "Kırpart", "2026-10-01", 1, 50000, 365, "Aktif"),
]
for dem, ad, tip, ted, mlz, kap, sah, tes, goz, omur, per, dur in VAR:
    create("Varlıklar (Kalıp / Ekipman)", dem, {
        "Demirbaş No": dem, "Varlık Adı": ad, "Varlık Tipi": tip, "Tedarikçi (Bulunduğu Yer)": T[ted],
        "Malzemeler": mlz, "Proje": "PRJ-" + mlz[0].split("-")[1], "Kapsam": kap, "Sahiplik": sah,
        "Teslim Tarihi": tes, "Göz Sayısı": goz, "Tasarım Ömrü (baskı)": omur, "Bakım Periyodu (gün)": per,
        "Durum": dur})
BAK = [  # demirbaş, tarih, tip, baskı, işlem
    ("KLP-31020-01", "2026-06-20", "Periyodik Bakım", 588000, "Kalıp temizliği, soğutma kanalı kireç sökme."),
    ("KLP-31020-01", "2026-09-18", "Periyodik Bakım", 655000, "Periyodik bakım; 2. göz maça aşınması tespit edildi."),
    ("KLP-31020-01", "2026-10-03", "Revizyon", 662000, "2. göz pim maçası yenilendi (8D aksiyonu)."),
    ("KLP-31044-01", "2026-08-01", "Periyodik Bakım", 141000, "Rutin bakım, itici pimler yağlandı."),
    ("KLP-31044-01", "2026-10-10", "Baskı Sayısı Bildirimi", 176500, "Aylık baskı sayacı bildirimi."),
    ("KLP-24101-P1", "2026-08-25", "Periyodik Bakım", 1214000, "Kesici zımbalar bilendi."),
    ("KLP-24101-P1", "2026-10-11", "Arıza", 1281000, "Delme zımbası kırıldı; yedek ile değiştirildi (çapak vakası)."),
    ("KLP-40118-01", "2026-09-30", "Baskı Sayısı Bildirimi", 38000, "SOP sonrası ilk sayaç bildirimi."),
    ("KLP-35210-E1", "2026-07-15", "Periyodik Bakım", 271000, "Kalıp ağzı parlatma."),
    ("KLP-35210-E1", "2026-09-20", "Revizyon", 286500, "Aşınma nedeniyle revizyona alındı; yeni kalıp siparişi verildi."),
    ("FKS-24115-01", "2026-05-12", "Periyodik Bakım", 21000, "Referans pimleri kontrol edildi."),
]
for dem, tar, tip, baski, islem in BAK:
    create("Bakım & Baskı Kayıtları", f"{dem} {tar}", {"Özet": f"{dem} – {tip}", "Varlık": dem, "Tarih": tar,
                                                       "Kayıt Tipi": tip, "Güncel Baskı Sayısı": baski,
                                                       "Yapılan İşlem": islem, "Kırpart Kontrolü": tar < "2026-10-01"})
    time.sleep(2)  # otomasyon varlığı sırayla güncellesin

# ═══════════════════════════════════════════════════════════════════════════════
section("Performans kartları (Ağustos & Eylül 2026)")
PERF = {  # kısa: [(dönem, teslim alınan, hatalı, hat iadesi, gkk, otd%, 8d gün, denetim%, sertifika, sapma, iletişim)]
    "Özmetal": [("2026-8", 96000, 9, 0, 0, 97, 0, 92, 1, 0, 90), ("2026-9", 118000, 18, 1, 0, 96, 0, 92, 1, 0, 90)],
    "Nilüfer Plastik": [("2026-8", 61000, 9, 0, 0, 94, 0, 74, 1, 0, 75),
                        ("2026-9", 72000, 256, 0, 2, 88, 14, 74, 1, 1, 70)],
    "Anadolu Polimer": [("2026-8", 140000, 0, 0, 0, 100, 0, 88, 1, 0, 95), ("2026-9", 155000, 0, 0, 0, 98, 0, 88, 1, 0, 95)],
    "Marmara Kauçuk": [("2026-8", 11000, 180, 1, 0, 90, 35, 61, 0, 0, 60),
                       ("2026-9", 12500, 520, 0, 1, 86, 42, 61, 0, 1, 55)],
    "Ege Ambalaj": [("2026-8", 38000, 12, 0, 0, 96, 0, 80, 0, 0, 80), ("2026-9", 41000, 20, 0, 0, 95, 0, 80, 0, 0, 80)],
    "Kessler": [("2026-8", 18000, 0, 0, 0, 100, 0, 95, 1, 0, 95), ("2026-9", 9000, 12, 0, 0, 98, 0, 95, 1, 0, 90)],
    "Ningbo Hengtai": [("2026-8", 22000, 140, 0, 1, 85, 32, 0, 0, 1, 70),
                       ("2026-9", 15000, 30, 0, 0, 91, 0, 0, 0, 0, 75)],
}
BAS_BIT = {"2026-8": ("2026-08-01", "2026-08-31"), "2026-9": ("2026-09-01", "2026-09-30")}
for kisa, rows in PERF.items():
    for (don, tes, hat, hi, gkk, otd, d8, den, sert, sap, ilt) in rows:
        key = f"{kisa} {don}"
        create("Performans Kartları", key, {
            "Dönem": f"{don} {kisa}", "Tedarikçi": T[kisa], "Dönem Başlangıcı": BAS_BIT[don][0],
            "Dönem Bitişi": BAS_BIT[don][1], "Teslim Alınan Miktar": tes, "Hatalı Miktar": hat,
            "Hat İadesi Vaka Sayısı": hi, "GKK Parti Reddi Sayısı": gkk, "Zamanında Teslim %": otd,
            "Ort. 8D Kapanış (gün)": d8, "Son Denetim Başarı %": den, "Geçerli Sertifika (1/0)": sert,
            "Sapma Talebi Sayısı": sap, "İletişim Puanı": ilt,
            "Kırpart Yorumu": "Dönem değerlendirmesi tedarikçi ile paylaşıldı." if don == "2026-9" else ""})
time.sleep(10)
for kisa, rows in PERF.items():
    for r in rows:
        update("Performans Kartları", f"{kisa} {r[0]}", {"Yayınlandı": True})  # → 32: puan tedarikçi kartına

section("BİTTİ")
print(f"Toplam: {STATS['create']} kayıt oluşturuldu, {STATS['update']} güncelleme, {STATS['error']} hata")
