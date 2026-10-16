"""A4 · Planlama & Üretim — İstasyonlar, Üretim Planları, İş Emirleri (doküman 6.4).
Formül / sayım alanları ileri_computed.py'de."""
from workiom.constants import F, V
from apps.ileri_common import sel, txt, link, lookup, APP_PRJ

PLAN_DURUM = ["Planlandı", "İmalata Sunuldu", "Üretimde", "Kalite Kontrol", "Sevke Hazır",
              "Sevk Edildi", "Montaj Bekliyor", "Montaj Tamamlandı", "Montaj Yok"]
PLAN_RENK = ["#8ed6ff", "#4e86f7", "#f5c044", "#7942e3", "#5bd7d0", "#ffa979",
             "#ff86c7", "#5bd77e", "#5bd77e"]

IS_RENGI = ["Yeşil", "Gri", "Sarı", "Mor", "Mavi", "Turuncu", "Kırmızı", "Pembe", "Turkuaz"]
IS_RENGI_RENK = ["#5bd77e", "#8ed6ff", "#f5c044", "#7942e3", "#4e86f7", "#ffa979",
                 "#ea346f", "#ff86c7", "#5bd7d0"]

SPEC = {
    "name": "Planlama & Üretim",
    "icon": "fas fa-industry",
    "color": "#ffa979",
    "description": "Sözleşmeli işlerin planlanması, istasyon bazlı imalat, sevkiyat ve montaj (A4)",

    "lists": [
        {
            "name": "İstasyonlar",
            "icon": "far fa-warehouse",
            "primary": "İstasyon Adı",
            "fields": [
                txt("İstasyon Adı", required=True),
                {"name": "Sorumlu", "type": F.USER},
                {"name": "Sıra", "type": F.NUMBER},
                sel("Aşama Grubu", ["Hazırlık", "Toplama", "Paketleme"]),
                {"name": "Aktif mi", "type": F.BOOLEAN},
            ],
            "views": [{"name": "Tüm İstasyonlar", "type": V.GRID}],
            "forms": [],
        },
        {
            "name": "Üretim Planları",
            "icon": "far fa-industry-alt",
            "primary": "Plan Adı",
            "fields": [
                txt("Plan Adı"),
                {"name": "Plan No", "type": F.AUTONUMBER},
                {"name": "Satış Sorumlusu", "type": F.USER},
                {"name": "İmalat Sorumlusu", "type": F.USER},
                txt("İmalat Talimatı", multiline=True),
                {"name": "Teknik Resim / Arşiv Linki", "type": F.URL},
                sel("İş Rengi", IS_RENGI, IS_RENGI_RENK),
                {"name": "Başlangıç Tarihi", "type": F.DATE},
                {"name": "Hedef Bitiş Tarihi", "type": F.DATE},
                {"name": "İmalata Sunma Tarihi", "type": F.DATE},
                {"name": "İmalata Alınma Tarihi", "type": F.DATE},
                {"name": "Biten Panel", "type": F.NUMBER},
                {"name": "Biten Teleskop", "type": F.NUMBER},
                {"name": "Biten Kapı", "type": F.NUMBER},
                sel("Durum", PLAN_DURUM, PLAN_RENK),
                txt("Kalite Kontrol Notu", multiline=True),
                {"name": "Sevk Tarihi", "type": F.DATE},
                {"name": "Montaj Sorumlusu", "type": F.USER},
                {"name": "Montaj Tarihi", "type": F.DATE},
                {"name": "Montaj Fotoğrafları", "type": F.FILE},
                txt("Yorum", multiline=True),
                link("Sözleşme", "Sözleşmeler", APP_PRJ, backlink="Üretim Planları"),
                # PRJ-17 doldurur (lookup zinciri ve otomasyonlar için gerçek bağlantı)
                link("Proje", "Projeler", APP_PRJ, backlink="Üretim Planları"),
                link("Esas Revizyon", "Teklif Revizyonları", APP_PRJ, backlink="Üretim Planları"),
                lookup("Firma", "Sözleşme", "Firma"),
                lookup("Proje Yeri", "Sözleşme", "Proje Yeri"),
                lookup("Montaj Var mı", "Sözleşme", "Montaj Var mı"),
            ],
            "views": [
                {"name": "Tüm Planlar", "type": V.GRID},
                {"name": "Duruma Göre", "type": V.KANBAN, "group_by": "Durum"},
                {"name": "Zaman Çizelgesi", "type": V.TIMELINE, "date_field": "Başlangıç Tarihi"},
                {"name": "Takvim", "type": V.CALENDAR, "date_field": "Hedef Bitiş Tarihi"},
                {"name": "Biten İşler", "type": V.GRID,
                 "filter": {"field": "Durum", "value": ["Montaj Tamamlandı", "Montaj Yok"]}},
                {"name": "Montaj", "type": V.CALENDAR, "date_field": "Montaj Tarihi"},
            ],
            "forms": [],
        },
        {
            "name": "İş Emirleri",
            "icon": "far fa-hard-hat",
            "primary": "İş Emri",
            "fields": [
                txt("İş Emri"),
                {"name": "İş Emri No", "type": F.AUTONUMBER},
                txt("Renk / Desen Bilgisi"),
                sel("Durum", ["Bekliyor", "Hazır", "Devam Ediyor", "Tamamlandı", "Gerekmiyor"],
                    ["#8ed6ff", "#4e86f7", "#f5c044", "#5bd77e", "#ff86c7"]),
                {"name": "Operatör", "type": F.USER},
                {"name": "Planlanan Tarih", "type": F.DATE},
                {"name": "Başlama Zamanı", "type": F.DATE},
                {"name": "Tamamlanma Zamanı", "type": F.DATE},
                {"name": "Kalite Onayı", "type": F.BOOLEAN},
                txt("Not", multiline=True),
                link("Üretim Planı", "Üretim Planları", backlink="İş Emirleri"),
                link("İstasyon", "İstasyonlar", backlink="İş Emirleri"),
                lookup("İstasyon Sırası", "İstasyon", "Sıra"),
                lookup("Aşama Grubu", "İstasyon", "Aşama Grubu"),
                lookup("İstasyon Sorumlusu", "İstasyon", "Sorumlu"),
                lookup("İş Rengi", "Üretim Planı", "İş Rengi"),
                lookup("Hedef Bitiş Tarihi", "Üretim Planı", "Hedef Bitiş Tarihi"),
            ],
            "views": [
                {"name": "Tüm İş Emirleri", "type": V.GRID},
                {"name": "Duruma Göre", "type": V.KANBAN, "group_by": "Durum"},
                {"name": "Planlanan Takvim", "type": V.CALENDAR, "date_field": "Planlanan Tarih"},
                {"name": "Açık İş Emirleri", "type": V.GRID,
                 "filter": {"field": "Durum", "value": ["Bekliyor", "Hazır", "Devam Ediyor"]}},
                {"name": "Benim İstasyonum", "type": V.GRID},
            ],
            "forms": [],
        },
    ],
    "automations": [],
}
