"""
Farmatek — Ar-Ge Proje Yönetimi 2  (workiom-builder spec)

Model 2: Fazlar ve Kilometre Taşları ayrı listelerde; Görevler'de yalnızca görev (alt görev yok),
her görev bir faza bağlı. İlk app ("Ar-Ge Proje Yönetimi") olduğu gibi duruyor.

Build sırası:
  1) python main.py --api-key $KEY build  farmatek_arge2.py
  2) FARMATEK_APP=2 python farmatek_ileri2.py yapi|gorunum|otomasyon|yetki
  3) FARMATEK_APP=2 python farmatek_seed2.py kutuphane

TASK listelerinde sistem alanları (başlık, durum, bitiş, atanan) Workiom tarafından oluşturulur;
adları 2. adımda değiştirilir. Görevler TASK listesi Gantt (başlangıç/bitiş eşlemesi ve native
bağımlılık alanı) için gerekli; sistemin üst/alt görev alanları gizlenir ve kullanılmaz.
"""
from workiom.constants import F, LT, V

C_GREEN, C_YELLOW, C_RED, C_BLUE, C_ORANGE, C_PINK, C_LBLUE, C_TEAL, C_PURPLE = (
    "#5bd77e", "#f5c044", "#ea346f", "#4e86f7", "#ffa979", "#ff86c7", "#8ed6ff", "#5bd7d0", "#7942e3")

GOREV_DURUMLARI = [
    {"label": "Başlamadı",        "color": C_LBLUE,  "closed": False},
    {"label": "Başlayabilir",     "color": C_BLUE,   "closed": False},
    {"label": "Devam Ediyor",     "color": C_YELLOW, "closed": False},
    {"label": "Onay Bekliyor",    "color": C_PURPLE, "closed": False},
    {"label": "Revizyon Gerekli", "color": C_RED,    "closed": False},
    {"label": "Beklemede",        "color": C_ORANGE, "closed": False},
    {"label": "Tamamlandı",       "color": C_GREEN,  "closed": True},
    {"label": "İptal",            "color": C_PINK,   "closed": True},
]
PROJE_DURUMLARI = [
    {"label": "Taslak",                    "color": C_LBLUE,  "closed": False},
    {"label": "Planlanıyor",               "color": C_BLUE,   "closed": False},
    {"label": "Plan Onaylandı (Baseline)", "color": C_PURPLE, "closed": False},
    {"label": "Devam Ediyor",              "color": C_YELLOW, "closed": False},
    {"label": "Beklemede",                 "color": C_ORANGE, "closed": False},
    {"label": "Tamamlandı",                "color": C_GREEN,  "closed": True},
    {"label": "İptal",                     "color": C_RED,    "closed": True},
]

SPEC = {
    "name": "Ar-Ge Proje Yönetimi 2",
    "icon": "fas fa-flask",
    "color": C_TEAL,
    "description": "İlaç Ar-Ge projeleri — fazlar, kilometre taşları ve görevler ayrı listelerde; şablon kütüphanesinden "
                   "otomatik plan, öncül kilidi, zorunlu onay, baseline ve gecikme takibi.",

    "folders": [
        # ════════════════════════════════════════════════════════════════════
        {"name": "Kütüphane", "lists": [
            {
                "name": "Departmanlar",
                "list_type": LT.DATA,
                "icon": "fas fa-sitemap",
                "fields": [
                    {"name": "Kod",                  "type": F.TEXT},
                    {"name": "Departman Yöneticisi", "type": F.USER},
                    {"name": "Onaylayıcı",           "type": F.USER},
                    {"name": "Ekip Üyeleri",         "type": F.MULTIUSER},
                    {"name": "Açıklama",             "type": F.TEXT, "multiline": True},
                ],
                "views": [{"name": "Tüm Departmanlar", "type": V.GRID}],
                "forms": [],
            },
            {
                "name": "Proje Şablonları",
                "list_type": LT.DATA,
                "icon": "fas fa-layer-group",
                "fields": [
                    {"name": "Açıklama",          "type": F.TEXT, "multiline": True},
                    {"name": "Aktif",             "type": F.BOOLEAN},
                    {"name": "Toplam Süre (gün)", "type": F.NUMBER},
                ],
                "views": [{"name": "Tüm Şablonlar", "type": V.GRID}],
                "forms": [],
            },
            {
                "name": "Faz Kütüphanesi",
                "list_type": LT.DATA,
                "icon": "fas fa-stream",
                "fields": [
                    {"name": "Sıra",                   "type": F.NUMBER},
                    {"name": "Başlangıç Ofseti (gün)", "type": F.NUMBER},
                    {"name": "Süre (gün)",             "type": F.NUMBER},
                    {"name": "Açıklama",               "type": F.TEXT, "multiline": True},
                    {"name": "Şablonlar",              "type": F.LINK, "target_list": "Proje Şablonları", "multiple": True},
                ],
                "views": [{"name": "Tüm Fazlar", "type": V.GRID}],
                "forms": [],
            },
            {
                "name": "Kilometre Taşı Kütüphanesi",
                "list_type": LT.DATA,
                "icon": "fas fa-flag-checkered",
                "fields": [
                    {"name": "Gün Ofseti",   "type": F.NUMBER},
                    {"name": "Kritik",       "type": F.BOOLEAN},
                    {"name": "Açıklama",     "type": F.TEXT, "multiline": True},
                    {"name": "Faz",          "type": F.LINK, "target_list": "Faz Kütüphanesi"},
                    {"name": "Şablonlar",    "type": F.LINK, "target_list": "Proje Şablonları", "multiple": True},
                ],
                "views": [{"name": "Tüm Kilometre Taşları", "type": V.GRID}],
                "forms": [],
            },
            {
                # Görev şablonları — yalnızca görev; faza bağlı; öncüller native bağımlılık (ileri script)
                "name": "Görev Kütüphanesi",
                "list_type": LT.TASK,
                "icon": "fas fa-book",
                "fields": [
                    {"name": "WBS No",            "type": F.NUMBER},
                    {"name": "Başlangıç",         "type": F.DATE},
                    {"name": "Referans Tarih",    "type": F.DATE},
                    {"name": "Onay Gerekli",      "type": F.BOOLEAN},
                    {"name": "Kabul Kriteri",     "type": F.TEXT, "multiline": True},
                    {"name": "Varsayım",          "type": F.BOOLEAN},
                    {"name": "Faz",               "type": F.LINK, "target_list": "Faz Kütüphanesi"},
                    {"name": "Kilometre Taşları", "type": F.LINK, "target_list": "Kilometre Taşı Kütüphanesi", "multiple": True},
                    {"name": "Şablonlar",         "type": F.LINK, "target_list": "Proje Şablonları", "multiple": True},
                    {"name": "Sorumlu Departman", "type": F.LINK, "target_list": "Departmanlar"},
                    {"name": "Departman Onaylayıcı", "type": F.LOOKUP, "via": "Sorumlu Departman", "lookup_field": "Onaylayıcı"},
                ],
                "views": [{"name": "Kütüphane Tablosu", "type": V.GRID}],
                "forms": [],
            },
        ]},

        # ════════════════════════════════════════════════════════════════════
        {"name": "Proje Yönetimi", "lists": [
            {
                "name": "Projeler",
                "list_type": LT.TASK,
                "icon": "fas fa-flask",
                "status_options": PROJE_DURUMLARI,
                "default_status": "Taslak",
                "fields": [
                    {"name": "Proje Kodu",       "type": F.AUTONUMBER},
                    {"name": "Ürün / Molekül",   "type": F.TEXT},
                    {"name": "Başlangıç Tarihi", "type": F.DATE},
                    {"name": "Plan Durumu",      "type": F.SELECT, "required": False,
                     "options": ["Bekliyor", "Fazlar Oluşturuldu", "Görevler Oluşturuldu", "Hazır"],
                     "colors":  [C_LBLUE, C_BLUE, C_YELLOW, C_GREEN]},
                    {"name": "Baseline No",      "type": F.NUMBER},
                    {"name": "Baseline Tarihi",  "type": F.DATE},
                    {"name": "Proje Ekibi",      "type": F.MULTIUSER},
                    {"name": "Dokümanlar",       "type": F.FILE},
                    {"name": "Şablon",           "type": F.LINK, "target_list": "Proje Şablonları"},
                ],
                "views": [{"name": "Tüm Projeler", "type": V.GRID}],
                "forms": [],
            },
            {
                "name": "Fazlar",
                "list_type": LT.DATA,
                "icon": "fas fa-stream",
                "fields": [
                    {"name": "Sıra",              "type": F.NUMBER},
                    {"name": "Başlangıç",         "type": F.DATE},
                    {"name": "Bitiş",             "type": F.DATE},
                    {"name": "Baseline Başlangıç", "type": F.DATE},
                    {"name": "Baseline Bitiş",    "type": F.DATE},
                    {"name": "Açıklama",          "type": F.TEXT, "multiline": True},
                    {"name": "Proje",             "type": F.LINK, "target_list": "Projeler"},
                    {"name": "Faz Şablonu",       "type": F.LINK, "target_list": "Faz Kütüphanesi"},
                ],
                "views": [
                    {"name": "Tüm Fazlar",          "type": V.GRID},
                    {"name": "Faz Zaman Çizelgesi", "type": V.TIMELINE, "date_field": "Başlangıç"},
                ],
                "forms": [],
            },
            {
                "name": "Görevler",
                "list_type": LT.TASK,
                "icon": "fas fa-tasks",
                "status_options": GOREV_DURUMLARI,
                "default_status": "Başlamadı",
                "fields": [
                    {"name": "WBS No",                "type": F.NUMBER},
                    {"name": "Başlangıç",             "type": F.DATE},
                    {"name": "% Tamamlanma",          "type": F.NUMBER},
                    {"name": "Onay Gerekli",          "type": F.BOOLEAN},
                    {"name": "Onaylayıcı",            "type": F.USER},
                    {"name": "Onay Durumu",           "type": F.SELECT, "required": False,
                     "options": ["Gerekmiyor", "Bekliyor", "Onaylandı", "Reddedildi"],
                     "colors":  [C_LBLUE, C_YELLOW, C_GREEN, C_RED]},
                    {"name": "Gerçekleşen Başlangıç", "type": F.DATE},
                    {"name": "Gerçekleşen Bitiş",     "type": F.DATE},
                    {"name": "Baseline Başlangıç",    "type": F.DATE},
                    {"name": "Baseline Bitiş",        "type": F.DATE},
                    {"name": "Gecikmede",             "type": F.BOOLEAN},
                    {"name": "Kapalı",                "type": F.NUMBER},   # 0/1 — rollup için
                    {"name": "Notlar",                "type": F.TEXT, "multiline": True},
                    {"name": "Dokümanlar",            "type": F.FILE},
                    {"name": "Proje",                 "type": F.LINK, "target_list": "Projeler"},
                    {"name": "Faz",                   "type": F.LINK, "target_list": "Fazlar"},
                    {"name": "Sorumlu Departman",     "type": F.LINK, "target_list": "Departmanlar"},
                    {"name": "Şablon Öğesi",          "type": F.LINK, "target_list": "Görev Kütüphanesi"},
                    {"name": "Öncül Kayıtları",       "type": F.LINK, "target_list": "Görevler", "multiple": True},
                ],
                "views": [
                    {"name": "Tüm Görevler",     "type": V.GRID},
                    {"name": "Geciken Görevler", "type": V.GRID, "filter": {"field": "Gecikmede", "value": True}},
                    {"name": "Onay Bekleyenler", "type": V.GRID, "filter": {"field": "Onay Durumu", "value": "Bekliyor"}},
                ],
                "layout": {"tabs": [
                    {"name": "Görev",   "fields": ["WBS No", "Proje", "Faz", "Sorumlu Departman", "Başlangıç", "% Tamamlanma", "Notlar"]},
                    {"name": "Onay",    "fields": ["Onay Gerekli", "Onaylayıcı", "Onay Durumu"]},
                    {"name": "Gerçekleşen & Baseline", "fields": [
                        "Gerçekleşen Başlangıç", "Gerçekleşen Bitiş", "Baseline Başlangıç", "Baseline Bitiş", "Gecikmede"]},
                    {"name": "Dokümanlar", "fields": ["Dokümanlar"]},
                ]},
                "forms": [],
            },
            {
                "name": "Kilometre Taşları",
                "list_type": LT.DATA,
                "icon": "fas fa-flag-checkered",
                "fields": [
                    {"name": "Hedef Tarih",       "type": F.DATE},
                    {"name": "Gerçekleşen Tarih", "type": F.DATE},
                    {"name": "Baseline Tarih",    "type": F.DATE},
                    {"name": "KT Durumu",         "type": F.SELECT, "required": False,
                     "options": ["Bekleniyor", "Ulaşıldı", "Gecikti"],
                     "colors":  [C_BLUE, C_GREEN, C_RED]},
                    {"name": "Kritik",            "type": F.BOOLEAN},
                    {"name": "Açıklama",          "type": F.TEXT, "multiline": True},
                    {"name": "Proje",             "type": F.LINK, "target_list": "Projeler"},
                    {"name": "Faz",               "type": F.LINK, "target_list": "Fazlar"},
                    {"name": "KT Şablonu",        "type": F.LINK, "target_list": "Kilometre Taşı Kütüphanesi"},
                    {"name": "Bağlı Görevler",    "type": F.LINK, "target_list": "Görevler", "multiple": True},
                ],
                "views": [
                    {"name": "Tüm Kilometre Taşları", "type": V.GRID},
                    {"name": "Duruma Göre",           "type": V.KANBAN, "group_by": "KT Durumu"},
                    {"name": "KT Takvimi",            "type": V.CALENDAR, "date_field": "Hedef Tarih"},
                ],
                "forms": [],
            },
            {
                "name": "Onay Geçmişi",
                "list_type": LT.DATA,
                "icon": "fas fa-stamp",
                "fields": [
                    {"name": "Kayıt No",  "type": F.AUTONUMBER},
                    {"name": "Karar",     "type": F.SELECT, "required": False,
                     "options": ["Onaylandı", "Reddedildi"], "colors": [C_GREEN, C_RED]},
                    {"name": "Onaylayan", "type": F.USER},
                    {"name": "Tarih",     "type": F.DATE},
                    {"name": "Not",       "type": F.TEXT, "multiline": True},
                    {"name": "Görev",     "type": F.LINK, "target_list": "Görevler"},
                    {"name": "Proje",     "type": F.LINK, "target_list": "Projeler"},
                ],
                "views": [{"name": "Tüm Onaylar", "type": V.GRID}, {"name": "Karara Göre", "type": V.KANBAN, "group_by": "Karar"}],
                "forms": [],
            },
            {
                "name": "Baseline Arşivi",
                "list_type": LT.DATA,
                "icon": "fas fa-history",
                "fields": [
                    {"name": "Kayıt No",            "type": F.AUTONUMBER},
                    {"name": "Baseline No",         "type": F.NUMBER},
                    {"name": "Baseline Tarihi",     "type": F.DATE},
                    {"name": "Planlanan Başlangıç", "type": F.DATE},
                    {"name": "Planlanan Bitiş",     "type": F.DATE},
                    {"name": "Proje",               "type": F.LINK, "target_list": "Projeler"},
                    {"name": "Görev",               "type": F.LINK, "target_list": "Görevler"},
                ],
                "views": [{"name": "Tüm Baseline Kayıtları", "type": V.GRID}],
                "forms": [],
            },
        ]},
    ],

    "lists": [],

    "reports": [
        {"label": "Geciken Görevler", "list": "Görevler", "type": "kpi_count",
         "filter": {"field": "Gecikmede", "value": True}, "icon": "fal fa-exclamation-triangle", "pin": True},
        {"label": "Onay Bekleyen", "list": "Görevler", "type": "kpi_count",
         "filter": {"field": "Onay Durumu", "value": "Bekliyor"}, "icon": "fal fa-stamp", "pin": True},
        {"label": "Ulaşılan Kilometre Taşı", "list": "Kilometre Taşları", "type": "kpi_count",
         "filter": {"field": "KT Durumu", "value": "Ulaşıldı"}, "icon": "fal fa-flag-checkered", "pin": True},
        {"label": "Geciken Kilometre Taşı", "list": "Kilometre Taşları", "type": "kpi_count",
         "filter": {"field": "KT Durumu", "value": "Gecikti"}, "icon": "fal fa-flag", "pin": True},
        {"label": "Görevler – Departmana Göre", "list": "Görevler", "type": "bar",
         "group_by": "Sorumlu Departman", "aggregation": "count", "icon": "fal fa-sitemap", "pin": True},
        {"label": "Görevler – Faza Göre", "list": "Görevler", "type": "bar",
         "group_by": "Faz", "aggregation": "count", "icon": "fal fa-stream", "pin": True},
        {"label": "Kilometre Taşları – Duruma Göre", "list": "Kilometre Taşları", "type": "pie",
         "group_by": "KT Durumu", "aggregation": "count", "icon": "fal fa-flag-checkered", "pin": True},
        {"label": "Kilometre Taşları", "list": "Kilometre Taşları", "type": "table", "icon": "fal fa-flag", "pin": True},
        {"label": "Onay Kararları", "list": "Onay Geçmişi", "type": "pie",
         "group_by": "Karar", "aggregation": "count", "icon": "fal fa-stamp", "pin": True},
    ],

    # Otomasyonlar TASK sistem alanlarına (Durum/Bitiş/Sorumlu) dayandığı için farmatek_ileri2.py'de.
    "automations": [],
    "seed": {},
}
