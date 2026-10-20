"""Performans Yönetimi — uygulama panosu widget'ları (TASARIM.md bölüm 8).

    python3 apps/performans_reports.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from wk import client  # noqa: E402
from workiom.builder import Builder  # noqa: E402
from workiom.resolver import Resolver  # noqa: E402
from workiom.state import AppState  # noqa: E402

K, O, KR = "Performans Karneleri", "Objective'ler", "Key Result'lar"
ACIK = ["Hedef Belirleme", "Yönetici Onayında", "Aktif", "Değerlendirme", "Kalibrasyon"]


def r(label, lst, typ, **kw):
    return {"label": label, "list": lst, "type": typ, "pin": True, **kw}


REPORTS = [
    # Pano 1 · Performans Karnesi
    r("Karne · Açık karneler", K, "kpi_count", icon="fal fa-id-card", filter={"field": "Durum", "value": ACIK}),
    r("Karne · Onay bekleyen", K, "kpi_count", icon="fal fa-user-check",
      filter={"field": "Durum", "value": "Yönetici Onayında"}),
    r("Karne · Ortalama toplam puan", K, "kpi", aggregation="avg", value_field="Toplam Puan",
      icon="fal fa-tachometer-alt"),
    r("Karne · Performans grubu dağılımı", K, "pie", group_by="Performans Grubu", aggregation="count"),
    r("Karne · Final performans grubu", K, "pie", group_by="Final Performans Grubu", aggregation="count"),
    r("Karne · Durumlara göre", K, "bar", group_by="Durum", aggregation="count"),
    r("Karne · Döneme göre ortalama puan", K, "bar", group_by="Dönem", aggregation="avg",
      value_field="Toplam Puan"),
    # Pano 2 · OKR
    r("OKR · Aktif objective", O, "kpi_count", icon="fal fa-flag", filter={"field": "Durum", "value": "Aktif"}),
    r("OKR · Ortalama ilerleme (aktif)", O, "kpi", aggregation="avg", value_field="İlerleme",
      icon="fal fa-chart-line", filter={"field": "Durum", "value": "Aktif"}),
    r("OKR · Ortalama güven (aktif)", O, "kpi", aggregation="avg", value_field="Ortalama Güven",
      icon="fal fa-heartbeat", filter={"field": "Durum", "value": "Aktif"}),
    r("OKR · Renk dağılımı", O, "pie", group_by="Renk", aggregation="count"),
    r("OKR · Seviyeye göre", O, "bar", group_by="Seviye", aggregation="count"),
    r("OKR · Döneme göre ortalama ilerleme", O, "bar", group_by="Dönem", aggregation="avg",
      value_field="İlerleme"),
    r("OKR · Departmana göre objective", O, "bar", group_by="Departman", aggregation="count"),
    r("OKR · Check-in bekleyen KR'lar", KR, "kpi_count", icon="fal fa-bell",
      filter={"field": "Check-in Gecikti", "value": 1}),
]

if __name__ == "__main__":
    c = client()
    st = AppState("Performans Yönetimi")
    b = Builder(c, st, Resolver(c))
    for lst in {x["list"] for x in REPORTS}:
        b._sync_fields_to_state(lst, st.get_list_id(lst))
    for rep in REPORTS:
        b._ensure_report(st.app_id, rep)
    print(f"{len(REPORTS)} widget")
