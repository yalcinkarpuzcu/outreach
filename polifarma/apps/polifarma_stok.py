"""
Polifarma PoC — Uygulama 2: Numune ve Hammadde Stok  (BUILD SIRASI: 2)

Bağımlılık: "Ar-Ge Proje Takibi" önce kurulmuş olmalı (Ar-Ge Projeleri, Formülasyon Denemeleri'ne cross-app LINK).

Stok mantığı (FR-2.1 — manuel stok alanı yok):
  • Her hareket "Giriş Miktarı" (giriş/iade/sayım fazlası) VEYA "Çıkış Miktarı" (çıkış/imha/sayım eksiği) taşır.
  • Upgrade script: Stok Hareketleri."Stok Etkisi" = Giriş − Çıkış (formül)
                   Lotlar."Kalan Miktar"          = SUM(Stok Etkisi)   (rollup)
                   Malzeme Kartları."Toplam Stok" = SUM(Lot.Kalan Miktar) (rollup)
  • Lot açıldığında giriş hareketi otomatik oluşur; talep onaylandığında ve formül bileşeni
    girildiğinde çıkış hareketi otomatik oluşur.
"""
from workiom.constants import F, LT, V

PROJE_APP = "Ar-Ge Proje Takibi"

BIRIM = {"options": ["g", "kg", "mg", "mL", "L", "Adet"],
         "colors":  ["#8ed6ff", "#4e86f7", "#5bd7d0", "#7942e3", "#ffa979", "#f5c044"]}

SPEC = {
    "name": "Numune ve Hammadde Stok",
    "icon": "fas fa-boxes",
    "color": "#5bd7d0",
    "description": "Ar-Ge etken madde, eksipiyan, referans ürün ve numunelerin lot bazında giriş/çıkış, kalan miktar ve SKT takibi",

    "folders": [
        # ─────────────────────────────────────────────────────────────
        # TANIMLAR
        # ─────────────────────────────────────────────────────────────
        {
            "name": "Tanımlar",
            "lists": [
                {
                    "name": "Tedarikçiler",
                    "icon": "fas fa-truck",
                    "fields": [
                        {"name": "Tedarikçi Adı",      "type": F.TEXT,  "required": True},
                        {"name": "İletişim Kişisi",    "type": F.TEXT},
                        {"name": "E-Posta",            "type": F.EMAIL},
                        {"name": "Telefon",            "type": F.PHONE},
                        {"name": "Onaylı Tedarikçi",   "type": F.BOOLEAN},
                        {"name": "Notlar",             "type": F.TEXT,  "multiline": True},
                        # "Sağlanan Malzemeler" → upgrade script back-link
                    ],
                    "views": [
                        {"name": "Tüm Tedarikçiler",   "type": V.GRID},
                        {"name": "Onaylı Tedarikçiler", "type": V.GRID,
                         "filter": {"field": "Onaylı Tedarikçi", "value": True}},
                    ],
                    "forms": [],
                },
                {
                    "name": "Malzeme Kartları",
                    "icon": "fas fa-cubes",
                    "fields": [
                        {"name": "Malzeme Kodu",          "type": F.TEXT,  "required": True},
                        {"name": "Malzeme Adı",           "type": F.TEXT,  "required": True},
                        {"name": "Tip",                   "type": F.SELECT,
                         "options": ["Etken Madde", "Eksipiyan", "Referans Ürün", "Standart Madde", "Çözücü", "Ambalaj"],
                         "colors":  ["#ea346f", "#4e86f7", "#7942e3", "#f5c044", "#5bd7d0", "#ffa979"]},
                        {"name": "Birim",                 "type": F.SELECT, **BIRIM},
                        {"name": "Depolama Koşulu",       "type": F.SELECT,
                         "options": ["Oda Sıcaklığı (15-25°C)", "Buzdolabı (2-8°C)", "Dondurucu (-20°C)", "Işıktan Korunmalı", "Nemden Korunmalı"],
                         "colors":  ["#5bd77e", "#8ed6ff", "#4e86f7", "#f5c044", "#5bd7d0"]},
                        {"name": "Kritik Stok Seviyesi",  "type": F.NUMBER},
                        {"name": "Stok Sorumlusu",        "type": F.USER},
                        {"name": "Notlar",                "type": F.TEXT,  "multiline": True},
                        {"name": "Tedarikçi",             "type": F.LINK,  "target_list": "Tedarikçiler", "back_link": "Sağlanan Malzemeler"},
                        # "Lotlar", "Toplam Stok", "Kritik Seviye Altında" → upgrade script
                    ],
                    "views": [
                        {"name": "Tüm Malzeme Kartları", "type": V.GRID},
                        {"name": "Tipe Göre",            "type": V.KANBAN, "group_by": "Tip"},
                        # "Kritik Seviyedeki Malzemeler" görünümü → polifarma_stok_faz2.py
                    ],
                    "forms": [],
                },
            ],
        },

        # ─────────────────────────────────────────────────────────────
        # STOK
        # ─────────────────────────────────────────────────────────────
        {
            "name": "Stok",
            "lists": [
                {
                    "name": "Lotlar",
                    "icon": "fas fa-barcode",
                    "fields": [
                        {"name": "Lot No",               "type": F.TEXT,   "required": True},
                        {"name": "Tedarikçi Lot No",     "type": F.TEXT},
                        {"name": "Giriş Tarihi",         "type": F.DATE},
                        {"name": "Üretim Tarihi",        "type": F.DATE},
                        {"name": "SKT / Retest Tarihi",  "type": F.DATE},
                        {"name": "Tarih Tipi",           "type": F.SELECT,
                         "options": ["Son Kullanma", "Retest"],
                         "colors":  ["#ea346f", "#f5c044"]},
                        {"name": "Giriş Miktarı",        "type": F.NUMBER},
                        {"name": "Birim Maliyet",        "type": F.CURRENCY},
                        {"name": "Raf / Lokasyon",       "type": F.TEXT},
                        {"name": "CoA",                  "type": F.FILE},
                        {"name": "Lot Durumu",           "type": F.SELECT,
                         "options": ["Karantinada", "Onaylı", "Ret", "Kullanılamaz (SKT/Retest)"],
                         "colors":  ["#f5c044", "#5bd77e", "#ea346f", "#ff86c7"]},
                        {"name": "SKT Yaklaşıyor",       "type": F.BOOLEAN},
                        {"name": "Stok Sorumlusu",       "type": F.USER},
                        {"name": "Malzeme",              "type": F.LINK,   "target_list": "Malzeme Kartları", "back_link": "Lotlar"},
                        {"name": "Tedarikçi",            "type": F.LINK,   "target_list": "Tedarikçiler"},
                        {"name": "Birim",                "type": F.LOOKUP, "via": "Malzeme", "lookup_field": "Birim"},
                        # "Hareketler", "Kalan Miktar", "SKT'ye Kalan Gün", "QR Kod" → upgrade script
                    ],
                    "views": [
                        {"name": "Tüm Lotlar",          "type": V.GRID},
                        {"name": "Lot Durumuna Göre",   "type": V.KANBAN,   "group_by": "Lot Durumu"},
                        {"name": "SKT Takvimi",         "type": V.CALENDAR, "date_field": "SKT / Retest Tarihi"},
                        {"name": "Karantinadaki Lotlar", "type": V.GRID,
                         "filter": {"field": "Lot Durumu", "value": "Karantinada"}},
                        {"name": "30 Gün İçinde SKT Dolan Lotlar", "type": V.GRID,
                         "filter": {"field": "SKT Yaklaşıyor", "value": True}},
                    ],
                    "layout": {
                        "tabs": [
                            {"name": "Lot Bilgileri", "fields": [
                                "Malzeme", "Lot No", "Tedarikçi", "Tedarikçi Lot No",
                                "Lot Durumu", "Raf / Lokasyon", "Stok Sorumlusu",
                            ]},
                            {"name": "Tarihler", "fields": [
                                "Giriş Tarihi", "Üretim Tarihi", "SKT / Retest Tarihi", "Tarih Tipi", "SKT Yaklaşıyor",
                            ]},
                            {"name": "Miktar ve Belge", "fields": ["Giriş Miktarı", "Birim Maliyet", "CoA"]},
                        ]
                    },
                    "forms": [
                        {"name": "Lot Girişi",
                         "fields": ["Malzeme", "Lot No", "Tedarikçi", "Tedarikçi Lot No", "Giriş Tarihi",
                                    "Üretim Tarihi", "SKT / Retest Tarihi", "Tarih Tipi", "Giriş Miktarı",
                                    "Birim Maliyet", "Raf / Lokasyon", "CoA"]},
                    ],
                },

                {
                    "name": "Stok Hareketleri",
                    "icon": "fas fa-exchange-alt",
                    "fields": [
                        {"name": "Hareket No",      "type": F.AUTONUMBER},
                        {"name": "Tarih",           "type": F.DATE},
                        {"name": "Hareket Tipi",    "type": F.SELECT,
                         "options": ["Giriş", "Çıkış", "İade", "İmha", "Sayım Fazlası", "Sayım Eksiği"],
                         "colors":  ["#5bd77e", "#4e86f7", "#5bd7d0", "#ea346f", "#8ed6ff", "#ffa979"]},
                        {"name": "Giriş Miktarı",   "type": F.NUMBER,
                         "validation": [{"if": "{{Giriş Miktarı}} < 0", "message": "Miktar negatif olamaz."}]},
                        {"name": "Çıkış Miktarı",   "type": F.NUMBER,
                         "validation": [{"if": "{{Çıkış Miktarı}} < 0", "message": "Miktar negatif olamaz."}],
                         "required_when": "{{Hareket Tipi}} = 'Çıkış' or {{Hareket Tipi}} = 'İmha' or {{Hareket Tipi}} = 'Sayım Eksiği'"},
                        {"name": "Yapan Kişi",      "type": F.USER},
                        {"name": "Açıklama",        "type": F.TEXT, "multiline": True},
                        {"name": "Lot",             "type": F.LINK, "target_list": "Lotlar", "back_link": "Hareketler"},
                        {"name": "İlgili Proje",    "type": F.LINK, "target_app": PROJE_APP, "target_list": "Ar-Ge Projeleri", "back_link": "Stok Tüketimi"},
                        {"name": "İlgili Deneme",   "type": F.LINK, "target_app": PROJE_APP, "target_list": "Formülasyon Denemeleri"},
                        {"name": "Malzeme",         "type": F.LOOKUP, "via": "Lot", "lookup_field": "Malzeme"},
                        {"name": "Lot Durumu",      "type": F.LOOKUP, "via": "Lot", "lookup_field": "Lot Durumu"},
                        {"name": "Birim Maliyet",   "type": F.LOOKUP, "via": "Lot", "lookup_field": "Birim Maliyet"},
                        # "Stok Etkisi", "Tüketim Maliyeti" → upgrade script (formül)
                    ],
                    "views": [
                        {"name": "Tüm Stok Hareketleri", "type": V.GRID},
                        {"name": "Hareket Tipine Göre",  "type": V.KANBAN,   "group_by": "Hareket Tipi"},
                        {"name": "Hareket Takvimi",      "type": V.CALENDAR, "date_field": "Tarih"},
                        {"name": "Çıkışlar",             "type": V.GRID,
                         "filter": {"field": "Hareket Tipi", "value": ["Çıkış", "İmha"]}},
                    ],
                    "layout": {
                        "tabs": [
                            {"name": "Hareket", "fields": [
                                "Tarih", "Hareket Tipi", "Lot", "Giriş Miktarı", "Çıkış Miktarı",
                                "İlgili Proje", "İlgili Deneme", "Yapan Kişi", "Açıklama",
                            ]},
                        ]
                    },
                    "forms": [
                        {"name": "Stok Çıkışı",
                         "fields": ["Tarih", "Hareket Tipi", "Lot", "Çıkış Miktarı",
                                    "İlgili Proje", "İlgili Deneme", "Yapan Kişi", "Açıklama"]},
                    ],
                },

                {
                    "name": "Formül Bileşenleri",
                    "icon": "fas fa-mortar-pestle",
                    "fields": [
                        {"name": "Bileşen No",      "type": F.AUTONUMBER},
                        {"name": "Fonksiyon",       "type": F.SELECT,
                         "options": ["Etken Madde", "Dolgu", "Bağlayıcı", "Dağıtıcı", "Kaydırıcı", "Kaplama", "Çözücü", "Diğer"],
                         "colors":  ["#ea346f", "#4e86f7", "#7942e3", "#5bd7d0", "#f5c044", "#ffa979", "#8ed6ff", "#ff86c7"]},
                        {"name": "Miktar",          "type": F.NUMBER, "required": True},
                        {"name": "Formüldeki Oran (%)", "type": F.NUMBER},
                        {"name": "Not",             "type": F.TEXT},
                        {"name": "Deneme",          "type": F.LINK, "target_app": PROJE_APP, "target_list": "Formülasyon Denemeleri", "back_link": "Formül Bileşenleri"},
                        {"name": "İlgili Proje",    "type": F.LINK, "target_app": PROJE_APP, "target_list": "Ar-Ge Projeleri"},
                        {"name": "Lot",             "type": F.LINK, "target_list": "Lotlar"},
                        {"name": "Malzeme",         "type": F.LOOKUP, "via": "Lot", "lookup_field": "Malzeme"},
                        {"name": "Birim",           "type": F.LOOKUP, "via": "Lot", "lookup_field": "Birim"},
                    ],
                    "views": [
                        {"name": "Tüm Formül Bileşenleri", "type": V.GRID},
                        {"name": "Fonksiyona Göre",       "type": V.KANBAN, "group_by": "Fonksiyon"},
                    ],
                    "forms": [],
                },

                {
                    "name": "Numuneler",
                    "icon": "fas fa-prescription-bottle",
                    "fields": [
                        {"name": "Numune No",            "type": F.AUTONUMBER},
                        {"name": "Numune Adı",           "type": F.TEXT, "required": True},
                        {"name": "Tip",                  "type": F.SELECT,
                         "options": ["Gelen Numune — Tedarikçi", "Gelen Numune — Referans Ürün", "Üretilen Numune — Deneme Batch'i"],
                         "colors":  ["#4e86f7", "#7942e3", "#5bd7d0"]},
                        {"name": "Miktar",               "type": F.NUMBER},
                        {"name": "Birim",                "type": F.SELECT, **BIRIM},
                        {"name": "Saklama Koşulu",       "type": F.SELECT,
                         "options": ["Oda Sıcaklığı (15-25°C)", "Buzdolabı (2-8°C)", "Dondurucu (-20°C)",
                                     "Stabilite Kabini 25/60", "Stabilite Kabini 30/65", "Stabilite Kabini 40/75"],
                         "colors":  ["#5bd77e", "#8ed6ff", "#4e86f7", "#5bd7d0", "#f5c044", "#ea346f"]},
                        {"name": "Lokasyon",             "type": F.TEXT},
                        {"name": "Saklama Bitiş Tarihi", "type": F.DATE},
                        {"name": "Durum",                "type": F.SELECT,
                         "options": ["Saklamada", "Analizde", "Karar Bekliyor", "Tüketildi", "İmha"],
                         "colors":  ["#5bd77e", "#4e86f7", "#f5c044", "#5bd7d0", "#ea346f"]},
                        {"name": "Sorumlu",              "type": F.USER},
                        {"name": "Ekler",                "type": F.FILE},
                        {"name": "Tedarikçi",            "type": F.LINK, "target_list": "Tedarikçiler"},
                        {"name": "Malzeme",              "type": F.LINK, "target_list": "Malzeme Kartları"},
                        {"name": "İlgili Proje",         "type": F.LINK, "target_app": PROJE_APP, "target_list": "Ar-Ge Projeleri", "back_link": "Numuneler"},
                        {"name": "İlgili Deneme",        "type": F.LINK, "target_app": PROJE_APP, "target_list": "Formülasyon Denemeleri", "back_link": "Üretilen Numuneler"},
                        # "QR Kod" → upgrade script
                    ],
                    "views": [
                        {"name": "Tüm Numuneler",       "type": V.GRID},
                        {"name": "Duruma Göre",         "type": V.KANBAN,   "group_by": "Durum"},
                        {"name": "Tipe Göre",           "type": V.KANBAN,   "group_by": "Tip"},
                        {"name": "Saklama Bitiş Takvimi", "type": V.CALENDAR, "date_field": "Saklama Bitiş Tarihi"},
                        {"name": "Karar Bekleyenler",   "type": V.GRID,
                         "filter": {"field": "Durum", "value": "Karar Bekliyor"}},
                    ],
                    "forms": [],
                },
            ],
        },

        # ─────────────────────────────────────────────────────────────
        # TALEP VE GÖREVLER
        # ─────────────────────────────────────────────────────────────
        {
            "name": "Talep ve Görevler",
            "lists": [
                {
                    "name": "Malzeme ve Numune Talepleri",
                    "icon": "fas fa-hand-holding-medical",
                    "list_type": LT.PROCESS,
                    "status_options": [
                        {"label": "Taslak",         "color": "#8ed6ff", "closed": False},
                        {"label": "Onay Bekliyor",  "color": "#f5c044", "closed": False},
                        {"label": "Onaylandı",      "color": "#4e86f7", "closed": False},
                        {"label": "Teslim Edildi",  "color": "#5bd77e", "closed": True},
                        {"label": "Reddedildi",     "color": "#ea346f", "closed": True},
                    ],
                    "default_status": "Taslak",
                    "fields": [
                        {"name": "Talep No",          "type": F.AUTONUMBER},
                        {"name": "Talep Tipi",        "type": F.SELECT,
                         "options": ["Malzeme", "Numune"],
                         "colors":  ["#4e86f7", "#7942e3"]},
                        {"name": "Talep Eden",        "type": F.USER},
                        {"name": "İstenen Miktar",    "type": F.NUMBER, "required": True},
                        {"name": "Gerekçe",           "type": F.TEXT,   "multiline": True},
                        {"name": "İstenen Tarih",     "type": F.DATE},
                        {"name": "Teslim Tarihi",     "type": F.DATE},
                        {"name": "Onaylayıcı (Stok Sorumlusu)", "type": F.USER},
                        {"name": "Red Gerekçesi",     "type": F.TEXT,   "multiline": True},
                        {"name": "İlgili Proje",      "type": F.LINK, "target_app": PROJE_APP, "target_list": "Ar-Ge Projeleri", "back_link": "Malzeme Talepleri"},
                        {"name": "İlgili Deneme",     "type": F.LINK, "target_app": PROJE_APP, "target_list": "Formülasyon Denemeleri"},
                        {"name": "Malzeme",           "type": F.LINK, "target_list": "Malzeme Kartları"},
                        {"name": "Lot",               "type": F.LINK, "target_list": "Lotlar"},
                        {"name": "Numune",            "type": F.LINK, "target_list": "Numuneler"},
                    ],
                    "views": [
                        {"name": "Tüm Talepler",       "type": V.GRID},
                        {"name": "Talep Tipine Göre",  "type": V.KANBAN,   "group_by": "Talep Tipi"},
                        {"name": "Teslim Takvimi",     "type": V.CALENDAR, "date_field": "İstenen Tarih"},
                        {"name": "Bekleyen Talepler",  "type": V.GRID,
                         "filter": {"field": "Status", "value": ["Onay Bekliyor", "Onaylandı"]}},
                    ],
                    "layout": {
                        "tabs": [
                            {"name": "Talep", "fields": [
                                "Talep Tipi", "Talep Eden", "İlgili Proje", "İlgili Deneme",
                                "Malzeme", "Numune", "İstenen Miktar", "İstenen Tarih", "Gerekçe",
                            ]},
                            {"name": "Onay ve Teslim", "fields": [
                                "Onaylayıcı (Stok Sorumlusu)", "Lot", "Teslim Tarihi", "Red Gerekçesi",
                            ]},
                        ]
                    },
                    "forms": [
                        {"name": "Malzeme / Numune Talebi",
                         "fields": ["Talep Tipi", "İlgili Proje", "İlgili Deneme", "Malzeme", "Numune",
                                    "İstenen Miktar", "İstenen Tarih", "Gerekçe"]},
                    ],
                },

                {
                    "name": "Depo Görevleri",
                    "icon": "fas fa-clipboard-check",
                    "list_type": LT.PROCESS,
                    "status_options": [
                        {"label": "Açık",          "color": "#8ed6ff", "closed": False},
                        {"label": "Devam Ediyor",  "color": "#f5c044", "closed": False},
                        {"label": "Tamamlandı",    "color": "#5bd77e", "closed": True},
                        {"label": "İptal",         "color": "#ff86c7", "closed": True},
                    ],
                    "default_status": "Açık",
                    "fields": [
                        {"name": "Görev No",          "type": F.AUTONUMBER},
                        {"name": "Başlık",            "type": F.TEXT, "required": True},
                        {"name": "Görev Tipi",        "type": F.SELECT,
                         "options": ["Numune İmha / Uzatma Kararı", "Lot SKT Kontrolü", "Sayım", "Diğer"],
                         "colors":  ["#ffa979", "#ea346f", "#4e86f7", "#8ed6ff"]},
                        {"name": "Atanan",            "type": F.USER},
                        {"name": "Son Tarih",         "type": F.DATE},
                        {"name": "Karar",             "type": F.SELECT,
                         "options": ["İmha", "Saklama Süresi Uzatıldı", "Analize Gönderildi"],
                         "colors":  ["#ea346f", "#5bd77e", "#4e86f7"]},
                        {"name": "Yeni Saklama Bitiş Tarihi", "type": F.DATE},
                        {"name": "Not",               "type": F.TEXT, "multiline": True},
                        {"name": "Numune",            "type": F.LINK, "target_list": "Numuneler", "back_link": "Depo Görevleri"},
                        {"name": "Lot",               "type": F.LINK, "target_list": "Lotlar"},
                    ],
                    "views": [
                        {"name": "Tüm Depo Görevleri", "type": V.GRID},
                        {"name": "Görev Tipine Göre",  "type": V.KANBAN,   "group_by": "Görev Tipi"},
                        {"name": "Görev Takvimi",      "type": V.CALENDAR, "date_field": "Son Tarih"},
                    ],
                    "forms": [],
                },
            ],
        },
    ],

    "reports": [
        {"label": "Bekleyen Talepler",        "list": "Malzeme ve Numune Talepleri", "type": "kpi_count",
         "filter": {"field": "Status", "value": "Onay Bekliyor"}, "icon": "fal fa-inbox", "pin": True},
        {"label": "30 Gün İçinde SKT Dolan Lotlar", "list": "Lotlar", "type": "kpi_count",
         "filter": {"field": "SKT Yaklaşıyor", "value": True}, "icon": "fal fa-hourglass-half", "pin": True},
        {"label": "Karantinadaki Lotlar",     "list": "Lotlar", "type": "kpi_count",
         "filter": {"field": "Lot Durumu", "value": "Karantinada"}, "icon": "fal fa-lock", "pin": True},
        {"label": "Lot Durum Dağılımı",       "list": "Lotlar", "type": "pie",
         "group_by": "Lot Durumu", "aggregation": "count", "icon": "fal fa-chart-pie", "pin": True},
        {"label": "Hareket Tipine Göre",      "list": "Stok Hareketleri", "type": "bar",
         "group_by": "Hareket Tipi", "aggregation": "count", "icon": "fal fa-exchange-alt", "pin": True},
        {"label": "Numune Durumları",         "list": "Numuneler", "type": "bar",
         "group_by": "Durum", "aggregation": "count", "icon": "fal fa-vials", "pin": True},
    ],

    "automations": [
        # FR-2.1 — Lot girişi = giriş hareketi (kalan miktar hareketlerden hesaplanır)
        {
            "name": "Lot oluşturuldu → otomatik giriş hareketi",
            "trigger": {"type": "record_created", "list": "Lotlar"},
            "actions": [
                {"type": "update_record", "fields": {"Lot Durumu": "Karantinada"}},
                {
                    "type": "create_record",
                    "list": "Stok Hareketleri",
                    "fields": {
                        "Tarih":          "formula:Today()",
                        "Hareket Tipi":   "Giriş",
                        "Giriş Miktarı":  "trigger:Giriş Miktarı",
                        "Lot":            "trigger:_id",
                        "Açıklama":       "Lot girişi (otomatik)",
                    },
                },
            ],
        },
        # FR-2.3 — SKT/Retest 30 gün kala uyarı
        {
            "name": "SKT / Retest tarihine 30 gün kala uyar",
            "trigger": {"type": "time_trigger", "list": "Lotlar", "date_field": "SKT / Retest Tarihi", "offset": -30},
            "actions": [
                {"type": "update_record", "fields": {"SKT Yaklaşıyor": "true"}},
                {"type": "notify", "to_field": "Stok Sorumlusu",
                 "message": "SKT/Retest 30 gün içinde doluyor: {{Malzeme}} — Lot {{Lot No}} — {{SKT / Retest Tarihi}}"},
            ],
        },
        # FR-2.3 — Tarihi geçen lot kullanılamaz
        {
            "name": "SKT / Retest tarihi geldi → Kullanılamaz",
            "trigger": {"type": "time_trigger", "list": "Lotlar", "date_field": "SKT / Retest Tarihi", "offset": 0},
            "actions": [
                {"type": "update_record", "fields": {"Lot Durumu": "Kullanılamaz (SKT/Retest)"}},
                {"type": "notify", "to_field": "Stok Sorumlusu",
                 "message": "Lot kullanılamaz olarak işaretlendi (SKT/Retest): {{Malzeme}} — Lot {{Lot No}}"},
            ],
        },
        # FR-2.4 — Karantina/ret/kullanılamaz lottan çıkış (validation'a ek emniyet: uyarı)
        {
            "name": "Onaysız lottan çıkış girildi → uyarı",
            "trigger": {"type": "record_created", "list": "Stok Hareketleri"},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Çıkış Miktarı}} > 0 and {{Lot Durumu}} != 'Onaylı' and isNotBlank({{Yapan Kişi}})",
                    "then": [
                        {"type": "notify", "to_field": "Yapan Kişi",
                         "message": "UYARI: {{Lot}} lotu onaylı değil ({{Lot Durumu}}). Çıkış hareketi #{{Hareket No}} geçersiz — stok sorumlusuyla görüşün."},
                    ],
                },
            ],
        },
        # FR-2.6 — Talep onayı ve otomatik çıkış hareketi
        {
            "name": "Talep onaya gönderildi → Stok Sorumlusu onayı",
            "trigger": {"type": "record_updated", "list": "Malzeme ve Numune Talepleri", "watch_field": "Status"},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Status}} = 'Onay Bekliyor'",
                    "then": [
                        {
                            "type": "approval",
                            "title":    "Malzeme / Numune Talebi",
                            "subtitle": "Talep #{{Talep No}} ({{Talep Tipi}}) — {{Talep Eden}} — {{İstenen Miktar}} — Proje: {{İlgili Proje}}",
                            "approver": "field:Onaylayıcı (Stok Sorumlusu)",
                            "timeout_days": 2,
                            "require_rejection_message": True,
                            "on_approve": [
                                {"type": "update_record", "fields": {"Status": "Onaylandı"}},
                                {
                                    "type": "condition",
                                    "if":   "{{Talep Tipi}} = 'Malzeme' and isNotBlank({{Lot}})",
                                    "then": [
                                        {
                                            "type": "create_record",
                                            "list": "Stok Hareketleri",
                                            "fields": {
                                                "Tarih":          "formula:Today()",
                                                "Hareket Tipi":   "Çıkış",
                                                "Çıkış Miktarı":  "trigger:İstenen Miktar",
                                                "Lot":            "trigger:Lot",
                                                "İlgili Proje":   "trigger:İlgili Proje",
                                                "İlgili Deneme":  "trigger:İlgili Deneme",
                                                "Yapan Kişi":     "trigger:Onaylayıcı (Stok Sorumlusu)",
                                                "Açıklama":       "Talep onayı ile otomatik çıkış",
                                            },
                                        },
                                    ],
                                },
                                {"type": "notify", "to_field": "Talep Eden",
                                 "message": "Talebiniz onaylandı: Talep #{{Talep No}} ({{Talep Tipi}}) — {{İstenen Miktar}}"},
                            ],
                            "on_reject": [
                                {"type": "update_record", "fields": {"Status": "Reddedildi"}},
                                {"type": "notify", "to_field": "Talep Eden",
                                 "message": "Talebiniz reddedildi: Talep #{{Talep No}} ({{Talep Tipi}}) — {{İstenen Miktar}}"},
                            ],
                        },
                    ],
                },
            ],
        },
        # FR-2.5 + izlenebilirlik — Formül bileşeni girildiğinde lottan çıkış
        {
            "name": "Formül bileşeni girildi → lottan otomatik çıkış",
            "trigger": {"type": "record_created", "list": "Formül Bileşenleri"},
            "actions": [
                {
                    "type": "create_record",
                    "list": "Stok Hareketleri",
                    "fields": {
                        "Tarih":          "formula:Today()",
                        "Hareket Tipi":   "Çıkış",
                        "Çıkış Miktarı":  "trigger:Miktar",
                        "Lot":            "trigger:Lot",
                        "İlgili Proje":   "trigger:İlgili Proje",
                        "İlgili Deneme":  "trigger:Deneme",
                        "Açıklama":       "Formülasyon denemesi bileşeni (otomatik)",
                    },
                },
            ],
        },
        # FR-2.7 — Numune saklama süresi bitti → karar görevi
        {
            "name": "Numune saklama süresi bitti → imha/uzatma görevi",
            "trigger": {"type": "time_trigger", "list": "Numuneler", "date_field": "Saklama Bitiş Tarihi", "offset": 0},
            "actions": [
                {"type": "update_record", "fields": {"Durum": "Karar Bekliyor"}},
                {
                    "type": "create_record",
                    "list": "Depo Görevleri",
                    "fields": {
                        "Başlık":      "Numune saklama süresi doldu — imha / uzatma kararı",
                        "Görev Tipi":  "Numune İmha / Uzatma Kararı",
                        "Atanan":      "trigger:Sorumlu",
                        "Son Tarih":   "formula:DateAdd(Today(), 7, \"day\")",
                        "Numune":      "trigger:_id",
                    },
                },
                {"type": "notify", "to_field": "Sorumlu",
                 "message": "Numune saklama süresi doldu: {{Numune Adı}} — imha veya uzatma kararı gerekiyor."},
            ],
        },
        {
            "name": "Depo görevi atandığında bildir",
            "trigger": {"type": "record_created", "list": "Depo Görevleri"},
            "actions": [
                {"type": "notify", "to_field": "Atanan",
                 "message": "Yeni depo görevi: {{Başlık}} — Son tarih: {{Son Tarih}}"},
            ],
        },
    ],

    "seed": {},
}


# ── Plan uyumluluğu ───────────────────────────────────────────────────────────
# Polifarma deneme planı (2024Business) süreç listelerini desteklemiyor. False iken
# süreç listeleri veri listesi olarak kurulur; yerleşik "Status" yerine aynı
# seçeneklerle bir "Durum" SELECT alanı eklenir ve tüm referanslar ona çevrilir.
PLAN_SUPPORTS_PROCESS = False


def _process_to_data(spec):
    def swap(o):
        if isinstance(o, dict):
            return {("Durum" if k == "Status" else k): swap(v) for k, v in o.items()}
        if isinstance(o, list):
            return [swap(x) for x in o]
        if isinstance(o, str):
            return "Durum" if o == "Status" else o.replace("{{Status}}", "{{Durum}}")
        return o

    lists = [l for f in spec.get("folders", []) for l in f["lists"]] + spec.get("lists", [])
    for l in lists:
        if "status_options" not in l:
            continue
        opts = l.pop("status_options")
        l.pop("default_status", None)
        l.pop("list_type", None)
        durum = {"name": "Durum", "type": F.SELECT,
                 "options": [o["label"] for o in opts], "colors": [o["color"] for o in opts]}
        fields = l["fields"]
        fields.insert(1 if fields and fields[0]["type"] == F.AUTONUMBER else 0, durum)
        l["views"] = swap(l["views"])
        for tab in l.get("layout", {}).get("tabs", [])[:1]:
            tab["fields"].insert(0, "Durum")
    spec["reports"] = swap(spec.get("reports", []))
    spec["automations"] = swap(spec.get("automations", []))
    return spec


if not PLAN_SUPPORTS_PROCESS:
    SPEC = _process_to_data(SPEC)
