"""
Farmatek Ar-Ge — görev kütüphanesi kaynak verisi.

Kaynak: "Calcium Carbonate Tablet Proje Takip Çizelgesi.xlsx" (sayfa: Yeni Ürün).
- 1–26: süre ve öncül Excel'den birebir alındı ("18.9" → 18 ve 9 olarak yorumlandı).
- 27–38: Excel'de No / süre / öncül yok → hedef tarihlerden VARSAYIM olarak türetildi
  (VARSAYIM=True). Müşteriyle teyit edilecek.
- Süre birimi takvim günü: 1 hafta=7, 15 gün=15, 1 ay=30, 2 ay=60, 4 ay=120.
- "Alternatif Kaynak" şablonu = Yeni Ürün − {4 DMF temini, 11 Referans ürün temini}
  (Excel'in 2. sayfasında bu iki satır yok).

`hesapla()` ileri geçiş (CPM, FS bağımlılık) ile her kalemin proje başlangıcına göre
başlangıç/bitiş ofsetini (gün) hesaplar. Kütüphanedeki tarihler bu ofsetlerin
REFERANS_TARIH'e eklenmesiyle yazılır.
"""
from datetime import date, timedelta

REFERANS_TARIH = date(2026, 1, 1)   # Kütüphane Gantt'ında "Gün 0"

DEPARTMANLAR = ["Proje Yönetimi", "Formülasyon Geliştirme", "Analitik Metot Geliştirme",
                "Ruhsat", "Kalite Güvence"]

# (kod, ad, sıra)
FAZLAR = [
    ("F1", "Proje Başlangıç",      1),
    ("F2", "Proje Değerlendirme",  2),
    ("F3", "Proje Geliştirme",     3),
    ("F4", "Validasyon",           4),
    ("F5", "Dosya Başvurusu",      5),
    ("F6", "Ruhsat Alımı",         6),
]

PM, FOR, ANA, RUH = DEPARTMANLAR[:4]

# no, faz, ad, süre(gün), öncüller, departman, kilometre_taşı, onay_gerekli, varsayım
GOREVLER = [
    (1,  "F1", "Proje Başlangıcı",                                     0,   [],            PM,  True,  False, False),
    (2,  "F1", "Proje Duyurusunun Yapılması",                          1,   [1],           PM,  False, False, False),
    (3,  "F2", "API Kaynağı Belirlenmesi",                             30,  [2],           FOR, False, True,  False),
    (4,  "F2", "DMF Temini ya da Teknik Paket Temini",                 7,   [2],           FOR, False, False, False),
    (5,  "F2", "Referans Ürün Seçimi (TR&EU Uyumluluğu)",              7,   [2],           FOR, False, True,  False),
    (6,  "F2", "Patent Değerlendirmesi",                               7,   [2],           FOR, False, False, False),
    (7,  "F2", "EP/USP/BP Monograf Değerlendirilmesi",                 7,   [2],           ANA, False, False, False),
    (8,  "F2", "Analitik Metot Gereksinimlerinin Belirlenmesi",        7,   [2],           ANA, False, False, False),
    (9,  "F3", "Seçilen API'nin Temini",                               60,  [3],           FOR, False, False, False),
    (10, "F3", "Analitik Gereksinimlerin Temini",                      60,  [3],           ANA, False, False, False),
    (11, "F3", "Referans Ürün TR/EU Temini, Sayısı ve SKT Değerlendirmesi", 7, [2],        FOR, False, False, False),
    (12, "F3", "Yardımcı Maddelerin Temini",                           60,  [3],           FOR, False, False, False),
    (13, "F3", "Gerekli Olması Durumunda Zımba Temini",                60,  [3],           FOR, False, False, False),
    (14, "F3", "Primer & Sekonder Ambalaj Malzemelerinin Temini",      60,  [3],           FOR, False, False, False),
    (15, "F3", "Geçimlilik Çalışması",                                 60,  [9],           ANA, False, False, False),
    (16, "F3", "Solubility Çalışması",                                 15,  [9],           ANA, False, False, False),
    (17, "F3", "Stress Çalışması",                                     15,  [9, 16],       ANA, False, False, False),
    (18, "F3", "Formülasyon Geliştirme Çalışmaları",                   60,  [9],           FOR, False, True,  False),
    (19, "F3", "Analitik Metotların Geliştirilmesi",                   30,  [18, 9],       ANA, False, True,  False),
    (20, "F3", "Stabilite Çalışmaları",                                30,  [18],          ANA, False, False, False),
    (21, "F4", "Scale Up Üretiminin Yapılması",                        15,  [20],          FOR, False, False, False),
    (22, "F4", "Proses Validasyonu Üretimi",                           30,  [21],          FOR, False, True,  False),
    (23, "F4", "Bitmiş Ürün Analitik Metotların Validasyonu ve Transferi", 30, [18],       ANA, False, True,  False),
    (24, "F4", "Hammadde Verifikasyonları ve Transferi",               30,  [9, 18],       ANA, False, False, False),
    (25, "F4", "PV Serilerine Ait Stabilite Başlangıcı",               30,  [22],          ANA, False, False, False),
    (26, "F4", "BE Çalışması (Pilot & Pivotal)",                       120, [25],          ANA, False, False, False),
    (27, "F5", "TR&EU Dosya Hazırlığı",                                60,  [23, 24],      FOR, False, True,  True),
    (28, "F5", "PV Stabilite 3 & 6 Ay Çalışmalarının Yapılması",       180, [25],          ANA, False, False, True),
    (29, "F5", "Ruhsat Departmanı ile Başvuru Dosyasının Paylaşılması ve Kontrolü", 15, [27], RUH, False, False, True),
    (30, "F5", "BE Sonucunun Alınması",                                0,   [26],          PM,  True,  False, True),
    (31, "F5", "Dosya Başvurusunun Yapılması",                         0,   [28, 29, 30],  RUH, True,  True,  True),
    (32, "F6", "Bakanlık İncelemesi ve Eksiklik Yazılarının Alınması", 90,  [31],          RUH, False, False, True),
    (33, "F6", "Teknik Komisyon Onayı",                                270, [32],          RUH, False, False, True),
    (34, "F6", "BE/BY Komisyon Onayı",                                 270, [32],          RUH, False, False, True),
    (35, "F6", "KUB/KT Komisyon Onayı",                                180, [33],          RUH, False, False, True),
    (36, "F6", "Raf Ömrü Onayı",                                       270, [32],          RUH, False, False, True),
    (37, "F6", "Ruhsatın Alınması",                                         0,   [33, 34, 35, 36], RUH, True, False, True),
    (38, "F6", "Geri Ödeme Alımı Başvurusu",                           30,  [37],          RUH, False, False, True),
]

SABLONLAR = {
    "Yeni Ürün":         [g[0] for g in GOREVLER],
    "Alternatif Kaynak": [g[0] for g in GOREVLER if g[0] not in (4, 11)],
}


def hesapla(nolar):
    """FS ileri geçiş. {no: (es, ef)} gün ofsetleri döner (Gün 0 = proje başlangıcı)."""
    by_no = {g[0]: g for g in GOREVLER}
    es, ef = {}, {}
    for no in sorted(nolar):                      # numaralar topolojik sırada
        g = by_no[no]
        preds = [p for p in g[4] if p in nolar]
        es[no] = max((ef[p] for p in preds), default=0)
        ef[no] = es[no] + g[3]
    return {n: (es[n], ef[n]) for n in nolar}


def faz_araliklari(nolar, ofset):
    out = {}
    for kod, *_ in FAZLAR:
        ns = [g[0] for g in GOREVLER if g[1] == kod and g[0] in nolar]
        if ns:
            out[kod] = (min(ofset[n][0] for n in ns), max(ofset[n][1] for n in ns))
    return out


def tarih(gun):
    return (REFERANS_TARIH + timedelta(days=gun)).isoformat()


if __name__ == "__main__":
    for ad, nolar in SABLONLAR.items():
        o = hesapla(nolar)
        print(f"\n== {ad}: {len(nolar)} görev, toplam süre {max(v[1] for v in o.values())} gün")
        for kod, (s, e) in faz_araliklari(nolar, o).items():
            print(f"  {kod} gün {s:>4}–{e:<4}")
        for g in GOREVLER:
            if g[0] in nolar:
                s, e = o[g[0]]
                print(f"  {g[0]:>2} {g[2][:55]:<55} {s:>4}→{e:<4} {tarih(s)} öncül={g[4]}")


# ════════════════════════════════════════════════════════════════════════════
# Model 2 — fazlar ve kilometre taşları ayrı listelerde, görevlerde yalnızca görev
# (alt görev yok). Excel'deki 0 günlük kilometre taşı satırları (1, 30, 31, 37)
# KT listesine taşınır; onlara bağlı görevlerin öncülleri KT'nin kendi öncüllerine
# yönlendirilir, böylece plan tarihleri değişmez.
# ════════════════════════════════════════════════════════════════════════════
KT_NOLAR = {1, 30, 31, 37}

# kod, ad, faz, bağlı görevler (tamamlanınca KT'ye ulaşılır), kritik
KILOMETRE_TASLARI = [
    ("KT1", "Proje Başlatıldı",              "F1", [2],              True),
    ("KT2", "BE Sonucu Alındı",              "F5", [26],             True),
    ("KT3", "Dosya Başvurusu Yapıldı",       "F5", [26, 28, 29],     True),
    ("KT4", "Ruhsat Alındı",                 "F6", [33, 34, 35, 36], True),
]


def _cozulmus_onculler(no, by_no):
    """KT satırlarını atlayarak gerçek görev öncüllerini döndürür."""
    out = []
    for p in by_no[no][4]:
        if p in KT_NOLAR:
            out += _cozulmus_onculler(p, by_no)
        else:
            out.append(p)
    return sorted(set(out))


def model2():
    """{'gorevler': [...], 'fazlar': [...], 'kt': [...], 'sablonlar': {...}} — gün ofsetleri dahil."""
    by_no = {g[0]: g for g in GOREVLER}
    gorevler = []
    for no, faz, ad, sure, onc, dep, kt, onay, vars_ in GOREVLER:
        if no in KT_NOLAR:
            continue
        gorevler.append({"no": no, "faz": faz, "ad": ad, "sure": sure, "onc": _cozulmus_onculler(no, by_no),
                         "dep": dep, "onay": onay, "vars": vars_})
    gno = {g["no"]: g for g in gorevler}
    es, ef = {}, {}
    for g in sorted(gorevler, key=lambda x: x["no"]):
        es[g["no"]] = max((ef[p] for p in g["onc"]), default=0)
        ef[g["no"]] = es[g["no"]] + g["sure"]
    for g in gorevler:
        g["s"], g["e"] = es[g["no"]], ef[g["no"]]
    fazlar = []
    for kod, ad, sira in FAZLAR:
        ns = [g for g in gorevler if g["faz"] == kod]
        fazlar.append({"kod": kod, "ad": ad, "sira": sira, "s": min(g["s"] for g in ns), "e": max(g["e"] for g in ns)})
    kts = [{"kod": k, "ad": a, "faz": f, "bagli": b, "kritik": kr, "gun": max(ef[n] for n in b)}
           for k, a, f, b, kr in KILOMETRE_TASLARI]
    sablonlar = {s: [n for n in nolar if n not in KT_NOLAR] for s, nolar in SABLONLAR.items()}
    return {"gorevler": gorevler, "fazlar": fazlar, "kt": kts, "sablonlar": sablonlar}


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "model2":
    m = model2()
    print(len(m["gorevler"]), "görev; toplam", max(g["e"] for g in m["gorevler"]), "gün")
    for f in m["fazlar"]: print(" ", f)
    for k in m["kt"]: print(" ", k)
    for g in m["gorevler"]:
        if g["no"] in (2, 3, 32, 38): print(" ", g)
