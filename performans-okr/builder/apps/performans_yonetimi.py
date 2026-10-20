"""Performans Yönetimi (KPI Karnesi + OKR) — Workiom builder spec.

Tasarım: performans-okr/TASARIM.md. İK bağlantısı: "İnsan Kaynakları" uygulaması
(Özlük Bilgileri = çalışanlar, Organizasyon = birimler).

Bu spec yalnızca listeleri, düz alanları, bağımsız bağlantıları ve görünümleri kurar.
Üst-alt (ters bağlantılı) ilişkiler, lookup, formül, rollup ve sayım alanları
apps/performans_computed.py ile kurulur.
"""
from workiom.constants import F, V, LT

PAL = ["#5bd77e", "#f5c044", "#ea346f", "#4e86f7", "#ffa979",
       "#ff86c7", "#8ed6ff", "#5bd7d0", "#7942e3"]

IK_APP = "İnsan Kaynakları"
IK_CALISAN = "Özlük Bilgileri"
IK_BIRIM = "Organizasyon"

BIRIMLER = ["%", "Puan", "Skor", "Adet", "Yıl", "Ay", "Hafta", "Gün", "Tutar", "Ton",
            "Dakika", "KWH/M²", "PPM", "TL/KG", "TL/M²", "M²", "Metre"]
GRUPLAR = ["Beklentinin Çok Altında", "Beklenenin Altında", "Beklenen Performans",
           "Beklentinin Üstünde", "Beklentinin Çok Üstünde"]
GRUP_RENK = ["#ea346f", "#ffa979", "#f5c044", "#5bd7d0", "#5bd77e"]


def sel(name, options, colors=None, multi=False):
    cols = colors or [PAL[i % len(PAL)] for i in range(len(options))]
    return {"name": name, "type": F.MULTISELECT if multi else F.SELECT,
            "options": options, "colors": cols}


def txt(name, required=False, multiline=False):
    d = {"name": name, "type": F.TEXT, "required": required}
    if multiline:
        d["multiline"] = True
    return d


def num(name):
    return {"name": name, "type": F.NUMBER}


def date(name):
    return {"name": name, "type": F.DATE}


def user(name):
    return {"name": name, "type": F.USER}


def link(name, target_list, target_app=None, multiple=False):
    d = {"name": name, "type": F.LINK, "target_list": target_list, "multiple": multiple}
    if target_app:
        d["target_app"] = target_app
    return d


SPEC = {
    "name": "Performans Yönetimi",
    "icon": "fas fa-chart-line",
    "color": "#7942e3",
    "description": "Yıllık KPI karnesi (KPI %90 + yetkinlik %10) ve çeyreklik OKR takibi. "
                   "Çalışan ve birim bilgisi İnsan Kaynakları uygulamasından gelir.",
    "folders": [
        # ═══ Klasör 1 · Tanımlar ═══════════════════════════════════════════
        {"name": "Tanımlar", "lists": [
            {"name": "Dönemler", "icon": "far fa-calendar-alt",
             "fields": [
                 txt("Dönem Adı", required=True),
                 sel("Tür", ["Yıl", "Çeyrek"], ["#7942e3", "#4e86f7"]),
                 date("Başlangıç"),
                 date("Bitiş"),
                 date("Hedef Giriş Son Tarihi"),
                 sel("Durum", ["Planlama", "Aktif", "Kapanış", "Kapalı"],
                     ["#8ed6ff", "#5bd77e", "#f5c044", "#ff86c7"]),
                 num("Tür Kodu"),
             ],
             "views": [
                 {"name": "Tüm Dönemler", "type": V.GRID},
                 {"name": "Takvim", "type": V.CALENDAR, "date_field": "Başlangıç"},
             ]},
            {"name": "Form Türleri", "icon": "far fa-layer-group",
             "fields": [
                 txt("Form Türü", required=True),
                 num("Operasyonel Oranı"),
                 num("Proje Oranı"),
                 num("Kurumsal Oranı"),
                 num("Yetkinlik Oranı"),
                 txt("Açıklama", multiline=True),
             ],
             "views": [{"name": "Tüm Form Türleri", "type": V.GRID}]},
            {"name": "Hedef Türleri", "icon": "far fa-tags",
             "fields": [
                 txt("Hedef Türü", required=True),
                 num("Kod"),
                 txt("Açıklama", multiline=True),
             ],
             "views": [{"name": "Tüm Hedef Türleri", "type": V.GRID}]},
            {"name": "Yetkinlikler", "icon": "far fa-star",
             "fields": [
                 txt("Yetkinlik", required=True),
                 txt("Tanım / Davranış Göstergeleri", multiline=True),
                 num("Aktif"),
                 num("Sıra"),
             ],
             "views": [{"name": "Tüm Yetkinlikler", "type": V.GRID}]},
        ]},

        # ═══ Klasör 2 · KPI Karnesi ════════════════════════════════════════
        {"name": "KPI Karnesi", "lists": [
            {"name": "Performans Karneleri", "icon": "far fa-id-card",
             "list_type": LT.PROCESS,
             "status_options": [
                 {"label": "Hedef Belirleme", "color": "#8ed6ff", "closed": False},
                 {"label": "Yönetici Onayında", "color": "#f5c044", "closed": False},
                 {"label": "Aktif", "color": "#4e86f7", "closed": False},
                 {"label": "Değerlendirme", "color": "#ffa979", "closed": False},
                 {"label": "Kalibrasyon", "color": "#7942e3", "closed": False},
                 {"label": "Tamamlandı", "color": "#5bd77e", "closed": True},
                 {"label": "İptal", "color": "#ff86c7", "closed": True},
             ],
             "default_status": "Hedef Belirleme",
             "fields": [
                 {"name": "Karne No", "type": F.AUTONUMBER},
                 txt("Karne"),
                 user("Çalışan (kullanıcı)"),
                 user("Yönetici (kullanıcı)"),
                 sel("Performans Grubu", GRUPLAR, GRUP_RENK),
                 sel("Kalibre Grup", GRUPLAR, GRUP_RENK),
                 txt("Kalibrasyon Notu", multiline=True),
                 sel("Final Performans Grubu", GRUPLAR, GRUP_RENK),
                 date("Onay Tarihi"),
                 txt("Red Notu", multiline=True),
                 link("Çalışan", IK_CALISAN, IK_APP),
                 link("Form Türü", "Form Türleri"),
             ],
             "views": [
                 {"name": "Tüm Karneler", "type": V.GRID},
                 {"name": "Ekibimin Karneleri", "type": V.KANBAN, "group_by": "Status"},
                 {"name": "Kalibrasyon", "type": V.GRID},
             ]},
            {"name": "KPI Hedefleri", "icon": "far fa-bullseye",
             "fields": [
                 {"name": "Hedef No", "type": F.AUTONUMBER},
                 txt("Hedef", required=True),
                 txt("Açıklama / Ölçüm Yöntemi", multiline=True),
                 sel("Hedef Yönelimi", ["Artan", "Azalan"], ["#5bd77e", "#4e86f7"]),
                 sel("Birim", BIRIMLER),
                 num("Hedef Ağırlığı (%)"),
                 num("Hedeflenen"),
                 num("Gerçekleşen"),
                 num("Kilitli"),
                 date("Son Güncelleme"),
                 link("Hedef Türü", "Hedef Türleri"),
             ],
             "views": [
                 {"name": "Tüm Hedefler", "type": V.GRID},
                 {"name": "Gerçekleşen Girişi", "type": V.GRID},
             ]},
            {"name": "Yetkinlik Değerlendirmeleri", "icon": "far fa-user-check",
             "fields": [
                 txt("Değerlendirme"),
                 num("Puan (1–5)"),
                 user("Değerlendiren"),
                 txt("Açıklama", multiline=True),
                 link("Yetkinlik", "Yetkinlikler"),
             ],
             "views": [{"name": "Tüm Değerlendirmeler", "type": V.GRID}]},
        ]},

        # ═══ Klasör 3 · OKR ════════════════════════════════════════════════
        {"name": "OKR", "lists": [
            {"name": "Objective'ler", "icon": "far fa-flag",
             "list_type": LT.PROCESS,
             "status_options": [
                 {"label": "Taslak", "color": "#8ed6ff", "closed": False},
                 {"label": "Onayda", "color": "#f5c044", "closed": False},
                 {"label": "Aktif", "color": "#4e86f7", "closed": False},
                 {"label": "Kapanış", "color": "#ffa979", "closed": False},
                 {"label": "Kapandı", "color": "#5bd77e", "closed": True},
                 {"label": "İptal", "color": "#ff86c7", "closed": True},
             ],
             "default_status": "Taslak",
             "fields": [
                 {"name": "OKR No", "type": F.AUTONUMBER},
                 txt("Objective", required=True),
                 txt("Açıklama / Neden", multiline=True),
                 sel("Seviye", ["Şirket", "Departman", "Kişi"], ["#7942e3", "#4e86f7", "#5bd7d0"]),
                 num("Seviye Kodu"),
                 user("Sahip"),
                 {"name": "Katkı Verenler", "type": F.MULTIUSER},
                 user("Onaylayıcı"),
                 sel("OKR Türü", ["Zorunlu (Committed)", "İddialı (Aspirational)"],
                     ["#4e86f7", "#7942e3"]),
                 num("Başarı Eşiği"),
                 sel("Renk", ["Yeşil", "Sarı", "Kırmızı"], ["#5bd77e", "#f5c044", "#ea346f"]),
                 num("Kapanış Puanı"),
                 txt("Retro Notu", multiline=True),
                 date("Kapanış Tarihi"),
                 txt("Red Notu", multiline=True),
                 link("Departman", IK_BIRIM, IK_APP),
                 link("Katkı Veren Departmanlar", IK_BIRIM, IK_APP, multiple=True),
                 link("Sahip Çalışan", IK_CALISAN, IK_APP),
             ],
             "views": [
                 {"name": "Tüm OKR'lar", "type": V.GRID},
                 {"name": "Bu Çeyrek", "type": V.KANBAN, "group_by": "Renk"},
                 {"name": "Durumlara Göre", "type": V.KANBAN, "group_by": "Status"},
                 {"name": "Seviyeye Göre", "type": V.KANBAN, "group_by": "Seviye"},
             ]},
            {"name": "Key Result'lar", "icon": "far fa-chart-bar",
             "fields": [
                 {"name": "KR No", "type": F.AUTONUMBER},
                 txt("Key Result", required=True),
                 user("Sahip"),
                 sel("KR Tipi", ["Metrik", "Kilometre Taşı"], ["#4e86f7", "#7942e3"]),
                 num("Başlangıç Değeri"),
                 num("Hedef Değer"),
                 num("Güncel Değer"),
                 sel("Birim", BIRIMLER),
                 num("Güven (1–10)"),
                 date("Son Check-in Tarihi"),
                 num("Takipte"),
             ],
             "views": [
                 {"name": "Tüm KR'lar", "type": V.GRID},
                 {"name": "KR'larım", "type": V.GRID},
             ]},
            {"name": "Check-in'ler", "icon": "far fa-check-circle",
             "fields": [
                 txt("Check-in"),
                 date("Tarih"),
                 num("Yeni Değer"),
                 num("Güven (1–10)"),
                 txt("Bu Hafta Yapılan", multiline=True),
                 txt("Engel / İhtiyaç", multiline=True),
                 user("Giren"),
             ],
             "views": [
                 {"name": "Son Check-in'ler", "type": V.GRID},
                 {"name": "Takvim", "type": V.CALENDAR, "date_field": "Tarih"},
             ]},
        ]},
    ],
    "lists": [],
    "automations": [],
}
