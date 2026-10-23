# Polifarma Workiom PoC — Builder Spec'leri

Kaynak: *Polifarma Workiom PoC — Proje ve İster Analizi* (23.10.2026). Bu klasör, PDF'teki 3 uygulamayı
`workiom-builder` formatında (deklaratif Python spec) tanımlar.

## Dosyalar ve kurulum sırası

**Ön koşul — builder yaması:** `builder_patch/associated_link.diff` builder'a uygulanmalı (`patch -p1 < associated_link.diff`, builder kökünde). Workiom bir back-link'i mevcut LINK alanıyla eşleştirmez, her seferinde yeni bir ikiz alan açar; yama, spec'te `"back_link"` taşıyan LINK alanlarını back-link'i önce açıp ikizini o alan olarak kullanarak kurar. Yamasız kurulumda rollup/COUNT'lar boş kalır.

| # | Komut | Ne yapar |
|---|---|---|
| 1 | `python main.py build apps/polifarma_arge_proje.py` | Uygulama 1 — Ar-Ge Proje Takibi (ortak bağlantı noktası, ilk kurulur) |
| 2 | `python main.py build apps/polifarma_stok.py` | Uygulama 2 — Numune ve Hammadde Stok (Proje'ye cross-app link) |
| 3 | `python main.py build apps/polifarma_toplanti.py` | Uygulama 3 — Toplantı Yönetimi (Proje'ye cross-app link) |
| 4 | `python apps/upgrade_polifarma_titles.py` | Zorunlu "Ad" alanlarını formüle çevirir (adım 2-3'teki 5 kayıt-oluşturan otomasyon bu yüzden ilk seferde uyarı verir) |
| 5 | `python main.py build apps/polifarma_stok.py` ve `... polifarma_toplanti.py` | Tekrar build: eksik kalan 5 otomasyonu kurar |
| 6 | `python apps/upgrade_polifarma_computed.py` | Rollup, COUNT, formül, QR alanları |
| 7 | `python main.py build apps/polifarma_stok_faz2.py` | Kritik stok görünümü + günlük uyarı + stok raporları |
| 8 | `python main.py build apps/polifarma_proje_faz2.py` | Bütçe / gerçekleşen maliyet raporları |
| 9 | `python main.py seed apps/polifarma_toplanti.py` | Toplantı serileri (Haftalık Ar-Ge, PoC Geri Bildirim) |

Dosyaları skill klasöründeki `apps/` altına kopyalayıp komutları oradan çalıştırın. API anahtarı `--api-key` ya da `API_KEY` ile verilir.

**Plan uyumluluğu:** Spec'lerde `PLAN_SUPPORTS_PROCESS = False` iken süreç listeleri veri listesi olarak kurulur ve yerleşik Status yerine aynı seçeneklerle "Durum" alanı kullanılır (2024Business deneme planı süreç listesi ve klasör desteklemiyor; klasörleri builder kendisi atlar). Süreç listesi destekleyen planda `True` yapılır.

**Polifarma tenant'ı (23.10.2026):** Yukarıdaki 9 adım hatasız tamamlandı. Test kayıtlarıyla doğrulandı: lot girişi → otomatik giriş hareketi, formül bileşeni → otomatik çıkış, Kalan Miktar / Toplam Stok / Kritik Seviye Altında ve proje Gerçekleşen Maliyet doğru hesaplanıyor (test kayıtları silindi).

---

## Uygulama 1 — Ar-Ge Proje Takibi

| Klasör | Liste | Tip | Alanlar | Bağlantılar |
|---|---|---|---|---|
| Projeler | **Ar-Ge Projeleri** | Data | Proje Kodu*, Ürün Adı*, Dozaj Formu (Tablet/Kapsül/Süspansiyon/Enjektabl/Krem), Proje Tipi (Jenerik/Yeni Formülasyon/Line Extension), Referans Ürün, Mevcut Faz (8 faz), Proje Lideri, Ekip (çoklu kullanıcı), Ar-Ge Direktörü, Başlangıç Tarihi, Hedef Ruhsat Tarihi, Bütçe, Risk Seviyesi, Durum, Açıklama | ← diğer tüm listeler (aşağıda Proje 360) |
| Projeler | **Faz Kapıları** | Process: Planlandı → Devam Ediyor → Direktör Onayı Bekliyor → QA Onayı Bekliyor → Onaylandı / Reddedildi | Kapı No, Faz Adı, Sonraki Faz, Planlanan Başlangıç/Bitiş, Gerçekleşen Bitiş, Giriş/Çıkış Kriterleri, 1. Onaylayan (Direktör), 2. Onaylayan (QA/Ruhsat), Onay Notu, Gecikmede, Ekler | Proje → Ar-Ge Projeleri; lookup: Proje Kodu, Proje Lideri, Proje Ekibi |
| Projeler | **Görevler ve Sapmalar** | Process: Açık / Devam Ediyor / Gecikmede / Tamamlandı / İptal | Kayıt No, Başlık*, Tip (Görev/Sapma/CAPA), Açıklama, Atanan, Son Tarih, Öncelik, Kök Neden, Kapanış Notu, Ekler | Proje; lookup: Proje Lideri, Ar-Ge Direktörü |
| Laboratuvar | **Formülasyon Denemeleri** | Data | Deneme No, Deneme Kodu*, Batch No, Batch Büyüklüğü, Batch Birimi, Proses Parametreleri, Sonuç (Devam Ediyor/Uygun/Uygun Değil/Tekrar), Sonuç Notu, Sorumlu, Tarih, Ekler | Proje |
| Laboratuvar | **Analitik Çalışmalar** | Data | Çalışma No, Test Tipi (Çözünürlük/Safsızlık/İçerik Tayini), Metot, Validasyon Durumu, Sonuç, Sorumlu, Tarih, Ekler | Proje, Deneme |
| Laboratuvar | **Stabilite Çalışmaları** | Data | Çalışma No, Koşul (25/60, 30/65, 40/75), Başlangıç Tarihi, Zaman Noktaları (0-1-3-6-9-12-18-24 ay), Sonraki Ölçüm Tarihi, Sorumlu, Sonuç, Sapma, Sapma Açıklaması, Ekler | Proje, Batch (Deneme) |
| Laboratuvar | **Stabilite Ölçümleri** *(ek)* | Data | Ölçüm No, Zaman Noktası, Planlanan/Gerçekleşen Tarih, Sonuç (Uygun/OOT/OOS), Bulgular, Sorumlu, Ekler | Stabilite Çalışması |

**Görünümler:** Faza göre kanban (FR-1.1), proje zaman çizelgesi, hedef ruhsat takvimi, onay bekleyen / geciken kapılar, sapma-CAPA, stabilite ölçüm takvimi.

## Uygulama 2 — Numune ve Hammadde Stok

| Klasör | Liste | Tip | Alanlar | Bağlantılar |
|---|---|---|---|---|
| Tanımlar | **Tedarikçiler** | Data | Tedarikçi Adı*, İletişim Kişisi, E-Posta, Telefon, Onaylı Tedarikçi, Notlar | ← Sağlanan Malzemeler (back-link) |
| Tanımlar | **Malzeme Kartları** | Data | Malzeme Kodu*, Malzeme Adı*, Tip (Etken Madde/Eksipiyan/Referans Ürün/Standart Madde/Çözücü/Ambalaj), Birim, Depolama Koşulu, Kritik Stok Seviyesi, Stok Sorumlusu, Notlar · *hesaplanan:* Toplam Stok, Kritik Seviye Altında | Tedarikçi; ← Lotlar |
| Stok | **Lotlar** | Data | Lot No*, Tedarikçi Lot No, Giriş/Üretim Tarihi, SKT / Retest Tarihi, Tarih Tipi, Giriş Miktarı, Birim Maliyet, Raf/Lokasyon, CoA, Lot Durumu (Karantinada/Onaylı/Ret/Kullanılamaz), SKT Yaklaşıyor, Stok Sorumlusu · *hesaplanan:* Kalan Miktar, SKT'ye Kalan Gün, QR Kod | Malzeme, Tedarikçi; lookup: Birim; ← Hareketler |
| Stok | **Stok Hareketleri** | Data | Hareket No, Tarih, Hareket Tipi (Giriş/Çıkış/İade/İmha/Sayım Fazlası/Sayım Eksiği), Giriş Miktarı, Çıkış Miktarı, Yapan Kişi, Açıklama · *hesaplanan:* Stok Etkisi, Tüketim Maliyeti | Lot, **İlgili Proje ⇄ App1**, **İlgili Deneme ⇄ App1**; lookup: Malzeme, Lot Durumu, Birim Maliyet |
| Stok | **Formül Bileşenleri** *(ek)* | Data | Bileşen No, Fonksiyon, Miktar*, Formüldeki Oran (%), Not | **Deneme ⇄ App1**, **İlgili Proje ⇄ App1**, Lot; lookup: Malzeme, Birim |
| Stok | **Numuneler** | Data | Numune No, Numune Adı*, Tip (Tedarikçi/Referans/Deneme Batch'i), Miktar, Birim, Saklama Koşulu, Lokasyon, Saklama Bitiş Tarihi, Durum (Saklamada/Analizde/Karar Bekliyor/Tüketildi/İmha), Sorumlu, Ekler · QR Kod | Tedarikçi, Malzeme, **İlgili Proje ⇄ App1**, **İlgili Deneme ⇄ App1** |
| Talep ve Görevler | **Malzeme ve Numune Talepleri** | Process: Taslak / Onay Bekliyor / Onaylandı / Teslim Edildi / Reddedildi | Talep No, Talep Tipi, Talep Eden, İstenen Miktar*, Gerekçe, İstenen/Teslim Tarihi, Onaylayıcı (Stok Sorumlusu), Red Gerekçesi | **İlgili Proje / Deneme ⇄ App1**, Malzeme, Lot, Numune |
| Talep ve Görevler | **Depo Görevleri** *(ek)* | Process | Görev No, Başlık*, Görev Tipi, Atanan, Son Tarih, Karar (İmha/Uzatıldı/Analize), Yeni Saklama Bitiş Tarihi, Not | Numune, Lot |

**Stok mantığı (FR-2.1):** Manuel stok alanı yok. `Stok Etkisi = Giriş − Çıkış` → `Lot.Kalan Miktar = SUM(Stok Etkisi)` → `Malzeme.Toplam Stok = SUM(Lot.Kalan Miktar)`. Lot açılınca giriş hareketi, talep onayı ve formül bileşeni girişiyle çıkış hareketi otomatik oluşur.

## Uygulama 3 — Toplantı Yönetimi

| Liste | Tip | Alanlar | Bağlantılar |
|---|---|---|---|
| **Toplantı Serileri** *(ek, FR-3.1)* | Data | Seri Adı*, Tip, Periyot, Gün, Saat, Süre, Yer/Link, Organizatör, Katılımcılar, Aktif | ← Toplantılar |
| **Toplantılar** | Process: Planlandı / Yapıldı / İptal | Toplantı No, Başlık*, Tip (Haftalık Ar-Ge/Proje/Faz Kapısı Değerlendirme/Tedarikçi/Yönetim), Tarih, Saat, Süre, Yer/Online Link, Organizatör, Katılımcılar, Toplantı Notu, Kayıt/Transkript, AI Özeti | Toplantı Serisi, **İlgili Projeler (çoklu) ⇄ App1**; ← Gündem, Kararlar, Aksiyonlar |
| **Gündem Maddeleri** | Data | Sıra, Konu*, Sunan Kişi, Ayrılan Süre, Kaynak (Manuel/Açık Aksiyon) | Toplantı, İlgili Aksiyon, **İlgili Proje ⇄ App1** |
| **Kararlar** | Data | Karar No, Karar Metni*, Karar Tipi, Karar Veren, Tarih | Toplantı, **İlgili Proje ⇄ App1**, **İlgili Faz Kapısı ⇄ App1** |
| **Aksiyonlar** | Process: Açık / Devam Ediyor / Gecikmede / Tamamlandı | Aksiyon No, Aksiyon*, Sorumlu, Son Tarih, Öncelik, Kapanış Notu | Toplantı, Karar, **İlgili Proje ⇄ App1** |

Toplantılar listesinde **"Toplantı Tutanağı"** adında bir doküman görünümü var.

---

## Bağlantılı listeler: Proje 360 (FR-1.6, FR-2.5, FR-3.5)

Upgrade script, **Ar-Ge Projeleri** kaydına şu back-link alanlarını ekler (proje detay sayfasında sekme olarak düzenlenir):

| Back-link alanı | Kaynak liste (uygulama) |
|---|---|
| Faz Kapıları, Denemeler, Analitik Çalışmalar, Stabilite Çalışmaları, Görevler ve Sapmalar | App1 |
| Stok Tüketimi, Malzeme Talepleri, Numuneler | App2 |
| Toplantılar, Toplantı Kararları, Toplantı Aksiyonları | App3 |
| **Gerçekleşen Maliyet** (rollup: Σ Tüketim Maliyeti), Deneme Sayısı, Görev / Sapma Sayısı, Aksiyon Sayısı | hesaplanan |

Diğer back-link'ler:
- **Formülasyon Denemesi:** Formül Bileşenleri (hangi lottan ne kadar kullanıldığı), Üretilen Numuneler, Stabilite, Analitik.
- **Faz Kapısı:** Toplantı Kararları (kapı onayının gerekçesi).
- **Toplantı:** Gündem, Kararlar, Aksiyonlar. **Karar:** Aksiyonlar.
- **Tedarikçi:** Sağlanan Malzemeler. **Numune:** Depo Görevleri.

**Önerilen proje kaydı sekmeleri (UI'da):** Proje Bilgileri · Ekip ve Takvim · Faz Kapıları · Laboratuvar (Denemeler, Analitik, Stabilite) · Görevler/Sapmalar · Stok ve Maliyet (Stok Tüketimi, Talepler, Numuneler, Bütçe, Gerçekleşen Maliyet) · Toplantılar (Toplantılar, Kararlar, Aksiyonlar)

---

## İsterlerin karşılanma durumu

| İster | Karşılık |
|---|---|
| FR-1.1 | Faza göre kanban, timeline ve takvim görünümleri |
| FR-1.2 | Çift onay: Direktör onayı → QA/Ruhsat onayı (iki approval otomasyonu) |
| FR-1.3 | 2. onay verilince `Sonraki Faz`a göre projenin `Mevcut Faz` alanı güncellenir, ekip ve lider bilgilendirilir |
| FR-1.4 | Stabilite ölçümüne 7 gün kala hatırlatma (çalışma ve ölçüm listelerinde) |
| FR-1.5 | Sapma veya CAPA açılınca Proje Lideri ve Direktör bilgilendirilir |
| FR-1.6 | Proje 360 back-link'leri |
| FR-1.7 | Tarihi geçen görev "Gecikmede" statüsüne, tarihi geçen kapı `Gecikmede = ✓` olur |
| FR-1.8 | Workiom aktivite geçmişi (yerleşik) |
| FR-2.1 | Hareketlerden hesaplanan rollup |
| FR-2.2 | Faz 2: her iş günü 08:00'de kritik seviyedeki malzemeler Stok Sorumlusu'na bildirilir |
| FR-2.3 | SKT'ye 30 gün kala uyarı ve bayrak; tarih gelince "Kullanılamaz" |
| FR-2.4 | Validation (Çıkış + lot onaysız) ve uyarı otomasyonu |
| FR-2.5 | Çıkış hareketi Proje ve Deneme'ye bağlanır; tüketim maliyeti projeye toplanır |
| FR-2.6 | Talep onayında çıkış hareketi otomatik oluşur |
| FR-2.7 | Saklama süresi bitince Depo Görevi açılır, numune "Karar Bekliyor" olur |
| FR-2.8 | Workiom Excel içe aktarma (UI) — Malzeme Kartları ve Lotlar |
| FR-2.9 | Lot ve numune için `CreateQRCode` alanı |
| FR-3.1 | Her pazartesi aktif haftalık serilerden toplantı oluşturulur |
| FR-3.2 | Yeni "Haftalık Ar-Ge" toplantısında açık aksiyonlar gündem maddesi olarak eklenir |
| FR-3.3 | Toplantı "Yapıldı" olunca katılımcılara bildirim gider |
| FR-3.4 | Atama bildirimi, son tarihe 2 gün kala hatırlatma, tarih geçince "Gecikmede" |
| FR-3.5 | Kararlar ve aksiyonlar projeye bağlı, proje sayfasında görünür |
| FR-3.6 | `Kayıt / Transkript` + `AI Özeti` alanları; AI agent UI'da bağlanır |
| FR-3.7 | UI'da "Sorumlu = Ben" filtresiyle kişisel görünüm |
| FR-3.8 | Kapsam dışı (opsiyonel) |

## Build sonrası UI'da yapılacaklar

1. **Roller ve yetki matrisi** (API ile kurulmuyor): Ar-Ge Direktörü, Proje Lideri, Ar-Ge Uzmanı, Stok Sorumlusu, Kalite/Ruhsat. Satır bazlı kurallar:
   - Proje Lideri: kendi projeleri (`Proje Lideri = Ben`).
   - Uzman: atandığı projeler (`Ekip içerir Ben`).
   - Stok Sorumlusu: Proje uygulamasını görmez.
   - QA: yalnızca `Lot Durumu` alanını düzenler.
2. **`Mevcut Faz` alanı** yalnızca okunur olmalı (yalnızca otomasyon günceller). FR-1.2'nin "kapı onayı olmadan faz geçilemez" kuralını bu sağlar.
3. **FR-3.7:** Aksiyonlar listesine "Bana Atanan Açık Aksiyonlar" görünümü eklenir (filtre: Sorumlu = Geçerli kullanıcı, Status ≠ Tamamlandı).
4. **FR-3.3:** E-posta isteniyorsa bildirim aksiyonunun yanına UI'dan "Send Email" adımı eklenir. Builder'da e-posta aksiyonu henüz yarım destekli.
5. **FR-3.6:** Toplantılar listesine AI Agent otomasyonu kurulur (transkriptten özet, karar ve aksiyon taslağı).
6. **Direktör dashboard'u:** Raporlar her uygulamanın kendi dashboard'unda. Tek ekranda birleşik görünüm için bir Vibe App (`workiom-vibe-apps` skill) ya da paylaşılan dashboard kurulur.
7. **Proje kaydı sekmeleri:** Upgrade sonrası back-link alanları yukarıdaki "Önerilen proje kaydı sekmeleri" düzenine göre layout'a eklenir.

## İlk kurulumda doğrulanacak noktalar

- **Faz ilerletme (FR-1.3):** `find_records` filtresi lookup alanı (`Faz Kapıları.Proje Kodu`) üzerinden çalışıyor. Bu yüzden Proje Kodu benzersiz olmalı.
- **Lookup kullanıcı alanlarına bildirim:** Proje Lideri, Proje Ekibi ve Ar-Ge Direktörü bildirimlerinin gittiği kontrol edilmeli. Gitmiyorsa ilgili listeye USER alanı eklenip otomasyonla doldurulur.
- **Rollup zincirleri:** `Malzeme.Toplam Stok` (rollup'ın rollup'ı) ve `Gerçekleşen Maliyet` (lookup içeren formülün rollup'ı) değerleri kontrol edilmeli. Hatalıysa:
  - Stok Hareketleri'ne doğrudan `Malzeme` LINK alanı eklenir ve Toplam Stok buradan toplanır.
  - Birim maliyet harekete otomasyonla yazılır.
- **FR-2.4 validation** lookup alanına (`Lot Durumu`) dayanıyor. Çalışmazsa uyarı otomasyonu emniyet olarak kalır.
- **FR-3.2:** Haftalık Ar-Ge toplantısı **tüm** açık aksiyonları gündeme alır. Bunu seri bazında daraltmak PoC sonrası iş.
