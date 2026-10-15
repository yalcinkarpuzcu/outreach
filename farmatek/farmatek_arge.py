"""
Farmatek — Ar-Ge Proje Yönetimi  (workiom-builder spec)

Tasarım: farmatek/TASARIM.md

Build sırası:
  1) python main.py --api-key $KEY build  <bu dosya>          # listeler, skaler/link alanlar, grid görünümler, raporlar, basit otomasyonlar
  2) python farmatek/farmatek_ileri.py                         # TASK alan eşlemeleri + sistem alanı adları, native bağımlılık (dataType 21),
                                                               # Gantt (viewType 12), formül/rollup, iç içe otomasyonlar (A1,A2,A3,A5,A6,A9),
                                                               # validasyonlar, roller
  3) python farmatek/farmatek_seed.py                          # departman, şablon, kütüphane (tarih+öncül+hiyerarşi), demo projeler

Not: TASK tipindeki listelerin sistem alanları (başlık, durum, bitiş, atanan, parent/subtasks)
Workiom tarafından otomatik oluşturulur; bu spec'te tekrar tanımlanmaz. Adları ve durum
seçenekleri 2. adımda düzenlenir. Bu yüzden sistem alanına dayanan Kanban/Takvim/Gantt
görünümleri ve otomasyonlar da 2. adımdadır.
"""
from workiom.constants import F, LT, V

C_GREEN, C_YELLOW, C_RED, C_BLUE, C_ORANGE, C_PINK, C_LBLUE, C_TEAL, C_PURPLE = (
    "#5bd77e", "#f5c044", "#ea346f", "#4e86f7", "#ffa979", "#ff86c7", "#8ed6ff", "#5bd7d0", "#7942e3")

TUR = {"name": "Tür", "type": F.SELECT, "required": False,
       "options": ["Faz", "Alt Faz", "Görev", "Alt Görev", "Kilometre Taşı"],
       "colors":  [C_PURPLE, C_BLUE, C_LBLUE, C_TEAL, C_ORANGE]}

SPEC = {
    "name": "Ar-Ge Proje Yönetimi",
    "icon": "fas fa-flask",
    "color": C_BLUE,
    "description": "İlaç Ar-Ge projelerinin şablon kütüphanesinden planlanması, Gantt ile takibi, "
                   "öncül kilitleri, zorunlu onaylar, baseline ve gecikme yönetimi.",

    "folders": [
        # ════════════════════════════════════════════════════════════════════
        {"name": "Kütüphane", "lists": [
            {
                "name": "Departmanlar",
                "list_type": LT.DATA,
                "icon": "fas fa-sitemap",
                "fields": [
                    {"name": "Departman Adı",        "type": F.TEXT, "required": True},
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
                    {"name": "Şablon Adı", "type": F.TEXT, "required": True},
                    {"name": "Açıklama",   "type": F.TEXT, "multiline": True},
                    {"name": "Aktif",      "type": F.BOOLEAN},
                ],
                "views": [{"name": "Tüm Şablonlar", "type": V.GRID}],
                "forms": [],
            },
            {
                # MS Project şablonu gibi: fazlar = üst öğe, öncüller = native bağımlılık (2. adım)
                "name": "Görev Kütüphanesi",
                "list_type": LT.TASK,
                "icon": "fas fa-book",
                "fields": [
                    {"name": "WBS No",              "type": F.NUMBER},
                    TUR,
                    {"name": "Başlangıç",           "type": F.DATE},     # → startDateFieldId (2. adım)
                    {"name": "Referans Tarih",      "type": F.DATE},     # Gün 0 = 2026-01-01 (seed)
                    {"name": "Kilometre Taşı",      "type": F.BOOLEAN},
                    {"name": "Onay Gerekli",        "type": F.BOOLEAN},
                    {"name": "Onaylayıcı (Özel)",   "type": F.USER},
                    {"name": "Kabul Kriteri",       "type": F.TEXT, "multiline": True},
                    {"name": "Varsayım",            "type": F.BOOLEAN},
                    {"name": "Şablonlar",           "type": F.LINK, "target_list": "Proje Şablonları", "multiple": True},
                    {"name": "Sorumlu Departman",   "type": F.LINK, "target_list": "Departmanlar"},
                    {"name": "Departman Yöneticisi", "type": F.LOOKUP, "via": "Sorumlu Departman",
                     "lookup_field": "Departman Yöneticisi"},
                    {"name": "Departman Onaylayıcı", "type": F.LOOKUP, "via": "Sorumlu Departman",
                     "lookup_field": "Onaylayıcı"},
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
                "fields": [
                    {"name": "Proje Kodu",       "type": F.AUTONUMBER},
                    {"name": "Ürün / Molekül",   "type": F.TEXT},
                    {"name": "Başlangıç Tarihi", "type": F.DATE},       # → startDateFieldId
                    {"name": "Plan Durumu",      "type": F.SELECT, "required": False,
                     "options": ["Bekliyor", "Görevler Oluşturuldu", "Hazır"],
                     "colors":  [C_LBLUE, C_YELLOW, C_GREEN]},
                    {"name": "Baseline No",      "type": F.NUMBER},
                    {"name": "Baseline Tarihi",  "type": F.DATE},
                    {"name": "Proje Ekibi",      "type": F.MULTIUSER},
                    {"name": "Açıklama",         "type": F.TEXT, "multiline": True},
                    {"name": "Dokümanlar",       "type": F.FILE},
                    {"name": "Şablon",           "type": F.LINK, "target_list": "Proje Şablonları"},
                ],
                "views": [{"name": "Tüm Projeler", "type": V.GRID}],
                "forms": [],
            },
            {
                "name": "Görevler",
                "list_type": LT.TASK,
                "icon": "fas fa-tasks",
                "fields": [
                    {"name": "WBS No",                 "type": F.NUMBER},
                    TUR,
                    {"name": "Başlangıç",              "type": F.DATE},  # → startDateFieldId
                    {"name": "% Tamamlanma",           "type": F.NUMBER},
                    {"name": "Kilometre Taşı",         "type": F.BOOLEAN},
                    {"name": "Onay Gerekli",           "type": F.BOOLEAN},
                    {"name": "Onaylayıcı",             "type": F.USER},
                    {"name": "Onay Durumu",            "type": F.SELECT, "required": False,
                     "options": ["Gerekmiyor", "Bekliyor", "Onaylandı", "Reddedildi"],
                     "colors":  [C_LBLUE, C_YELLOW, C_GREEN, C_RED]},
                    {"name": "Son Onay Notu",          "type": F.TEXT, "multiline": True},
                    {"name": "Gerçekleşen Başlangıç",  "type": F.DATE},
                    {"name": "Gerçekleşen Bitiş",      "type": F.DATE},
                    {"name": "Baseline Başlangıç",     "type": F.DATE},
                    {"name": "Baseline Bitiş",         "type": F.DATE},
                    {"name": "Gecikmede",              "type": F.BOOLEAN},
                    {"name": "Gecikme Sayacı",         "type": F.NUMBER},   # 0/1 — rollup için
                    {"name": "Kapalı",                 "type": F.NUMBER},   # 0/1 — rollup için
                    {"name": "Notlar",                 "type": F.TEXT, "multiline": True},
                    {"name": "Dokümanlar",             "type": F.FILE},
                    {"name": "Proje",                  "type": F.LINK, "target_list": "Projeler"},
                    {"name": "Sorumlu Departman",      "type": F.LINK, "target_list": "Departmanlar"},
                    {"name": "Şablon Öğesi",           "type": F.LINK, "target_list": "Görev Kütüphanesi"},
                    {"name": "Öncül Kayıtları",        "type": F.LINK, "target_list": "Görevler", "multiple": True},
                    # "Proje Yöneticisi" lookup'ı (Projeler.atanan sistem alanı) 2. adımda eklenir.
                ],
                "views": [
                    {"name": "Tüm Görevler",      "type": V.GRID},
                    {"name": "Geciken Görevler",  "type": V.GRID,
                     "filter": {"field": "Gecikmede", "value": True}},
                    {"name": "Kilometre Taşları", "type": V.GRID,
                     "filter": {"field": "Kilometre Taşı", "value": True}},
                    {"name": "Onay Bekleyenler",  "type": V.GRID,
                     "filter": {"field": "Onay Durumu", "value": "Bekliyor"}},
                ],
                "layout": {"tabs": [
                    {"name": "Görev",   "fields": ["WBS No", "Tür", "Proje", "Sorumlu Departman",
                                                   "Başlangıç", "Kilometre Taşı", "% Tamamlanma", "Notlar"]},
                    {"name": "Onay",    "fields": ["Onay Gerekli", "Onaylayıcı", "Onay Durumu", "Son Onay Notu"]},
                    {"name": "Gerçekleşen & Baseline", "fields": [
                        "Gerçekleşen Başlangıç", "Gerçekleşen Bitiş",
                        "Baseline Başlangıç", "Baseline Bitiş", "Gecikmede"]},
                    {"name": "Dokümanlar", "fields": ["Dokümanlar"]},
                ]},
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
                "views": [
                    {"name": "Tüm Onaylar",   "type": V.GRID},
                    {"name": "Karara Göre",   "type": V.KANBAN, "group_by": "Karar"},
                ],
                "forms": [],
            },
            {
                "name": "Baseline Arşivi",
                "list_type": LT.DATA,
                "icon": "fas fa-history",
                "fields": [
                    {"name": "Kayıt No",              "type": F.AUTONUMBER},
                    {"name": "Baseline No",           "type": F.NUMBER},
                    {"name": "Baseline Tarihi",       "type": F.DATE},
                    {"name": "Planlanan Başlangıç",   "type": F.DATE},
                    {"name": "Planlanan Bitiş",       "type": F.DATE},
                    {"name": "Proje",                 "type": F.LINK, "target_list": "Projeler"},
                    {"name": "Görev",                 "type": F.LINK, "target_list": "Görevler"},
                ],
                "views": [{"name": "Tüm Baseline Kayıtları", "type": V.GRID}],
                "forms": [],
            },
        ]},
    ],

    "lists": [],

    # Sistem alanına (Durum/Bitiş/Sorumlu) dayanan raporlar 2. adımda eklenir.
    "reports": [
        {"label": "Geciken Görevler", "list": "Görevler", "type": "kpi_count",
         "filter": {"field": "Gecikmede", "value": True}, "icon": "fal fa-exclamation-triangle", "pin": True},
        {"label": "Onay Bekleyen", "list": "Görevler", "type": "kpi_count",
         "filter": {"field": "Onay Durumu", "value": "Bekliyor"}, "icon": "fal fa-stamp", "pin": True},
        {"label": "Görevler – Departmana Göre", "list": "Görevler", "type": "bar",
         "group_by": "Sorumlu Departman", "aggregation": "count", "icon": "fal fa-sitemap", "pin": True},
        {"label": "Onay Kararları", "list": "Onay Geçmişi", "type": "pie",
         "group_by": "Karar", "aggregation": "count", "icon": "fal fa-stamp", "pin": True},
        {"label": "Kilometre Taşları", "list": "Görevler", "type": "table",
         "icon": "fal fa-flag", "pin": True},
    ],

    # Basit otomasyonlar burada; iç içe olanlar (A1, A2, A3, A5, A6, A9) farmatek_ileri.py'de.
    # Tüm otomasyonlar TASK sistem alanlarına (Durum/Bitiş/Sorumlu) dayandığı için
    # farmatek_ileri.py'de kurulur (A1–A9, bkz. TASARIM.md §3).
    "automations": [],

    "seed": {},   # seed farmatek_seed.py ile (tarih/öncül/hiyerarşi API ile yazılır)
}
