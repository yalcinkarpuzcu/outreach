"""
Upgrade script: Polifarma PoC — back-link, rollup, COUNT ve formül alanları
Run AFTER the three main builds:
    python main.py build apps/polifarma_arge_proje.py
    python main.py build apps/polifarma_stok.py
    python main.py build apps/polifarma_toplanti.py
    python apps/upgrade_polifarma_computed.py
    python main.py build apps/polifarma_stok_faz2.py
    python main.py build apps/polifarma_proje_faz2.py

Phase 1: Stok formülleri — Stok Etkisi, Tüketim Maliyeti, SKT'ye Kalan Gün, QR kodlar
Phase 2: Stok rollup'ları — Lot.Kalan Miktar → Malzeme.Toplam Stok → Kritik Seviye Altında
Phase 3: Proje 360 — Ar-Ge Projeleri'ne tüm ilişkili listelerin back-link'leri + Gerçekleşen Maliyet
Phase 4: Diğer back-link'ler — Deneme, Stabilite, Faz Kapısı, Toplantı, Karar, Tedarikçi

İdempotent: aynı isimde alan varsa atlanır.
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
PROJE  = AppState("Ar-Ge Proje Takibi")
STOK   = AppState("Numune ve Hammadde Stok")
TOPL   = AppState("Toplantı Yönetimi")

SUM, AVG, COUNT_ = 0, 1, 4


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _existing(list_id: str, name: str) -> int | None:
    for f in client.get_all_fields(list_id):
        if f.get("name") == name:
            return f["id"]
    return None


def _create(state: AppState, list_name: str, payload: dict) -> int | None:
    list_id = state.get_list_id(list_name)
    name = payload["name"]
    fid = _existing(list_id, name)
    if fid:
        print(f"   ↺  {list_name}.{name} zaten var (id={fid})")
    else:
        try:
            fid = client.post(f"/api/services/app/Fields/Create?listId={list_id}", payload)["id"]
            print(f"   ✅ {list_name}.{name} (id={fid})")
        except WorkiomAPIError as e:
            print(f"   ❌ {list_name}.{name}: {e.message}")
            return None
    state.set_field_id(list_name, name, fid)
    state.save()
    return fid


def formula(state, list_name, name, expression, data_type=1):
    return _create(state, list_name, {
        "name": name, "dataType": data_type, "isRequired": False, "isVisible": True,
        "isComputed": True, "expression": expression,
    })


def backlink(parent: AppState, parent_list: str, child: AppState, child_list: str,
             fk_field: str, name: str):
    payload = {
        "name": name, "dataType": 5,
        "linkedListId": child.get_list_id(child_list),
        "linkedFieldId": child.get_field_id(child_list, fk_field),
        "isAssociation": True, "hasAssociatedLinkedField": True,
        "allowMultiple": True, "isRequired": False, "isVisible": True,
    }
    if child.app_id != parent.app_id:
        payload["linkedAppId"] = child.app_id
    return _create(parent, parent_list, payload)


def rollup(parent: AppState, parent_list: str, child: AppState, child_list: str,
           value_field_id: int, backlink_id: int, name: str, summary=SUM):
    return _create(parent, parent_list, {
        "name": name, "dataType": 1, "isRollup": True, "isRequired": False, "isVisible": True,
        "linkedListId": child.get_list_id(child_list),
        "linkedFieldId": value_field_id,
        "rollupFieldId": backlink_id,
        "rollupSummaryType": summary,
    })


def count(parent: AppState, parent_list: str, backlink_id: int, name: str):
    return _create(parent, parent_list, {
        "name": name, "dataType": 12, "isRequired": False, "isVisible": True,
        "countLocalLinkedFieldId": backlink_id,
    })


def F_(state: AppState, list_name: str, field: str) -> str:
    fid = state.get_field_id(list_name, field)
    if not fid:
        sys.exit(f"Alan bulunamadı: {list_name}.{field} — önce ana build'leri çalıştırın.")
    return f"_F_{fid}"


def phase(title: str):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


# ─── Phase 1 — Stok formülleri ────────────────────────────────────────────────
phase("Phase 1 — Stok formülleri")

stok_etkisi = formula(STOK, "Stok Hareketleri", "Stok Etkisi",
    f"Coalesce({F_(STOK, 'Stok Hareketleri', 'Giriş Miktarı')}, 0) - "
    f"Coalesce({F_(STOK, 'Stok Hareketleri', 'Çıkış Miktarı')}, 0)")

tuketim_maliyeti = formula(STOK, "Stok Hareketleri", "Tüketim Maliyeti",
    f"Coalesce({F_(STOK, 'Stok Hareketleri', 'Çıkış Miktarı')}, 0) * "
    f"Coalesce({F_(STOK, 'Stok Hareketleri', 'Birim Maliyet')}, 0)")

formula(STOK, "Lotlar", "SKT'ye Kalan Gün",
    f"SubtractDate({F_(STOK, 'Lotlar', 'SKT / Retest Tarihi')}, Today())")

# FR-2.9 (opsiyonel) — QR kodlar (dataType 9 = FILE)
formula(STOK, "Lotlar", "QR Kod", f"CreateQRCode({F_(STOK, 'Lotlar', 'Lot No')})", data_type=9)
formula(STOK, "Numuneler", "QR Kod", f"CreateQRCode({F_(STOK, 'Numuneler', 'Numune No')})", data_type=9)


# ─── Phase 2 — Stok rollup'ları ───────────────────────────────────────────────
phase("Phase 2 — Kalan miktar ve toplam stok")

lot_hareketler = backlink(STOK, "Lotlar", STOK, "Stok Hareketleri", "Lot", "Hareketler")
kalan = None
if lot_hareketler and stok_etkisi:
    kalan = rollup(STOK, "Lotlar", STOK, "Stok Hareketleri", stok_etkisi, lot_hareketler, "Kalan Miktar")

malz_lotlar = backlink(STOK, "Malzeme Kartları", STOK, "Lotlar", "Malzeme", "Lotlar")
toplam = None
if malz_lotlar and kalan:
    toplam = rollup(STOK, "Malzeme Kartları", STOK, "Lotlar", kalan, malz_lotlar, "Toplam Stok")
if toplam:
    formula(STOK, "Malzeme Kartları", "Kritik Seviye Altında",
        f"If(_F_{toplam} < Coalesce({F_(STOK, 'Malzeme Kartları', 'Kritik Stok Seviyesi')}, 0), 1, 0)")



# ─── Phase 3 — Proje 360 (FR-1.6, FR-2.5, FR-3.5) ─────────────────────────────
phase("Phase 3 — Ar-Ge Projeleri: Proje 360")

backlink(PROJE, "Ar-Ge Projeleri", PROJE, "Faz Kapıları",           "Proje", "Faz Kapıları")
bl_den  = backlink(PROJE, "Ar-Ge Projeleri", PROJE, "Formülasyon Denemeleri", "Proje", "Denemeler")
backlink(PROJE, "Ar-Ge Projeleri", PROJE, "Analitik Çalışmalar",    "Proje", "Analitik Çalışmalar")
backlink(PROJE, "Ar-Ge Projeleri", PROJE, "Stabilite Çalışmaları",  "Proje", "Stabilite Çalışmaları")
bl_gor  = backlink(PROJE, "Ar-Ge Projeleri", PROJE, "Görevler ve Sapmalar", "Proje", "Görevler ve Sapmalar")

bl_stok = backlink(PROJE, "Ar-Ge Projeleri", STOK, "Stok Hareketleri", "İlgili Proje", "Stok Tüketimi")
backlink(PROJE, "Ar-Ge Projeleri", STOK, "Malzeme ve Numune Talepleri", "İlgili Proje", "Malzeme Talepleri")
backlink(PROJE, "Ar-Ge Projeleri", STOK, "Numuneler",            "İlgili Proje", "Numuneler")

backlink(PROJE, "Ar-Ge Projeleri", TOPL, "Toplantılar",          "İlgili Projeler", "Toplantılar")
backlink(PROJE, "Ar-Ge Projeleri", TOPL, "Kararlar",             "İlgili Proje", "Toplantı Kararları")
bl_aks  = backlink(PROJE, "Ar-Ge Projeleri", TOPL, "Aksiyonlar", "İlgili Proje", "Toplantı Aksiyonları")

if bl_stok and tuketim_maliyeti:
    rollup(PROJE, "Ar-Ge Projeleri", STOK, "Stok Hareketleri", tuketim_maliyeti, bl_stok, "Gerçekleşen Maliyet")
if bl_den:
    count(PROJE, "Ar-Ge Projeleri", bl_den, "Deneme Sayısı")
if bl_gor:
    count(PROJE, "Ar-Ge Projeleri", bl_gor, "Görev / Sapma Sayısı")
if bl_aks:
    count(PROJE, "Ar-Ge Projeleri", bl_aks, "Aksiyon Sayısı")


# ─── Phase 4 — Diğer back-link'ler ────────────────────────────────────────────
phase("Phase 4 — İzlenebilirlik back-link'leri")

# Deneme → kullanılan lotlar, üretilen numuneler, stabilite, analitik
backlink(PROJE, "Formülasyon Denemeleri", STOK,  "Formül Bileşenleri", "Deneme",         "Formül Bileşenleri")
backlink(PROJE, "Formülasyon Denemeleri", STOK,  "Numuneler",          "İlgili Deneme",  "Üretilen Numuneler")
backlink(PROJE, "Formülasyon Denemeleri", PROJE, "Stabilite Çalışmaları", "Batch (Deneme)", "Stabilite Çalışmaları")
backlink(PROJE, "Formülasyon Denemeleri", PROJE, "Analitik Çalışmalar",   "Deneme",      "Analitik Çalışmalar")

backlink(PROJE, "Stabilite Çalışmaları", PROJE, "Stabilite Ölçümleri", "Stabilite Çalışması", "Ölçümler")

# Faz kapısı → gerekçe kararları (FR: toplantı kararı kapı onayının gerekçesi)
backlink(PROJE, "Faz Kapıları", TOPL, "Kararlar", "İlgili Faz Kapısı", "Toplantı Kararları")

# Toplantı detay sayfası
backlink(TOPL, "Toplantılar", TOPL, "Gündem Maddeleri", "Toplantı", "Gündem")
backlink(TOPL, "Toplantılar", TOPL, "Kararlar",         "Toplantı", "Kararlar")
backlink(TOPL, "Toplantılar", TOPL, "Aksiyonlar",       "Toplantı", "Aksiyonlar")
backlink(TOPL, "Kararlar",    TOPL, "Aksiyonlar",       "Karar",    "Aksiyonlar")

# Stok tanımları
backlink(STOK, "Tedarikçiler", STOK, "Malzeme Kartları", "Tedarikçi", "Sağlanan Malzemeler")
backlink(STOK, "Numuneler",    STOK, "Depo Görevleri",   "Numune",    "Depo Görevleri")

phase("Upgrade complete")
