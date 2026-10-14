"""
Kırpart Tedarikçi Portalı — Workiom spec
Kaynak: Tedarikçi Portalı rev1 isterler dokümanı + Workiom Veri Modeli (26 liste, 5 grup)

Kurulum:
  python main.py build apps/kirpart_tedarikci_portali.py
  python apps/upgrade_kirpart_tedarikci_portali_computed.py   # formül, rollup, sayaç + bunlara bağlı otomasyon/raporlar
  python main.py seed  apps/kirpart_tedarikci_portali.py      # Denetim Tipleri, PPAP Belge Tipleri, Denetim Soruları
"""
from workiom.constants import F, LT, V

# ─── Renkler ───────────────────────────────────────────────────────────────────
GREEN, YELLOW, RED, BLUE, ORANGE, PINK, LBLUE, TEAL, PURPLE = (
    "#5bd77e", "#f5c044", "#ea346f", "#4e86f7", "#ffa979", "#ff86c7", "#8ed6ff", "#5bd7d0", "#7942e3")


def opts(*pairs):
    """opts(("Aktif", GREEN), ...) → SELECT options"""
    return [{"label": l, "color": c} for l, c in pairs]


def sel(name, *pairs):
    return {"name": name, "type": F.SELECT, "options": opts(*pairs)}


def msel(name, *pairs):
    return {"name": name, "type": F.MULTISELECT, "options": opts(*pairs)}


def txt(name, required=False):
    return {"name": name, "type": F.TEXT, "required": required}


def pk(name):
    """Listenin birincil (başlık) alanı — bağlantılarda bu değer görünür"""
    return {"name": name, "type": F.TEXT, "primary": True}


def ml(name):
    return {"name": name, "type": F.TEXT, "multiline": True}


def num(name):
    return {"name": name, "type": F.NUMBER}


def date(name):
    return {"name": name, "type": F.DATE}


def cur(name):
    return {"name": name, "type": F.CURRENCY}


def boolf(name):
    return {"name": name, "type": F.BOOLEAN}


def filef(name):
    return {"name": name, "type": F.FILE}


def user(name):
    return {"name": name, "type": F.USER}


def link(name, target, multiple=False):
    return {"name": name, "type": F.LINK, "target_list": target, "multiple": multiple}


def lk(name, via, field):
    return {"name": name, "type": F.LOOKUP, "via": via, "lookup_field": field}


def tab(name, *groups, columns=1):
    return {"name": name, "columns": columns,
            "groups": [{"name": g[0], "fields": g[1], "col": g[2] if len(g) > 2 else 1} for g in groups]}


PARA = (("TRY", BLUE), ("EUR", PURPLE), ("USD", GREEN))

# Tedarikçi kartından taşınan bildirim alıcıları (lookup) — otomasyonlar bunları kullanır
TED_LOOKUPS = {
    "satinalma": lk("Satınalma Sorumlusu", "Tedarikçi", "Satınalma Sorumlusu (Kırpart)"),
    "kalite":    lk("Kalite Sorumlusu", "Tedarikçi", "Kalite Sorumlusu (Kırpart)"),
    "lojistik":  lk("Lojistik Sorumlusu", "Tedarikçi", "Lojistik Sorumlusu (Kırpart)"),
    "finans":    lk("Finans Sorumlusu", "Tedarikçi", "Finans Sorumlusu (Kırpart)"),
    "portal":    lk("Portal Kullanıcıları", "Tedarikçi", "Tedarikçi Portal Kullanıcıları"),
    "kod":       lk("Tedarikçi Kodu", "Tedarikçi", "Tedarikçi Kodu"),
}


def T(*keys):
    return [TED_LOOKUPS[k] for k in keys]


# ═══════════════════════════════════════════════════════════════════════════════
#  A. ANA VERİ
# ═══════════════════════════════════════════════════════════════════════════════
TEDARIKCILER = {
    "name": "Tedarikçiler",
    "icon": "fas fa-industry",
    "fields": [
        pk("Tedarikçi Adı"),
        txt("Tedarikçi Kodu", True),
        txt("Kısa Ad"),
        sel("Durum", ("Aktif", GREEN), ("Aday", LBLUE), ("Pasif", ORANGE), ("Bloke", RED)),
        sel("Ülke", ("Türkiye", RED), ("Almanya", YELLOW), ("İtalya", GREEN), ("Çin", ORANGE), ("Diğer", LBLUE)),
        txt("Şehir"),
        ml("Adres"),
        msel("Ürün Çeşit Kodu", ("Plastik Hammadde", BLUE), ("Plastik Enjeksiyon", TEAL), ("Metal İşleme", PURPLE),
             ("Kauçuk", ORANGE), ("Elektronik", YELLOW), ("Ambalaj", LBLUE), ("Kimyasal", PINK)),
        msel("Üretim Yöntemi", ("Enjeksiyon", TEAL), ("Pres", BLUE), ("Talaşlı İmalat", PURPLE), ("Döküm", ORANGE),
             ("Montaj", GREEN), ("Boya-Kaplama", PINK)),
        sel("Fiyat Segmenti", ("Düşük", GREEN), ("Orta", YELLOW), ("Yüksek", RED)),
        txt("Vergi Dairesi"),
        txt("Vergi No"),
        num("Ödeme Vadesi (gün)"),
        sel("Para Birimi", *PARA),
        ml("Genel Kapasite Açıklaması"),
        user("Satınalma Sorumlusu (Kırpart)"),
        user("Kalite Sorumlusu (Kırpart)"),
        user("Lojistik Sorumlusu (Kırpart)"),
        user("Finans Sorumlusu (Kırpart)"),
        {"name": "Tedarikçi Portal Kullanıcıları", "type": F.MULTIUSER},
        cur("Son Yıl Ciro"),
        cur("Son Yıl Net Kâr"),
        cur("Kredi Limiti / Risk"),
        txt("Finansal Veri Yılı"),
        num("PPM Hedefi"),
        num("Zamanında Teslim Hedefi %"),
        num("Vaka Sayısı Hedefi (dönem)"),
        num("8D Kapanış Hedefi (gün)"),
        num("Min. Denetim Puanı %"),
        date("Son Denetim Tarihi"),
        num("Güncel Performans Puanı"),
        sel("Performans Sınıfı", ("A", GREEN), ("B", YELLOW), ("C", RED)),
    ],
    "views": [
        {"name": "Tüm Tedarikçiler", "type": V.GRID},
        {"name": "Aktif Tedarikçiler", "type": V.GRID, "filter": {"field": "Durum", "value": "Aktif"}},
        {"name": "Lokasyona Göre", "type": V.KANBAN, "group_by": "Ülke"},
        {"name": "Performans Sınıfına Göre", "type": V.KANBAN, "group_by": "Performans Sınıfı"},
        {"name": "Fiyat Segmentine Göre", "type": V.KANBAN, "group_by": "Fiyat Segmenti"},
        {"name": "Duruma Göre", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "Tedarikçi Kartları", "type": V.GALLERY},
    ],
    "layout": {
        "name": "Tedarikçi Bilgi Ekranı", "default": True,
        "tabs": [
            tab("Genel Bilgiler",
                ("Kimlik", ["Tedarikçi Kodu", "Tedarikçi Adı", "Kısa Ad", "Durum"], 1),
                ("Lokasyon", ["Ülke", "Şehir", "Adres"], 2),
                ("Gruplama", ["Ürün Çeşit Kodu", "Üretim Yöntemi", "Fiyat Segmenti", "Performans Sınıfı"], 1),
                ("Kapasite", ["Genel Kapasite Açıklaması"], 2), columns=2),
            tab("Cari & Finans",
                ("Cari Bilgiler", ["Vergi Dairesi", "Vergi No", "Ödeme Vadesi (gün)", "Para Birimi"], 1),
                ("Finansal Özet", ["Finansal Veri Yılı", "Son Yıl Ciro", "Son Yıl Net Kâr", "Kredi Limiti / Risk"], 2),
                columns=2),
            tab("Sorumlular & Portal",
                ("Kırpart Sorumluları", ["Satınalma Sorumlusu (Kırpart)", "Kalite Sorumlusu (Kırpart)",
                                         "Lojistik Sorumlusu (Kırpart)", "Finans Sorumlusu (Kırpart)"], 1),
                ("Portal", ["Tedarikçi Portal Kullanıcıları"], 2), columns=2),
            tab("KPI Hedefleri & Performans",
                ("Hedefler", ["PPM Hedefi", "Zamanında Teslim Hedefi %", "Vaka Sayısı Hedefi (dönem)",
                              "8D Kapanış Hedefi (gün)", "Min. Denetim Puanı %"], 1),
                ("Güncel Durum", ["Güncel Performans Puanı", "Performans Sınıfı", "Son Denetim Tarihi"], 2),
                columns=2),
        ],
    },
}

KONTAKLAR = {
    "name": "Kontaklar & Portal Kullanıcıları",
    "icon": "fas fa-address-book",
    "fields": [
        pk("Ad Soyad"),
        txt("Unvan"),
        {"name": "E-posta", "type": F.EMAIL},
        {"name": "Telefon", "type": F.PHONE},
        sel("Dil", ("TR", RED), ("EN", BLUE)),
        msel("Departman Yetkisi", ("Kalite", PURPLE), ("Lojistik", TEAL), ("Satınalma", BLUE), ("Finans", GREEN)),
        boolf("Master Kullanıcı"),
        boolf("Otomatik E-posta Listesinde"),
        msel("Bildirim Konuları", ("Sipariş", BLUE), ("Sevkiyat", TEAL), ("8D", RED), ("PPAP", PURPLE),
             ("Sertifika", YELLOW), ("Denetim", ORANGE), ("Maliyet", PINK), ("Mutabakat", GREEN)),
        sel("Kırpart Onay Durumu", ("Talep Edildi", YELLOW), ("Onaylandı", GREEN), ("Reddedildi", RED)),
        user("Workiom Kullanıcısı"),
        boolf("Aktif"),
        link("Tedarikçi", "Tedarikçiler"),
        *T("satinalma"),
    ],
    "views": [
        {"name": "Tüm Kontaklar", "type": V.GRID},
        {"name": "Kırpart Onayı Bekleyenler", "type": V.GRID,
         "filter": {"field": "Kırpart Onay Durumu", "value": "Talep Edildi"}},
        {"name": "Onay Durumuna Göre", "type": V.KANBAN, "group_by": "Kırpart Onay Durumu"},
        {"name": "Dile Göre", "type": V.KANBAN, "group_by": "Dil"},
    ],
    "forms": [{
        "name": "Kontak Ekleme / Değişiklik Talebi", "private": True,
        "description": "Tedarikçi master kullanıcısı yeni kişi ekler; kayıt Kırpart onayına düşer.",
        "fields": ["Tedarikçi", "Ad Soyad", "Unvan", "E-posta", "Telefon", "Dil", "Departman Yetkisi",
                   "Otomatik E-posta Listesinde", "Bildirim Konuları", "Aktif"],
        "required_fields": {"Tedarikçi": True, "Ad Soyad": True, "E-posta": True},
        "end_message": "Talebiniz Kırpart onayına iletildi.",
    }],
}

MALZEMELER = {
    "name": "Malzemeler",
    "icon": "fas fa-cubes",
    "fields": [
        pk("Malzeme Kodu"),
        txt("Malzeme Adı", True),
        txt("Malzeme Adı (EN)"),
        sel("Malzeme Tipi", ("Hammadde", BLUE), ("Parça", TEAL), ("Yarı Mamul", PURPLE), ("Kasa-Ambalaj", ORANGE)),
        sel("Birim", ("Adet", BLUE), ("Kg", GREEN), ("Metre", YELLOW), ("Litre", LBLUE)),
        txt("Çizim No"),
        txt("Revizyon"),
        txt("PLM Kodu"),
        txt("Proje / Müşteri"),
        boolf("Aktif"),
    ],
    "views": [
        {"name": "Tüm Malzemeler", "type": V.GRID},
        {"name": "Tipe Göre", "type": V.KANBAN, "group_by": "Malzeme Tipi"},
        {"name": "Kasa & Ambalaj", "type": V.GRID, "filter": {"field": "Malzeme Tipi", "value": "Kasa-Ambalaj"}},
    ],
}

TM_KARTLARI = {
    "name": "Tedarikçi–Malzeme Kartları",
    "icon": "fas fa-boxes",
    "fields": [
        pk("Kart Adı"),
        {"name": "Kart No", "type": F.AUTONUMBER},
        boolf("Ana Tedarikçi"),
        num("Haftalık Kapasite"),
        num("Lead Time (gün)"),
        num("Kutu İçi Adet"),
        num("Birim Ağırlık (kg)"),
        num("Kutu Dara (kg)"),
        ml("Paketleme Açıklaması"),
        date("Son Güncelleme"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Malzeme", "Malzemeler"),
        link("Kutu / Kasa", "Malzemeler"),
        lk("Malzeme Adı", "Malzeme", "Malzeme Adı"),
    ],
    "views": [
        {"name": "Tüm Kartlar", "type": V.GRID},
        {"name": "Ana Kaynaklar", "type": V.GRID, "filter": {"field": "Ana Tedarikçi", "value": True}},
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
#  B. SİPARİŞ & LOJİSTİK
# ═══════════════════════════════════════════════════════════════════════════════
SIPARISLER = {
    "name": "Siparişler",
    "icon": "fas fa-file-invoice",
    "fields": [
        pk("Sipariş No"),
        txt("Yayın No"),
        date("Sipariş Tarihi"),
        sel("Durum", ("Açık", LBLUE), ("Teyit Bekliyor", YELLOW), ("Kısmi Teyit", ORANGE),
            ("Teyit Edildi", GREEN), ("Kapandı", TEAL), ("İptal", PINK)),
        ml("Kırpart Notu"),
        link("Tedarikçi", "Tedarikçiler"),
        *T("kod", "satinalma", "portal"),
    ],
    "views": [
        {"name": "Tüm Siparişler", "type": V.GRID},
        {"name": "Sipariş Durumu", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "Teyit Bekleyen Siparişler", "type": V.GRID,
         "filter": {"field": "Durum", "value": ["Teyit Bekliyor", "Kısmi Teyit"]}},
        {"name": "Sipariş Takvimi", "type": V.CALENDAR, "date_field": "Sipariş Tarihi"},
    ],
}

SIPARIS_KALEMLERI = {
    "name": "Sipariş Kalemleri",
    "icon": "fas fa-list-ol",
    "fields": [
        pk("Kalem Kodu"),
        num("Satır No"),
        date("İstenen Teslim Tarihi"),
        num("Sipariş Miktarı"),
        txt("Son Teslim Alınan İrsaliye No"),
        date("Son Teslim Alma Tarihi"),
        sel("Teyit Durumu", ("Bekliyor", YELLOW), ("Onaylandı", GREEN), ("Kısmi Onay", ORANGE), ("Reddedildi", RED)),
        num("Teyit Edilen Miktar"),
        date("Teyit Edilen Tarih"),
        sel("Mevcut Kapasite Yeterli mi?", ("Evet", GREEN), ("Hayır", RED)),
        ml("Neye İhtiyacın Var?"),
        {**sel("Red Gerekçesi", ("Kapasite Yetersiz", RED), ("Hammadde Yok", ORANGE), ("Termin Uygun Değil", YELLOW),
               ("Fiyat", PURPLE), ("Diğer", LBLUE)),
         "required_when": "{{Teyit Durumu}} = 'Reddedildi'"},
        ml("Red Açıklaması"),
        date("Teyit Zamanı"),
        num("Teyit Bekliyor (1/0)"),
        link("Sipariş", "Siparişler"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Malzeme", "Malzemeler"),
        lk("Sipariş No", "Sipariş", "Sipariş No"),
        lk("Yayın No", "Sipariş", "Yayın No"),
        lk("Malzeme Adı", "Malzeme", "Malzeme Adı"),
        *T("satinalma", "portal"),
    ],
    "views": [
        {"name": "Tüm Sipariş Kalemleri", "type": V.GRID},
        {"name": "Sipariş Formu", "type": V.GRID},
        {"name": "Teyit Bekleyenler", "type": V.GRID, "filter": {"field": "Teyit Durumu", "value": "Bekliyor"}},
        {"name": "Teyit Panosu", "type": V.KANBAN, "group_by": "Teyit Durumu"},
        {"name": "Kapasite Sorunu Bildirilenler", "type": V.GRID,
         "filter": {"field": "Mevcut Kapasite Yeterli mi?", "value": "Hayır"}},
        {"name": "Teslim Takvimi (Tarih Aralığı)", "type": V.CALENDAR, "date_field": "İstenen Teslim Tarihi"},
    ],
    "layout": {
        "name": "Sipariş Kalemi", "default": True,
        "tabs": [
            tab("Sipariş Formu",
                ("Sipariş", ["Kalem Kodu", "Sipariş", "Sipariş No", "Yayın No", "Satır No", "Tedarikçi",
                             "Malzeme", "Malzeme Adı"], 1),
                ("Miktar & Termin", ["Sipariş Miktarı", "İstenen Teslim Tarihi", "Son Teslim Alma Tarihi",
                                     "Son Teslim Alınan İrsaliye No"], 2), columns=2),
            tab("Teyit & Kapasite",
                ("Teyit", ["Teyit Durumu", "Teyit Edilen Miktar", "Teyit Edilen Tarih", "Teyit Zamanı"], 1),
                ("Kapasite Sorgusu", ["Mevcut Kapasite Yeterli mi?", "Neye İhtiyacın Var?",
                                      "Red Gerekçesi", "Red Açıklaması"], 2), columns=2),
        ],
    },
}

SEVKIYATLAR = {
    "name": "Sevkiyatlar",
    "icon": "fas fa-truck",
    "fields": [
        {"name": "ASN No", "type": F.AUTONUMBER},
        pk("İrsaliye No"),
        sel("Durum", ("Planlandı", LBLUE), ("Yolda", YELLOW), ("Teslim Alındı", GREEN), ("Kısmi Kabul", ORANGE),
            ("İptal", PINK)),
        date("Planlanan Sevk Tarihi"),
        date("Gerçek Sevk Tarihi"),
        date("Tahmini Varış"),
        date("Teslim Alma Tarihi"),
        txt("Taşıyıcı Firma"),
        txt("Araç Plakası"),
        filef("İrsaliye Dosyası"),
        filef("Etiket / Sevkiyat Raporu"),
        boolf("Etiketleme Uygun"),
        boolf("Ambalaj Uygun"),
        ml("Kabul Notu"),
        link("Tedarikçi", "Tedarikçiler"),
        *T("lojistik", "portal"),
    ],
    "views": [
        {"name": "Tüm Sevkiyatlar", "type": V.GRID},
        {"name": "Sevkiyat Durumu", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "Yoldaki Mallar (ASN)", "type": V.GRID, "filter": {"field": "Durum", "value": "Yolda"}},
        {"name": "Günlük Sevkiyat Planı", "type": V.CALENDAR, "date_field": "Planlanan Sevk Tarihi"},
        {"name": "Planlanan Sevkiyatlar", "type": V.GRID, "filter": {"field": "Durum", "value": "Planlandı"}},
        {"name": "Varış Takvimi", "type": V.CALENDAR, "date_field": "Tahmini Varış"},
    ],
    "forms": [{
        "name": "ASN / Sevkiyat Bildirimi", "private": True,
        "description": "Günlük sevkiyat planı ve yoldaki malzeme bildirimi; irsaliye dosyasını ekleyin.",
        "fields": ["Tedarikçi", "İrsaliye No", "Durum", "Planlanan Sevk Tarihi", "Gerçek Sevk Tarihi",
                   "Tahmini Varış", "Taşıyıcı Firma", "Araç Plakası", "İrsaliye Dosyası", "Etiket / Sevkiyat Raporu"],
        "required_fields": {"Tedarikçi": True, "İrsaliye No": True, "Planlanan Sevk Tarihi": True},
        "end_message": "ASN kaydınız alındı. Sevkiyat kalemlerini sevkiyat kaydına ekleyin.",
    }],
}

SEVKIYAT_KALEMLERI = {
    "name": "Sevkiyat Kalemleri",
    "icon": "fas fa-dolly",
    "fields": [
        pk("Lot No"),
        {"name": "Kalem No", "type": F.AUTONUMBER},
        num("Sevk Edilen Miktar"),
        num("Kabul Edilen Miktar"),
        num("Kutu Adedi"),
        link("Sevkiyat", "Sevkiyatlar"),
        link("Sipariş Kalemi", "Sipariş Kalemleri"),
        link("Tedarikçi", "Tedarikçiler"),
        lk("ASN No", "Sevkiyat", "ASN No"),
        lk("İrsaliye No", "Sevkiyat", "İrsaliye No"),
        lk("Sevkiyat Durumu", "Sevkiyat", "Durum"),
        lk("Teslim Alma Tarihi", "Sevkiyat", "Teslim Alma Tarihi"),
        lk("Sipariş Kalem Kodu", "Sipariş Kalemi", "Kalem Kodu"),
        lk("İstenen Teslim Tarihi", "Sipariş Kalemi", "İstenen Teslim Tarihi"),
    ],
    "views": [
        {"name": "Tüm Sevkiyat Kalemleri", "type": V.GRID},
        {"name": "İrsaliye Bazlı Sipariş Tarihçesi", "type": V.GRID},
    ],
}

ENVANTER = {
    "name": "Envanter Bildirimleri",
    "icon": "fas fa-warehouse",
    "fields": [
        pk("Özet"),
        {"name": "Bildirim No", "type": F.AUTONUMBER},
        num("Mevcut Miktar"),
        date("Bildirim Tarihi"),
        ml("Not"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Malzeme", "Malzemeler"),
        lk("Envanter Tipi", "Malzeme", "Malzeme Tipi"),
    ],
    "views": [
        {"name": "Tüm Envanter Bildirimleri", "type": V.GRID},
        {"name": "Bildirim Takvimi", "type": V.CALENDAR, "date_field": "Bildirim Tarihi"},
    ],
    "forms": [{
        "name": "Envanter Bildirimi", "private": True,
        "description": "Elinizdeki kasa, hammadde ve parça stoğunu paylaşın.",
        "fields": ["Tedarikçi", "Malzeme", "Mevcut Miktar", "Bildirim Tarihi", "Not"],
        "required_fields": {"Tedarikçi": True, "Malzeme": True, "Mevcut Miktar": True},
    }],
}

CARI = {
    "name": "Cari Mutabakatlar",
    "icon": "fas fa-balance-scale",
    "fields": [
        pk("Mutabakat Dönemi"),
        {"name": "Mutabakat No", "type": F.AUTONUMBER},
        date("Dönem Sonu"),
        sel("Para Birimi", *PARA),
        cur("Kırpart Bakiyesi"),
        cur("Tedarikçi Bakiyesi"),
        sel("Durum", ("Gönderildi", BLUE), ("Mutabık", GREEN), ("Mutabık Değil", RED), ("Çözüldü", TEAL)),
        {**ml("Fark Açıklaması"), "required_when": "{{Durum}} = 'Mutabık Değil'"},
        filef("Kırpart Ekstresi"),
        filef("Tedarikçi Ekstresi"),
        date("Yanıt Tarihi"),
        user("Finans Sorumlusu (Kırpart)"),
        link("Tedarikçi", "Tedarikçiler"),
        *T("portal"),
    ],
    "views": [
        {"name": "Tüm Mutabakatlar", "type": V.GRID},
        {"name": "Mutabakat Durumu", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "Mutabık Olunmayanlar", "type": V.GRID, "filter": {"field": "Durum", "value": "Mutabık Değil"}},
    ],
    "layout": {
        "name": "Mutabakat", "default": True,
        "tabs": [tab("Cari Hesap Mutabakatı",
                     ("Dönem", ["Tedarikçi", "Dönem Sonu", "Para Birimi", "Durum", "Finans Sorumlusu (Kırpart)"], 1),
                     ("Bakiyeler", ["Kırpart Bakiyesi", "Tedarikçi Bakiyesi", "Fark Açıklaması", "Yanıt Tarihi"], 2),
                     ("Ekstreler", ["Kırpart Ekstresi", "Tedarikçi Ekstresi"], 1), columns=2)],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
#  C. KALİTE
# ═══════════════════════════════════════════════════════════════════════════════
D_FIELDS = ["D1 Ekip", "D2 Problem Tanımı", "D3 Geçici Önlem", "D4 Kök Neden", "D5 Kalıcı Önlem",
            "D6 Uygulama ve Doğrulama", "D7 Tekrarı Önleme", "D8 Kapanış"]
MALIYETLER = ["Ayıklama Maliyeti", "Rework Maliyeti", "Hurda Maliyeti", "Ek Nakliye Maliyeti",
              "Ceza / Müşteri Yansıması", "Diğer Maliyet"]

KALITE_VAKALARI = {
    "name": "Kalite Vakaları",
    "icon": "fas fa-exclamation-triangle",
    "fields": [
        pk("Vaka Başlığı"),
        {"name": "Vaka No", "type": F.AUTONUMBER},
        sel("Vaka Kaynağı", ("Hat İadesi (ERP)", RED), ("GKK Parti Reddi (ERP)", ORANGE),
            ("Müşteri Şikayeti (PLM)", PURPLE), ("Lojistik Uygunsuzluk", YELLOW), ("Manuel", LBLUE)),
        txt("ERP / PLM Referans No"),
        txt("Lot No"),
        date("Tespit Tarihi"),
        num("Kontrol Edilen Miktar"),
        {**num("Hatalı Miktar"), "validation": [{"if": "{{Hatalı Miktar}} < 0",
                                                  "message": "Hatalı miktar negatif olamaz."}]},
        sel("Hata Kategorisi", ("Boyutsal", BLUE), ("Görsel", YELLOW), ("Malzeme", ORANGE), ("Fonksiyonel", RED),
            ("Ambalaj-Etiket", TEAL), ("Karışık Parça", PURPLE)),
        ml("Hata Tanımı"),
        filef("Fotoğraflar"),
        sel("İade Durumu", ("İade Yok", LBLUE), ("İade Edilecek", YELLOW), ("Sevk Edildi", BLUE),
            ("Tedarikçi Teslim Aldı", GREEN)),
        txt("İade İrsaliye No"),
        boolf("8D Gerekli"),
        sel("8D Durumu", ("Taslak", LBLUE), ("Kırpart Onayında", YELLOW), ("Tedarikçiye Gönderildi", BLUE),
            ("Tedarikçi Sundu", PURPLE), ("Revizyon İstendi", ORANGE), ("Onaylandı", GREEN), ("Kapandı", TEAL)),
        date("8D Termin"),
        *[ml(d) for d in D_FIELDS],
        filef("Kanıt Dokümanları"),
        num("Revizyon No"),
        {**ml("Son Revizyon Notu"), "required_when": "{{8D Durumu}} = 'Revizyon İstendi'"},
        user("8D Onaylayan"),
        date("8D Kapanış Tarihi"),
        *[cur(m) for m in MALIYETLER],
        sel("Maliyet Para Birimi", *PARA),
        ml("Maliyet Açıklaması"),
        sel("Maliyet Onay Durumu", ("Maliyet Yok", LBLUE), ("Taslak", YELLOW), ("Tedarikçi Onayında", BLUE),
            ("İtiraz", RED), ("Onaylandı", GREEN), ("Faturalandı", TEAL)),
        {**ml("Tedarikçi İtiraz Notu"), "required_when": "{{Maliyet Onay Durumu}} = 'İtiraz'"},
        link("Tedarikçi", "Tedarikçiler"),
        link("Malzeme", "Malzemeler"),
        link("Sevkiyat Kalemi", "Sevkiyat Kalemleri"),
        lk("İrsaliye No", "Sevkiyat Kalemi", "İrsaliye No"),
        *T("kalite", "finans", "portal"),
    ],
    "views": [
        {"name": "Tüm Kalite Vakaları", "type": V.GRID},
        {"name": "Vaka Kaynağına Göre", "type": V.KANBAN, "group_by": "Vaka Kaynağı"},
        {"name": "8D Panosu", "type": V.KANBAN, "group_by": "8D Durumu"},
        {"name": "8D Gereken Vakalar", "type": V.GRID, "filter": {"field": "8D Gerekli", "value": True}},
        {"name": "İade Yönetimi", "type": V.KANBAN, "group_by": "İade Durumu"},
        {"name": "Kalitesizlik Maliyeti Onayı", "type": V.KANBAN, "group_by": "Maliyet Onay Durumu"},
        {"name": "Tespit Takvimi", "type": V.CALENDAR, "date_field": "Tespit Tarihi"},
        {"name": "8D Raporu", "type": V.DOCUMENT, "template": [
            {"type": "header", "text": "8D RAPORU — KIRPART", "level": 2, "align": "center"},
            {"type": "field", "name": "Vaka No"}, {"type": "field", "name": "Tedarikçi"},
            {"type": "field", "name": "Malzeme"}, {"type": "field", "name": "Hata Tanımı"},
            *[blk for d in D_FIELDS for blk in ({"type": "header", "text": d, "level": 4},
                                               {"type": "field", "name": d})],
            {"type": "field", "name": "8D Durumu"}, {"type": "field", "name": "8D Kapanış Tarihi"},
        ]},
    ],
    "layout": {
        "name": "Kalite Vakası", "default": True,
        "tabs": [
            tab("Vaka",
                ("Kaynak", ["Vaka No", "Vaka Kaynağı", "ERP / PLM Referans No", "Tedarikçi", "Malzeme",
                            "Sevkiyat Kalemi", "İrsaliye No", "Lot No"], 1),
                ("Uygunsuzluk", ["Tespit Tarihi", "Kontrol Edilen Miktar", "Hatalı Miktar", "Hata Kategorisi",
                                 "Hata Tanımı", "Fotoğraflar"], 2), columns=2),
            tab("İade", ("İade Yönetimi", ["İade Durumu", "İade İrsaliye No"])),
            tab("8D",
                ("8D Akışı", ["8D Gerekli", "8D Durumu", "8D Termin", "Revizyon No", "Son Revizyon Notu",
                              "8D Onaylayan", "8D Kapanış Tarihi"], 1),
                ("D1–D8", D_FIELDS + ["Kanıt Dokümanları"], 2), columns=2),
            tab("Kalitesizlik Maliyeti",
                ("Maliyet Kalemleri", MALIYETLER + ["Maliyet Para Birimi"], 1),
                ("Onay", ["Maliyet Onay Durumu", "Maliyet Açıklaması", "Tedarikçi İtiraz Notu"], 2), columns=2),
        ],
    },
}

DENETIM_TIPLERI = {
    "name": "Denetim Tipleri",
    "icon": "fas fa-clipboard-check",
    "fields": [
        pk("Denetim Tipi"),
        txt("Denetim Tipi (EN)"),
        num("Periyot (gün)"),
        num("A Sınıfı Alt Sınırı %"),
        num("B Sınıfı Alt Sınırı %"),
        ml("Açıklama"),
        boolf("Aktif"),
    ],
    "views": [{"name": "Tüm Denetim Tipleri", "type": V.GRID}],
}

DENETIM_SORULARI = {
    "name": "Denetim Soruları",
    "icon": "fas fa-question-circle",
    "fields": [
        pk("Soru Kodu"),
        txt("Bölüm"),
        ml("Soru"),
        ml("Soru (EN)"),
        num("Maksimum Puan"),
        num("Ağırlık"),
        num("Sıra"),
        boolf("Aktif"),
        link("Denetim Tipi", "Denetim Tipleri"),
    ],
    "views": [
        {"name": "Tüm Sorular", "type": V.GRID},
        {"name": "Aktif Sorular", "type": V.GRID, "filter": {"field": "Aktif", "value": True}},
    ],
}

DENETIMLER = {
    "name": "Denetimler",
    "icon": "fas fa-search",
    "fields": [
        pk("Denetim Başlığı"),
        {"name": "Denetim No", "type": F.AUTONUMBER},
        date("Planlanan Tarih"),
        date("Gerçekleşen Tarih"),
        sel("Durum", ("Planlandı", BLUE), ("Yapıldı", GREEN), ("Ertelendi", ORANGE), ("İptal", PINK)),
        {"name": "Denetçiler", "type": F.MULTIUSER},
        ml("Genel Bulgular"),
        filef("Denetim Raporu"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Denetim Tipi", "Denetim Tipleri"),
        link("Tedarikçi Katılımcıları", "Kontaklar & Portal Kullanıcıları", multiple=True),
        lk("Periyot (gün)", "Denetim Tipi", "Periyot (gün)"),
        lk("A Sınıfı Alt Sınırı %", "Denetim Tipi", "A Sınıfı Alt Sınırı %"),
        lk("B Sınıfı Alt Sınırı %", "Denetim Tipi", "B Sınıfı Alt Sınırı %"),
        *T("kod", "kalite", "portal"),
    ],
    "views": [
        {"name": "Tüm Denetimler", "type": V.GRID},
        {"name": "Denetim Planı", "type": V.CALENDAR, "date_field": "Planlanan Tarih"},
        {"name": "Denetim Durumu", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "Planlanan Denetimler", "type": V.GRID, "filter": {"field": "Durum", "value": "Planlandı"}},
        {"name": "Denetim Geçmişi", "type": V.GRID, "filter": {"field": "Durum", "value": "Yapıldı"}},
    ],
}

DENETIM_CEVAPLARI = {
    "name": "Denetim Cevapları",
    "icon": "fas fa-check-double",
    "fields": [
        pk("Cevap"),
        {"name": "Cevap No", "type": F.AUTONUMBER},
        {**num("Verilen Puan"), "validation": [{"if": "{{Verilen Puan}} < 0",
                                                 "message": "Puan 0'dan küçük olamaz."}]},
        ml("Bulgu / Yorum"),
        filef("Kanıt"),
        boolf("Aksiyon Gerekli"),
        link("Denetim", "Denetimler"),
        link("Denetim Sorusu", "Denetim Soruları"),
        link("Tedarikçi", "Tedarikçiler"),
        lk("Soru Kodu", "Denetim Sorusu", "Soru Kodu"),
        lk("Bölüm", "Denetim Sorusu", "Bölüm"),
        lk("Soru", "Denetim Sorusu", "Soru"),
        lk("Maksimum Puan", "Denetim Sorusu", "Maksimum Puan"),
        lk("Ağırlık", "Denetim Sorusu", "Ağırlık"),
    ],
    "views": [
        {"name": "Tüm Cevaplar", "type": V.GRID},
        {"name": "Aksiyon Gerektirenler", "type": V.GRID, "filter": {"field": "Aksiyon Gerekli", "value": True}},
    ],
    "layout": {"name": "Cevap", "default": True,
               "tabs": [tab("Puanlama", ("Soru", ["Denetim", "Denetim Sorusu", "Soru Kodu", "Bölüm", "Soru",
                                                  "Maksimum Puan", "Ağırlık"], 1),
                            ("Cevap", ["Verilen Puan", "Bulgu / Yorum", "Kanıt", "Aksiyon Gerekli"], 2),
                            columns=2)]},
}

PPAP_SEVIYE = (("Seviye 1", LBLUE), ("Seviye 2", BLUE), ("Seviye 3", PURPLE), ("Seviye 4", ORANGE),
               ("Seviye 5", RED))

PPAP_BELGE_TIPLERI = {
    "name": "PPAP Belge Tipleri",
    "icon": "fas fa-folder-open",
    "fields": [
        pk("Belge Tipi"),
        txt("Belge Tipi (EN)"),
        *[boolf(f"Seviye {i} Zorunlu") for i in range(1, 6)],
        ml("Açıklama"),
        filef("Şablon Dosya"),
        boolf("PLM'e Aktarılsın"),
        num("Sıra"),
    ],
    "views": [{"name": "Tüm PPAP Belge Tipleri", "type": V.GRID}],
}

PPAP_TALEPLERI = {
    "name": "PPAP Talepleri",
    "icon": "fas fa-file-signature",
    "fields": [
        pk("Talep Başlığı"),
        {"name": "PPAP No", "type": F.AUTONUMBER},
        sel("PPAP Seviyesi", *PPAP_SEVIYE),
        sel("Sunum Sebebi", ("Yeni Parça", BLUE), ("Mühendislik Değişikliği", PURPLE), ("Kalıp Değişimi", ORANGE),
            ("Kaynak Değişimi", YELLOW), ("Proses Değişikliği", TEAL), ("Uzun Süre Üretilmeyen", LBLUE)),
        date("Talep Tarihi"),
        date("Termin"),
        sel("Durum", ("Açıldı", LBLUE), ("Tedarikçide", BLUE), ("İncelemede", YELLOW), ("Revizyon İstendi", ORANGE),
            ("Onaylandı", GREEN), ("Şartlı Onay", TEAL), ("Reddedildi", RED)),
        user("Kırpart Sorumlusu"),
        date("PSW Onay Tarihi"),
        sel("PLM Aktarım Durumu", ("Bekliyor", YELLOW), ("Aktarıldı", GREEN), ("Hata", RED)),
        ml("Notlar"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Malzeme", "Malzemeler"),
        lk("Çizim Revizyonu", "Malzeme", "Revizyon"),
        *T("portal"),
    ],
    "views": [
        {"name": "Tüm PPAP Talepleri", "type": V.GRID},
        {"name": "PPAP Durumu", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "PPAP Termin Takvimi", "type": V.CALENDAR, "date_field": "Termin"},
    ],
}

PPAP_DOKUMANLARI = {
    "name": "PPAP Dokümanları",
    "icon": "fas fa-file-upload",
    "fields": [
        pk("Doküman"),
        {"name": "Doküman No", "type": F.AUTONUMBER},
        filef("Dosya"),
        num("Versiyon"),
        date("Yükleme Tarihi"),
        sel("Durum", ("Bekliyor", LBLUE), ("Yüklendi", BLUE), ("İncelemede", YELLOW), ("Revizyon İstendi", ORANGE),
            ("Onaylandı", GREEN), ("Reddedildi", RED)),
        user("İnceleyen"),
        {**ml("İnceleme Notu"), "required_when": "{{Durum}} = 'Revizyon İstendi'"},
        ml("Tedarikçi Yanıtı"),
        date("Onay Tarihi"),
        num("Onaylı (1/0)"),
        boolf("PLM'e Aktarıldı"),
        date("PLM Aktarım Tarihi"),
        link("PPAP Talebi", "PPAP Talepleri"),
        link("Belge Tipi", "PPAP Belge Tipleri"),
        link("Tedarikçi", "Tedarikçiler"),
        lk("Açıklama", "Belge Tipi", "Açıklama"),
        lk("PPAP Sorumlusu", "PPAP Talebi", "Kırpart Sorumlusu"),
        *T("portal"),
    ],
    "views": [
        {"name": "Tüm PPAP Dokümanları", "type": V.GRID},
        {"name": "Doküman Onay Panosu", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "İnceleme Bekleyenler", "type": V.GRID, "filter": {"field": "Durum", "value": ["Yüklendi", "İncelemede"]}},
    ],
    "layout": {"name": "PPAP Dokümanı", "default": True,
               "tabs": [tab("Doküman", ("Belge", ["PPAP Talebi", "Belge Tipi", "Açıklama", "Tedarikçi", "Dosya",
                                                  "Versiyon", "Yükleme Tarihi", "Tedarikçi Yanıtı"], 1),
                            ("Onay", ["Durum", "İnceleyen", "İnceleme Notu", "Onay Tarihi", "PLM'e Aktarıldı",
                                      "PLM Aktarım Tarihi"], 2), columns=2)]},
}

SAPMA_TALEPLERI = {
    "name": "Sapma Talepleri",
    "icon": "fas fa-random",
    "fields": [
        pk("Sapma Konusu"),
        {"name": "Sapma No", "type": F.AUTONUMBER},
        sel("Sapma Tipi", ("Boyutsal", BLUE), ("Malzeme", ORANGE), ("Proses", PURPLE), ("Ambalaj", TEAL), ("Diğer", LBLUE)),
        ml("Sapma Tanımı"),
        ml("Sebep"),
        txt("Spesifikasyon Değeri"),
        txt("Gerçek Değer"),
        num("Talep Edilen Miktar"),
        date("Geçerlilik Başlangıcı"),
        date("Geçerlilik Bitişi"),
        ml("Risk Değerlendirmesi"),
        filef("Destek Dokümanları"),
        sel("Durum", ("Taslak", LBLUE), ("Kalite Onayında", YELLOW), ("Proje Onayında", ORANGE),
            ("Satınalma Onayında", BLUE), ("Onaylandı", GREEN), ("Reddedildi", RED), ("Süresi Doldu", PINK)),
        user("Proje Onaycısı"),
        ml("Onay / Red Notu"),
        date("Onay Tarihi"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Malzeme", "Malzemeler"),
        link("Talep Eden", "Kontaklar & Portal Kullanıcıları"),
        *T("kalite", "satinalma", "portal"),
    ],
    "views": [
        {"name": "Tüm Sapma Talepleri", "type": V.GRID},
        {"name": "Onay Akışı", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "Onaylı Sapmalar", "type": V.GRID, "filter": {"field": "Durum", "value": "Onaylandı"}},
        {"name": "Geçerlilik Takvimi", "type": V.CALENDAR, "date_field": "Geçerlilik Bitişi"},
    ],
    "forms": [{
        "name": "Sapma Talebi Formu", "private": True,
        "description": "Spesifikasyon dışı sevkiyat için sapma talebi açın; talep Kırpart onay zincirine girer.",
        "fields": ["Tedarikçi", "Malzeme", "Talep Eden", "Sapma Tipi", "Sapma Tanımı", "Sebep",
                   "Spesifikasyon Değeri", "Gerçek Değer", "Talep Edilen Miktar", "Geçerlilik Başlangıcı",
                   "Geçerlilik Bitişi", "Risk Değerlendirmesi", "Destek Dokümanları"],
        "required_fields": {"Tedarikçi": True, "Malzeme": True, "Sapma Tanımı": True, "Sebep": True},
        "end_message": "Sapma talebiniz Kırpart kalite onayına iletildi.",
    }],
}

SAPMALI_LOTLAR = {
    "name": "Sapmalı Lotlar",
    "icon": "fas fa-tags",
    "fields": [
        pk("Lot No"),
        num("Miktar"),
        date("Sevk Tarihi"),
        ml("Not"),
        link("Sapma Talebi", "Sapma Talepleri"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Sevkiyat", "Sevkiyatlar"),
        lk("Sapma No", "Sapma Talebi", "Sapma No"),
        lk("Kalite Sorumlusu", "Sapma Talebi", "Kalite Sorumlusu"),
    ],
    "views": [{"name": "Tüm Sapmalı Lotlar", "type": V.GRID},
              {"name": "Sevk Takvimi", "type": V.CALENDAR, "date_field": "Sevk Tarihi"}],
}

AKSIYONLAR = {
    "name": "Aksiyonlar",
    "icon": "fas fa-tasks",
    "fields": [
        pk("Aksiyon Başlığı"),
        {"name": "Aksiyon No", "type": F.AUTONUMBER},
        sel("Kaynak Tipi", ("8D", RED), ("Denetim", BLUE), ("Sapma", ORANGE), ("Ziyaret-Toplantı", TEAL), ("Diğer", LBLUE)),
        ml("Aksiyon Tanımı"),
        sel("Aksiyon Tipi", ("Düzeltici", ORANGE), ("Önleyici", BLUE), ("İyileştirme", GREEN)),
        sel("Sorumlu Taraf", ("Tedarikçi", PURPLE), ("Kırpart", BLUE)),
        user("Sorumlu Kişi (Kırpart)"),
        date("Açılış Tarihi"),
        date("Termin"),
        sel("Durum", ("Açık", LBLUE), ("Devam Ediyor", YELLOW), ("Doğrulama Bekliyor", BLUE), ("Kapandı", GREEN),
            ("İptal", PINK)),
        filef("Kanıt"),
        ml("Tamamlanma Notu"),
        date("Kapanış Tarihi"),
        user("Doğrulayan"),
        num("Açık (1/0)"),
        link("Kalite Vakası", "Kalite Vakaları"),
        link("Denetim", "Denetimler"),
        link("Sapma Talebi", "Sapma Talepleri"),
        link("Ziyaret / Toplantı", "Ziyaret & Toplantılar"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Sorumlu Kişi (Tedarikçi)", "Kontaklar & Portal Kullanıcıları"),
        *T("kalite", "portal"),
    ],
    "views": [
        {"name": "Tüm Aksiyonlar", "type": V.GRID},
        {"name": "Açık Aksiyonlar", "type": V.GRID,
         "filter": {"field": "Durum", "value": ["Açık", "Devam Ediyor", "Doğrulama Bekliyor"]}},
        {"name": "Aksiyon Panosu", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "Kaynağa Göre", "type": V.KANBAN, "group_by": "Kaynak Tipi"},
        {"name": "Termin Takvimi", "type": V.CALENDAR, "date_field": "Termin"},
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
#  D. BELGE, VARLIK, İLETİŞİM
# ═══════════════════════════════════════════════════════════════════════════════
REHBERLER = ["Portal Kullanım Kılavuzu", "MRP Okuma Rehberi", "ASN Oluşturma Rehberi"]

BELGELER = {
    "name": "Belgeler",
    "icon": "fas fa-file-alt",
    "fields": [
        pk("Belge Adı"),
        sel("Belge Türü", ("Kalite Sertifikası", GREEN), ("Satınalma Sözleşmesi", BLUE), ("Kalite Sözleşmesi", PURPLE),
            ("Finansal Tablo", YELLOW), ("Teknik Şartname", TEAL), ("Çizim", LBLUE),
            ("Portal Kullanım Kılavuzu", ORANGE), ("MRP Okuma Rehberi", ORANGE), ("ASN Oluşturma Rehberi", ORANGE),
            ("Diğer", PINK)),
        sel("Yön", ("Tedarikçiden Gelen", PURPLE), ("Kırpart'ın Paylaştığı", BLUE)),
        sel("Sertifika Standardı", ("IATF 16949", RED), ("ISO 9001", BLUE), ("ISO 14001", GREEN), ("ISO 45001", ORANGE),
            ("ISO 50001", YELLOW), ("VDA 6.3", PURPLE), ("Diğer", LBLUE)),
        txt("Belge No"),
        txt("Veren Kuruluş"),
        date("Geçerlilik Başlangıcı"),
        {**date("Geçerlilik Bitişi"), "required_when": "{{Belge Türü}} = 'Kalite Sertifikası'"},
        txt("Finansal Yıl"),
        filef("Dosya"),
        txt("Versiyon"),
        sel("Dil", ("TR", RED), ("EN", BLUE), ("TR+EN", PURPLE)),
        sel("Kırpart Onayı", ("Bekliyor", YELLOW), ("Onaylandı", GREEN), ("Reddedildi", RED)),
        user("Kırpart Sorumlusu"),
        link("Tedarikçiler", "Tedarikçiler", multiple=True),
        link("Malzemeler", "Malzemeler", multiple=True),
        lk("Portal Kullanıcıları", "Tedarikçiler", "Tedarikçi Portal Kullanıcıları"),
    ],
    "views": [
        {"name": "Tüm Belgeler", "type": V.GRID},
        {"name": "Sertifikalar", "type": V.GRID, "filter": {"field": "Belge Türü", "value": "Kalite Sertifikası"}},
        {"name": "Sözleşmeler", "type": V.GRID,
         "filter": {"field": "Belge Türü", "value": ["Satınalma Sözleşmesi", "Kalite Sözleşmesi"]}},
        {"name": "Şartnameler & Çizimler", "type": V.GRID,
         "filter": {"field": "Belge Türü", "value": ["Teknik Şartname", "Çizim"]}},
        {"name": "Bilgi Bankası", "type": V.GRID, "filter": {"field": "Belge Türü", "value": REHBERLER}},
        {"name": "Finansal Tablolar", "type": V.GRID, "filter": {"field": "Belge Türü", "value": "Finansal Tablo"}},
        {"name": "Kırpart Onayı Bekleyenler", "type": V.GRID, "filter": {"field": "Kırpart Onayı", "value": "Bekliyor"}},
        {"name": "Geçerlilik Bitiş Takvimi", "type": V.CALENDAR, "date_field": "Geçerlilik Bitişi"},
        {"name": "Belge Türüne Göre", "type": V.KANBAN, "group_by": "Belge Türü"},
    ],
    "forms": [{
        "name": "Sertifika / Belge Yükleme", "private": True,
        "description": "Kalite sertifikası, finansal tablo vb. belgeleri yükleyin.",
        "fields": ["Tedarikçiler", "Belge Adı", "Belge Türü", "Sertifika Standardı", "Belge No", "Veren Kuruluş",
                   "Geçerlilik Başlangıcı", "Geçerlilik Bitişi", "Finansal Yıl", "Dosya", "Dil"],
        "required_fields": {"Belge Adı": True, "Belge Türü": True, "Dosya": True},
    }],
    "layout": {"name": "Belge", "default": True,
               "tabs": [tab("Belge", ("Belge", ["Belge Adı", "Belge Türü", "Yön", "Tedarikçiler", "Malzemeler",
                                                "Dosya", "Versiyon", "Dil"], 1),
                            ("Geçerlilik & Onay", ["Sertifika Standardı", "Belge No", "Veren Kuruluş",
                                                   "Geçerlilik Başlangıcı", "Geçerlilik Bitişi", "Finansal Yıl",
                                                   "Kırpart Onayı", "Kırpart Sorumlusu"], 2), columns=2)]},
}

ZIYARETLER = {
    "name": "Ziyaret & Toplantılar",
    "icon": "fas fa-handshake",
    "fields": [
        pk("Konu"),
        sel("Tür", ("Tedarikçi Ziyareti", BLUE), ("Kırpart'ta Toplantı", PURPLE), ("Online", TEAL)),
        date("Tarih"),
        ml("Gündem"),
        {"name": "Kırpart Katılımcıları", "type": F.MULTIUSER},
        ml("Toplantı Notları"),
        ml("Kararlar"),
        filef("Ekler"),
        link("Tedarikçi", "Tedarikçiler"),
        link("Tedarikçi Katılımcıları", "Kontaklar & Portal Kullanıcıları", multiple=True),
    ],
    "views": [
        {"name": "Tüm Ziyaret & Toplantılar", "type": V.GRID},
        {"name": "Toplantı Takvimi", "type": V.CALENDAR, "date_field": "Tarih"},
        {"name": "Toplantı Tutanağı", "type": V.DOCUMENT, "template": [
            {"type": "header", "text": "TOPLANTI TUTANAĞI", "level": 2, "align": "center"},
            {"type": "field", "name": "Konu"}, {"type": "field", "name": "Tedarikçi"},
            {"type": "field", "name": "Tarih"}, {"type": "header", "text": "Gündem", "level": 4},
            {"type": "field", "name": "Gündem"}, {"type": "header", "text": "Notlar", "level": 4},
            {"type": "field", "name": "Toplantı Notları"}, {"type": "header", "text": "Kararlar", "level": 4},
            {"type": "field", "name": "Kararlar"},
        ]},
    ],
}

VARLIKLAR = {
    "name": "Varlıklar (Kalıp / Ekipman)",
    "icon": "fas fa-tools",
    "fields": [
        pk("Demirbaş No"),
        txt("Varlık Adı", True),
        sel("Varlık Tipi", ("Kalıp", BLUE), ("Fikstür", TEAL), ("Kontrol Aparatı", PURPLE), ("Ekipman", ORANGE)),
        txt("Proje"),
        sel("Kapsam", ("Outsource", ORANGE), ("Yeni Proje", BLUE)),
        sel("Sahiplik", ("Kırpart", BLUE), ("Müşteri", PURPLE), ("Tedarikçi", TEAL)),
        date("Teslim Tarihi"),
        num("Göz Sayısı"),
        num("Tasarım Ömrü (baskı)"),
        num("Bakım Periyodu (gün)"),
        date("Son Bakım Tarihi"),
        num("Güncel Baskı Sayısı"),
        sel("Durum", ("Aktif", GREEN), ("Bakımda", YELLOW), ("Revizyonda", ORANGE), ("Hurda", RED), ("İade Alındı", LBLUE)),
        filef("Fotoğraf"),
        link("Tedarikçi (Bulunduğu Yer)", "Tedarikçiler"),
        link("Malzemeler", "Malzemeler", multiple=True),
        lk("Portal Kullanıcıları", "Tedarikçi (Bulunduğu Yer)", "Tedarikçi Portal Kullanıcıları"),
        lk("Satınalma Sorumlusu", "Tedarikçi (Bulunduğu Yer)", "Satınalma Sorumlusu (Kırpart)"),
    ],
    "views": [
        {"name": "Tüm Varlıklar", "type": V.GRID},
        {"name": "Varlık Durumu", "type": V.KANBAN, "group_by": "Durum"},
        {"name": "Varlık Tipine Göre", "type": V.KANBAN, "group_by": "Varlık Tipi"},
        {"name": "Varlık Kartları", "type": V.GALLERY},
    ],
}

BAKIM = {
    "name": "Bakım & Baskı Kayıtları",
    "icon": "fas fa-wrench",
    "fields": [
        pk("Özet"),
        {"name": "Kayıt No", "type": F.AUTONUMBER},
        date("Tarih"),
        sel("Kayıt Tipi", ("Periyodik Bakım", GREEN), ("Baskı Sayısı Bildirimi", BLUE), ("Arıza", RED), ("Revizyon", ORANGE)),
        num("Güncel Baskı Sayısı"),
        ml("Yapılan İşlem"),
        filef("Kanıt / Fotoğraf"),
        boolf("Kırpart Kontrolü"),
        link("Varlık", "Varlıklar (Kalıp / Ekipman)"),
        link("Tedarikçi", "Tedarikçiler"),
        lk("Demirbaş No", "Varlık", "Demirbaş No"),
        lk("Satınalma Sorumlusu", "Varlık", "Satınalma Sorumlusu"),
    ],
    "views": [
        {"name": "Tüm Bakım & Baskı Kayıtları", "type": V.GRID},
        {"name": "Kayıt Tipine Göre", "type": V.KANBAN, "group_by": "Kayıt Tipi"},
        {"name": "Bakım Takvimi", "type": V.CALENDAR, "date_field": "Tarih"},
    ],
    "forms": [{
        "name": "Bakım / Baskı Sayısı Bildirimi", "private": True,
        "description": "Kırpart varlıklarının periyodik bakımını ve baskı sayacını bildirin.",
        "fields": ["Varlık", "Tarih", "Kayıt Tipi", "Güncel Baskı Sayısı", "Yapılan İşlem", "Kanıt / Fotoğraf"],
        "required_fields": {"Varlık": True, "Tarih": True},
    }],
}

# ═══════════════════════════════════════════════════════════════════════════════
#  E. PERFORMANS
# ═══════════════════════════════════════════════════════════════════════════════
PERFORMANS = {
    "name": "Performans Kartları",
    "icon": "fas fa-chart-line",
    "fields": [
        pk("Dönem"),
        {"name": "Kart No", "type": F.AUTONUMBER},
        date("Dönem Başlangıcı"),
        date("Dönem Bitişi"),
        num("Teslim Alınan Miktar"),
        num("Hatalı Miktar"),
        num("Hat İadesi Vaka Sayısı"),
        num("GKK Parti Reddi Sayısı"),
        num("Zamanında Teslim %"),
        num("Ort. 8D Kapanış (gün)"),
        num("Son Denetim Başarı %"),
        num("Geçerli Sertifika (1/0)"),
        num("Sapma Talebi Sayısı"),
        num("İletişim Puanı"),
        ml("Kırpart Yorumu"),
        boolf("Yayınlandı"),
        link("Tedarikçi", "Tedarikçiler"),
        lk("PPM Hedefi", "Tedarikçi", "PPM Hedefi"),
        lk("Vaka Hedefi", "Tedarikçi", "Vaka Sayısı Hedefi (dönem)"),
        lk("Zamanında Teslim Hedefi", "Tedarikçi", "Zamanında Teslim Hedefi %"),
        lk("8D Kapanış Hedefi", "Tedarikçi", "8D Kapanış Hedefi (gün)"),
        *T("kod", "portal"),
    ],
    "views": [
        {"name": "Tüm Performans Kartları", "type": V.GRID},
        {"name": "Yayınlanan Kartlar", "type": V.GRID, "filter": {"field": "Yayınlandı", "value": True}},
        {"name": "Dönem Takvimi", "type": V.CALENDAR, "date_field": "Dönem Bitişi"},
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
#  OTOMASYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

def notify(field, msg):
    return {"type": "notify", "to_field": field, "message": msg}


def when(cond, *actions, otherwise=None):
    a = {"type": "condition", "if": cond, "then": list(actions)}
    if otherwise:
        a["else"] = otherwise
    return a


def copy_tedarikci(trigger_list, parent_list, key_child, key_parent, parent_ted="Tedarikçi"):
    """Kayıt açılınca Tedarikçi'yi üst kayıttan kopyala (portal veri güvenliği)."""
    return {
        "type": "find_records", "list": parent_list, "max": 1,
        "where": {"field": key_parent, "op": "equals", "value": f"trigger:{key_child}"},
        "actions": [{"type": "update_record", "target": "trigger",
                     "fields": {"Tedarikçi": f"loop:{parent_ted}"}}],
    }


PPAP_AUTOS = [{
    "name": f"PPAP talebi açıldı — {s} doküman kayıtlarını oluştur",
    "trigger": {"type": "record_created", "list": "PPAP Talepleri"},
    "actions": [when(f"{{{{PPAP Seviyesi}}}} = '{s}'", {
        "type": "find_records", "list": "PPAP Belge Tipleri", "max": 50, "sort_by": "Sıra ASC",
        "where": {"field": f"{s} Zorunlu", "op": "equals", "value": True},
        "actions": [{"type": "create_record", "list": "PPAP Dokümanları", "fields": {
            "Doküman": "loop:Belge Tipi", "PPAP Talebi": "trigger:_id", "Belge Tipi": "loop:_id", "Tedarikçi": "trigger:Tedarikçi",
            "Durum": "Bekliyor", "Versiyon": "0", "Onaylı (1/0)": "0"}}],
    })],
} for s in ("Seviye 1", "Seviye 2", "Seviye 3", "Seviye 4", "Seviye 5")]

AUTOMATIONS = [
    # ── 1. Sipariş değişikliği bildirimi ───────────────────────────────────────
    {"name": "01a Sipariş kalemi açıldı — teyit beklemeye al",
     "trigger": {"type": "record_created", "list": "Sipariş Kalemleri"},
     "actions": [{"type": "update_record", "fields": {"Teyit Durumu": "Bekliyor", "Teyit Bekliyor (1/0)": "1"}},
                 notify("Portal Kullanıcıları", "Yeni sipariş kalemi: {{Kalem Kodu}} — {{Malzeme Adı}}, "
                        "{{Sipariş Miktarı}} adet, istenen tarih {{İstenen Teslim Tarihi}}. Lütfen teyit verin.")]},
    {"name": "01b Sipariş miktarı değişti — tedarikçiye bildir",
     "trigger": {"type": "record_updated", "list": "Sipariş Kalemleri", "watch_field": "Sipariş Miktarı"},
     "actions": [{"type": "update_record", "fields": {"Teyit Durumu": "Bekliyor", "Teyit Bekliyor (1/0)": "1"}},
                 notify("Portal Kullanıcıları", "Sipariş değişikliği: {{Kalem Kodu}} miktarı {{Sipariş Miktarı}} "
                        "olarak güncellendi. Lütfen yeniden teyit verin.")]},
    {"name": "01c İstenen teslim tarihi değişti — tedarikçiye bildir",
     "trigger": {"type": "record_updated", "list": "Sipariş Kalemleri", "watch_field": "İstenen Teslim Tarihi"},
     "actions": [{"type": "update_record", "fields": {"Teyit Durumu": "Bekliyor", "Teyit Bekliyor (1/0)": "1"}},
                 notify("Portal Kullanıcıları", "Sipariş değişikliği: {{Kalem Kodu}} istenen teslim tarihi "
                        "{{İstenen Teslim Tarihi}} olarak güncellendi. Lütfen yeniden teyit verin.")]},
    {"name": "01d Kırpart sipariş notu değişti — tedarikçiye bildir",
     "trigger": {"type": "record_updated", "list": "Siparişler", "watch_field": "Kırpart Notu"},
     "actions": [notify("Portal Kullanıcıları", "Sipariş {{Sipariş No}} için Kırpart notu: {{Kırpart Notu}}")]},
    # ── 2. Sipariş teyidi ─────────────────────────────────────────────────────
    {"name": "02 Sipariş teyidi verildi — Kırpart satınalmaya bildir",
     "trigger": {"type": "record_updated", "list": "Sipariş Kalemleri", "watch_field": "Teyit Durumu"},
     "actions": [when("{{Teyit Durumu}} != 'Bekliyor'",
                      {"type": "update_record", "fields": {"Teyit Zamanı": "formula:Today()",
                                                           "Teyit Bekliyor (1/0)": "0"}},
                      notify("Satınalma Sorumlusu", "Sipariş teyidi: {{Kalem Kodu}} → {{Teyit Durumu}}. "
                             "Teyit miktarı {{Teyit Edilen Miktar}}, tarih {{Teyit Edilen Tarih}}. "
                             "Kapasite yeterli mi: {{Mevcut Kapasite Yeterli mi?}} — İhtiyaç: {{Neye İhtiyacın Var?}} "
                             "— Red gerekçesi: {{Red Gerekçesi}}"))]},
    # ── 3. Sevkiyat kalemi tedarikçi kopyalama ───────────────────────────────
    {"name": "03 Sevkiyat kalemi — tedarikçiyi sevkiyattan kopyala",
     "trigger": {"type": "record_created", "list": "Sevkiyat Kalemleri"},
     "actions": [copy_tedarikci("Sevkiyat Kalemleri", "Sevkiyatlar", "ASN No", "ASN No")]},
    # ── 4–5. Sevkiyat durumu ─────────────────────────────────────────────────
    {"name": "04 Sevkiyat yola çıktı — Kırpart lojistiğe bildir",
     "trigger": {"type": "record_updated", "list": "Sevkiyatlar", "watch_field": "Durum"},
     "actions": [when("{{Durum}} = 'Yolda'",
                      notify("Lojistik Sorumlusu", "Yoldaki malzeme (ASN {{ASN No}}): irsaliye {{İrsaliye No}}, "
                             "tahmini varış {{Tahmini Varış}}, taşıyıcı {{Taşıyıcı Firma}} / {{Araç Plakası}}."))]},
    {"name": "05a Sevkiyat teslim alındı — tarih yaz ve tedarikçiye bildir",
     "trigger": {"type": "record_updated", "list": "Sevkiyatlar", "watch_field": "Durum"},
     "actions": [when("{{Durum}} = 'Teslim Alındı'",
                      {"type": "update_record", "fields": {"Teslim Alma Tarihi": "formula:Today()"}},
                      notify("Portal Kullanıcıları", "İrsaliye {{İrsaliye No}} (ASN {{ASN No}}) Kırpart tarafından "
                             "teslim alındı."))]},
    {"name": "05b Kabul miktarı girildi — sipariş kalemine son irsaliyeyi yaz",
     "trigger": {"type": "record_updated", "list": "Sevkiyat Kalemleri", "watch_field": "Kabul Edilen Miktar"},
     "actions": [{"type": "find_records", "list": "Sipariş Kalemleri", "max": 1,
                  "where": {"field": "Kalem Kodu", "op": "equals", "value": "trigger:Sipariş Kalem Kodu"},
                  "actions": [{"type": "update_record", "fields": {
                      "Son Teslim Alınan İrsaliye No": "trigger:İrsaliye No",
                      "Son Teslim Alma Tarihi": "formula:Today()"}}]}]},
    # ── 6. Kontak / e-posta listesi onayı ────────────────────────────────────
    {"name": "06a Kontak eklendi — Kırpart onayına düşür",
     "trigger": {"type": "record_created", "list": "Kontaklar & Portal Kullanıcıları"},
     "actions": [{"type": "update_record", "fields": {"Kırpart Onay Durumu": "Talep Edildi"}},
                 notify("Satınalma Sorumlusu", "Tedarikçi yeni kontak/e-posta listesi talebi açtı: {{Ad Soyad}} "
                        "({{E-posta}}). Lütfen onaylayın.")]},
    {"name": "06b Kontak e-posta listesi değişti — Kırpart onayına düşür",
     "trigger": {"type": "record_updated", "list": "Kontaklar & Portal Kullanıcıları",
                 "watch_field": "Otomatik E-posta Listesinde"},
     "actions": [{"type": "update_record", "fields": {"Kırpart Onay Durumu": "Talep Edildi"}},
                 notify("Satınalma Sorumlusu", "E-posta listesi değişiklik talebi: {{Ad Soyad}} ({{E-posta}}).")]},
    {"name": "06c Kontak onaylandı — aktif et",
     "trigger": {"type": "record_updated", "list": "Kontaklar & Portal Kullanıcıları",
                 "watch_field": "Kırpart Onay Durumu"},
     "actions": [when("{{Kırpart Onay Durumu}} = 'Onaylandı'", {"type": "update_record", "fields": {"Aktif": "true"}}),
                 when("{{Kırpart Onay Durumu}} = 'Reddedildi'", {"type": "update_record", "fields": {"Aktif": "false"}})]},
    # ── 7–11. 8D süreci ──────────────────────────────────────────────────────
    {"name": "07 Kalite vakası açıldı — 8D Kırpart onayı",
     "trigger": {"type": "record_created", "list": "Kalite Vakaları"},
     "actions": [when("{{8D Gerekli}} = 'true'",
                      {"type": "update_record", "fields": {"8D Durumu": "Kırpart Onayında", "Revizyon No": "0"}},
                      {"type": "approval", "title": "8D Onayı",
                       "subtitle": "Kalite vakası {{Vaka No}} — {{Hata Tanımı}} için tedarikçiye 8D açılsın mı?",
                       "approver": "field:Kalite Sorumlusu", "timeout_days": 3,
                       "require_rejection_message": True,
                       "on_approve": [{"type": "update_record", "fields": {"8D Durumu": "Tedarikçiye Gönderildi"}}],
                       "on_reject": [{"type": "update_record", "fields": {"8D Durumu": "Kapandı"}}]}),
                 notify("Kalite Sorumlusu", "Yeni kalite vakası {{Vaka No}} ({{Vaka Kaynağı}}): {{Hata Tanımı}} — "
                        "hatalı miktar {{Hatalı Miktar}}.")]},
    {"name": "08 8D tedarikçiye gönderildi — tedarikçiye bildir",
     "trigger": {"type": "record_updated", "list": "Kalite Vakaları", "watch_field": "8D Durumu"},
     "actions": [when("{{8D Durumu}} = 'Tedarikçiye Gönderildi'",
                      notify("Portal Kullanıcıları", "8D talebi / 8D request: Vaka {{Vaka No}} — {{Hata Tanımı}}. "
                             "Termin / Due: {{8D Termin}}. Lütfen D1–D8 alanlarını doldurup sunun."))]},
    {"name": "09 Tedarikçi 8D sundu — Kırpart kaliteye bildir",
     "trigger": {"type": "record_updated", "list": "Kalite Vakaları", "watch_field": "8D Durumu"},
     "actions": [when("{{8D Durumu}} = 'Tedarikçi Sundu'",
                      notify("Kalite Sorumlusu", "Tedarikçi 8D formunu sundu: Vaka {{Vaka No}}. İnceleme bekliyor."))]},
    {"name": "10 8D revizyon istendi — tedarikçiye bildir",
     "trigger": {"type": "record_updated", "list": "Kalite Vakaları", "watch_field": "8D Durumu"},
     "actions": [when("{{8D Durumu}} = 'Revizyon İstendi'",
                      notify("Portal Kullanıcıları", "8D revizyon talebi / revision requested: Vaka {{Vaka No}}. "
                             "Not: {{Son Revizyon Notu}}"))]},
    {"name": "11 8D kapandı — kapanış tarihini yaz",
     "trigger": {"type": "record_updated", "list": "Kalite Vakaları", "watch_field": "8D Durumu"},
     "actions": [when("{{8D Durumu}} = 'Kapandı'",
                      {"type": "update_record", "fields": {"8D Kapanış Tarihi": "formula:Today()"}}),
                 when("{{8D Durumu}} = 'Onaylandı'",
                      notify("Portal Kullanıcıları", "8D onaylandı / approved: Vaka {{Vaka No}}."))]},
    # ── 12. Kalitesizlik maliyeti onayı ──────────────────────────────────────
    {"name": "12 Kalitesizlik maliyeti onay akışı",
     "trigger": {"type": "record_updated", "list": "Kalite Vakaları", "watch_field": "Maliyet Onay Durumu"},
     "actions": [
         when("{{Maliyet Onay Durumu}} = 'Tedarikçi Onayında'",
              notify("Portal Kullanıcıları", "Kalitesizlik maliyeti onayınızı bekliyor: Vaka {{Vaka No}} — "
                     "ayıklama {{Ayıklama Maliyeti}}, rework {{Rework Maliyeti}}, hurda {{Hurda Maliyeti}}, "
                     "ceza {{Ceza / Müşteri Yansıması}}. {{Maliyet Açıklaması}}")),
         when("{{Maliyet Onay Durumu}} = 'İtiraz'",
              notify("Kalite Sorumlusu", "Tedarikçi kalitesizlik maliyetine itiraz etti: Vaka {{Vaka No}} — "
                     "{{Tedarikçi İtiraz Notu}}")),
         when("{{Maliyet Onay Durumu}} = 'Onaylandı'",
              notify("Finans Sorumlusu", "Kalitesizlik maliyeti onaylandı, faturalanabilir: Vaka {{Vaka No}}.")),
     ]},
    # ── 13–15. Aksiyonlar ────────────────────────────────────────────────────
    {"name": "13a Aksiyon açıldı — sorumlulara bildir",
     "trigger": {"type": "record_created", "list": "Aksiyonlar"},
     "actions": [{"type": "update_record", "fields": {"Açılış Tarihi": "formula:Today()", "Açık (1/0)": "1"}},
                 when("{{Sorumlu Taraf}} = 'Tedarikçi'",
                      notify("Portal Kullanıcıları", "Yeni aksiyon {{Aksiyon No}} ({{Kaynak Tipi}}): "
                             "{{Aksiyon Tanımı}} — termin {{Termin}}."),
                      otherwise=[notify("Sorumlu Kişi (Kırpart)", "Size aksiyon atandı {{Aksiyon No}}: "
                                        "{{Aksiyon Tanımı}} — termin {{Termin}}.")])]},
    {"name": "13b Aksiyon termini 3 gün kaldı — hatırlat",
     "trigger": {"type": "time_trigger", "list": "Aksiyonlar", "date_field": "Termin", "offset": 3},
     "actions": [when("{{Açık (1/0)}} = '1'",
                      notify("Portal Kullanıcıları", "Hatırlatma: aksiyon {{Aksiyon No}} termini {{Termin}} "
                             "(3 gün kaldı) — {{Aksiyon Tanımı}}"),
                      notify("Sorumlu Kişi (Kırpart)", "Hatırlatma: aksiyon {{Aksiyon No}} termini {{Termin}}."))]},
    {"name": "14 Aksiyon termini geldi — gecikme uyarısı",
     "trigger": {"type": "time_trigger", "list": "Aksiyonlar", "date_field": "Termin", "offset": 0},
     "actions": [when("{{Açık (1/0)}} = '1'",
                      notify("Portal Kullanıcıları", "Aksiyon {{Aksiyon No}} termini bugün doldu ve hâlâ açık."),
                      notify("Kalite Sorumlusu", "Geciken aksiyon: {{Aksiyon No}} — {{Tedarikçi}} — "
                             "{{Aksiyon Tanımı}}"))]},
    {"name": "15 Aksiyon durumu değişti — doğrulama / kapanış",
     "trigger": {"type": "record_updated", "list": "Aksiyonlar", "watch_field": "Durum"},
     "actions": [
         when("{{Durum}} = 'Doğrulama Bekliyor'",
              notify("Sorumlu Kişi (Kırpart)", "Aksiyon {{Aksiyon No}} doğrulamanızı bekliyor. "
                     "Not: {{Tamamlanma Notu}}"),
              notify("Kalite Sorumlusu", "Aksiyon {{Aksiyon No}} doğrulama bekliyor.")),
         when("{{Durum}} = 'Kapandı'",
              {"type": "update_record", "fields": {"Kapanış Tarihi": "formula:Today()", "Açık (1/0)": "0"}}),
         when("{{Durum}} = 'İptal'", {"type": "update_record", "fields": {"Açık (1/0)": "0"}}),
     ]},
    # ── 16–19. Denetimler ────────────────────────────────────────────────────
    {"name": "16 Denetim açıldı — soru listesinden cevap kayıtlarını oluştur",
     "trigger": {"type": "record_created", "list": "Denetimler"},
     "actions": [{"type": "find_records", "list": "Denetim Soruları", "max": 200, "sort_by": "Sıra ASC",
                  "where": {"field": "Denetim Tipi", "op": "equals", "value": "trigger:Denetim Tipi"},
                  "actions": [when("{{Aktif}} = 'true'", {"type": "create_record", "list": "Denetim Cevapları",
                                                         "fields": {"Cevap": "loop:Soru Kodu", "Denetim": "trigger:_id",
                                                                    "Denetim Sorusu": "loop:_id",
                                                                    "Tedarikçi": "trigger:Tedarikçi"}})]}]},
    {"name": "17 Planlı denetime 14 gün kaldı — hatırlat",
     "trigger": {"type": "time_trigger", "list": "Denetimler", "date_field": "Planlanan Tarih", "offset": 14},
     "actions": [when("{{Durum}} = 'Planlandı'",
                      notify("Portal Kullanıcıları", "Planlı denetim / scheduled audit: {{Denetim No}} — "
                             "{{Denetim Tipi}}, tarih {{Planlanan Tarih}}."),
                      notify("Denetçiler", "Denetim hatırlatması: {{Denetim No}} — {{Tedarikçi}}, {{Planlanan Tarih}}."))]},
    {"name": "18 Denetim bulgusu — aksiyon aç",
     "trigger": {"type": "record_updated", "list": "Denetim Cevapları", "watch_field": "Aksiyon Gerekli"},
     "actions": [when("{{Aksiyon Gerekli}} = 'true'", {"type": "create_record", "list": "Aksiyonlar", "fields": {
         "Aksiyon Başlığı": "trigger:Cevap", "Kaynak Tipi": "Denetim", "Denetim": "trigger:Denetim", "Tedarikçi": "trigger:Tedarikçi",
         "Aksiyon Tanımı": "trigger:Bulgu / Yorum", "Aksiyon Tipi": "Düzeltici", "Sorumlu Taraf": "Tedarikçi",
         "Durum": "Açık", "Termin": "formula:DateAdd(Today(), 30, 'day')"}})]},
    {"name": "19a Denetim yapıldı — tedarikçinin son denetim tarihini güncelle",
     "trigger": {"type": "record_updated", "list": "Denetimler", "watch_field": "Durum"},
     "actions": [when("{{Durum}} = 'Yapıldı'", {
         "type": "find_records", "list": "Tedarikçiler", "max": 1,
         "where": {"field": "Tedarikçi Kodu", "op": "equals", "value": "trigger:Tedarikçi Kodu"},
         "actions": [{"type": "update_record", "fields": {"Son Denetim Tarihi": "trigger:Gerçekleşen Tarih"}}]})]},
    {"name": "19b Bir yıldır denetlenmeyen tedarikçi — Kırpart kaliteye uyar",
     "trigger": {"type": "time_trigger", "list": "Tedarikçiler", "date_field": "Son Denetim Tarihi", "offset": 365},
     "actions": [when("{{Durum}} = 'Aktif'",
                      notify("Kalite Sorumlusu (Kırpart)", "{{Tedarikçi Adı}} 365 gündür denetlenmedi "
                             "(son denetim {{Son Denetim Tarihi}}). Denetim planlayın."))]},
    # ── 20–22. PPAP ──────────────────────────────────────────────────────────
    *PPAP_AUTOS,
    {"name": "20 PPAP talebi açıldı — tedarikçiye bildir",
     "trigger": {"type": "record_created", "list": "PPAP Talepleri"},
     "actions": [{"type": "update_record", "fields": {"Durum": "Tedarikçide", "Talep Tarihi": "formula:Today()"}},
                 notify("Portal Kullanıcıları", "PPAP talebi / PPAP request {{PPAP No}}: {{Malzeme}} — "
                        "{{PPAP Seviyesi}}, sebep {{Sunum Sebebi}}, termin {{Termin}}. "
                        "Lütfen istenen dokümanları yükleyin.")]},
    {"name": "21 PPAP dokümanı yüklendi — incelemeye gönder",
     "trigger": {"type": "record_updated", "list": "PPAP Dokümanları", "watch_field": "Dosya"},
     "actions": [when("isNotBlank({{Dosya}})",
                      {"type": "update_record", "fields": {"Durum": "Yüklendi", "Yükleme Tarihi": "formula:Today()"}},
                      notify("PPAP Sorumlusu", "PPAP dokümanı yüklendi: {{Doküman No}} — {{Belge Tipi}} "
                             "({{PPAP Talebi}}). İnceleme bekliyor."))]},
    {"name": "22 PPAP doküman onay / revizyon",
     "trigger": {"type": "record_updated", "list": "PPAP Dokümanları", "watch_field": "Durum"},
     "actions": [
         when("{{Durum}} = 'Revizyon İstendi'",
              notify("Portal Kullanıcıları", "PPAP doküman revizyonu / revision: {{Belge Tipi}} ({{PPAP Talebi}}). "
                     "Not: {{İnceleme Notu}}")),
         when("{{Durum}} = 'Onaylandı'",
              {"type": "update_record", "fields": {"Onay Tarihi": "formula:Today()", "Onaylı (1/0)": "1"}},
              notify("Portal Kullanıcıları", "PPAP dokümanı onaylandı / approved: {{Belge Tipi}} ({{PPAP Talebi}})."),
              otherwise=[{"type": "update_record", "fields": {"Onaylı (1/0)": "0"}}]),
         when("{{Durum}} = 'Reddedildi'",
              notify("Portal Kullanıcıları", "PPAP dokümanı reddedildi / rejected: {{Belge Tipi}}. {{İnceleme Notu}}")),
     ]},
    {"name": "22b PPAP talebi sonuçlandı — tedarikçiye bildir",
     "trigger": {"type": "record_updated", "list": "PPAP Talepleri", "watch_field": "Durum"},
     "actions": [when("{{Durum}} = 'Onaylandı' or {{Durum}} = 'Şartlı Onay' or {{Durum}} = 'Reddedildi'",
                      {"type": "update_record", "fields": {"PSW Onay Tarihi": "formula:Today()",
                                                           "PLM Aktarım Durumu": "Bekliyor"}},
                      notify("Portal Kullanıcıları", "PPAP {{PPAP No}} sonucu / result: {{Durum}}."))]},
    # ── 23–24. Sapma ─────────────────────────────────────────────────────────
    {"name": "23a Sapma talebi açıldı — kalite onayına gönder",
     "trigger": {"type": "record_created", "list": "Sapma Talepleri"},
     "actions": [{"type": "update_record", "fields": {"Durum": "Kalite Onayında"}}]},
    {"name": "23b Sapma onay zinciri (Kalite → Proje → Satınalma)",
     "trigger": {"type": "record_updated", "list": "Sapma Talepleri", "watch_field": "Durum"},
     "actions": [
         when("{{Durum}} = 'Kalite Onayında'", {
             "type": "approval", "title": "Sapma Talebi — Kalite Onayı",
             "subtitle": "Sapma {{Sapma No}} ({{Sapma Tipi}}): {{Sapma Tanımı}} — miktar {{Talep Edilen Miktar}}",
             "approver": "field:Kalite Sorumlusu", "timeout_days": 3, "require_rejection_message": True,
             "on_approve": [{"type": "update_record", "fields": {"Durum": "Proje Onayında"}}],
             "on_reject": [{"type": "update_record", "fields": {"Durum": "Reddedildi"}}]}),
         when("{{Durum}} = 'Proje Onayında'", {
             "type": "approval", "title": "Sapma Talebi — Proje Onayı",
             "subtitle": "Sapma {{Sapma No}}: {{Sapma Tanımı}}",
             "approver": "field:Proje Onaycısı", "timeout_days": 3, "require_rejection_message": True,
             "on_approve": [{"type": "update_record", "fields": {"Durum": "Satınalma Onayında"}}],
             "on_reject": [{"type": "update_record", "fields": {"Durum": "Reddedildi"}}]}),
         when("{{Durum}} = 'Satınalma Onayında'", {
             "type": "approval", "title": "Sapma Talebi — Satınalma Onayı",
             "subtitle": "Sapma {{Sapma No}}: {{Sapma Tanımı}}",
             "approver": "field:Satınalma Sorumlusu", "timeout_days": 3, "require_rejection_message": True,
             "on_approve": [{"type": "update_record", "fields": {"Durum": "Onaylandı",
                                                                 "Onay Tarihi": "formula:Today()"}}],
             "on_reject": [{"type": "update_record", "fields": {"Durum": "Reddedildi"}}]}),
     ]},
    {"name": "24a Sapma sonuçlandı — tedarikçiye bildir",
     "trigger": {"type": "record_updated", "list": "Sapma Talepleri", "watch_field": "Durum"},
     "actions": [when("{{Durum}} = 'Onaylandı' or {{Durum}} = 'Reddedildi'",
                      notify("Portal Kullanıcıları", "Sapma talebi {{Sapma No}} sonucu / result: {{Durum}}. "
                             "{{Onay / Red Notu}}"))]},
    {"name": "24b Sapma geçerliliği doldu",
     "trigger": {"type": "time_trigger", "list": "Sapma Talepleri", "date_field": "Geçerlilik Bitişi", "offset": 0},
     "actions": [when("{{Durum}} = 'Onaylandı'",
                      {"type": "update_record", "fields": {"Durum": "Süresi Doldu"}},
                      notify("Portal Kullanıcıları", "Sapma {{Sapma No}} geçerlilik süresi doldu."))]},
    # ── 25. Sapmalı lot ──────────────────────────────────────────────────────
    {"name": "25 Sapmalı lot girildi — tedarikçiyi kopyala, kaliteye bildir",
     "trigger": {"type": "record_created", "list": "Sapmalı Lotlar"},
     "actions": [copy_tedarikci("Sapmalı Lotlar", "Sapma Talepleri", "Sapma No", "Sapma No"),
                 notify("Kalite Sorumlusu", "Sapmalı lot sevk edildi: {{Lot No}} — {{Miktar}} adet "
                        "(sapma {{Sapma No}}).")]},
    # ── 26–27. Belgeler ──────────────────────────────────────────────────────
    *[{"name": f"26 Belge geçerliliğine {d} gün kaldı — uyar",
       "trigger": {"type": "time_trigger", "list": "Belgeler", "date_field": "Geçerlilik Bitişi", "offset": d},
       "actions": [notify("Portal Kullanıcıları", f"{{{{Belge Adı}}}} ({{{{Belge Türü}}}}) geçerliliği "
                          f"{{{{Geçerlilik Bitişi}}}} tarihinde bitiyor ({d} gün). Lütfen güncel belgeyi yükleyin."),
                   notify("Kırpart Sorumlusu", f"Belge geçerliliği yaklaşıyor ({d} gün): {{{{Belge Adı}}}} — "
                          f"{{{{Tedarikçiler}}}}")]}
      for d in (60, 30, 0)],
    {"name": "27 Tedarikçi belge yükledi — Kırpart onayına düşür",
     "trigger": {"type": "record_created", "list": "Belgeler"},
     "actions": [when("{{Yön}} = 'Tedarikçiden Gelen' or {{Belge Türü}} = 'Kalite Sertifikası' or "
                      "{{Belge Türü}} = 'Finansal Tablo'",
                      {"type": "update_record", "fields": {"Kırpart Onayı": "Bekliyor", "Yön": "Tedarikçiden Gelen"}},
                      notify("Kırpart Sorumlusu", "Tedarikçi belge yükledi: {{Belge Adı}} ({{Belge Türü}}). "
                             "Onayınızı bekliyor."),
                      otherwise=[{"type": "update_record", "fields": {"Yön": "Kırpart'ın Paylaştığı"}},
                                 notify("Portal Kullanıcıları", "Kırpart yeni belge paylaştı: {{Belge Adı}} "
                                        "({{Belge Türü}}).")])]},
    # ── 29. Bakım kayıtları ──────────────────────────────────────────────────
    {"name": "29 Bakım/baskı kaydı — tedarikçiyi kopyala, varlığı güncelle",
     "trigger": {"type": "record_created", "list": "Bakım & Baskı Kayıtları"},
     "actions": [{"type": "find_records", "list": "Varlıklar (Kalıp / Ekipman)", "max": 1,
                  "where": {"field": "Demirbaş No", "op": "equals", "value": "trigger:Demirbaş No"},
                  "actions": [
                      {"type": "update_record", "target": "trigger",
                       "fields": {"Tedarikçi": "loop:Tedarikçi (Bulunduğu Yer)"}},
                      when("isNotBlank({{Güncel Baskı Sayısı}})", {"type": "update_record", "fields": {
                          "Güncel Baskı Sayısı": "trigger:Güncel Baskı Sayısı"}}),
                  ]},
                 when("{{Kayıt Tipi}} = 'Periyodik Bakım'", {
                     "type": "find_records", "list": "Varlıklar (Kalıp / Ekipman)", "max": 1,
                     "where": {"field": "Demirbaş No", "op": "equals", "value": "trigger:Demirbaş No"},
                     "actions": [{"type": "update_record", "fields": {"Son Bakım Tarihi": "trigger:Tarih"}}]}),
                 when("{{Kayıt Tipi}} = 'Arıza'",
                      notify("Satınalma Sorumlusu", "Varlık arıza bildirimi: {{Demirbaş No}} — {{Yapılan İşlem}}"))]},
    # ── 30. Cari mutabakat ───────────────────────────────────────────────────
    {"name": "30a Cari mutabakat gönderildi — tedarikçiye bildir",
     "trigger": {"type": "record_created", "list": "Cari Mutabakatlar"},
     "actions": [{"type": "update_record", "fields": {"Durum": "Gönderildi"}},
                 notify("Portal Kullanıcıları", "Cari hesap mutabakatı {{Mutabakat No}}: dönem sonu {{Dönem Sonu}}, "
                        "Kırpart bakiyesi {{Kırpart Bakiyesi}} {{Para Birimi}}. Lütfen yanıtlayın.")]},
    {"name": "30b Cari mutabakat yanıtlandı",
     "trigger": {"type": "record_updated", "list": "Cari Mutabakatlar", "watch_field": "Durum"},
     "actions": [when("{{Durum}} = 'Mutabık' or {{Durum}} = 'Mutabık Değil'",
                      {"type": "update_record", "fields": {"Yanıt Tarihi": "formula:Today()"}}),
                 when("{{Durum}} = 'Mutabık Değil'",
                      notify("Finans Sorumlusu (Kırpart)", "Tedarikçi mutabık değil: {{Mutabakat No}} — "
                             "tedarikçi bakiyesi {{Tedarikçi Bakiyesi}}. Açıklama: {{Fark Açıklaması}}"))]},
    # ── 31. Dönem sonu performans kartları ───────────────────────────────────
    {"name": "31 Ay sonu — aktif tedarikçiler için performans kartı aç",
     "trigger": {"type": "cron", "cron": "0 6 1 * *"},
     "actions": [{"type": "loop", "list": "Tedarikçiler", "view": "Aktif Tedarikçiler", "max_records": 500,
                  "actions": [{"type": "create_record", "list": "Performans Kartları", "fields": {
                      "Tedarikçi": "loop:_id",
                      "Dönem Başlangıcı": "formula:DateAdd(Today(), -1, 'month')",
                      "Dönem Bitişi": "formula:DateAdd(Today(), -1, 'day')",
                      "Dönem": "formula:Concat(Year(DateAdd(Today(), -1, 'day')), '-', "
                               "Month(DateAdd(Today(), -1, 'day')))",
                      "Yayınlandı": "false"}}]}]},
]

# Formül/rollup alanlarına bağlı olanlar — upgrade script'inden sonra kurulur
POST_AUTOMATIONS = [
    {"name": "28a Varlık bakım tarihine 7 gün kaldı — hatırlat",
     "trigger": {"type": "time_trigger", "list": "Varlıklar (Kalıp / Ekipman)",
                 "date_field": "Sonraki Bakım Tarihi", "offset": 7},
     "actions": [when("{{Durum}} = 'Aktif'",
                      notify("Portal Kullanıcıları", "Periyodik bakım hatırlatması: {{Demirbaş No}} {{Varlık Adı}} — "
                             "bakım tarihi {{Sonraki Bakım Tarihi}}. Bakım kaydını portala girin."),
                      notify("Satınalma Sorumlusu", "Varlık bakımı yaklaşıyor: {{Demirbaş No}} — "
                             "{{Sonraki Bakım Tarihi}}."))]},
    {"name": "28b Kalıp ömrü sınıra yaklaştı — Kırpart'a uyar",
     "trigger": {"type": "record_updated", "list": "Varlıklar (Kalıp / Ekipman)", "watch_field": "Güncel Baskı Sayısı"},
     "actions": [when("{{Kalan Ömür %}} <= 20",
                      notify("Satınalma Sorumlusu", "Kalıp ömrü uyarısı: {{Demirbaş No}} {{Varlık Adı}} — "
                             "kalan ömür %{{Kalan Ömür %}} ({{Güncel Baskı Sayısı}} / {{Tasarım Ömrü (baskı)}})."),
                      notify("Portal Kullanıcıları", "Kalıp ömrü sınıra yaklaştı: {{Demirbaş No}} — "
                             "kalan ömür %{{Kalan Ömür %}}."))]},
    {"name": "32 Performans kartı yayınlandı — tedarikçiye bildir, puanı karta yaz",
     "trigger": {"type": "record_updated", "list": "Performans Kartları", "watch_field": "Yayınlandı"},
     "actions": [when("{{Yayınlandı}} = 'true'",
                      notify("Portal Kullanıcıları", "Performans skor kartınız yayınlandı / scorecard published: "
                             "{{Dönem}} — toplam puan {{Toplam Puan}}, sınıf {{Sınıf}}."),
                      {"type": "find_records", "list": "Tedarikçiler", "max": 1,
                       "where": {"field": "Tedarikçi Kodu", "op": "equals", "value": "trigger:Tedarikçi Kodu"},
                       "actions": [{"type": "update_record", "fields": {
                           "Güncel Performans Puanı": "trigger:Toplam Puan"}}]})]},
]

# ═══════════════════════════════════════════════════════════════════════════════
#  RAPORLAR (uygulama panosu)
# ═══════════════════════════════════════════════════════════════════════════════
REPORTS = [
    # KPI kartları
    {"label": "Aktif Tedarikçi", "list": "Tedarikçiler", "type": "kpi_count",
     "filter": {"field": "Durum", "value": "Aktif"}, "icon": "fal fa-industry"},
    {"label": "Teyit Bekleyen Sipariş Kalemi", "list": "Sipariş Kalemleri", "type": "kpi_count",
     "filter": {"field": "Teyit Durumu", "value": "Bekliyor"}, "icon": "fal fa-hourglass-half"},
    {"label": "Yoldaki Sevkiyat (ASN)", "list": "Sevkiyatlar", "type": "kpi_count",
     "filter": {"field": "Durum", "value": "Yolda"}, "icon": "fal fa-truck"},
    {"label": "Açık 8D", "list": "Kalite Vakaları", "type": "kpi_count",
     "filter": {"field": "8D Durumu", "value": ["Kırpart Onayında", "Tedarikçiye Gönderildi", "Tedarikçi Sundu",
                                                 "Revizyon İstendi"]}, "icon": "fal fa-exclamation-triangle"},
    {"label": "Açık Aksiyon", "list": "Aksiyonlar", "type": "kpi_count",
     "filter": {"field": "Durum", "value": ["Açık", "Devam Ediyor", "Doğrulama Bekliyor"]}, "icon": "fal fa-tasks"},
    {"label": "İnceleme Bekleyen PPAP Dokümanı", "list": "PPAP Dokümanları", "type": "kpi_count",
     "filter": {"field": "Durum", "value": ["Yüklendi", "İncelemede"]}, "icon": "fal fa-file-upload"},
    {"label": "Onay Bekleyen Sapma", "list": "Sapma Talepleri", "type": "kpi_count",
     "filter": {"field": "Durum", "value": ["Kalite Onayında", "Proje Onayında", "Satınalma Onayında"]},
     "icon": "fal fa-random"},
    {"label": "Planlanan Denetim", "list": "Denetimler", "type": "kpi_count",
     "filter": {"field": "Durum", "value": "Planlandı"}, "icon": "fal fa-search"},
    {"label": "Onay Bekleyen Belge", "list": "Belgeler", "type": "kpi_count",
     "filter": {"field": "Kırpart Onayı", "value": "Bekliyor"}, "icon": "fal fa-file-alt"},
    {"label": "Mutabık Olunmayan Cari", "list": "Cari Mutabakatlar", "type": "kpi_count",
     "filter": {"field": "Durum", "value": "Mutabık Değil"}, "icon": "fal fa-balance-scale"},
    {"label": "Toplam Hatalı Miktar", "list": "Kalite Vakaları", "type": "kpi", "aggregation": "sum",
     "value_field": "Hatalı Miktar", "icon": "fal fa-times-circle"},
    # Tedarikçi havuzu
    {"label": "Tedarikçiler — Lokasyon", "list": "Tedarikçiler", "type": "pie", "group_by": "Ülke"},
    {"label": "Tedarikçiler — Performans Sınıfı", "list": "Tedarikçiler", "type": "pie", "group_by": "Performans Sınıfı"},
    {"label": "Tedarikçiler — Ürün Çeşit Kodu", "list": "Tedarikçiler", "type": "bar", "group_by": "Ürün Çeşit Kodu"},
    {"label": "Tedarikçiler — Fiyat Segmenti", "list": "Tedarikçiler", "type": "pie", "group_by": "Fiyat Segmenti"},
    {"label": "Güncel Performans Puanı (Tedarikçi)", "list": "Tedarikçiler", "type": "bar",
     "group_by": "Tedarikçi Adı", "aggregation": "max", "value_field": "Güncel Performans Puanı"},
    # Sipariş & lojistik
    {"label": "Sipariş Teyit Durumu", "list": "Sipariş Kalemleri", "type": "pie", "group_by": "Teyit Durumu"},
    {"label": "Red Gerekçeleri", "list": "Sipariş Kalemleri", "type": "bar", "group_by": "Red Gerekçesi"},
    {"label": "Sevkiyat Durumu", "list": "Sevkiyatlar", "type": "pie", "group_by": "Durum"},
    {"label": "Aylık Sevkiyat Planı", "list": "Sevkiyatlar", "type": "bar", "group_by": "Planlanan Sevk Tarihi",
     "group_date_freq": "month"},
    {"label": "Cari Mutabakat Durumu", "list": "Cari Mutabakatlar", "type": "pie", "group_by": "Durum"},
    # Kalite
    {"label": "Kalite Vakaları — Kaynak", "list": "Kalite Vakaları", "type": "pie", "group_by": "Vaka Kaynağı"},
    {"label": "Kalite Vakaları — Hata Kategorisi", "list": "Kalite Vakaları", "type": "bar", "group_by": "Hata Kategorisi"},
    {"label": "Aylık Kalite Vakası Trendi", "list": "Kalite Vakaları", "type": "bar", "group_by": "Tespit Tarihi",
     "group_date_freq": "month", "sub_group_by": "Vaka Kaynağı"},
    {"label": "Tedarikçi Bazlı Hatalı Miktar", "list": "Kalite Vakaları", "type": "bar", "group_by": "Tedarikçi",
     "aggregation": "sum", "value_field": "Hatalı Miktar"},
    {"label": "8D Durumu", "list": "Kalite Vakaları", "type": "bar", "group_by": "8D Durumu"},
    {"label": "Maliyet Onay Durumu", "list": "Kalite Vakaları", "type": "pie", "group_by": "Maliyet Onay Durumu"},
    {"label": "Aksiyonlar — Durum", "list": "Aksiyonlar", "type": "pie", "group_by": "Durum"},
    {"label": "Aksiyonlar — Kaynak", "list": "Aksiyonlar", "type": "bar", "group_by": "Kaynak Tipi",
     "sub_group_by": "Durum"},
    {"label": "Tedarikçi Bazlı Açık Aksiyon", "list": "Aksiyonlar", "type": "bar", "group_by": "Tedarikçi",
     "aggregation": "sum", "value_field": "Açık (1/0)"},
    {"label": "Denetim Durumu", "list": "Denetimler", "type": "pie", "group_by": "Durum"},
    {"label": "Aylık Denetim Planı", "list": "Denetimler", "type": "bar", "group_by": "Planlanan Tarih",
     "group_date_freq": "month"},
    {"label": "PPAP Talepleri — Durum", "list": "PPAP Talepleri", "type": "pie", "group_by": "Durum"},
    {"label": "Sapma Talepleri — Durum", "list": "Sapma Talepleri", "type": "pie", "group_by": "Durum"},
    {"label": "Belgeler — Tür", "list": "Belgeler", "type": "bar", "group_by": "Belge Türü"},
    {"label": "Varlıklar — Durum", "list": "Varlıklar (Kalıp / Ekipman)", "type": "pie", "group_by": "Durum"},
    {"label": "Kırpart Onayı Bekleyen Kontaklar", "list": "Kontaklar & Portal Kullanıcıları", "type": "kpi_count",
     "filter": {"field": "Kırpart Onay Durumu", "value": "Talep Edildi"}, "icon": "fal fa-user-clock"},
]

POST_REPORTS = [
    {"label": "Toplam Kalitesizlik Maliyeti", "list": "Kalite Vakaları", "type": "kpi", "aggregation": "sum",
     "value_field": "Toplam Kalitesizlik Maliyeti", "icon": "fal fa-money-bill-wave"},
    {"label": "Tedarikçi Bazlı Kalitesizlik Maliyeti", "list": "Kalite Vakaları", "type": "bar",
     "group_by": "Tedarikçi", "aggregation": "sum", "value_field": "Toplam Kalitesizlik Maliyeti"},
    {"label": "Ort. 8D Kapanış Süresi (gün)", "list": "Kalite Vakaları", "type": "kpi", "aggregation": "avg",
     "value_field": "8D Kapanış Süresi (gün)", "icon": "fal fa-stopwatch"},
    {"label": "Toplam Sipariş Bakiyesi", "list": "Sipariş Kalemleri", "type": "kpi", "aggregation": "sum",
     "value_field": "Bakiye", "icon": "fal fa-boxes"},
    {"label": "Tedarikçi Bazlı Sipariş Bakiyesi", "list": "Sipariş Kalemleri", "type": "bar", "group_by": "Tedarikçi",
     "aggregation": "sum", "value_field": "Bakiye"},
    {"label": "Yoldaki Miktar (Tedarikçi)", "list": "Sipariş Kalemleri", "type": "bar", "group_by": "Tedarikçi",
     "aggregation": "sum", "value_field": "Yoldaki Miktar"},
    {"label": "Zamanında Teslim Oranı (OTD)", "list": "Sevkiyatlar", "type": "kpi", "aggregation": "avg",
     "value_field": "Zamanında (1/0)", "icon": "fal fa-shipping-fast"},
    {"label": "Tedarikçi Bazlı Ort. Gecikme (gün)", "list": "Sevkiyatlar", "type": "bar", "group_by": "Tedarikçi",
     "aggregation": "avg", "value_field": "Gecikme (gün)"},
    {"label": "Tedarikçi Bazlı Denetim Başarısı %", "list": "Denetimler", "type": "bar", "group_by": "Tedarikçi",
     "aggregation": "avg", "value_field": "Başarı %"},
    {"label": "Skor Kartı — Toplam Puan", "list": "Performans Kartları", "type": "bar", "group_by": "Tedarikçi",
     "aggregation": "avg", "value_field": "Toplam Puan"},
    {"label": "Skor Kartı — PPM Gerçekleşen", "list": "Performans Kartları", "type": "bar", "group_by": "Tedarikçi",
     "aggregation": "avg", "value_field": "PPM Gerçekleşen"},
    {"label": "KPI Puanları Trendi", "list": "Performans Kartları", "type": "bar", "group_by": "Dönem Bitişi",
     "group_date_freq": "month", "aggregation": "avg", "value_field": "Toplam Puan"},
    {"label": "Tedarikçi Skor Kartı Tablosu", "list": "Performans Kartları", "type": "table",
     "icon": "fal fa-table"},
    {"label": "Kalıp Kalan Ömür %", "list": "Varlıklar (Kalıp / Ekipman)", "type": "bar",
     "group_by": "Demirbaş No", "aggregation": "min", "value_field": "Kalan Ömür %"},
]

# ═══════════════════════════════════════════════════════════════════════════════
#  SEED — referans veriler
# ═══════════════════════════════════════════════════════════════════════════════
PPAP_BELGELER = [
    # (ad, EN, seviyeler)
    ("PSW (Parça Sunum Garantisi)", "Part Submission Warrant", {1, 2, 3, 4, 5}),
    ("Tasarım Kayıtları", "Design Records", {2, 3, 4, 5}),
    ("Mühendislik Değişikliği Dokümanları", "Engineering Change Documents", {2, 3, 4, 5}),
    ("Müşteri Mühendislik Onayı", "Customer Engineering Approval", {3, 4, 5}),
    ("DFMEA", "Design FMEA", {3, 4, 5}),
    ("Proses Akış Şeması", "Process Flow Diagram", {3, 4, 5}),
    ("PFMEA", "Process FMEA", {3, 4, 5}),
    ("Kontrol Planı", "Control Plan", {3, 4, 5}),
    ("MSA", "Measurement System Analysis", {3, 4, 5}),
    ("Boyutsal Sonuçlar", "Dimensional Results", {2, 3, 4, 5}),
    ("Malzeme-Performans Test Sonuçları", "Material / Performance Test Results", {2, 3, 4, 5}),
    ("İlk Proses Çalışmaları", "Initial Process Studies", {3, 4, 5}),
    ("Akredite Lab. Dokümanları", "Qualified Laboratory Documentation", {3, 4, 5}),
    ("Görünüş Onay Raporu", "Appearance Approval Report", {1, 2, 3, 4, 5}),
    ("Numune Parça", "Sample Production Parts", {2, 3, 4, 5}),
    ("Master Numune", "Master Sample", {5}),
    ("Kontrol Aparatları", "Checking Aids", {5}),
    ("Müşteriye Özel Gereklilikler", "Customer-Specific Requirements", {2, 3, 4, 5}),
]

SEED = {
    "Denetim Tipleri": [
        {"Name": n, "Denetim Tipi (EN)": en, "Periyot (gün)": p, "A Sınıfı Alt Sınırı %": 90,
         "B Sınıfı Alt Sınırı %": 75, "Aktif": True, "Açıklama": a}
        for n, en, p, a in [
            ("Süreç Denetimi", "Process Audit", 365, "VDA 6.3 bazlı proses denetimi"),
            ("Ürün Denetimi", "Product Audit", 180, "Ürün uygunluk denetimi"),
            ("Sistem Denetimi", "System Audit", 730, "IATF 16949 / ISO 9001 kalite sistemi"),
            ("Ön Değerlendirme", "Pre-Assessment", 0, "Aday tedarikçi değerlendirmesi"),
            ("Sosyal Uygunluk", "Social Compliance", 730, "İSG, çevre ve sosyal uygunluk"),
        ]
    ],
    "PPAP Belge Tipleri": [
        {"Name": n, "Belge Tipi (EN)": en, "Sıra": i + 1, "PLM'e Aktarılsın": True,
         **{f"Seviye {s} Zorunlu": s in lv for s in range(1, 6)}}
        for i, (n, en, lv) in enumerate(PPAP_BELGELER)
    ],
    "Denetim Soruları": [
        {"Name": f"SÜR-0{i}", "Soru Kodu": f"SÜR-0{i}", "Bölüm": b, "Soru": s, "Maksimum Puan": 10, "Ağırlık": w,
         "Sıra": i, "Aktif": True, "Denetim Tipi": "Süreç Denetimi"}
        for i, (b, s, w) in enumerate([
            ("Proses Kontrol", "Kontrol planı güncel ve sahada uygulanıyor mu?", 3),
            ("Proses Kontrol", "Proses parametreleri kayıt altına alınıyor mu?", 2),
            ("Ölçüm", "Ölçüm cihazlarının kalibrasyonları geçerli mi?", 2),
            ("İzlenebilirlik", "Lot bazlı izlenebilirlik sağlanıyor mu?", 3),
            ("Uygunsuz Ürün", "Uygunsuz ürün ayrıştırma ve etiketleme yapılıyor mu?", 2),
            ("Ambalaj & Sevkiyat", "Ambalaj ve etiketleme Kırpart şartnamesine uygun mu?", 1),
        ], start=1)
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
SPEC = {
    "name": "Kırpart Tedarikçi Portalı",
    "icon": "fas fa-truck-loading",
    "color": "#4e86f7",
    "description": "Tedarik zinciri modülü: sipariş & teyit, ASN/sevkiyat, envanter, cari mutabakat, 8D, denetim, "
                   "PPAP, sapma, aksiyon, belge/sertifika, varlık ve tedarikçi performans yönetimi.",
    "folders": [
        {"name": "A. Ana Veri", "lists": [TEDARIKCILER, KONTAKLAR, MALZEMELER, TM_KARTLARI]},
        {"name": "B. Sipariş & Lojistik", "lists": [SIPARISLER, SIPARIS_KALEMLERI, SEVKIYATLAR, SEVKIYAT_KALEMLERI,
                                                   ENVANTER, CARI]},
        {"name": "C. Kalite", "lists": [KALITE_VAKALARI, DENETIM_TIPLERI, DENETIM_SORULARI, DENETIMLER,
                                        DENETIM_CEVAPLARI, PPAP_BELGE_TIPLERI, PPAP_TALEPLERI, PPAP_DOKUMANLARI,
                                        SAPMA_TALEPLERI, SAPMALI_LOTLAR, AKSIYONLAR]},
        {"name": "D. Belge, Varlık, İletişim", "lists": [BELGELER, ZIYARETLER, VARLIKLAR, BAKIM]},
        {"name": "E. Performans", "lists": [PERFORMANS]},
    ],
    "lists": [],
    "reports": REPORTS,
    "automations": AUTOMATIONS,
    "post_automations": POST_AUTOMATIONS,
    "post_reports": POST_REPORTS,
    "seed": SEED,
}
