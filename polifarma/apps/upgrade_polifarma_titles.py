"""
Upgrade script: Polifarma PoC — kayıt başlığı ("Ad") alanlarını formüle çevirir
Run AFTER the three main builds, BEFORE re-running polifarma_stok.py / polifarma_toplanti.py:
    python apps/upgrade_polifarma_titles.py

Workiom her listeye zorunlu, birincil bir "Ad" metin alanı ekler. Boş kalırsa formlar ve
kayıt oluşturan otomasyonlar ("Otomasyon eşlemesinde gerekli alan eksik") çalışmaz.
Bu script "Ad"ı listenin anlamlı alanlarından hesaplanan bir formüle çevirir; kullanıcı
doldurmaz, bağlantı alanlarında kayıtlar bu başlıkla görünür.

İdempotent: zaten aynı formüle sahip alan atlanır.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workiom.client import WorkiomClient, WorkiomAPIError
from workiom.state import AppState


def _load_api_key() -> str:
    if os.path.exists(".env"):
        for line in open(".env"):
            if line.startswith("API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("API_KEY", "")


API_KEY = _load_api_key()
if not API_KEY:
    sys.exit("API_KEY bulunamadı (.env veya ortam değişkeni).")

client = WorkiomClient(API_KEY)

# Liste → başlık parçaları. Metin parçası tek tırnakla, alan adı düz yazılır.
TITLES = {
    "Ar-Ge Proje Takibi": {
        "Ar-Ge Projeleri":        ["Proje Kodu", "' — '", "Ürün Adı"],
        "Faz Kapıları":           ["'Kapı #'", "Kapı No"],
        "Görevler ve Sapmalar":   ["Başlık"],
        "Formülasyon Denemeleri": ["Deneme Kodu"],
        "Analitik Çalışmalar":    ["'Analitik #'", "Çalışma No"],
        "Stabilite Çalışmaları":  ["'Stabilite #'", "Çalışma No"],
        "Stabilite Ölçümleri":    ["'Ölçüm #'", "Ölçüm No"],
    },
    "Numune ve Hammadde Stok": {
        "Tedarikçiler":                  ["Tedarikçi Adı"],
        "Malzeme Kartları":              ["Malzeme Kodu", "' — '", "Malzeme Adı"],
        "Lotlar":                        ["Lot No"],
        "Stok Hareketleri":              ["'Hareket #'", "Hareket No"],
        "Formül Bileşenleri":            ["'Bileşen #'", "Bileşen No"],
        "Numuneler":                     ["Numune Adı"],
        "Malzeme ve Numune Talepleri":   ["'Talep #'", "Talep No"],
        "Depo Görevleri":                ["Başlık"],
    },
    "Toplantı Yönetimi": {
        "Toplantı Serileri":  ["Seri Adı"],
        "Toplantılar":        ["Başlık"],
        "Gündem Maddeleri":   ["Konu"],
        "Kararlar":           ["'Karar #'", "Karar No"],
        "Aksiyonlar":         ["Aksiyon"],
    },
}

for app_name, lists in TITLES.items():
    state = AppState(app_name)
    print(f"\n{'='*60}\n  {app_name}\n{'='*60}")
    for list_name, parts in lists.items():
        list_id = state.get_list_id(list_name)
        fields = {f["name"]: f for f in client.get_all_fields(list_id)}
        ad = fields.get("Ad")
        if not ad:
            print(f"   ·  {list_name}: 'Ad' alanı yok, atlandı")
            continue
        refs = [p if p.startswith("'") else f"_F_{fields[p]['id']}" for p in parts]
        expr = f"Concat({', '.join(refs)})"
        if ad.get("isComputed") and ad.get("expression") == expr:
            print(f"   ↺  {list_name}.Ad zaten formül")
            continue
        body = dict(ad)
        body.update({"isComputed": True, "expression": expr, "isRequired": True, "defaultValue": "-"})
        try:
            client.update_field(list_id, ad["id"], body)
            print(f"   ✅ {list_name}.Ad = {expr}")
        except WorkiomAPIError as e:
            print(f"   ❌ {list_name}.Ad: {e.message} {e.details.strip()}")

print("\nDone.")
