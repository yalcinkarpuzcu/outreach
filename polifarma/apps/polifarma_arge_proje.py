"""
Polifarma PoC — Uygulama 1: Ar-Ge Proje Takibi  (BUILD SIRASI: 1)

Ortak bağlantı noktası: "Ar-Ge Projeleri". Stok ve Toplantı uygulamaları bu listeye
cross-app LINK verir; bu yüzden ilk bu uygulama kurulur.

Kurulum sırası:
  1) python main.py build apps/polifarma_arge_proje.py
  2) python main.py build apps/polifarma_stok.py
  3) python main.py build apps/polifarma_toplanti.py
  4) python apps/upgrade_polifarma_computed.py      # back-link, rollup, count, formül
  5) python main.py build apps/polifarma_stok_faz2.py
  6) python main.py build apps/polifarma_proje_faz2.py
"""
from workiom.constants import F, LT, V

# ── Ortak sabitler ────────────────────────────────────────────────────────────
FAZLAR = [
    "1. Literatür ve Fizibilite",
    "2. Ön Formülasyon",
    "3. Formülasyon Geliştirme",
    "4. Analitik Metot Geliştirme ve Validasyon",
    "5. Stabilite",
    "6. Pilot Üretim / Scale-up",
    "7. Ruhsat Dosyası (CTD)",
    "8. Üretime Transfer",
]
FAZ_RENK = ["#8ed6ff", "#4e86f7", "#7942e3", "#5bd7d0", "#f5c044", "#ffa979", "#ff86c7", "#5bd77e"]

ONCELIK = {"options": ["Düşük", "Orta", "Yüksek", "Kritik"],
           "colors":  ["#8ed6ff", "#f5c044", "#ffa979", "#ea346f"]}


def _faz_guncelle_aksiyonlari():
    """Kapı 2. onayı verildiğinde: 'Sonraki Faz' değerine göre projenin 'Mevcut Faz'ını güncelle.
    İki farklı SELECT alanının option UUID'leri farklı olduğundan değer doğrudan kopyalanamaz;
    her faz için ayrı condition kurulur."""
    return [
        {
            "type": "condition",
            "if":   f"{{{{Sonraki Faz}}}} = '{faz}'",
            "then": [
                {
                    "type":  "find_records",
                    "list":  "Ar-Ge Projeleri",
                    "where": {"field": "Proje Kodu", "op": "equals", "value": "trigger:Proje Kodu"},
                    "max":   1,
                    "actions": [
                        {"type": "update_record", "fields": {"Mevcut Faz": faz}},
                    ],
                },
            ],
        }
        for faz in FAZLAR
    ]


SPEC = {
    "name": "Ar-Ge Proje Takibi",
    "icon": "fas fa-flask",
    "color": "#7942e3",
    "description": "Polifarma Ar-Ge projeleri: stage-gate faz kapıları, formülasyon denemeleri, analitik, stabilite, görev ve sapmalar",

    "folders": [
        # ─────────────────────────────────────────────────────────────
        # PROJELER
        # ─────────────────────────────────────────────────────────────
        {
            "name": "Projeler",
            "lists": [
                {
                    "name": "Ar-Ge Projeleri",
                    "icon": "fas fa-flask",
                    "fields": [
                        {"name": "Proje Kodu",          "type": F.TEXT,     "required": True},
                        {"name": "Ürün Adı",            "type": F.TEXT,     "required": True},
                        {"name": "Dozaj Formu",         "type": F.SELECT,
                         "options": ["Tablet", "Kapsül", "Süspansiyon", "Enjektabl", "Krem"],
                         "colors":  ["#4e86f7", "#7942e3", "#5bd7d0", "#ea346f", "#ffa979"]},
                        {"name": "Proje Tipi",          "type": F.SELECT,
                         "options": ["Jenerik", "Yeni Formülasyon", "Line Extension"],
                         "colors":  ["#4e86f7", "#7942e3", "#5bd7d0"]},
                        {"name": "Referans Ürün",       "type": F.TEXT},
                        {"name": "Mevcut Faz",          "type": F.SELECT,
                         "options": FAZLAR, "colors": FAZ_RENK},
                        {"name": "Proje Lideri",        "type": F.USER},
                        {"name": "Ekip",                "type": F.MULTIUSER},
                        {"name": "Ar-Ge Direktörü",     "type": F.USER},
                        {"name": "Başlangıç Tarihi",    "type": F.DATE},
                        {"name": "Hedef Ruhsat Tarihi", "type": F.DATE},
                        {"name": "Bütçe",               "type": F.CURRENCY},
                        # "Gerçekleşen Maliyet" → upgrade script'te rollup olarak eklenir (stok tüketimi)
                        {"name": "Risk Seviyesi",       "type": F.SELECT,
                         "options": ["Düşük", "Orta", "Yüksek"],
                         "colors":  ["#5bd77e", "#f5c044", "#ea346f"]},
                        {"name": "Durum",               "type": F.SELECT,
                         "options": ["Aktif", "Beklemede", "Tamamlandı", "İptal"],
                         "colors":  ["#5bd77e", "#ffa979", "#5bd7d0", "#ff86c7"]},
                        {"name": "Açıklama",            "type": F.TEXT,     "multiline": True},
                    ],
                    "views": [
                        {"name": "Tüm Projeler",        "type": V.GRID},
                        {"name": "Faza Göre (Kanban)",  "type": V.KANBAN,   "group_by": "Mevcut Faz"},
                        {"name": "Riske Göre",          "type": V.KANBAN,   "group_by": "Risk Seviyesi"},
                        {"name": "Proje Zaman Çizelgesi", "type": V.TIMELINE, "date_field": "Başlangıç Tarihi"},
                        {"name": "Hedef Ruhsat Takvimi", "type": V.CALENDAR, "date_field": "Hedef Ruhsat Tarihi"},
                        {"name": "Aktif Projeler",      "type": V.GRID,
                         "filter": {"field": "Durum", "value": "Aktif"}},
                    ],
                    # İlişkili kayıt sekmeleri (Faz Kapıları, Denemeler, Stabilite, Görevler, Stok Tüketimi,
                    # Toplantı Kararları, Aksiyonlar) upgrade script'teki back-link'lerle oluşur → README "Proje 360".
                    "layout": {
                        "tabs": [
                            {"name": "Proje Bilgileri", "fields": [
                                "Proje Kodu", "Ürün Adı", "Dozaj Formu", "Proje Tipi", "Referans Ürün",
                                "Mevcut Faz", "Durum", "Risk Seviyesi", "Açıklama",
                            ]},
                            {"name": "Ekip ve Takvim", "fields": [
                                "Proje Lideri", "Ekip", "Ar-Ge Direktörü",
                                "Başlangıç Tarihi", "Hedef Ruhsat Tarihi",
                            ]},
                            {"name": "Bütçe", "fields": ["Bütçe"]},
                        ]
                    },
                    "forms": [],
                },

                {
                    "name": "Faz Kapıları",
                    "icon": "fas fa-door-open",
                    "list_type": LT.PROCESS,
                    "status_options": [
                        {"label": "Planlandı",                "color": "#8ed6ff", "closed": False},
                        {"label": "Devam Ediyor",             "color": "#f5c044", "closed": False},
                        {"label": "Direktör Onayı Bekliyor",  "color": "#4e86f7", "closed": False},
                        {"label": "QA Onayı Bekliyor",        "color": "#7942e3", "closed": False},
                        {"label": "Onaylandı",                "color": "#5bd77e", "closed": True},
                        {"label": "Reddedildi",               "color": "#ea346f", "closed": True},
                    ],
                    "default_status": "Planlandı",
                    "fields": [
                        {"name": "Kapı No",                  "type": F.AUTONUMBER},
                        {"name": "Faz Adı",                  "type": F.SELECT, "options": FAZLAR, "colors": FAZ_RENK},
                        {"name": "Sonraki Faz",              "type": F.SELECT, "options": FAZLAR, "colors": FAZ_RENK},
                        {"name": "Planlanan Başlangıç",      "type": F.DATE},
                        {"name": "Planlanan Bitiş",          "type": F.DATE},
                        {"name": "Gerçekleşen Bitiş",        "type": F.DATE},
                        {"name": "Giriş Kriterleri",         "type": F.TEXT, "multiline": True},
                        {"name": "Çıkış Kriterleri",         "type": F.TEXT, "multiline": True},
                        {"name": "1. Onaylayan (Direktör)",  "type": F.USER},
                        {"name": "2. Onaylayan (QA/Ruhsat)", "type": F.USER},
                        {"name": "Onay Notu",                "type": F.TEXT, "multiline": True},
                        {"name": "Gecikmede",                "type": F.BOOLEAN},
                        {"name": "Ekler",                    "type": F.FILE},
                        {"name": "Proje",                    "type": F.LINK, "target_list": "Ar-Ge Projeleri"},
                        {"name": "Proje Kodu",               "type": F.LOOKUP, "via": "Proje", "lookup_field": "Proje Kodu"},
                        {"name": "Proje Lideri",             "type": F.LOOKUP, "via": "Proje", "lookup_field": "Proje Lideri"},
                        {"name": "Proje Ekibi",              "type": F.LOOKUP, "via": "Proje", "lookup_field": "Ekip"},
                    ],
                    "views": [
                        {"name": "Tüm Faz Kapıları",   "type": V.GRID},
                        {"name": "Faza Göre",          "type": V.KANBAN,   "group_by": "Faz Adı"},
                        {"name": "Kapı Zaman Çizelgesi", "type": V.TIMELINE, "date_field": "Planlanan Başlangıç"},
                        {"name": "Kapı Takvimi",       "type": V.CALENDAR, "date_field": "Planlanan Bitiş"},
                        {"name": "Onay Bekleyenler",   "type": V.GRID,
                         "filter": {"field": "Status", "value": ["Direktör Onayı Bekliyor", "QA Onayı Bekliyor"]}},
                        {"name": "Geciken Kapılar",    "type": V.GRID,
                         "filter": {"field": "Gecikmede", "value": True}},
                    ],
                    "layout": {
                        "tabs": [
                            {"name": "Kapı Bilgileri", "fields": [
                                "Proje", "Faz Adı", "Sonraki Faz",
                                "Planlanan Başlangıç", "Planlanan Bitiş", "Gerçekleşen Bitiş", "Gecikmede",
                            ]},
                            {"name": "Kriterler", "fields": ["Giriş Kriterleri", "Çıkış Kriterleri", "Ekler"]},
                            {"name": "Onay", "fields": [
                                "1. Onaylayan (Direktör)", "2. Onaylayan (QA/Ruhsat)", "Onay Notu",
                            ]},
                        ]
                    },
                    "forms": [],
                },

                {
                    "name": "Görevler ve Sapmalar",
                    "icon": "fas fa-tasks",
                    "list_type": LT.PROCESS,
                    "status_options": [
                        {"label": "Açık",          "color": "#8ed6ff", "closed": False},
                        {"label": "Devam Ediyor",  "color": "#f5c044", "closed": False},
                        {"label": "Gecikmede",     "color": "#ea346f", "closed": False},
                        {"label": "Tamamlandı",    "color": "#5bd77e", "closed": True},
                        {"label": "İptal",         "color": "#ff86c7", "closed": True},
                    ],
                    "default_status": "Açık",
                    "fields": [
                        {"name": "Kayıt No",      "type": F.AUTONUMBER},
                        {"name": "Başlık",        "type": F.TEXT, "required": True},
                        {"name": "Tip",           "type": F.SELECT,
                         "options": ["Görev", "Sapma", "CAPA"],
                         "colors":  ["#4e86f7", "#ea346f", "#ffa979"]},
                        {"name": "Açıklama",      "type": F.TEXT, "multiline": True},
                        {"name": "Atanan",        "type": F.USER},
                        {"name": "Son Tarih",     "type": F.DATE},
                        {"name": "Öncelik",       "type": F.SELECT, **ONCELIK},
                        {"name": "Kök Neden",     "type": F.TEXT, "multiline": True},
                        {"name": "Kapanış Notu",  "type": F.TEXT, "multiline": True},
                        {"name": "Ekler",         "type": F.FILE},
                        {"name": "Proje",         "type": F.LINK, "target_list": "Ar-Ge Projeleri"},
                        {"name": "Proje Lideri",  "type": F.LOOKUP, "via": "Proje", "lookup_field": "Proje Lideri"},
                        {"name": "Ar-Ge Direktörü", "type": F.LOOKUP, "via": "Proje", "lookup_field": "Ar-Ge Direktörü"},
                    ],
                    "views": [
                        {"name": "Tüm Görevler ve Sapmalar", "type": V.GRID},
                        {"name": "Tipe Göre",          "type": V.KANBAN,   "group_by": "Tip"},
                        {"name": "Önceliğe Göre",      "type": V.KANBAN,   "group_by": "Öncelik"},
                        {"name": "Son Tarih Takvimi",  "type": V.CALENDAR, "date_field": "Son Tarih"},
                        {"name": "Sapma ve CAPA",      "type": V.GRID,
                         "filter": {"field": "Tip", "value": ["Sapma", "CAPA"]}},
                        {"name": "Gecikenler",         "type": V.GRID,
                         "filter": {"field": "Status", "value": "Gecikmede"}},
                    ],
                    "layout": {
                        "tabs": [
                            {"name": "Kayıt", "fields": [
                                "Başlık", "Tip", "Proje", "Atanan", "Son Tarih", "Öncelik", "Açıklama",
                            ]},
                            {"name": "Kök Neden ve Kapanış", "fields": ["Kök Neden", "Kapanış Notu", "Ekler"]},
                        ]
                    },
                    "forms": [
                        {"name": "Sapma / Görev Bildir",
                         "fields": ["Başlık", "Tip", "Proje", "Atanan", "Son Tarih", "Öncelik", "Açıklama", "Ekler"]},
                    ],
                },
            ],
        },

        # ─────────────────────────────────────────────────────────────
        # LABORATUVAR
        # ─────────────────────────────────────────────────────────────
        {
            "name": "Laboratuvar",
            "lists": [
                {
                    "name": "Formülasyon Denemeleri",
                    "icon": "fas fa-vial",
                    "fields": [
                        {"name": "Deneme No",              "type": F.AUTONUMBER},
                        {"name": "Deneme Kodu",            "type": F.TEXT, "required": True},
                        {"name": "Batch No",               "type": F.TEXT},
                        {"name": "Batch Büyüklüğü",        "type": F.NUMBER},
                        {"name": "Batch Birimi",           "type": F.SELECT,
                         "options": ["g", "kg", "mL", "L", "Adet (tablet/kapsül)"],
                         "colors":  ["#8ed6ff", "#4e86f7", "#5bd7d0", "#7942e3", "#ffa979"]},
                        # Formül bileşenleri (hammadde/lot + miktar) → Stok uygulamasındaki
                        # "Formül Bileşenleri" listesinde tutulur; upgrade script back-link ile buraya getirir.
                        {"name": "Proses Parametreleri",   "type": F.TEXT, "multiline": True},
                        {"name": "Sonuç",                  "type": F.SELECT,
                         "options": ["Devam Ediyor", "Uygun", "Uygun Değil", "Tekrar"],
                         "colors":  ["#f5c044", "#5bd77e", "#ea346f", "#ffa979"]},
                        {"name": "Sonuç Notu",             "type": F.TEXT, "multiline": True},
                        {"name": "Sorumlu",                "type": F.USER},
                        {"name": "Tarih",                  "type": F.DATE},
                        {"name": "Ekler",                  "type": F.FILE},
                        {"name": "Proje",                  "type": F.LINK, "target_list": "Ar-Ge Projeleri"},
                    ],
                    "views": [
                        {"name": "Tüm Denemeler",      "type": V.GRID},
                        {"name": "Sonuca Göre",        "type": V.KANBAN,   "group_by": "Sonuç"},
                        {"name": "Deneme Takvimi",     "type": V.CALENDAR, "date_field": "Tarih"},
                    ],
                    "layout": {
                        "tabs": [
                            {"name": "Deneme", "fields": [
                                "Deneme Kodu", "Proje", "Batch No", "Batch Büyüklüğü", "Batch Birimi",
                                "Sorumlu", "Tarih",
                            ]},
                            {"name": "Proses ve Sonuç", "fields": [
                                "Proses Parametreleri", "Sonuç", "Sonuç Notu", "Ekler",
                            ]},
                        ]
                    },
                    "forms": [],
                },

                {
                    "name": "Analitik Çalışmalar",
                    "icon": "fas fa-microscope",
                    "fields": [
                        {"name": "Çalışma No",          "type": F.AUTONUMBER},
                        {"name": "Test Tipi",           "type": F.SELECT,
                         "options": ["Çözünürlük", "Safsızlık", "İçerik Tayini", "Diğer"],
                         "colors":  ["#4e86f7", "#ea346f", "#5bd7d0", "#8ed6ff"]},
                        {"name": "Metot",               "type": F.TEXT},
                        {"name": "Validasyon Durumu",   "type": F.SELECT,
                         "options": ["Planlandı", "Geliştirmede", "Validasyonda", "Valide Edildi", "Başarısız"],
                         "colors":  ["#8ed6ff", "#f5c044", "#4e86f7", "#5bd77e", "#ea346f"]},
                        {"name": "Sonuç",               "type": F.TEXT, "multiline": True},
                        {"name": "Sorumlu",             "type": F.USER},
                        {"name": "Tarih",               "type": F.DATE},
                        {"name": "Ekler",               "type": F.FILE},
                        {"name": "Proje",               "type": F.LINK, "target_list": "Ar-Ge Projeleri"},
                        {"name": "Deneme",              "type": F.LINK, "target_list": "Formülasyon Denemeleri"},
                    ],
                    "views": [
                        {"name": "Tüm Analitik Çalışmalar", "type": V.GRID},
                        {"name": "Validasyon Durumuna Göre", "type": V.KANBAN, "group_by": "Validasyon Durumu"},
                        {"name": "Test Tipine Göre",    "type": V.KANBAN, "group_by": "Test Tipi"},
                    ],
                    "forms": [],
                },

                {
                    "name": "Stabilite Çalışmaları",
                    "icon": "fas fa-thermometer-half",
                    "fields": [
                        {"name": "Çalışma No",              "type": F.AUTONUMBER},
                        {"name": "Koşul",                   "type": F.SELECT,
                         "options": ["25°C / %60 RH", "30°C / %65 RH", "40°C / %75 RH"],
                         "colors":  ["#5bd77e", "#f5c044", "#ea346f"]},
                        {"name": "Başlangıç Tarihi",        "type": F.DATE},
                        {"name": "Zaman Noktaları",         "type": F.MULTISELECT,
                         "options": ["0. Ay", "1. Ay", "3. Ay", "6. Ay", "9. Ay", "12. Ay", "18. Ay", "24. Ay"],
                         "colors":  ["#8ed6ff", "#4e86f7", "#5bd7d0", "#7942e3", "#f5c044", "#ffa979", "#ff86c7", "#5bd77e"]},
                        {"name": "Sonraki Ölçüm Tarihi",    "type": F.DATE},
                        {"name": "Sorumlu",                 "type": F.USER},
                        {"name": "Sonuç",                   "type": F.SELECT,
                         "options": ["Devam Ediyor", "Uygun", "OOT (Trend)", "OOS (Spek Dışı)"],
                         "colors":  ["#f5c044", "#5bd77e", "#ffa979", "#ea346f"]},
                        {"name": "Sapma",                   "type": F.BOOLEAN},
                        {"name": "Sapma Açıklaması",        "type": F.TEXT, "multiline": True},
                        {"name": "Ekler",                   "type": F.FILE},
                        {"name": "Proje",                   "type": F.LINK, "target_list": "Ar-Ge Projeleri"},
                        {"name": "Batch (Deneme)",          "type": F.LINK, "target_list": "Formülasyon Denemeleri"},
                    ],
                    "views": [
                        {"name": "Tüm Stabilite Çalışmaları", "type": V.GRID},
                        {"name": "Koşula Göre",         "type": V.KANBAN,   "group_by": "Koşul"},
                        {"name": "Ölçüm Takvimi",       "type": V.CALENDAR, "date_field": "Sonraki Ölçüm Tarihi"},
                        {"name": "Sapmalı Çalışmalar",  "type": V.GRID,
                         "filter": {"field": "Sapma", "value": True}},
                    ],
                    "forms": [],
                },

                {
                    "name": "Stabilite Ölçümleri",
                    "icon": "fas fa-chart-line",
                    "fields": [
                        {"name": "Ölçüm No",           "type": F.AUTONUMBER},
                        {"name": "Zaman Noktası",      "type": F.SELECT,
                         "options": ["0. Ay", "1. Ay", "3. Ay", "6. Ay", "9. Ay", "12. Ay", "18. Ay", "24. Ay"],
                         "colors":  ["#8ed6ff", "#4e86f7", "#5bd7d0", "#7942e3", "#f5c044", "#ffa979", "#ff86c7", "#5bd77e"]},
                        {"name": "Planlanan Tarih",    "type": F.DATE},
                        {"name": "Gerçekleşen Tarih",  "type": F.DATE},
                        {"name": "Sonuç",              "type": F.SELECT,
                         "options": ["Uygun", "OOT (Trend)", "OOS (Spek Dışı)"],
                         "colors":  ["#5bd77e", "#ffa979", "#ea346f"]},
                        {"name": "Bulgular",           "type": F.TEXT, "multiline": True},
                        {"name": "Sorumlu",            "type": F.USER},
                        {"name": "Ekler",              "type": F.FILE},
                        {"name": "Stabilite Çalışması", "type": F.LINK, "target_list": "Stabilite Çalışmaları"},
                    ],
                    "views": [
                        {"name": "Tüm Stabilite Ölçümleri", "type": V.GRID},
                        {"name": "Planlanan Ölçümler", "type": V.CALENDAR, "date_field": "Planlanan Tarih"},
                        {"name": "Sonuca Göre",        "type": V.KANBAN,   "group_by": "Sonuç"},
                    ],
                    "forms": [],
                },
            ],
        },
    ],

    "reports": [
        {"label": "Aktif Projeler",        "list": "Ar-Ge Projeleri", "type": "kpi_count",
         "filter": {"field": "Durum", "value": "Aktif"}, "icon": "fal fa-flask", "pin": True},
        {"label": "Faza Göre Proje Dağılımı", "list": "Ar-Ge Projeleri", "type": "bar",
         "group_by": "Mevcut Faz", "aggregation": "count", "icon": "fal fa-layer-group", "pin": True},
        {"label": "Riske Göre Projeler",   "list": "Ar-Ge Projeleri", "type": "pie",
         "group_by": "Risk Seviyesi", "aggregation": "count", "icon": "fal fa-exclamation-triangle", "pin": True},
        {"label": "Geciken Faz Kapıları",  "list": "Faz Kapıları", "type": "kpi_count",
         "filter": {"field": "Gecikmede", "value": True}, "icon": "fal fa-door-open", "pin": True},
        {"label": "Geciken Görevler",      "list": "Görevler ve Sapmalar", "type": "kpi_count",
         "filter": {"field": "Status", "value": "Gecikmede"}, "icon": "fal fa-clock", "pin": True},
        {"label": "Açık Sapma / CAPA",     "list": "Görevler ve Sapmalar", "type": "bar",
         "group_by": "Tip", "aggregation": "count", "icon": "fal fa-bug", "pin": True},
        {"label": "Yaklaşan Stabilite Ölçümleri", "list": "Stabilite Çalışmaları", "type": "table",
         "icon": "fal fa-thermometer-half", "pin": True},
    ],

    "automations": [
        # FR-1.2 — Çift onay: 1. aşama Direktör
        {
            "name": "Faz kapısı — Direktör onayı (1. onay)",
            "trigger": {"type": "record_updated", "list": "Faz Kapıları", "watch_field": "Status"},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Status}} = 'Direktör Onayı Bekliyor'",
                    "then": [
                        {
                            "type": "approval",
                            "title":    "Faz Kapısı Onayı (Direktör)",
                            "subtitle": "{{Proje}} — {{Faz Adı}} kapısı onayınızı bekliyor",
                            "approver": "field:1. Onaylayan (Direktör)",
                            "timeout_days": 5,
                            "require_rejection_message": True,
                            "on_approve": [
                                {"type": "update_record", "fields": {"Status": "QA Onayı Bekliyor"}},
                            ],
                            "on_reject": [
                                {"type": "update_record", "fields": {"Status": "Reddedildi"}},
                                {"type": "notify", "to_field": "Proje Lideri",
                                 "message": "Faz kapısı Direktör tarafından reddedildi: {{Proje}} — {{Faz Adı}}"},
                            ],
                        },
                    ],
                },
            ],
        },
        # FR-1.2 + FR-1.3 — 2. aşama QA/Ruhsat; onayda proje fazı güncellenir ve ekip bilgilendirilir
        {
            "name": "Faz kapısı — QA/Ruhsat onayı (2. onay) ve faz ilerletme",
            "trigger": {"type": "record_updated", "list": "Faz Kapıları", "watch_field": "Status"},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Status}} = 'QA Onayı Bekliyor'",
                    "then": [
                        {
                            "type": "approval",
                            "title":    "Faz Kapısı Onayı (QA / Ruhsat)",
                            "subtitle": "{{Proje}} — {{Faz Adı}} kapısı Direktör onayını aldı, 2. onay bekleniyor",
                            "approver": "field:2. Onaylayan (QA/Ruhsat)",
                            "timeout_days": 5,
                            "require_rejection_message": True,
                            "on_approve": [
                                {"type": "update_record", "fields": {
                                    "Status": "Onaylandı",
                                    "Gerçekleşen Bitiş": "formula:Today()",
                                }},
                                *_faz_guncelle_aksiyonlari(),
                                {"type": "notify", "to_field": "Proje Ekibi",
                                 "message": "Faz kapısı onaylandı: {{Proje}} → yeni faz: {{Sonraki Faz}}"},
                                {"type": "notify", "to_field": "Proje Lideri",
                                 "message": "Faz kapısı onaylandı: {{Proje}} → yeni faz: {{Sonraki Faz}}"},
                            ],
                            "on_reject": [
                                {"type": "update_record", "fields": {"Status": "Reddedildi"}},
                                {"type": "notify", "to_field": "Proje Lideri",
                                 "message": "Faz kapısı QA/Ruhsat tarafından reddedildi: {{Proje}} — {{Faz Adı}}"},
                            ],
                        },
                    ],
                },
            ],
        },
        # FR-1.7 — Geciken faz kapısı
        {
            "name": "Faz kapısı planlanan bitişi geçti → Gecikmede",
            "trigger": {"type": "time_trigger", "list": "Faz Kapıları", "date_field": "Planlanan Bitiş", "offset": 1},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Status}} != 'Onaylandı' and {{Status}} != 'Reddedildi'",
                    "then": [
                        {"type": "update_record", "fields": {"Gecikmede": "true"}},
                        {"type": "notify", "to_field": "Proje Lideri",
                         "message": "Faz kapısı gecikmede: {{Proje}} — {{Faz Adı}} (planlanan bitiş: {{Planlanan Bitiş}})"},
                    ],
                },
            ],
        },
        # FR-1.4 — Stabilite zaman noktası 7 gün kala hatırlatma
        {
            "name": "Stabilite ölçümüne 7 gün kala hatırlat",
            "trigger": {"type": "time_trigger", "list": "Stabilite Çalışmaları",
                        "date_field": "Sonraki Ölçüm Tarihi", "offset": -7},
            "actions": [
                {"type": "notify", "to_field": "Sorumlu",
                 "message": "Stabilite ölçümü 7 gün sonra: {{Proje}} — {{Koşul}} — Tarih: {{Sonraki Ölçüm Tarihi}}"},
            ],
        },
        {
            "name": "Planlanan stabilite ölçümüne 7 gün kala hatırlat",
            "trigger": {"type": "time_trigger", "list": "Stabilite Ölçümleri",
                        "date_field": "Planlanan Tarih", "offset": -7},
            "actions": [
                {"type": "notify", "to_field": "Sorumlu",
                 "message": "Stabilite zaman noktası yaklaşıyor: {{Stabilite Çalışması}} — {{Zaman Noktası}} — {{Planlanan Tarih}}"},
            ],
        },
        # FR-1.5 — Sapma / CAPA açıldığında proje lideri ve direktör
        {
            "name": "Sapma / CAPA açıldı → Proje Lideri ve Direktör",
            "trigger": {"type": "record_created", "list": "Görevler ve Sapmalar"},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Tip}} = 'Sapma' or {{Tip}} = 'CAPA'",
                    "then": [
                        {"type": "notify", "to_field": "Proje Lideri",
                         "message": "Yeni {{Tip}} kaydı: {{Başlık}} — Proje: {{Proje}} — Öncelik: {{Öncelik}}"},
                        {"type": "notify", "to_field": "Ar-Ge Direktörü",
                         "message": "Yeni {{Tip}} kaydı: {{Başlık}} — Proje: {{Proje}} — Öncelik: {{Öncelik}}"},
                    ],
                },
            ],
        },
        {
            "name": "Görev atandığında atanana bildir",
            "trigger": {"type": "record_created", "list": "Görevler ve Sapmalar"},
            "actions": [
                {"type": "notify", "to_field": "Atanan",
                 "message": "Size yeni bir {{Tip}} atandı: {{Başlık}} — Proje: {{Proje}} — Son tarih: {{Son Tarih}}"},
            ],
        },
        # FR-1.7 — Geciken görev
        {
            "name": "Görev son tarihi geçti → Gecikmede",
            "trigger": {"type": "time_trigger", "list": "Görevler ve Sapmalar", "date_field": "Son Tarih", "offset": 1},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Status}} != 'Tamamlandı' and {{Status}} != 'İptal'",
                    "then": [
                        {"type": "update_record", "fields": {"Status": "Gecikmede"}},
                        {"type": "notify", "to_field": "Atanan",
                         "message": "Gecikmede: {{Başlık}} — Proje: {{Proje}} — Son tarih: {{Son Tarih}}"},
                    ],
                },
            ],
        },
    ],

    "seed": {},
}
