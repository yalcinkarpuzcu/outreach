# İleri Acoustic (Turkowall) – Workiom kurulumu

Tenant: `ileriacoustic-demo`. Kaynak: *Proje Yol Haritası ve Mutabakat Dokümanı v1.0*, bölüm 6.

| Uygulama | Listeler | Otomasyon |
|---|---|---|
| CRM | Firmalar, Kişiler, Talepler, Görevler | 16 |
| Proje & Teklif | Projeler, Teklifler, Teklif Revizyonları, Teklif Takipleri, Sözleşmeler | 19 + PRJ-04c |
| Teknik Hesaplama | Sistemler, Hesap Parametreleri, Reçete Şablonu, Duvar Kalemleri, Reçete Düzeltmeleri, Reçete Kalemleri | 8 |
| Planlama & Üretim | İstasyonlar, Üretim Planları, İş Emirleri | 16 |
| Satınalma & Stok | Tedarikçiler, Malzemeler, Malzeme İhtiyaçları, Satınalma Talepleri, Stok Hareketleri | 14 |

Otomasyonlar tetikleyici listenin uygulamasında kurulur (STN-01/12 → Planlama & Üretim, HSP-04 → Proje & Teklif).

## Kurulum sırası
Builder (workiom-builder skill) klasörüne bu dosyaları kopyalayıp, `.env` içinde `API_KEY` ile:

```bash
./build_all.sh                               # 5 uygulama, 2 geçiş (uygulamalar arası bağlantılar 2. geçişte)
python3 apps/ileri_fix_primary.py            # birincil alanlar zorunlu değil (zorunluluk formlarda)
python3 apps/ileri_computed.py               # formül / lookup / toplam / sayım alanları
python3 apps/ileri_seed.py                   # ana veri
python3 apps/ileri_roles.py                  # 6.7 rolleri → roles.json
python3 apps/ileri_build_automations.py      # 74 otomasyon
python3 apps/ileri_reports.py                # 7 pano, 29 widget
```

## Builder eklentileri
- `workiom/builder.py`: `primary` (birincil alan adı), `backlink` (ters bağlantı adı).
- `workiom/multi_automation.py`: uygulamalar arası create/find, `in (...)`, `{{trigger:X}}` / `{{loop:X}}`,
  iç içe find'da `loop:` filtresi, önce/sonra zaman tetikleyicisi, rol adları, webhook,
  `send_email` → bildirim, ve koşul dalı başına tek find kuralı (`flatten_finds`).

## Canlı testle doğrulanan API kısıtları
- Bir koşul dalında yalnızca ilk `find_records` çalışır → `flatten_finds` her find'ı kendi üst seviye koşuluna taşır.
- `_id` ile doğrudan arama yok → üst kayıt ters bağlantı ile aranır (`Projeler.Teklifler = trigger:_id`).
- Döngüdeki kaydın bağlantısına `trigger:_id`, otomatik numara yazılamaz → PRJ-04c yardımcı otomasyonu,
  `Kayıt No (sayı)` / `Talep No (sayı)` formül kopyaları.
- Toplama (rollup) yalnızca sayısal; filtreli toplam yok → çocuk listede `(gösterge)` formülü + SUM.
- Arama filtresinde onay kutusu / seçim alanı desteklenmiyor; sayı eşitliği operatörü 0.
- Formül motorunda `Ceiling` yok; tarih `Today() + n`.
- API ile açılan her kayıtta birincil alan dolu olmalı.
