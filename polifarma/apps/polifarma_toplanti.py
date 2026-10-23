"""
Polifarma PoC — Uygulama 3: Toplantı Yönetimi  (BUILD SIRASI: 3)

Bağımlılık: "Ar-Ge Proje Takibi" önce kurulmuş olmalı (Ar-Ge Projeleri, Faz Kapıları'na cross-app LINK).
Kararlar ve aksiyonlar projeye bağlanır; proje kaydında upgrade script'teki back-link'lerle görünür (FR-3.5).
"""
from workiom.constants import F, LT, V

PROJE_APP = "Ar-Ge Proje Takibi"

TOPLANTI_TIPI = {"options": ["Haftalık Ar-Ge", "Proje Toplantısı", "Faz Kapısı Değerlendirme", "Tedarikçi", "Yönetim"],
                 "colors":  ["#4e86f7", "#7942e3", "#5bd7d0", "#ffa979", "#ea346f"]}

SPEC = {
    "name": "Toplantı Yönetimi",
    "icon": "fas fa-users",
    "color": "#4e86f7",
    "description": "Ar-Ge toplantılarının gündemi, kararları ve aksiyon takibi; kararlar ve aksiyonlar projelere bağlı",

    "folders": [
        {
            "name": "Toplantılar",
            "lists": [
                # FR-3.1 — tekrarlayan toplantı şablonları
                {
                    "name": "Toplantı Serileri",
                    "icon": "fas fa-redo",
                    "fields": [
                        {"name": "Seri Adı",         "type": F.TEXT, "required": True},
                        {"name": "Tip",              "type": F.SELECT, **TOPLANTI_TIPI},
                        {"name": "Periyot",          "type": F.SELECT,
                         "options": ["Haftalık", "İki Haftalık", "Aylık"],
                         "colors":  ["#4e86f7", "#5bd7d0", "#7942e3"]},
                        {"name": "Gün",              "type": F.SELECT,
                         "options": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"],
                         "colors":  ["#8ed6ff", "#4e86f7", "#5bd7d0", "#7942e3", "#f5c044"]},
                        {"name": "Saat",             "type": F.TEXT},
                        {"name": "Süre (dk)",        "type": F.NUMBER},
                        {"name": "Yer / Online Link", "type": F.TEXT},
                        {"name": "Organizatör",      "type": F.USER},
                        {"name": "Katılımcılar",     "type": F.MULTIUSER},
                        {"name": "Aktif",            "type": F.BOOLEAN},
                    ],
                    "views": [
                        {"name": "Tüm Toplantı Serileri", "type": V.GRID},
                        {"name": "Aktif Haftalık Seriler", "type": V.GRID,
                         "filter": {"field": "Periyot", "value": "Haftalık"}},
                    ],
                    "forms": [],
                },

                {
                    "name": "Toplantılar",
                    "icon": "fas fa-calendar-alt",
                    "list_type": LT.PROCESS,
                    "status_options": [
                        {"label": "Planlandı", "color": "#4e86f7", "closed": False},
                        {"label": "Yapıldı",   "color": "#5bd77e", "closed": True},
                        {"label": "İptal",     "color": "#ff86c7", "closed": True},
                    ],
                    "default_status": "Planlandı",
                    "fields": [
                        {"name": "Toplantı No",          "type": F.AUTONUMBER},
                        {"name": "Başlık",               "type": F.TEXT, "required": True},
                        {"name": "Tip",                  "type": F.SELECT, **TOPLANTI_TIPI},
                        {"name": "Tarih",                "type": F.DATE},
                        {"name": "Saat",                 "type": F.TEXT},
                        {"name": "Süre (dk)",            "type": F.NUMBER},
                        {"name": "Yer / Online Link",    "type": F.TEXT},
                        {"name": "Organizatör",          "type": F.USER},
                        {"name": "Katılımcılar",         "type": F.MULTIUSER},
                        {"name": "Toplantı Notu",        "type": F.TEXT, "multiline": True},
                        {"name": "Kayıt / Transkript",   "type": F.FILE},
                        {"name": "AI Özeti",             "type": F.TEXT, "multiline": True},
                        {"name": "Toplantı Serisi",      "type": F.LINK, "target_list": "Toplantı Serileri"},
                        {"name": "İlgili Projeler",      "type": F.LINK, "target_app": PROJE_APP,
                         "target_list": "Ar-Ge Projeleri", "multiple": True},
                    ],
                    "views": [
                        {"name": "Tüm Toplantılar",      "type": V.GRID},
                        {"name": "Toplantı Takvimi",     "type": V.CALENDAR, "date_field": "Tarih"},
                        {"name": "Tipe Göre",            "type": V.KANBAN,   "group_by": "Tip"},
                        {"name": "Planlanan Toplantılar", "type": V.GRID,
                         "filter": {"field": "Status", "value": "Planlandı"}},
                        {"name": "Toplantı Tutanağı",    "type": V.DOCUMENT,
                         "template": [
                             {"type": "header",    "text": "Polifarma Ar-Ge — Toplantı Tutanağı", "level": 2, "align": "center"},
                             {"type": "field",     "name": "Başlık"},
                             {"type": "field",     "name": "Tarih"},
                             {"type": "field",     "name": "Tip"},
                             {"type": "field",     "name": "Organizatör"},
                             {"type": "field",     "name": "Katılımcılar"},
                             {"type": "field",     "name": "İlgili Projeler"},
                             {"type": "header",    "text": "Toplantı Notu", "level": 3},
                             {"type": "field",     "name": "Toplantı Notu"},
                             {"type": "header",    "text": "Özet", "level": 3},
                             {"type": "field",     "name": "AI Özeti"},
                         ]},
                    ],
                    "layout": {
                        "tabs": [
                            {"name": "Toplantı", "fields": [
                                "Başlık", "Tip", "Toplantı Serisi", "Tarih", "Saat", "Süre (dk)",
                                "Yer / Online Link", "Organizatör", "Katılımcılar", "İlgili Projeler",
                            ]},
                            {"name": "Notlar ve Kayıt", "fields": ["Toplantı Notu", "Kayıt / Transkript", "AI Özeti"]},
                        ]
                    },
                    "forms": [],
                },

                {
                    "name": "Gündem Maddeleri",
                    "icon": "fas fa-list-ol",
                    "fields": [
                        {"name": "Sıra",             "type": F.NUMBER},
                        {"name": "Konu",             "type": F.TEXT, "required": True},
                        {"name": "Sunan Kişi",       "type": F.USER},
                        {"name": "Ayrılan Süre (dk)", "type": F.NUMBER},
                        {"name": "Kaynak",           "type": F.SELECT,
                         "options": ["Manuel", "Açık Aksiyon (otomatik)"],
                         "colors":  ["#8ed6ff", "#ffa979"]},
                        {"name": "Toplantı",         "type": F.LINK, "target_list": "Toplantılar"},
                        {"name": "İlgili Aksiyon",   "type": F.LINK, "target_list": "Aksiyonlar"},
                        {"name": "İlgili Proje",     "type": F.LINK, "target_app": PROJE_APP, "target_list": "Ar-Ge Projeleri"},
                    ],
                    "views": [
                        {"name": "Tüm Gündem Maddeleri", "type": V.GRID},
                        {"name": "Kaynağa Göre",         "type": V.KANBAN, "group_by": "Kaynak"},
                    ],
                    "forms": [],
                },

                {
                    "name": "Kararlar",
                    "icon": "fas fa-gavel",
                    "fields": [
                        {"name": "Karar No",          "type": F.AUTONUMBER},
                        {"name": "Karar Metni",       "type": F.TEXT, "multiline": True, "required": True},
                        {"name": "Karar Tipi",        "type": F.SELECT,
                         "options": ["Genel", "Faz Kapısı — Geçiş Onayı", "Faz Kapısı — Revizyon", "Proje Durdurma", "Bütçe"],
                         "colors":  ["#8ed6ff", "#5bd77e", "#f5c044", "#ea346f", "#7942e3"]},
                        {"name": "Karar Veren",       "type": F.USER},
                        {"name": "Tarih",             "type": F.DATE},
                        {"name": "Toplantı",          "type": F.LINK, "target_list": "Toplantılar"},
                        {"name": "İlgili Proje",      "type": F.LINK, "target_app": PROJE_APP, "target_list": "Ar-Ge Projeleri"},
                        {"name": "İlgili Faz Kapısı", "type": F.LINK, "target_app": PROJE_APP, "target_list": "Faz Kapıları"},
                    ],
                    "views": [
                        {"name": "Tüm Kararlar",      "type": V.GRID},
                        {"name": "Karar Tipine Göre", "type": V.KANBAN,   "group_by": "Karar Tipi"},
                        {"name": "Karar Takvimi",     "type": V.CALENDAR, "date_field": "Tarih"},
                    ],
                    "forms": [],
                },

                {
                    "name": "Aksiyonlar",
                    "icon": "fas fa-bolt",
                    "list_type": LT.PROCESS,
                    "status_options": [
                        {"label": "Açık",          "color": "#8ed6ff", "closed": False},
                        {"label": "Devam Ediyor",  "color": "#f5c044", "closed": False},
                        {"label": "Gecikmede",     "color": "#ea346f", "closed": False},
                        {"label": "Tamamlandı",    "color": "#5bd77e", "closed": True},
                    ],
                    "default_status": "Açık",
                    "fields": [
                        {"name": "Aksiyon No",     "type": F.AUTONUMBER},
                        {"name": "Aksiyon",        "type": F.TEXT, "required": True},
                        {"name": "Sorumlu",        "type": F.USER},
                        {"name": "Son Tarih",      "type": F.DATE},
                        {"name": "Öncelik",        "type": F.SELECT,
                         "options": ["Düşük", "Orta", "Yüksek", "Kritik"],
                         "colors":  ["#8ed6ff", "#f5c044", "#ffa979", "#ea346f"]},
                        {"name": "Kapanış Notu",   "type": F.TEXT, "multiline": True},
                        {"name": "Toplantı",       "type": F.LINK, "target_list": "Toplantılar"},
                        {"name": "Karar",          "type": F.LINK, "target_list": "Kararlar"},
                        {"name": "İlgili Proje",   "type": F.LINK, "target_app": PROJE_APP, "target_list": "Ar-Ge Projeleri"},
                    ],
                    "views": [
                        {"name": "Tüm Aksiyonlar",   "type": V.GRID},
                        {"name": "Önceliğe Göre",    "type": V.KANBAN,   "group_by": "Öncelik"},
                        {"name": "Son Tarih Takvimi", "type": V.CALENDAR, "date_field": "Son Tarih"},
                        {"name": "Açık Aksiyonlar",  "type": V.GRID,
                         "filter": {"field": "Status", "value": ["Açık", "Devam Ediyor", "Gecikmede"]}},
                        {"name": "Geciken Aksiyonlar", "type": V.GRID,
                         "filter": {"field": "Status", "value": "Gecikmede"}},
                        # FR-3.7 "Bana Atanan Açık Aksiyonlar" → UI'da "Sorumlu = Ben" filtresiyle (bkz. README)
                    ],
                    "layout": {
                        "tabs": [
                            {"name": "Aksiyon", "fields": [
                                "Aksiyon", "Sorumlu", "Son Tarih", "Öncelik",
                                "Toplantı", "Karar", "İlgili Proje",
                            ]},
                            {"name": "Kapanış", "fields": ["Kapanış Notu"]},
                        ]
                    },
                    "forms": [],
                },
            ],
        },
    ],

    "reports": [
        {"label": "Açık Aksiyonlar",          "list": "Aksiyonlar", "type": "kpi_count",
         "filter": {"field": "Status", "value": ["Açık", "Devam Ediyor", "Gecikmede"]}, "icon": "fal fa-bolt", "pin": True},
        {"label": "Geciken Aksiyonlar",       "list": "Aksiyonlar", "type": "kpi_count",
         "filter": {"field": "Status", "value": "Gecikmede"}, "icon": "fal fa-clock", "pin": True},
        {"label": "Kişi Bazında Aksiyonlar",  "list": "Aksiyonlar", "type": "bar",
         "group_by": "Sorumlu", "aggregation": "count", "icon": "fal fa-user-check", "pin": True},
        {"label": "Aksiyon Durumları",        "list": "Aksiyonlar", "type": "pie",
         "group_by": "Status", "aggregation": "count", "icon": "fal fa-chart-pie", "pin": True},
        {"label": "Tipe Göre Toplantılar",    "list": "Toplantılar", "type": "bar",
         "group_by": "Tip", "aggregation": "count", "icon": "fal fa-calendar-alt", "pin": True},
    ],

    "automations": [
        # FR-3.1 — Haftalık seriden toplantı oluştur (her Pazartesi 07:00)
        {
            "name": "Haftalık serilerden toplantıları oluştur",
            "trigger": {"type": "cron", "cron": "0 7 * * 1", "list": "Toplantı Serileri"},
            "actions": [
                {
                    "type":        "loop",
                    "list":        "Toplantı Serileri",
                    "view":        "Aktif Haftalık Seriler",
                    "max_records": 50,
                    "actions": [
                        {
                            "type": "create_record",
                            "list": "Toplantılar",
                            "fields": {
                                "Başlık":            "loop:Seri Adı",
                                "Tip":               "Haftalık Ar-Ge",
                                "Saat":              "loop:Saat",
                                "Süre (dk)":         "loop:Süre (dk)",
                                "Yer / Online Link": "loop:Yer / Online Link",
                                "Organizatör":       "loop:Organizatör",
                                "Katılımcılar":      "loop:Katılımcılar",
                                "Toplantı Serisi":   "loop:_id",
                                "Tarih":             "formula:Today()",
                            },
                        },
                    ],
                },
            ],
        },
        # FR-3.2 — Yeni haftalık Ar-Ge toplantısında açık aksiyonlar gündeme gelir
        {
            "name": "Yeni toplantıda açık aksiyonları gündeme ekle",
            "trigger": {"type": "record_created", "list": "Toplantılar"},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Tip}} = 'Haftalık Ar-Ge'",
                    "then": [
                        {
                            "type":        "loop",
                            "list":        "Aksiyonlar",
                            "view":        "Açık Aksiyonlar",
                            "sort_by":     "Son Tarih ASC",
                            "max_records": 50,
                            "actions": [
                                {
                                    "type": "create_record",
                                    "list": "Gündem Maddeleri",
                                    "fields": {
                                        "Konu":           "loop:Aksiyon",
                                        "Sunan Kişi":     "loop:Sorumlu",
                                        "Kaynak":         "Açık Aksiyon (otomatik)",
                                        "Toplantı":       "trigger:_id",
                                        "İlgili Aksiyon": "loop:_id",
                                        "İlgili Proje":   "loop:İlgili Proje",
                                    },
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        # FR-3.3 — Toplantı yapıldı → katılımcılara özet
        {
            "name": "Toplantı yapıldı → katılımcılara karar/aksiyon özeti",
            "trigger": {"type": "record_updated", "list": "Toplantılar", "watch_field": "Status"},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Status}} = 'Yapıldı'",
                    "then": [
                        {"type": "notify", "to_field": "Katılımcılar",
                         "message": "Toplantı tamamlandı: {{Başlık}} ({{Tarih}}). Kararlar ve aksiyonlar toplantı kaydında. Özet: {{AI Özeti}}"},
                    ],
                },
            ],
        },
        # FR-3.4 — Aksiyon atandı
        {
            "name": "Aksiyon atandığında sorumluya bildir",
            "trigger": {"type": "record_created", "list": "Aksiyonlar"},
            "actions": [
                {"type": "notify", "to_field": "Sorumlu",
                 "message": "Size yeni aksiyon atandı: {{Aksiyon}} — Son tarih: {{Son Tarih}} — Toplantı: {{Toplantı}}"},
            ],
        },
        # FR-3.4 — Son tarihe 2 gün kala
        {
            "name": "Aksiyon son tarihine 2 gün kala hatırlat",
            "trigger": {"type": "time_trigger", "list": "Aksiyonlar", "date_field": "Son Tarih", "offset": -2},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Status}} != 'Tamamlandı'",
                    "then": [
                        {"type": "notify", "to_field": "Sorumlu",
                         "message": "Aksiyon son tarihi 2 gün sonra: {{Aksiyon}} — {{Son Tarih}}"},
                    ],
                },
            ],
        },
        # FR-3.4 — Son tarih geçti → Gecikmede
        {
            "name": "Aksiyon son tarihi geçti → Gecikmede",
            "trigger": {"type": "time_trigger", "list": "Aksiyonlar", "date_field": "Son Tarih", "offset": 1},
            "actions": [
                {
                    "type": "condition",
                    "if":   "{{Status}} != 'Tamamlandı'",
                    "then": [
                        {"type": "update_record", "fields": {"Status": "Gecikmede"}},
                        {"type": "notify", "to_field": "Sorumlu",
                         "message": "Aksiyon gecikmede: {{Aksiyon}} — Son tarih: {{Son Tarih}}"},
                    ],
                },
            ],
        },
    ],

    "seed": {
        "Toplantı Serileri": [
            {"Seri Adı": "Haftalık Ar-Ge Toplantısı", "Tip": "Haftalık Ar-Ge", "Periyot": "Haftalık",
             "Gün": "Pazartesi", "Saat": "10:00", "Süre (dk)": 60, "Aktif": True},
            {"Seri Adı": "PoC Geri Bildirim Toplantısı", "Tip": "Yönetim", "Periyot": "Haftalık",
             "Gün": "Cuma", "Saat": "15:00", "Süre (dk)": 45, "Aktif": True},
        ],
    },
}
