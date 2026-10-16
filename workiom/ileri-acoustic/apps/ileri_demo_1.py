"""Demo 1: ana veriler 10+ ve 12 talep (CRM-01/11/12 tetiklenir)."""
from apps.ileri_demo_lib import *
def ensure(l, rows):
    have = by_primary(l); n = 0
    for r in rows:
        if r[next(k for k in r)] not in have: create(l, r); n += 1
    print(f"  {l}: +{n}")
ensure("Sistemler", [{"Sistem Adı": n, "Sistem Ailesi": f, "Standart Panel Genişliği (cm)": w, "Kalınlık (mm)": t,
    "m² Birim Fiyatı": p, "Kapı Birim Fiyatı": 600, "Teleskopik Panel Birim Fiyatı": 230, "Aktif mi": False}
    for n, f, w, t, p in [("PANELITE 120 (Demo)", "Hareketli Panel", 120, 120, 205),
                          ("PANSMART CAM (Demo)", "Cam Bölme", 100, 90, 260),
                          ("PANPLUS AKUSTİK (Demo)", "Hareketli Panel", 120, 125, 255),
                          ("EPART-SLIM (Demo)", "Kapı", 90, 45, 130)]])
ensure("İstasyonlar", [{"İstasyon Adı": n, "Sıra": s, "Aşama Grubu": g, "Aktif mi": False, "Sorumlu": "OWNER"}
    for n, s, g in [("Kalite Kontrol (pasif)", 9, "Paketleme"), ("Sevkiyat Hazırlık (pasif)", 10, "Paketleme")]])
ensure("Tedarikçiler", [{"Firma Adı": n, "Yetkili": y, "Telefon": t, "E-posta": e, "Tedarik Ettiği Kategoriler": k}
    for n, y, t, e, k in [
     ("Ege Profil Sanayi", "Murat Kaya", "+902324000001", "satis@egeprofil.example.com", ["Profil"]),
     ("Anadolu Ray Sistemleri", "Selin Ak", "+903124000002", "info@anadoluray.example.com", ["Ray", "Makara"]),
     ("Marmara MDF", "Hakan Demir", "+902164000003", "siparis@marmaramdf.example.com", ["Plaka", "Yüzey"]),
     ("Renk Boya Kimya", "Elif Şahin", "+902124000004", "satis@renkboya.example.com", ["Boya"]),
     ("Cam Dünyası", "Okan Yıldız", "+902624000005", "info@camdunyasi.example.com", ["Cam"]),
     ("Paket Ambalaj", "Zeynep Arslan", "+902224000006", "satis@paketamb.example.com", ["Ambalaj"]),
     ("Teknik Aksesuar Ltd.", "Burak Çelik", "+902164000007", "info@teknikaks.example.com", ["Aksesuar"])]])
ensure("Hesap Parametreleri", [{"Parametre": p, "Parametre Kodu": k, "Değer": v, "Para Birimi": pb, "Birim": b,
    "Geçerlilik Tarihi": "2026-12-31T00:00:00Z"} for p, k, v, pb, b in [
     ("Nakliye bedeli (yurt dışı)", "FYT-NAKLIYE-YD", 1800, "USD", "sabit"),
     ("Sandık ambalaj (adet)", "FYT-SANDIK", 85, "USD", "adet"),
     ("Kapı aksesuar seti", "FYT-KAPI-AKS", 45, "USD", "adet"),
     ("Fırın boya (m²)", "FYT-BOYA-M2", 6, "USD", "m²"),
     ("Taşyünü (m²)", "FYT-TASYUNU", 4.5, "USD", "m²"),
     ("Ray R2 metre fiyatı", "FYT-RAY-R2", 32, "USD", "m")]])
FIRMALAR = [  # ad, tip, ülke, şehir, tür, sektör
 ("Pera Palas Otel", "Yurt İçi", "Türkiye", "İstanbul", "Son Kullanıcı", "Otel"),
 ("Ankara Kongre Merkezi", "Yurt İçi", "Türkiye", "Ankara", "Son Kullanıcı", "Kongre / Etkinlik"),
 ("Bilkent Mimarlık", "Yurt İçi", "Türkiye", "Ankara", "Mimarlık", "Ofis"),
 ("Ege Üniversitesi Yapı İşleri", "Yurt İçi", "Türkiye", "İzmir", "Son Kullanıcı", "Eğitim"),
 ("Akdeniz İnşaat", "Yurt İçi", "Türkiye", "Antalya", "Müteahhit", "Otel"),
 ("Bursa Şehir Hastanesi", "Yurt İçi", "Türkiye", "Bursa", "Son Kullanıcı", "Sağlık"),
 ("Baku Expo LLC", "Yurt Dışı", "Azerbaycan", "", "Bayi", "Kongre / Etkinlik"),
 ("Doha Hospitality Group", "Yurt Dışı", "Katar", "", "Son Kullanıcı", "Otel"),
 ("Riyadh Office Partners", "Yurt Dışı", "Suudi Arabistan", "", "Bayi", "Ofis"),
 ("Lagos Event Hall", "Yurt Dışı", "Nijerya", "", "Müteahhit", "Kongre / Etkinlik")]
ensure("Firmalar", [{"Firma Adı": a, "Müşteri Tipi": t, "Ülke": u, **({"Şehir": s} if s else {}), "Firma Türü": tr,
    "Sektör": se, "Müşteri Durumu": "Aday", "Satış Temsilcisi": "OWNER"} for a, t, u, s, tr, se in FIRMALAR])
KISI = ["Mehmet Aydın", "Ayten Koç", "Can Erdem", "Derya Öztürk", "Serkan Yılmaz", "Nur Çetin",
        "Elvin Aliyev", "Khalid Al-Thani", "Faisal Al-Saud", "Chinedu Okafor"]
ensure("Kişiler", [{"Ad Soyad": k, "Firma": FIRMALAR[i][0], "Unvan / Rol": ["Satın Alma Müdürü", "Proje Müdürü",
    "Mimar", "Yapı İşleri Şefi", "Şantiye Şefi", "Teknik Müdür", "Director", "Procurement Manager",
    "Architect", "Project Manager"][i], "Telefon": f"+90532100{i:04d}", "E-posta": f"kisi{i}@example.com",
    "Dil": "TR" if i < 6 else "EN"} for i, k in enumerate(KISI)])
SIS = ["PANELITE", "PANSMART", "PANPLUS", "PANSLIM 80", "PANSLIDE WOOD", "EPART-DOORSON"]
have = by_primary("Talepler"); n = 0
for i, (f, *_r) in enumerate(FIRMALAR + [("DEMO Grand Otel İzmir",), ("DEMO Accra Conference Centre",)]):
    konu = f"{f} – {SIS[i % 6]} bölme duvar talebi"
    if konu in have: continue
    kisi = KISI[i] if i < 10 else ("DEMO Ayşe Yılmaz" if i == 10 else "DEMO Kwame Mensah")
    ulke = FIRMALAR[i][2] if i < 10 else ("Türkiye" if i == 10 else "Gana")
    create("Talepler", {"Talep Konusu": konu, "Kaynak": ["Web", "Telefon", "E-posta", "Fuar", "Referans",
           "Düzenli Müşteri", "WhatsApp"][i % 7], "Firma": f, "Yetkili": kisi, "Ülke": ulke,
           "Sorumlu": "OWNER", "İlgilenilen Sistem": [SIS[i % 6]],
           "Talep İçeriği": f"{f} için yaklaşık {8 + i * 3} m uzunluğunda hareketli bölme duvar; teklif isteniyor.",
           "Gönderen Adı": kisi, "Gönderen E-posta": f"kisi{i}@example.com"})
    n += 1
print(f"  Talepler: +{n}")
