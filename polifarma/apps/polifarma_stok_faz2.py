"""
Polifarma PoC — Stok Faz 2  (upgrade_polifarma_computed.py'den SONRA çalıştırılır)

Upgrade script'in oluşturduğu hesaplanan alanlara ("Kritik Seviye Altında", "Kalan Miktar",
"Toplam Stok") dayanan görünüm, otomasyon ve raporlar. Mevcut "Numune ve Hammadde Stok"
uygulamasına eklenir; listeler state'ten bulunur, alan oluşturulmaz.
"""
from workiom.constants import V

SPEC = {
    "name": "Numune ve Hammadde Stok",
    "icon": "fas fa-boxes",
    "color": "#5bd7d0",
    "description": "Ar-Ge etken madde, eksipiyan, referans ürün ve numunelerin lot bazında giriş/çıkış, kalan miktar ve SKT takibi",

    "lists": [
        {
            "name": "Malzeme Kartları",
            "fields": [],
            "views": [
                {"name": "Kritik Seviyedeki Malzemeler", "type": V.GRID,
                 "filter": {"field": "Kritik Seviye Altında", "value": 1}},
            ],
            "forms": [],
        },
    ],

    "reports": [
        {"label": "Kritik Seviyedeki Malzemeler", "list": "Malzeme Kartları", "type": "kpi_count",
         "filter": {"field": "Kritik Seviye Altında", "value": 1}, "icon": "fal fa-exclamation-circle", "pin": True},
        {"label": "Malzeme Bazında Toplam Stok", "list": "Malzeme Kartları", "type": "table",
         "icon": "fal fa-cubes", "pin": True},
    ],

    "automations": [
        # FR-2.2 — Kritik stok uyarısı (her iş günü 08:00)
        {
            "name": "Kritik stok seviyesi uyarısı (günlük)",
            "trigger": {"type": "cron", "cron": "0 8 * * 1-5", "list": "Malzeme Kartları"},
            "actions": [
                {
                    "type":        "loop",
                    "list":        "Malzeme Kartları",
                    "view":        "Kritik Seviyedeki Malzemeler",
                    "max_records": 100,
                    "actions": [
                        {"type": "notify", "to_field": "Stok Sorumlusu",
                         "message": "Kritik stok: {{Malzeme Kodu}} {{Malzeme Adı}} — Toplam: {{Toplam Stok}} {{Birim}} / Kritik seviye: {{Kritik Stok Seviyesi}}"},
                    ],
                },
            ],
        },
    ],
}
