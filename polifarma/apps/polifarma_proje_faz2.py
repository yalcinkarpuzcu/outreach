"""
Polifarma PoC — Proje Faz 2  (upgrade_polifarma_computed.py'den SONRA çalıştırılır)

"Gerçekleşen Maliyet" (stok tüketiminden rollup) ve COUNT alanlarına dayanan raporlar.
"""
SPEC = {
    "name": "Ar-Ge Proje Takibi",
    "icon": "fas fa-flask",
    "color": "#7942e3",
    "description": "Polifarma Ar-Ge projeleri: stage-gate faz kapıları, formülasyon denemeleri, analitik, stabilite, görev ve sapmalar",

    "lists": [],

    "reports": [
        {"label": "Toplam Bütçe",              "list": "Ar-Ge Projeleri", "type": "kpi",
         "aggregation": "sum", "value_field": "Bütçe", "icon": "fal fa-wallet", "pin": True},
        {"label": "Toplam Gerçekleşen Maliyet", "list": "Ar-Ge Projeleri", "type": "kpi",
         "aggregation": "sum", "value_field": "Gerçekleşen Maliyet", "icon": "fal fa-coins", "pin": True},
        {"label": "Faza Göre Maliyet",          "list": "Ar-Ge Projeleri", "type": "bar",
         "group_by": "Mevcut Faz", "aggregation": "sum", "value_field": "Gerçekleşen Maliyet",
         "icon": "fal fa-chart-bar", "pin": True},
    ],

    "automations": [],
}
