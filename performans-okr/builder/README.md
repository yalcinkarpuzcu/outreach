# Performans Yönetimi (KPI Karnesi + OKR) – Workiom kurulumu

Tenant: `faydasicok` · App: `Performans Yönetimi` · İK bağlantısı: `İnsan Kaynakları` (Özlük Bilgileri, Organizasyon).
Tasarım ve kurulum sonrası notlar: `../TASARIM.md` (bölüm 12).

Bu klasör workiom-builder skill'inin bir kopyasıdır; `workiom/automation_builder.py`'de üç ekleme var:
formül eşlemesinde `{{Alan}}` / `{{loop:Alan}}`, başka uygulamada arama (`app_id`), döngü kaydına bildirim (`to_loop_field`).

## Kurulum sırası
`.env` içinde `API_KEY=...` (repoya girmez).

```bash
python3 main.py build apps/performans_yonetimi.py   # app, klasörler, listeler, düz alanlar, görünümler
python3 apps/performans_fix_primary.py              # otomatik birincil alanı (Ad/Başlık) spec'teki adla birleştirir
python3 apps/performans_computed.py                 # ilişkiler, İK'ya form türü alanı, lookup, formül, rollup
python3 apps/performans_seed.py                     # referans + demo verisi (ref ik karne okr post), sonra:
python3 apps/performans_seed.py fix                 # güven skorları + renk (bir kez)
python3 apps/performans_automations.py              # 25 otomasyon (kod önekiyle seçilebilir)
python3 apps/performans_roles.py                    # 4 rol → roles.json
python3 apps/performans_reports.py                  # 15 pano widget'ı
```

Bir otomasyonu yeniden kurmak: `python3 apps/performans_auto_reset.py KRN-04 && python3 apps/performans_automations.py KRN-04`

## Canlı testle doğrulanan API davranışları
- Formülde **bölme sonucu 3 ondalığa yuvarlanır** → oranlar ölçeklenerek hesaplanır (bkz. `performans_computed.py`).
- Formül/rollup değişimi kayıt güncelleme tetikleyicisi üretmez → grup ve renk gece zamanlanmış otomasyonla.
- Üst-alt ilişki: ters bağlantı üst listede `isAssociation` ile açılır, alt listedeki eş alan yeniden adlandırılır.
- Çoklu bağlantıda arama filtresi: `equals` üyelik kontrolü yapar, `contains` sonuç döndürmez.
- Sayı alanında eşitlik filtresinin operatörü 0'dır.
- Seed betiği KPI hedeflerini ve OKR'ları idempotent oluşturmaz; tekrar çalıştırmadan önce mevcut kayıtları kontrol et.
