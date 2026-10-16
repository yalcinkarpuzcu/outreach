"""İleri Acoustic (Turkowall) – ortak seçenek listeleri ve yardımcılar."""
from workiom.constants import F

PAL = ["#5bd77e", "#f5c044", "#ea346f", "#4e86f7", "#ffa979",
       "#ff86c7", "#8ed6ff", "#5bd7d0", "#7942e3"]

APP_CRM = "CRM"
APP_PRJ = "Proje & Teklif"
APP_HSP = "Teknik Hesaplama"
APP_URT = "Planlama & Üretim"
APP_STN = "Satınalma & Stok"


def sel(name, options, colors=None, multi=False, **kw):
    """SELECT / MULTISELECT — renkler paletten sırayla atanır (6.0)."""
    cols = colors or [PAL[i % len(PAL)] for i in range(len(options))]
    return {"name": name, "type": F.MULTISELECT if multi else F.SELECT,
            "options": options, "colors": cols, "required": False, **kw}


def txt(name, required=False, multiline=False):
    d = {"name": name, "type": F.TEXT, "required": required}
    if multiline:
        d["multiline"] = True
    return d


def link(name, target_list, target_app=None, backlink=None, multiple=False):
    d = {"name": name, "type": F.LINK, "target_list": target_list, "multiple": multiple}
    if target_app:
        d["target_app"] = target_app
    if backlink:
        d["backlink"] = backlink
    return d


def lookup(name, via, field):
    return {"name": name, "type": F.LOOKUP, "via": via, "lookup_field": field}


ULKELER = ["Türkiye", "Almanya", "Azerbaycan", "Birleşik Arap Emirlikleri", "Birleşik Krallık",
           "Fransa", "Gana", "Gürcistan", "Irak", "İtalya", "Katar", "Kazakistan",
           "Kuveyt", "Libya", "Mısır", "Nijerya", "Özbekistan", "Romanya", "Rusya",
           "Suudi Arabistan", "Türkmenistan", "Umman", "Ürdün", "Diğer"]

SISTEMLER = ["PANELITE", "PANSMART", "PANPLUS", "PANSLIM 80", "PANSLIDE WOOD",
             "EPART-DOORSON", "KARIŞIK"]

LISTE_TURU = ["Alüminyum Kesim", "Giyotin Borusu", "Ahşap Kesim", "Boya", "Aksesuar", "Ambalaj"]

MALZEME_KATEGORI = ["Profil", "Ray", "Makara", "Plaka", "Yüzey", "Boya", "Cam", "Aksesuar", "Ambalaj"]

PARA = ["USD", "EUR", "TL"]
