"""
Upgrade script: Kırpart Tedarikçi Portalı — formül, rollup ve sayaç alanları
Ana build'den SONRA çalıştır (skill klasöründen):

    python main.py build apps/kirpart_tedarikci_portali.py
    python apps/upgrade_kirpart_tedarikci_portali_computed.py

Sırayla:
  1. Formül alanları (aynı liste içi)
  2. Back-link (LINKLIST) + rollup / COUNT alanları
  3. Rollup'lara dayanan formüller
  4. Bu alanlara bağlı otomasyonlar (post_automations) ve raporlar (post_reports)

Idempotent: aynı isimde alan varsa atlanır.
"""
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workiom.client import WorkiomClient, WorkiomAPIError
from workiom.state import AppState


def _api_key() -> str:
    if os.environ.get("API_KEY"):
        return os.environ["API_KEY"]
    for line in open(".env").read().splitlines():
        if line.startswith("API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("❌ API_KEY bulunamadı (.env veya ortam değişkeni)")


APP_NAME = "Kırpart Tedarikçi Portalı"
client = WorkiomClient(_api_key())
state = AppState(APP_NAME)
if not state.app_id:
    sys.exit("❌ State yok — önce main.py build çalıştır.")

NUM, TEXT, DATE = 1, 0, 2
_live: dict[str, dict[str, int]] = {}


def live_fields(list_name: str) -> dict[str, int]:
    if list_name not in _live:
        lid = state.get_list_id(list_name)
        _live[list_name] = {f["name"]: f["id"] for f in client.get_all_fields(lid)}
    return _live[list_name]


def fid(list_name: str, field_name: str) -> int:
    f = live_fields(list_name).get(field_name) or state.get_field_id(list_name, field_name)
    if not f:
        raise KeyError(f"'{field_name}' alanı '{list_name}' listesinde yok")
    return f


def create(list_name: str, body: dict) -> int | None:
    name = body["name"]
    if name in live_fields(list_name):
        print(f"  · {list_name} / {name} zaten var")
        state.set_field_id(list_name, name, live_fields(list_name)[name])
        return live_fields(list_name)[name]
    body.setdefault("isRequired", False)
    body.setdefault("isVisible", True)
    try:
        res = client.create_field(state.get_list_id(list_name), body)
    except WorkiomAPIError as e:
        print(f"  ✗ {list_name} / {name}: {e.message} {e.details}")
        return None
    live_fields(list_name)[name] = res["id"]
    state.set_field_id(list_name, name, res["id"])
    print(f"  ✅ {list_name} / {name} ({res['id']})")
    return res["id"]


def formula(list_name: str, name: str, expr: str, dtype: int = NUM):
    """[[Alan Adı]] → _F_<id>"""
    try:
        compiled = re.sub(r"\[\[(.+?)\]\]", lambda m: f"_F_{fid(list_name, m.group(1))}", expr)
    except KeyError as e:
        print(f"  ✗ {list_name} / {name}: {e}")
        return None
    return create(list_name, {"name": name, "dataType": dtype, "isComputed": True, "expression": compiled})


def backlink(parent: str, name: str, child: str, fk: str):
    return create(parent, {
        "name": name, "dataType": 5, "linkedListId": state.get_list_id(child),
        "linkedFieldId": fid(child, fk), "isAssociation": True, "hasAssociatedLinkedField": True,
        "allowMultiple": True,
    })


SUM, AVG, MIN, MAX, COUNT = 0, 1, 2, 3, 4


def rollup(parent: str, name: str, child: str, bl_id: int | None, value_field: str, kind: int):
    if not bl_id:
        print(f"  ✗ {parent} / {name}: back-link yok")
        return None
    if kind == COUNT:
        return create(parent, {"name": name, "dataType": 12, "countLocalLinkedFieldId": bl_id})
    return create(parent, {
        "name": name, "dataType": NUM, "isRollup": True, "linkedListId": state.get_list_id(child),
        "linkedFieldId": fid(child, value_field), "rollupFieldId": bl_id, "rollupSummaryType": kind,
    })


def z(e: str) -> str:
    """negatifse 0"""
    return f"If(({e}) < 0, 0, ({e}))"


def phase(title):
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


# ─── 1. Liste içi formüller ───────────────────────────────────────────────────
phase("1 — Formül alanları")
formula("Tedarikçiler", "Net Kârlılık %",
        "If([[Son Yıl Ciro]] = 0, 0, Round([[Son Yıl Net Kâr]] / [[Son Yıl Ciro]] * 100, 1))")
formula("Tedarikçiler", "Denetimsiz Gün",
        "If(IsBlank([[Son Denetim Tarihi]]), 9999, SubtractDate(Today(), [[Son Denetim Tarihi]]))")
formula("Tedarikçi–Malzeme Kartları", "Dolu Kutu Ağırlığı (kg)",
        "[[Birim Ağırlık (kg)]] * [[Kutu İçi Adet]] + [[Kutu Dara (kg)]]")
formula("Cari Mutabakatlar", "Fark", "[[Kırpart Bakiyesi]] - [[Tedarikçi Bakiyesi]]")
formula("Kalite Vakaları", "Toplam Kalitesizlik Maliyeti",
        " + ".join(f"[[{m}]]" for m in ["Ayıklama Maliyeti", "Rework Maliyeti", "Hurda Maliyeti",
                                         "Ek Nakliye Maliyeti", "Ceza / Müşteri Yansıması", "Diğer Maliyet"]))
formula("Kalite Vakaları", "8D Kapanış Süresi (gün)",
        "If(IsBlank([[8D Kapanış Tarihi]]), 0, SubtractDate([[8D Kapanış Tarihi]], [[Tespit Tarihi]]))")
formula("Denetim Cevapları", "Ağırlıklı Puan", "[[Verilen Puan]] * [[Ağırlık]]")
formula("Denetim Cevapları", "Ağırlıklı Maks. Puan", "[[Maksimum Puan]] * [[Ağırlık]]")
formula("Aksiyonlar", "Kalan Gün", "SubtractDate([[Termin]], Today())")
formula("Aksiyonlar", "Gecikme (gün)",
        f"If([[Açık (1/0)]] = 1, {z('SubtractDate(Today(), [[Termin]])')}, 0)")
formula("Belgeler", "Kalan Gün",
        "If(IsBlank([[Geçerlilik Bitişi]]), 9999, SubtractDate([[Geçerlilik Bitişi]], Today()))")
formula("Belgeler", "Geçerlilik Durumu",
        "If(IsBlank([[Geçerlilik Bitişi]]), 'Süresiz', If(SubtractDate([[Geçerlilik Bitişi]], Today()) < 0, "
        "'Süresi Doldu', If(SubtractDate([[Geçerlilik Bitişi]], Today()) <= 60, 'Yaklaşıyor', 'Geçerli')))", TEXT)
formula("Sipariş Kalemleri", "Gelecek Sipariş (1/0)",
        "If(SubtractDate([[İstenen Teslim Tarihi]], Today()) > 0, 1, 0)")
formula("Varlıklar (Kalıp / Ekipman)", "Kalan Ömür %",
        "If([[Tasarım Ömrü (baskı)]] = 0, 100, Round((1 - [[Güncel Baskı Sayısı]] / [[Tasarım Ömrü (baskı)]]) * 100, 1))")
formula("Varlıklar (Kalıp / Ekipman)", "Ömür Durumu",
        "If([[Kalan Ömür %]] <= 0, 'Ömrü Doldu', If([[Kalan Ömür %]] <= 20, 'Revizyon Yaklaşıyor', 'Normal'))", TEXT)
formula("Varlıklar (Kalıp / Ekipman)", "Sonraki Bakım Tarihi",
        "DateAdd([[Son Bakım Tarihi]], [[Bakım Periyodu (gün)]], 'day')", DATE)
formula("Varlıklar (Kalıp / Ekipman)", "Bakım Durumu",
        "If(IsBlank([[Son Bakım Tarihi]]), 'Bakım Kaydı Yok', If(SubtractDate([[Sonraki Bakım Tarihi]], Today()) < 0, "
        "'Gecikti', 'Zamanında'))", TEXT)

# Performans kartı — KPI puanlama (ağırlıklar: veri modeli "KPI Puanlama" sekmesi)
P = "Performans Kartları"
formula(P, "PPM Gerçekleşen",
        "If([[Teslim Alınan Miktar]] = 0, 0, Round([[Hatalı Miktar]] / [[Teslim Alınan Miktar]] * 1000000, 0))")
formula(P, "PPM Puanı",
        f"If([[PPM Gerçekleşen]] <= [[PPM Hedefi]], 100, "
        f"{z('100 - ([[PPM Gerçekleşen]] / [[PPM Hedefi]] - 1) * 100')})")
formula(P, "Toplam Vaka", "[[Hat İadesi Vaka Sayısı]] + [[GKK Parti Reddi Sayısı]]")
formula(P, "Vaka Puanı",
        f"If([[Toplam Vaka]] <= [[Vaka Hedefi]], 100, {z('100 - ([[Toplam Vaka]] - [[Vaka Hedefi]]) * 20')})")
formula(P, "Lojistik Puanı",
        "If([[Zamanında Teslim Hedefi]] = 0, 100, If([[Zamanında Teslim %]] / [[Zamanında Teslim Hedefi]] * 100 > 100, "
        "100, Round([[Zamanında Teslim %]] / [[Zamanında Teslim Hedefi]] * 100, 1)))")
formula(P, "8D Puanı",
        f"If([[Ort. 8D Kapanış (gün)]] <= [[8D Kapanış Hedefi]], 100, "
        f"{z('100 - ([[Ort. 8D Kapanış (gün)]] - [[8D Kapanış Hedefi]]) * 2')})")
formula(P, "Denetim Puanı", "[[Son Denetim Başarı %]]")
formula(P, "Sertifika Puanı", "If([[Geçerli Sertifika (1/0)]] = 1, 100, 0)")
formula(P, "Sapma Puanı", z("100 - [[Sapma Talebi Sayısı]] * 25"))
formula(P, "Toplam Puan",
        "Round([[PPM Puanı]] * 0.25 + [[Vaka Puanı]] * 0.15 + [[Lojistik Puanı]] * 0.20 + [[8D Puanı]] * 0.10 + "
        "[[Denetim Puanı]] * 0.10 + [[Sertifika Puanı]] * 0.05 + [[Sapma Puanı]] * 0.05 + "
        "[[İletişim Puanı]] * 0.10, 1)")
formula(P, "Sınıf", "If([[Toplam Puan]] >= 85, 'A', If([[Toplam Puan]] >= 70, 'B', 'C'))", TEXT)

# ─── 2. Back-link + rollup ───────────────────────────────────────────────────
phase("2 — Back-link, rollup ve sayaçlar")
SK = "Sipariş Kalemleri"
bl = backlink(SK, "Sevkiyat Kalemleri (İrsaliye Tarihçesi)", "Sevkiyat Kalemleri", "Sipariş Kalemi")
rollup(SK, "Teslim Alınan Miktar", "Sevkiyat Kalemleri", bl, "Kabul Edilen Miktar", SUM)
rollup(SK, "Sevk Edilen Toplam", "Sevkiyat Kalemleri", bl, "Sevk Edilen Miktar", SUM)
formula(SK, "Bakiye", "[[Sipariş Miktarı]] - [[Teslim Alınan Miktar]]")
formula(SK, "Yoldaki Miktar", z("[[Sevk Edilen Toplam]] - [[Teslim Alınan Miktar]]"))

bl = backlink("Siparişler", "Sipariş Kalemleri (liste)", SK, "Sipariş")
rollup("Siparişler", "Kalem Sayısı", SK, bl, None, COUNT)
rollup("Siparişler", "Teyit Bekleyen Kalem", SK, bl, "Teyit Bekliyor (1/0)", SUM)
rollup("Siparişler", "Toplam Bakiye", SK, bl, "Bakiye", SUM)
rollup("Siparişler", "Son Teslim Alma Tarihi", SK, bl, "Son Teslim Alma Tarihi", MAX)

bl = backlink("Sevkiyatlar", "Sevkiyat Kalemleri (liste)", "Sevkiyat Kalemleri", "Sevkiyat")
rollup("Sevkiyatlar", "Toplam Kutu", "Sevkiyat Kalemleri", bl, "Kutu Adedi", SUM)
rollup("Sevkiyatlar", "En Erken İstenen Tarih", "Sevkiyat Kalemleri", bl, "İstenen Teslim Tarihi", MIN)
formula("Sevkiyatlar", "Gecikme (gün)",
        f"If(Or(IsBlank([[Teslim Alma Tarihi]]), IsBlank([[En Erken İstenen Tarih]])), 0, "
        f"{z('SubtractDate([[Teslim Alma Tarihi]], [[En Erken İstenen Tarih]])')})")
formula("Sevkiyatlar", "Zamanında (1/0)",
        "If(Or(IsBlank([[Teslim Alma Tarihi]]), IsBlank([[En Erken İstenen Tarih]])), 0, "
        "If(SubtractDate([[Teslim Alma Tarihi]], [[En Erken İstenen Tarih]]) <= 0, 1, 0))")

bl = backlink("Malzemeler", "Tedarikçi Kartları", "Tedarikçi–Malzeme Kartları", "Malzeme")
rollup("Malzemeler", "Tedarikçi Sayısı", "Tedarikçi–Malzeme Kartları", bl, None, COUNT)

bl = backlink("Denetim Tipleri", "Sorular", "Denetim Soruları", "Denetim Tipi")
rollup("Denetim Tipleri", "Soru Sayısı", "Denetim Soruları", bl, None, COUNT)

D = "Denetimler"
bl = backlink(D, "Denetim Cevapları (liste)", "Denetim Cevapları", "Denetim")
rollup(D, "Toplam Puan", "Denetim Cevapları", bl, "Ağırlıklı Puan", SUM)
rollup(D, "Maksimum Puan", "Denetim Cevapları", bl, "Ağırlıklı Maks. Puan", SUM)
formula(D, "Başarı %", "If([[Maksimum Puan]] = 0, 0, Round([[Toplam Puan]] / [[Maksimum Puan]] * 100, 1))")
formula(D, "Sonuç", "If([[Başarı %]] >= [[A Sınıfı Alt Sınırı %]], 'A', "
                    "If([[Başarı %]] >= [[B Sınıfı Alt Sınırı %]], 'B', 'C'))", TEXT)
formula(D, "Sonraki Denetim Tarihi", "DateAdd([[Gerçekleşen Tarih]], [[Periyot (gün)]], 'day')", DATE)

PT = "PPAP Talepleri"
bl = backlink(PT, "PPAP Dokümanları (liste)", "PPAP Dokümanları", "PPAP Talebi")
rollup(PT, "Toplam Doküman", "PPAP Dokümanları", bl, None, COUNT)
rollup(PT, "Onaylanan Doküman", "PPAP Dokümanları", bl, "Onaylı (1/0)", SUM)
formula(PT, "Tamamlanma %", "If([[Toplam Doküman]] = 0, 0, Round([[Onaylanan Doküman]] / [[Toplam Doküman]] * 100, 0))")

ST = "Sapma Talepleri"
bl = backlink(ST, "Sapmalı Lotlar (liste)", "Sapmalı Lotlar", "Sapma Talebi")
rollup(ST, "Sevk Edilen Sapmalı Miktar", "Sapmalı Lotlar", bl, "Miktar", SUM)
formula(ST, "Kalan Sapma Miktarı", "[[Talep Edilen Miktar]] - [[Sevk Edilen Sapmalı Miktar]]")

for parent, fk in [("Kalite Vakaları", "Kalite Vakası"), ("Denetimler", "Denetim"),
                   ("Sapma Talepleri", "Sapma Talebi"), ("Ziyaret & Toplantılar", "Ziyaret / Toplantı")]:
    bl = backlink(parent, "Aksiyonlar (liste)", "Aksiyonlar", fk)
    rollup(parent, "Açık Aksiyon Sayısı", "Aksiyonlar", bl, "Açık (1/0)", SUM)
    if parent == "Ziyaret & Toplantılar":
        rollup(parent, "Aksiyon Sayısı", "Aksiyonlar", bl, None, COUNT)

# ─── 3. Bağımlı otomasyon ve raporlar ────────────────────────────────────────
phase("3 — Hesaplanan alanlara bağlı otomasyon ve raporlar")
spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kirpart_tedarikci_portali.py")
_s = importlib.util.spec_from_file_location("kirpart_spec", spec_path)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)
SPEC = _m.SPEC

from workiom.automation_builder import AutomationBuilder
from workiom.builder import Builder
from workiom.resolver import Resolver

AutomationBuilder(client, state).build_all(state.app_id, SPEC.get("post_automations", []))
b = Builder(client, state, Resolver(client))
for r in SPEC.get("post_reports", []):
    b._ensure_report(state.app_id, r)

print(f"\n{'=' * 60}\n  Upgrade tamamlandı\n{'=' * 60}\n")
