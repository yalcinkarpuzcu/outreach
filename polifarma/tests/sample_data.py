"""
Polifarma PoC — örnek veri yükleyici. Builder klasöründen çalıştırılır (.env içinde API_KEY):
    python /path/to/sample_data.py [user_id]

Oluşturulan tüm kayıt id'leri sample_data_created.json'a yazılır (temizlik için).
Otomasyonlar çalışır: lot girişleri giriş hareketi, formül bileşenleri çıkış hareketi üretir;
kişi alanlarına atanan kullanıcıya bildirimler ve iki onay isteği gider.
"""
import json
import sys
import time

sys.path.insert(0, ".")
from workiom.client import WorkiomClient
from workiom.state import AppState

c = WorkiomClient(open(".env").read().split("=", 1)[1].strip())
P, S, T = AppState("Ar-Ge Proje Takibi"), AppState("Numune ve Hammadde Stok"), AppState("Toplantı Yönetimi")
U = sys.argv[1] if len(sys.argv) > 1 else "162102"
created = []

FAZ = ["1. Literatür ve Fizibilite", "2. Ön Formülasyon", "3. Formülasyon Geliştirme",
       "4. Analitik Metot Geliştirme ve Validasyon", "5. Stabilite", "6. Pilot Üretim / Scale-up",
       "7. Ruhsat Dosyası (CTD)", "8. Üretime Transfer"]


def mk(st, lst, vals):
    lid = st.get_list_id(lst)
    payload = {}
    for k, v in vals.items():
        fid = st.get_field_id(lst, k)
        if not fid:
            raise KeyError(f"{lst}.{k}")
        payload[str(fid)] = v
    rid = c.create_record(lid, payload)
    created.append([lid, rid, lst])
    return rid


def upd(st, lst, rid, vals):
    c.update_record(st.get_list_id(lst), rid, {str(st.get_field_id(lst, k)): v for k, v in vals.items()})


def L(*ids): return [{"_id": i} for i in ids]


def log(msg): print(msg, flush=True)


# ── 1. Tedarikçiler ve malzemeler ────────────────────────────────────────────
log("1) Tedarikçiler ve malzeme kartları")
ted = {}
for ad, kisi, mail, onay in [
    ("Granules India Ltd.", "Ravi Kumar", "api.sales@granules-sample.com", True),
    ("Aurobindo Pharma", "Sanjay Rao", "export@aurobindo-sample.com", True),
    ("Colorcon Türkiye", "Elif Aydın", "elif.aydin@colorcon-sample.com", True),
    ("Roquette Frères", "Marie Dubois", "pharma@roquette-sample.com", True),
    ("DFE Pharma", "Jan de Vries", "orders@dfepharma-sample.com", True),
    ("Gland Pharma", "Anil Mehta", "heparin@gland-sample.com", False),
    ("Merck Life Science", "Can Yılmaz", "tr.lab@merck-sample.com", True),
]:
    ted[ad] = mk(S, "Tedarikçiler", {"Tedarikçi Adı": ad, "İletişim Kişisi": kisi, "E-Posta": mail,
                                     "Telefon": "+90 212 555 01 00", "Onaylı Tedarikçi": onay})

mal = {}
MALZEME = [  # kod, ad, tip, birim, depolama, kritik, tedarikçi
    ("API-001", "Metformin HCl", "Etken Madde", "kg", "Oda Sıcaklığı (15-25°C)", 5, "Granules India Ltd."),
    ("API-002", "Amoksisilin Trihidrat", "Etken Madde", "kg", "Nemden Korunmalı", 3, "Aurobindo Pharma"),
    ("API-003", "Potasyum Klavulanat (1:1 Avicel)", "Etken Madde", "kg", "Buzdolabı (2-8°C)", 2, "Aurobindo Pharma"),
    ("API-004", "Diklofenak Sodyum", "Etken Madde", "kg", "Oda Sıcaklığı (15-25°C)", 1, "Granules India Ltd."),
    ("API-005", "Rosuvastatin Kalsiyum", "Etken Madde", "g", "Işıktan Korunmalı", 200, "Aurobindo Pharma"),
    ("API-006", "Enoksaparin Sodyum", "Etken Madde", "g", "Buzdolabı (2-8°C)", 50, "Gland Pharma"),
    ("EXC-001", "Mikrokristalin Selüloz PH102", "Eksipiyan", "kg", "Oda Sıcaklığı (15-25°C)", 10, "Roquette Frères"),
    ("EXC-002", "Laktoz Monohidrat (SuperTab 11SD)", "Eksipiyan", "kg", "Oda Sıcaklığı (15-25°C)", 10, "DFE Pharma"),
    ("EXC-003", "HPMC K100M", "Eksipiyan", "g", "Oda Sıcaklığı (15-25°C)", 1500, "Colorcon Türkiye"),
    ("EXC-004", "Magnezyum Stearat", "Eksipiyan", "g", "Oda Sıcaklığı (15-25°C)", 500, "Roquette Frères"),
    ("EXC-005", "Krospovidon", "Eksipiyan", "g", "Nemden Korunmalı", 500, "Colorcon Türkiye"),
    ("EXC-006", "Ksantan Gum", "Eksipiyan", "g", "Oda Sıcaklığı (15-25°C)", 300, "Roquette Frères"),
    ("EXC-007", "Karbomer 940", "Eksipiyan", "g", "Oda Sıcaklığı (15-25°C)", 300, "Merck Life Science"),
    ("COT-001", "Opadry II Beyaz 85F18422", "Ambalaj", "g", "Oda Sıcaklığı (15-25°C)", 1000, "Colorcon Türkiye"),
    ("REF-001", "Glucophage XR 1000 mg (referans)", "Referans Ürün", "Adet", "Oda Sıcaklığı (15-25°C)", 60, None),
    ("REF-002", "Augmentin BID 400/57 mg süspansiyon (referans)", "Referans Ürün", "Adet", "Oda Sıcaklığı (15-25°C)", 10, None),
    ("STD-001", "Metformin HCl USP Referans Standardı", "Standart Madde", "mg", "Buzdolabı (2-8°C)", 200, "Merck Life Science"),
    ("SOL-001", "Metanol HPLC Grade", "Çözücü", "L", "Oda Sıcaklığı (15-25°C)", 4, "Merck Life Science"),
]
for kod, ad, tip, birim, dep, krit, t in MALZEME:
    v = {"Malzeme Kodu": kod, "Malzeme Adı": ad, "Tip": tip, "Birim": birim, "Depolama Koşulu": dep,
         "Kritik Stok Seviyesi": krit, "Stok Sorumlusu": U}
    if t:
        v["Tedarikçi"] = L(ted[t])
    mal[kod] = mk(S, "Malzeme Kartları", v)

# ── 2. Lotlar (otomasyon giriş hareketi yazar) ───────────────────────────────
log("2) Lotlar")
lot = {}
LOTLAR = [  # lot no, malzeme, giriş, birim maliyet (TL), giriş tarihi, SKT, tarih tipi, durum
    ("MET-2604-01", "API-001", 25, 1450, "2026-04-02", "2028-03-31", "Retest", "Onaylı"),
    ("MET-2609-02", "API-001", 10, 1480, "2026-09-15", "2028-08-31", "Retest", "Karantinada"),
    ("AMX-2605-01", "API-002", 12, 2100, "2026-05-10", "2027-04-30", "Retest", "Onaylı"),
    ("CLV-2605-01", "API-003", 4, 9800, "2026-05-10", "2026-11-12", "Son Kullanma", "Onaylı"),
    ("DIK-2606-01", "API-004", 3, 1750, "2026-06-01", "2028-05-31", "Retest", "Onaylı"),
    ("ROS-2511-01", "API-005", 600, 38, "2025-11-20", "2027-10-31", "Retest", "Onaylı"),
    ("ENX-2610-01", "API-006", 120, 410, "2026-10-14", "2027-09-30", "Son Kullanma", "Karantinada"),
    ("MCC-2603-01", "EXC-001", 50, 165, "2026-03-05", "2029-02-28", "Son Kullanma", "Onaylı"),
    ("LAK-2603-01", "EXC-002", 40, 120, "2026-03-05", "2028-12-31", "Son Kullanma", "Onaylı"),
    ("HPM-2604-01", "EXC-003", 2000, 1.9, "2026-04-02", "2028-03-31", "Son Kullanma", "Onaylı"),
    ("MGS-2604-01", "EXC-004", 2500, 0.45, "2026-04-02", "2029-03-31", "Son Kullanma", "Onaylı"),
    ("KRP-2605-01", "EXC-005", 3000, 0.9, "2026-05-02", "2028-04-30", "Son Kullanma", "Onaylı"),
    ("KSN-2605-01", "EXC-006", 2000, 0.7, "2026-05-02", "2028-04-30", "Son Kullanma", "Onaylı"),
    ("KRB-2606-01", "EXC-007", 1500, 1.2, "2026-06-01", "2028-05-31", "Son Kullanma", "Onaylı"),
    ("OPD-2604-01", "COT-001", 5000, 0.8, "2026-04-02", "2028-03-31", "Son Kullanma", "Onaylı"),
    ("OPD-2608-02", "COT-001", 3000, 0.8, "2026-08-20", "2028-07-31", "Son Kullanma", "Ret"),
    ("GLX-2604-01", "REF-001", 180, 12, "2026-04-10", "2027-06-30", "Son Kullanma", "Onaylı"),
    ("AUG-2605-01", "REF-002", 30, 95, "2026-05-15", "2027-03-31", "Son Kullanma", "Onaylı"),
    ("STD-2604-01", "STD-001", 500, 6.5, "2026-04-15", "2027-04-15", "Son Kullanma", "Onaylı"),
    ("MEO-2609-01", "SOL-001", 20, 310, "2026-09-01", "2028-08-31", "Son Kullanma", "Onaylı"),
]
lot_status = {}
for no, m, mik, bm, gt, skt, tt, durum in LOTLAR:
    lot[no] = mk(S, "Lotlar", {"Lot No": no, "Malzeme": L(mal[m]), "Giriş Miktarı": mik, "Birim Maliyet": bm,
                               "Giriş Tarihi": gt, "Üretim Tarihi": gt, "SKT / Retest Tarihi": skt, "Tarih Tipi": tt,
                               "Raf / Lokasyon": f"Ar-Ge Depo / Raf {m[-1]}", "Stok Sorumlusu": U})
    lot_status[no] = durum
log("   giriş hareketleri ve karantina otomasyonu bekleniyor (45 sn)...")
time.sleep(45)
for no, durum in lot_status.items():
    if durum != "Karantinada":
        upd(S, "Lotlar", lot[no], {"Lot Durumu": durum})
upd(S, "Lotlar", lot["CLV-2605-01"], {"SKT Yaklaşıyor": True})   # SKT 20 gün içinde

# ── 3. Projeler ve faz kapıları ──────────────────────────────────────────────
log("3) Projeler ve faz kapıları")
prj = {}
PROJELER = [  # kod, ad, form, tip, ref, faz idx, başlangıç, hedef, bütçe, risk, durum
    ("PF-2026-001", "Metformin XR 1000 mg Film Tablet", "Tablet", "Jenerik", "Glucophage XR 1000 mg", 4, "2026-01-12", "2027-09-30", 1850000, "Orta", "Aktif"),
    ("PF-2026-002", "Amoksisilin/Klavulanat 400/57 mg Oral Süspansiyon", "Süspansiyon", "Jenerik", "Augmentin BID 400/57 mg", 2, "2026-03-02", "2028-03-31", 1200000, "Yüksek", "Aktif"),
    ("PF-2026-003", "Diklofenak Sodyum %1 Krem", "Krem", "Line Extension", "Voltaren Emulgel %1", 1, "2026-06-15", "2027-12-31", 650000, "Düşük", "Aktif"),
    ("PF-2026-004", "Enoksaparin Sodyum 40 mg/0,4 mL Enjektabl", "Enjektabl", "Yeni Formülasyon", "Clexane 40 mg", 0, "2026-09-01", "2029-06-30", 3400000, "Yüksek", "Aktif"),
    ("PF-2025-011", "Rosuvastatin 20 mg Film Tablet", "Tablet", "Jenerik", "Crestor 20 mg", 6, "2025-02-03", "2026-12-31", 900000, "Düşük", "Aktif"),
]
for kod, ad, form, tip, ref, fi, bas, hedef, butce, risk, durum in PROJELER:
    prj[kod] = mk(P, "Ar-Ge Projeleri", {"Proje Kodu": kod, "Ürün Adı": ad, "Dozaj Formu": form, "Proje Tipi": tip,
                                         "Referans Ürün": ref, "Mevcut Faz": FAZ[fi], "Proje Lideri": U, "Ekip": [U],
                                         "Ar-Ge Direktörü": U, "Başlangıç Tarihi": bas, "Hedef Ruhsat Tarihi": hedef,
                                         "Bütçe": butce, "Risk Seviyesi": risk, "Durum": durum,
                                         "Açıklama": f"{ref} referanslı {tip.lower()} geliştirme projesi."})

GATE_DATES = {  # proje: [(planlanan başlangıç, planlanan bitiş, gerçekleşen bitiş)] faz 1..n
    "PF-2026-001": [("2026-01-12", "2026-02-13", "2026-02-11"), ("2026-02-16", "2026-03-27", "2026-04-03"),
                    ("2026-04-06", "2026-06-12", "2026-06-10"), ("2026-06-15", "2026-08-28", "2026-09-04"),
                    ("2026-09-07", "2027-03-31", None)],
    "PF-2026-002": [("2026-03-02", "2026-04-10", "2026-04-08"), ("2026-04-13", "2026-06-05", "2026-06-19"),
                    ("2026-06-22", "2026-10-16", None)],
    "PF-2026-003": [("2026-06-15", "2026-07-31", "2026-07-29"), ("2026-08-03", "2026-10-09", None)],
    "PF-2026-004": [("2026-09-01", "2026-12-18", None)],
    "PF-2025-011": [("2025-02-03", "2025-03-14", "2025-03-12"), ("2025-03-17", "2025-05-02", "2025-04-30"),
                    ("2025-05-05", "2025-07-25", "2025-07-30"), ("2025-07-28", "2025-09-26", "2025-09-24"),
                    ("2025-09-29", "2026-06-26", "2026-07-03"), ("2026-07-06", "2026-08-28", "2026-08-27"),
                    ("2026-08-31", "2026-11-27", None)],
}
kapi = {}
for kod, rows in GATE_DATES.items():
    for i, (pb, pe, ge) in enumerate(rows):
        v = {"Faz Adı": FAZ[i], "Sonraki Faz": FAZ[min(i + 1, 7)], "Planlanan Başlangıç": pb, "Planlanan Bitiş": pe,
             "1. Onaylayan (Direktör)": U, "2. Onaylayan (QA/Ruhsat)": U, "Proje": L(prj[kod]),
             "Giriş Kriterleri": "Önceki faz çıktıları onaylı; ekip ve bütçe atanmış.",
             "Çıkış Kriterleri": f"{FAZ[i]} raporu tamamlandı ve gözden geçirildi."}
        if ge:
            v.update({"Durum": "Onaylandı", "Gerçekleşen Bitiş": ge, "Onay Notu": "Kriterler karşılandı, sonraki faza geçiş onaylandı."})
        else:
            v["Durum"] = "Devam Ediyor"
        kapi[(kod, i + 1)] = mk(P, "Faz Kapıları", v)
upd(P, "Faz Kapıları", kapi[("PF-2026-003", 2)], {"Gecikmede": True})   # planlanan bitiş geçti

# ── 4. Denemeler ve formül bileşenleri (otomasyon stoktan düşer) ─────────────
log("4) Formülasyon denemeleri ve formül bileşenleri")
den = {}
DENEMELER = [  # kod, proje, batch, büyüklük, birim, sonuç, tarih, parametre, not
    ("MET-F01", "PF-2026-001", "B-MET-001", 2, "kg", "Uygun Değil", "2026-04-14", "HPMC %25, yaş granülasyon, 12 kN baskı", "Çözünürlük profili referansın üstünde (1. saatte %48)."),
    ("MET-F02", "PF-2026-001", "B-MET-002", 2, "kg", "Tekrar", "2026-05-06", "HPMC %32, yaş granülasyon, 14 kN baskı", "Sertlik düşük; kurutma süresi uzatılarak tekrar edilecek."),
    ("MET-F03", "PF-2026-001", "B-MET-003", 3, "kg", "Uygun", "2026-05-28", "HPMC %32, kurutma 45 dk, 15 kN baskı", "f2 = 68; referansla benzer profil."),
    ("MET-F04", "PF-2026-001", "B-MET-004", 10, "kg", "Uygun", "2026-08-18", "F03 formülü, 10 kg ölçek büyütme", "Pilot öncesi doğrulama batch'i; stabiliteye alındı."),
    ("AMC-S01", "PF-2026-002", "B-AMC-001", 1, "kg", "Uygun Değil", "2026-07-08", "Ksantan %0,4, toz karışım", "Sulandırma sonrası çökme 2. günde."),
    ("AMC-S02", "PF-2026-002", "B-AMC-002", 1, "kg", "Devam Ediyor", "2026-09-22", "Ksantan %0,6, toz karışım", "7 günlük sulandırılmış stabilite devam ediyor."),
    ("DIK-K01", "PF-2026-003", "B-DIK-001", 2, "kg", "Devam Ediyor", "2026-09-10", "Karbomer %1, nötralizasyon TEA", "Viskozite hedefin altında."),
    ("ROS-T01", "PF-2025-011", "B-ROS-001", 2, "kg", "Uygun", "2025-06-12", "Direkt baskı, krospovidon %4", "Referansla eşdeğer çözünürlük."),
]
for kod, p, b, bb, br, sonuc, tarih, par, notu in DENEMELER:
    den[kod] = mk(P, "Formülasyon Denemeleri", {"Deneme Kodu": kod, "Proje": L(prj[p]), "Batch No": b, "Batch Büyüklüğü": bb,
                                                "Batch Birimi": br, "Proses Parametreleri": par, "Sonuç": sonuc,
                                                "Sonuç Notu": notu, "Sorumlu": U, "Tarih": tarih})
BILESEN = {  # deneme: [(lot, fonksiyon, miktar, oran)]
    "MET-F01": [("MET-2604-01", "Etken Madde", 1.0, 50), ("HPM-2604-01", "Bağlayıcı", 500, 25), ("MCC-2603-01", "Dolgu", 0.45, 22.5), ("MGS-2604-01", "Kaydırıcı", 20, 1)],
    "MET-F02": [("MET-2604-01", "Etken Madde", 1.0, 50), ("HPM-2604-01", "Bağlayıcı", 640, 32), ("MCC-2603-01", "Dolgu", 0.32, 16), ("MGS-2604-01", "Kaydırıcı", 20, 1)],
    "MET-F03": [("MET-2604-01", "Etken Madde", 1.5, 50), ("HPM-2604-01", "Bağlayıcı", 300, 32), ("MCC-2603-01", "Dolgu", 0.48, 16), ("MGS-2604-01", "Kaydırıcı", 30, 1), ("OPD-2604-01", "Kaplama", 90, 3)],
    "MET-F04": [("MET-2604-01", "Etken Madde", 5.0, 50), ("MCC-2603-01", "Dolgu", 1.6, 16), ("MGS-2604-01", "Kaydırıcı", 100, 1), ("OPD-2604-01", "Kaplama", 300, 3)],
    "AMC-S01": [("AMX-2605-01", "Etken Madde", 0.46, 46), ("CLV-2605-01", "Etken Madde", 0.13, 13), ("KSN-2605-01", "Diğer", 4, 0.4)],
    "AMC-S02": [("AMX-2605-01", "Etken Madde", 0.46, 46), ("CLV-2605-01", "Etken Madde", 0.13, 13), ("KSN-2605-01", "Diğer", 6, 0.6)],
    "DIK-K01": [("DIK-2606-01", "Etken Madde", 0.02, 1), ("KRB-2606-01", "Diğer", 20, 1)],
    "ROS-T01": [("ROS-2511-01", "Etken Madde", 42, 2.1), ("LAK-2603-01", "Dolgu", 1.2, 60), ("MCC-2603-01", "Dolgu", 0.6, 30), ("KRP-2605-01", "Dağıtıcı", 80, 4), ("MGS-2604-01", "Kaydırıcı", 20, 1)],
}
proj_of = {k: p for k, p, *_ in DENEMELER}
for d, rows in BILESEN.items():
    for lt, fonk, mik, oran in rows:
        mk(S, "Formül Bileşenleri", {"Deneme": L(den[d]), "İlgili Proje": L(prj[proj_of[d]]), "Lot": L(lot[lt]),
                                     "Fonksiyon": fonk, "Miktar": mik, "Formüldeki Oran (%)": oran})

# ── 5. Analitik, stabilite, görev/sapma ──────────────────────────────────────
log("5) Analitik, stabilite, görevler")
for p, d, tip, metot, val, sonuc, tarih in [
    ("PF-2026-001", "MET-F03", "Çözünürlük", "USP App. II, 50 rpm, pH 6.8 fosfat tamponu", "Valide Edildi", "f2 = 68, 1-2-4-8-12. saat profilleri spesifikasyon içinde.", "2026-07-20"),
    ("PF-2026-001", "MET-F03", "İçerik Tayini", "HPLC-UV 232 nm, C18 kolon", "Valide Edildi", "%99,4 (spek. %95-105).", "2026-08-05"),
    ("PF-2026-001", "MET-F04", "Safsızlık", "HPLC, siyanoguanidin ve melamin", "Validasyonda", "Doğrusallık ve doğruluk tamamlandı; sağlamlık devam ediyor.", "2026-10-02"),
    ("PF-2026-002", "AMC-S02", "İçerik Tayini", "HPLC-UV 220 nm, amoksisilin + klavulanat", "Geliştirmede", "Klavulanat pikinde kuyruklanma; mobil faz pH optimizasyonu.", "2026-10-12"),
    ("PF-2025-011", "ROS-T01", "Çözünürlük", "USP App. II, 50 rpm, pH 6.6 sitrat", "Valide Edildi", "Referansla eşdeğer (f2 = 74).", "2025-08-20"),
]:
    mk(P, "Analitik Çalışmalar", {"Proje": L(prj[p]), "Deneme": L(den[d]), "Test Tipi": tip, "Metot": metot,
                                  "Validasyon Durumu": val, "Sonuç": sonuc, "Sorumlu": U, "Tarih": tarih})

stab = {}
for key, p, d, kosul, bas, noktalar, sonraki, sonuc, sapma, acik in [
    ("MET-25", "PF-2026-001", "MET-F04", "25°C / %60 RH", "2026-05-01", ["0. Ay", "1. Ay", "3. Ay"], "2026-11-01", "Devam Ediyor", False, ""),
    ("MET-40", "PF-2026-001", "MET-F04", "40°C / %75 RH", "2026-05-01", ["0. Ay", "1. Ay", "3. Ay"], "2026-11-01", "OOT (Trend)", True, "3. ayda siyanoguanidin %0,08 → trend; spek. %0,15."),
    ("ROS-25", "PF-2025-011", "ROS-T01", "25°C / %60 RH", "2025-08-01", ["0. Ay", "1. Ay", "3. Ay", "6. Ay", "9. Ay", "12. Ay"], "2027-02-01", "Uygun", False, ""),
    ("ROS-40", "PF-2025-011", "ROS-T01", "40°C / %75 RH", "2025-08-01", ["0. Ay", "1. Ay", "3. Ay", "6. Ay"], None, "Uygun", False, ""),
]:
    v = {"Proje": L(prj[p]), "Batch (Deneme)": L(den[d]), "Koşul": kosul, "Başlangıç Tarihi": bas,
         "Zaman Noktaları": noktalar, "Sorumlu": U, "Sonuç": sonuc, "Sapma": sapma}
    if sonraki:
        v["Sonraki Ölçüm Tarihi"] = sonraki
    if acik:
        v["Sapma Açıklaması"] = acik
    stab[key] = mk(P, "Stabilite Çalışmaları", v)
OLCUM = {"MET-25": [("0. Ay", "2026-05-01", "Uygun"), ("1. Ay", "2026-06-01", "Uygun"), ("3. Ay", "2026-08-03", "Uygun")],
         "MET-40": [("0. Ay", "2026-05-01", "Uygun"), ("1. Ay", "2026-06-01", "Uygun"), ("3. Ay", "2026-08-03", "OOT (Trend)")],
         "ROS-25": [("6. Ay", "2026-02-02", "Uygun"), ("9. Ay", "2026-05-04", "Uygun"), ("12. Ay", "2026-08-03", "Uygun")],
         "ROS-40": [("3. Ay", "2025-11-03", "Uygun"), ("6. Ay", "2026-02-02", "Uygun")]}
for key, rows in OLCUM.items():
    for zn, tarih, sonuc in rows:
        mk(P, "Stabilite Ölçümleri", {"Stabilite Çalışması": L(stab[key]), "Zaman Noktası": zn, "Planlanan Tarih": tarih,
                                      "Gerçekleşen Tarih": tarih, "Sonuç": sonuc, "Sorumlu": U,
                                      "Bulgular": "Tüm parametreler spesifikasyon içinde." if sonuc == "Uygun" else "Safsızlıkta artış eğilimi; sapma açıldı."})
mk(P, "Stabilite Ölçümleri", {"Stabilite Çalışması": L(stab["MET-25"]), "Zaman Noktası": "6. Ay", "Planlanan Tarih": "2026-11-01", "Sorumlu": U})
mk(P, "Stabilite Ölçümleri", {"Stabilite Çalışması": L(stab["MET-40"]), "Zaman Noktası": "6. Ay", "Planlanan Tarih": "2026-11-01", "Sorumlu": U})

for baslik, tip, p, durum, son, onc, acik, kok in [
    ("40°C/%75 RH 3. ay siyanoguanidin trendi", "Sapma", "PF-2026-001", "Devam Ediyor", "2026-10-30", "Yüksek", "MET-F04 batch'i hızlandırılmış koşulda OOT.", "Nem geçirgenliği yüksek blister folyosu şüphesi."),
    ("Blister folyosunu Alu-Alu ile değiştirme", "CAPA", "PF-2026-001", "Açık", "2026-11-20", "Yüksek", "OOT sapmasının düzeltici faaliyeti.", ""),
    ("Klavulanat HPLC metodunda pik kuyruklanması", "Görev", "PF-2026-002", "Devam Ediyor", "2026-10-28", "Orta", "Mobil faz pH 4.4 ve 5.0 ile deneme.", ""),
    ("Karbomer tedarikçi CoA eksikliği", "Görev", "PF-2026-003", "Gecikmede", "2026-10-15", "Orta", "KRB-2606-01 lotunun güncel CoA'sı tedarikçiden istenecek.", ""),
    ("Enoksaparin anti-Xa aktivite metodu literatür taraması", "Görev", "PF-2026-004", "Açık", "2026-11-14", "Orta", "Ph. Eur. ve USP monografları karşılaştırılacak.", ""),
    ("CTD Modül 3.2.P.5 taslağı", "Görev", "PF-2025-011", "Devam Ediyor", "2026-11-06", "Yüksek", "Kontrol spesifikasyonları ve validasyon özetleri.", ""),
    ("Pilot batch kayıtlarının arşivlenmesi", "Görev", "PF-2025-011", "Tamamlandı", "2026-09-04", "Düşük", "", ""),
]:
    v = {"Başlık": baslik, "Tip": tip, "Proje": L(prj[p]), "Durum": durum, "Son Tarih": son, "Öncelik": onc,
         "Atanan": U, "Açıklama": acik}
    if kok:
        v["Kök Neden"] = kok
    if durum == "Tamamlandı":
        v["Kapanış Notu"] = "Tamamlandı ve QA'ya teslim edildi."
    mk(P, "Görevler ve Sapmalar", v)

# ── 6. Numuneler, talepler, ek stok hareketleri ──────────────────────────────
log("6) Numuneler, talepler, stok hareketleri")
for ad, tip, mik, br, kosul, bitis, durum, p, d, m, t in [
    ("MET-F04 batch numunesi (stabilite 25/60)", "Üretilen Numune — Deneme Batch'i", 120, "Adet", "Stabilite Kabini 25/60", "2027-11-30", "Saklamada", "PF-2026-001", "MET-F04", None, None),
    ("MET-F04 batch numunesi (stabilite 40/75)", "Üretilen Numune — Deneme Batch'i", 80, "Adet", "Stabilite Kabini 40/75", "2027-05-31", "Analizde", "PF-2026-001", "MET-F04", None, None),
    ("Glucophage XR referans numunesi", "Gelen Numune — Referans Ürün", 60, "Adet", "Oda Sıcaklığı (15-25°C)", "2027-06-30", "Saklamada", "PF-2026-001", None, "REF-001", None),
    ("Amoksisilin trihidrat tedarikçi numunesi", "Gelen Numune — Tedarikçi", 200, "g", "Oda Sıcaklığı (15-25°C)", "2026-10-20", "Karar Bekliyor", "PF-2026-002", None, "API-002", "Aurobindo Pharma"),
    ("ROS-T01 tutma numunesi", "Üretilen Numune — Deneme Batch'i", 60, "Adet", "Oda Sıcaklığı (15-25°C)", "2027-06-30", "Saklamada", "PF-2025-011", "ROS-T01", None, None),
]:
    v = {"Numune Adı": ad, "Tip": tip, "Miktar": mik, "Birim": br, "Saklama Koşulu": kosul, "Lokasyon": "Ar-Ge Numune Odası",
         "Saklama Bitiş Tarihi": bitis, "Durum": durum, "Sorumlu": U, "İlgili Proje": L(prj[p])}
    if d: v["İlgili Deneme"] = L(den[d])
    if m: v["Malzeme"] = L(mal[m])
    if t: v["Tedarikçi"] = L(ted[t])
    nid = mk(S, "Numuneler", v)
    if durum == "Karar Bekliyor":
        mk(S, "Depo Görevleri", {"Başlık": "Numune saklama süresi doldu — imha / uzatma kararı", "Görev Tipi": "Numune İmha / Uzatma Kararı",
                                 "Durum": "Açık", "Atanan": U, "Son Tarih": "2026-10-27", "Numune": L(nid)})
mk(S, "Depo Görevleri", {"Başlık": "Ekim ayı Ar-Ge deposu sayımı", "Görev Tipi": "Sayım", "Durum": "Devam Ediyor", "Atanan": U, "Son Tarih": "2026-10-31"})

mk(S, "Malzeme ve Numune Talepleri", {"Talep Tipi": "Malzeme", "Talep Eden": U, "İstenen Miktar": 0.5, "Gerekçe": "MET-F05 nem bariyeri denemesi",
                                      "İstenen Tarih": "2026-10-12", "Teslim Tarihi": "2026-10-13", "Onaylayıcı (Stok Sorumlusu)": U,
                                      "Durum": "Teslim Edildi", "İlgili Proje": L(prj["PF-2026-001"]), "Malzeme": L(mal["API-001"]), "Lot": L(lot["MET-2604-01"])})
mk(S, "Stok Hareketleri", {"Tarih": "2026-10-13", "Hareket Tipi": "Çıkış", "Çıkış Miktarı": 0.5, "Lot": L(lot["MET-2604-01"]),
                           "İlgili Proje": L(prj["PF-2026-001"]), "Yapan Kişi": U, "Açıklama": "Talep #1 teslimi"})
mk(S, "Malzeme ve Numune Talepleri", {"Talep Tipi": "Numune", "Talep Eden": U, "İstenen Miktar": 6, "Gerekçe": "Karşılaştırmalı çözünürlük testi",
                                      "İstenen Tarih": "2026-10-29", "Durum": "Taslak", "İlgili Proje": L(prj["PF-2026-001"])})
tal_bek = mk(S, "Malzeme ve Numune Talepleri", {"Talep Tipi": "Malzeme", "Talep Eden": U, "İstenen Miktar": 0.2, "Gerekçe": "AMC-S03 denemesi (ksantan %0,8)",
                                                "İstenen Tarih": "2026-10-27", "Onaylayıcı (Stok Sorumlusu)": U, "Durum": "Taslak",
                                                "İlgili Proje": L(prj["PF-2026-002"]), "Malzeme": L(mal["API-002"]), "Lot": L(lot["AMX-2605-01"])})
mk(S, "Stok Hareketleri", {"Tarih": "2026-09-30", "Hareket Tipi": "Sayım Eksiği", "Çıkış Miktarı": 15, "Lot": L(lot["MGS-2604-01"]),
                           "Yapan Kişi": U, "Açıklama": "Eylül sayımı farkı"})
mk(S, "Stok Hareketleri", {"Tarih": "2026-10-08", "Hareket Tipi": "İade", "Giriş Miktarı": 0.2, "Lot": L(lot["MCC-2603-01"]),
                           "Yapan Kişi": U, "Açıklama": "MET-F04 artan malzeme iadesi"})

# ── 7. Toplantılar, kararlar, aksiyonlar ─────────────────────────────────────
log("7) Toplantılar, kararlar, aksiyonlar")
seri = {}
for r in c.get_all_records(T.get_list_id("Toplantı Serileri")):
    seri[r.get(str(T.get_field_id("Toplantı Serileri", "Seri Adı")))] = r["_id"]
weekly = seri.get("Haftalık Ar-Ge Toplantısı")
top = {}
for key, baslik, tip, tarih, projeler, notu in [
    ("w1", "Haftalık Ar-Ge Toplantısı — 05.10.2026", "Haftalık Ar-Ge", "2026-10-05", ["PF-2026-001", "PF-2026-002", "PF-2026-003"], "Portföy gözden geçirildi; MET stabilite OOT sonucu tartışıldı."),
    ("g1", "PF-2026-001 Faz 4 kapısı değerlendirmesi", "Faz Kapısı Değerlendirme", "2026-09-02", ["PF-2026-001"], "Analitik validasyon raporları incelendi; Faz 5'e geçiş önerildi."),
    ("w2", "Haftalık Ar-Ge Toplantısı — 12.10.2026", "Haftalık Ar-Ge", "2026-10-12", ["PF-2026-001", "PF-2026-002", "PF-2026-004"], "Enoksaparin projesi başlatma planı görüşüldü."),
    ("w3", "Haftalık Ar-Ge Toplantısı — 19.10.2026", "Haftalık Ar-Ge", "2026-10-19", ["PF-2026-001", "PF-2026-002", "PF-2025-011"], "Rosuvastatin CTD takvimi ve AMC süspansiyon stabilitesi."),
    ("s1", "Colorcon — nem bariyerli kaplama sunumu", "Tedarikçi", "2026-10-15", ["PF-2026-001"], "Opadry amb II alternatifi değerlendirildi."),
]:
    v = {"Başlık": baslik, "Tip": tip, "Tarih": tarih, "Saat": "10:00", "Süre (dk)": 60, "Yer / Online Link": "Ar-Ge Toplantı Odası / Teams",
         "Organizatör": U, "Katılımcılar": [U], "Durum": "Yapıldı", "Toplantı Notu": notu,
         "AI Özeti": notu, "İlgili Projeler": L(*[prj[p] for p in projeler])}
    if tip == "Haftalık Ar-Ge" and weekly:
        v["Toplantı Serisi"] = L(weekly)
    top[key] = mk(T, "Toplantılar", v)
for key, rows in {"w3": [(1, "Açık aksiyonların gözden geçirilmesi", None), (2, "MET-F04 OOT sapması ve CAPA planı", "PF-2026-001"),
                         (3, "Rosuvastatin CTD Modül 3 takvimi", "PF-2025-011")],
                  "g1": [(1, "Analitik validasyon raporu sunumu", "PF-2026-001"), (2, "Faz 5 stabilite protokolü", "PF-2026-001")]}.items():
    for sira, konu, p in rows:
        v = {"Toplantı": L(top[key]), "Sıra": sira, "Konu": konu, "Sunan Kişi": U, "Ayrılan Süre (dk)": 15, "Kaynak": "Manuel"}
        if p: v["İlgili Proje"] = L(prj[p])
        mk(T, "Gündem Maddeleri", v)

karar = {}
for key, t, metin, tip, p, gate, tarih in [
    ("k1", "g1", "PF-2026-001 için Faz 4 kapısı onaylandı; Faz 5 (stabilite) başlatılacak.", "Faz Kapısı — Geçiş Onayı", "PF-2026-001", ("PF-2026-001", 4), "2026-09-02"),
    ("k2", "w1", "MET-F04 40/75 OOT için sapma açılacak, ambalaj alternatifi değerlendirilecek.", "Genel", "PF-2026-001", None, "2026-10-05"),
    ("k3", "w2", "Enoksaparin projesi için ek 400.000 TL bütçe onaylandı.", "Bütçe", "PF-2026-004", None, "2026-10-12"),
    ("k4", "w3", "Rosuvastatin ruhsat dosyası 27.11.2026'da sunulacak.", "Genel", "PF-2025-011", None, "2026-10-19"),
]:
    v = {"Toplantı": L(top[t]), "Karar Metni": metin, "Karar Tipi": tip, "Karar Veren": U, "Tarih": tarih, "İlgili Proje": L(prj[p])}
    if gate: v["İlgili Faz Kapısı"] = L(kapi[gate])
    karar[key] = mk(T, "Kararlar", v)
for aks, t, k, p, son, onc, durum, kapanis in [
    ("Alu-Alu blister ile 40/75 tekrar stabilite başlat", "w1", "k2", "PF-2026-001", "2026-10-30", "Yüksek", "Devam Ediyor", ""),
    ("Colorcon'dan nem bariyerli kaplama numunesi iste", "s1", None, "PF-2026-001", "2026-10-22", "Orta", "Tamamlandı", "Numune 21.10.2026'da teslim alındı."),
    ("Enoksaparin anti-Xa referans standardını sipariş et", "w2", "k3", "PF-2026-004", "2026-10-20", "Yüksek", "Gecikmede", ""),
    ("Klavulanat HPLC metodu için ikinci kolon dene", "w2", None, "PF-2026-002", "2026-10-28", "Orta", "Açık", ""),
    ("CTD Modül 3.2.P taslağını QA'ya gönder", "w3", "k4", "PF-2025-011", "2026-11-06", "Yüksek", "Açık", ""),
    ("Karbomer tedarikçisinden güncel CoA al", "w3", None, "PF-2026-003", "2026-10-26", "Düşük", "Açık", ""),
]:
    v = {"Aksiyon": aks, "Toplantı": L(top[t]), "İlgili Proje": L(prj[p]), "Sorumlu": U, "Son Tarih": son, "Öncelik": onc, "Durum": durum}
    if k: v["Karar"] = L(karar[k])
    if kapanis: v["Kapanış Notu"] = kapanis
    mk(T, "Aksiyonlar", v)

# gelecek haftanın toplantısı: açık aksiyonlar otomatik gündeme gelir
mk(T, "Toplantılar", {"Başlık": "Haftalık Ar-Ge Toplantısı — 26.10.2026", "Tip": "Haftalık Ar-Ge", "Tarih": "2026-10-26", "Saat": "10:00",
                      "Süre (dk)": 60, "Yer / Online Link": "Ar-Ge Toplantı Odası / Teams", "Organizatör": U, "Katılımcılar": [U],
                      "Durum": "Planlandı", "İlgili Projeler": L(prj["PF-2026-001"], prj["PF-2026-002"], prj["PF-2026-003"], prj["PF-2026-004"], prj["PF-2025-011"]),
                      **({"Toplantı Serisi": L(weekly)} if weekly else {})})

# ── 8. Canlı onay akışları: bekleyen iki onay isteği ─────────────────────────
log("8) Bekleyen onay istekleri oluşturuluyor")
time.sleep(10)
upd(P, "Faz Kapıları", kapi[("PF-2026-002", 3)], {"Durum": "Direktör Onayı Bekliyor"})
upd(S, "Malzeme ve Numune Talepleri", tal_bek, {"Durum": "Onay Bekliyor"})

json.dump(created, open("sample_data_created.json", "w"))
log(f"Bitti: {len(created)} kayıt oluşturuldu (otomasyonların ürettikleri hariç).")
