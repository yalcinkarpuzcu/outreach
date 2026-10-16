"""
6.8 Raporlar ve Panolar — 7 pano, uygulama panolarına (AppDashboard) widget olarak kurulur.
Widget etiketleri pano adıyla başlar. Hesaplanan alanlar oluştuktan SONRA çalıştırılır.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workiom.builder import Builder  # noqa: E402
from workiom.client import WorkiomClient  # noqa: E402
from workiom.resolver import Resolver  # noqa: E402
from workiom.state import AppState  # noqa: E402

c = WorkiomClient((ROOT / ".env").read_text().split("=", 1)[1].strip())


def r(label, lst, typ, **kw):
    return {"label": label, "list": lst, "type": typ, "pin": True, **kw}


REPORTS = {
    "CRM": [
        # Ekip İş Yükü (Yönetici)
        r("Ekip İş Yükü · Açık görevler", "Görevler", "kpi_count", icon="fal fa-tasks",
          filter={"field": "Durum", "value": ["Açık", "Devam Ediyor"]}),
        r("Ekip İş Yükü · Kişi bazında açık görev", "Görevler", "bar", group_by="Sorumlu",
          aggregation="count", filter={"field": "Durum", "value": ["Açık", "Devam Ediyor"]}),
        r("Ekip İş Yükü · Görev türü", "Görevler", "pie", group_by="Görev Türü", aggregation="count"),
        # Satış hunisi – talep tarafı
        r("Satış Hunisi · Talepler kaynağa göre", "Talepler", "pie", group_by="Kaynak", aggregation="count"),
        r("Teklif Takip · Ortalama ilk yanıt (saat)", "Talepler", "kpi", aggregation="avg",
          value_field="İlk Yanıt Süresi (saat)", icon="fal fa-stopwatch"),
        r("Satış Hunisi · Firmalar müşteri tipine göre", "Firmalar", "pie", group_by="Müşteri Tipi",
          aggregation="count"),
    ],
    "Proje & Teklif": [
        # Satış Hunisi
        r("Satış Hunisi · Aşamaya göre proje", "Projeler", "bar", group_by="Proje Aşaması",
          aggregation="count"),
        r("Satış Hunisi · Aşamaya göre tutar", "Projeler", "bar", group_by="Proje Aşaması",
          aggregation="sum", value_field="Geçerli Teklif Tutarı", sub_group_by="Para Birimi"),
        r("Satış Hunisi · Yurt içi / yurt dışı", "Projeler", "pie", group_by="Müşteri Tipi",
          aggregation="count"),
        # Temsilci Performansı
        r("Temsilci Performansı · Temsilci bazında teklif", "Projeler", "bar",
          group_by="Sorumlu Satış Temsilcisi", aggregation="count"),
        r("Temsilci Performansı · Teklif durumları", "Teklifler", "pie", group_by="Teklif Durumu",
          aggregation="count"),
        r("Temsilci Performansı · Kayıp nedeni dağılımı", "Projeler", "pie", group_by="Kayıp Nedeni",
          aggregation="count", filter={"field": "Proje Aşaması", "value": "Kaybedildi"}),
        # Teklif Takip
        r("Teklif Takip · Takipteki teklifler", "Teklifler", "kpi_count", icon="fal fa-paper-plane",
          filter={"field": "Teklif Durumu", "value": ["Gönderildi", "Revizyonda"]}),
        r("Teklif Takip · Takip sonuçları", "Teklif Takipleri", "pie", group_by="Sonuç", aggregation="count"),
        # Potansiyel & İşlerimiz
        r("Potansiyel & İşlerimiz · Potansiyel iş sayısı", "Projeler", "kpi_count", icon="fal fa-binoculars",
          filter={"field": "Proje Aşaması", "value": "Potansiyel"}),
        r("Potansiyel & İşlerimiz · Potansiyel panel adedi", "Projeler", "kpi", aggregation="sum",
          value_field="Toplam Panel", filter={"field": "Proje Aşaması", "value": "Potansiyel"},
          icon="fal fa-th-large"),
        r("Potansiyel & İşlerimiz · Potansiyel m²", "Projeler", "kpi", aggregation="sum",
          value_field="Toplam m²", filter={"field": "Proje Aşaması", "value": "Potansiyel"},
          icon="fal fa-ruler-combined"),
        r("Potansiyel & İşlerimiz · Beklenen onay (hafta)", "Projeler", "bar",
          group_by="Beklenen Onay Tarihi", group_date_freq="week", aggregation="sum",
          value_field="Toplam Panel", filter={"field": "Proje Aşaması", "value": "Potansiyel"}),
        r("Potansiyel & İşlerimiz · İşlerimiz", "Projeler", "table",
          filter={"field": "Proje Aşaması", "value": ["Sözleşmeli", "Üretimde"]}),
    ],
    "Planlama & Üretim": [
        r("Üretim Durumu · Plan durumları", "Üretim Planları", "bar", group_by="Durum", aggregation="count"),
        r("Üretim Durumu · Ortalama tamamlanma %", "Üretim Planları", "kpi", aggregation="avg",
          value_field="Tamamlanma (%)", icon="fal fa-percentage",
          filter={"field": "Durum", "value": ["İmalata Sunuldu", "Üretimde", "Kalite Kontrol"]}),
        r("Üretim Durumu · İstasyon yükü (açık iş emri)", "İş Emirleri", "bar", group_by="İstasyon",
          aggregation="count", filter={"field": "Durum", "value": ["Bekliyor", "Hazır", "Devam Ediyor"]}),
        r("Üretim Durumu · Termin durumu", "Üretim Planları", "pie", group_by="Termin Durumu",
          aggregation="count"),
        r("Üretim Durumu · Termin dağılımı", "Üretim Planları", "bar", group_by="Hedef Bitiş Tarihi",
          group_date_freq="week", aggregation="count"),
    ],
    "Satınalma & Stok": [
        r("Satınalma & Stok · Açık talepler", "Satınalma Talepleri", "kpi_count", icon="fal fa-shopping-basket",
          filter={"field": "Durum", "value": ["Talep", "Teklif", "Onay Bekliyor", "Onaylandı", "Sipariş Verildi"]}),
        r("Satınalma & Stok · Onay bekleyen", "Satınalma Talepleri", "kpi_count", icon="fal fa-user-check",
          filter={"field": "Durum", "value": "Onay Bekliyor"}),
        r("Satınalma & Stok · Talep durumları", "Satınalma Talepleri", "bar", group_by="Durum",
          aggregation="count"),
        r("Satınalma & Stok · Kategoriye göre stok", "Malzemeler", "bar", group_by="Kategori",
          aggregation="sum", value_field="Stok Bakiyesi"),
        r("Satınalma & Stok · Malzeme durumu", "Malzemeler", "table"),
    ],
}

total = 0
for app, reps in REPORTS.items():
    st = AppState(app)
    b = Builder(c, st, Resolver(c))
    for lst in {x["list"] for x in reps}:
        b._sync_fields_to_state(lst, st.get_list_id(lst))
    print(f"\n📊 {app}")
    for rep in reps:
        b._ensure_report(st.app_id, rep)
        total += 1
print(f"\nToplam widget: {total}")
