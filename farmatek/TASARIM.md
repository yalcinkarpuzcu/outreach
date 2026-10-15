# Farmatek — Ar-Ge Proje Yönetimi (Workiom) · Tasarım Dokümanı

**Tenant:** farmatek.workiom.com · **Yeni app adı:** `Ar-Ge Proje Yönetimi`
**Durum:** Taslak, onay bekliyor. Onay gelmeden build yapılmayacak.
**Kaynaklar:** Müşterinin ihtiyaç listesi (7 başlık + 7 demo senaryosu), `Calcium Carbonate Tablet Proje Takip Çizelgesi.xlsx`, mevcut deneme app'i "Yalçın 2".

---

## 0. Özet

MS Project alışkanlığı olan bir ekip için kurgu şöyle: **Görev Kütüphanesi** bir şablon Gantt'ı gibi çalışır. Fazlar, alt fazlar, görevler, öncüller, süreler, sorumlu departman ve onay gerekliliği burada tanımlanır. PM yeni bir **Proje** açıp şablonu ve başlangıç tarihini seçtiği anda görevler hiyerarşi, öncül bağları ve tarihlerle birlikte projeye kopyalanır. Gantt'ta bağımlılık okları ve kritik yol görünür, bir görev kaydırıldığında ardılları otomatik kayar. Ekip üyeleri sadece kendilerine atanan görevlerde durum, ilerleme ve doküman alanlarını güncelleyebilir. Öncülü bitmeyen görev başlatılamaz, onay gerektiren görev onaysız kapatılamaz.

### Eski app'ten (Yalçın 2) çıkan dersler

| Gözlem | Yeni tasarımda |
|---|---|
| Öncül bağlama otomasyonu görevi **sadece isimle** arıyordu ve proje filtresi yoktu. Bu yüzden bir görevin öncül alanına **diğer projelerin** aynı isimli görevleri de eklendi (ör. "Hammadde Verifikasyonu" görevinde 18 öncül var). | Eşleştirme **Proje + Şablon Öğesi (ID)** ile yapılır, isimle değil. Çapraz proje bağı oluşamaz. |
| Kütüphane 3 ayrı listeye dağılmıştı (Faz Kütüphane, Görevler Kütüphane, Öncüller Kütüphane, Öncüllük Eşleştirme). | Tek liste: **Görev Kütüphanesi**. Fazlar üst öğe, öncüller native bağımlılık alanında tutulur ve kütüphanenin kendisi Gantt'ta görünür. |
| Milestone'lar ayrı liste, Baseline ayrı liste, Proje bilgisi lookup zinciriyle taşınıyordu. | Kilometre taşı görevin bir özelliği. Baseline görev üzerindeki alanlar + arşiv listesi. Proje doğrudan link. |

---

## 1. Platformda doğrulanan yetenekler

Bunları farmatek tenant'ındaki API ve Workiom web uygulamasının kodunu inceleyerek doğruladım:

| Yetenek | Workiom karşılığı |
|---|---|
| Native bağımlılık alanı | `dataType 21 – Dependency`. Aynı listedeki kayıtlara bağlanır, değer `[{_id, dependencyType}]`. Tipler: **1 FS, 2 SS, 3 FF, 4 SF** |
| Gantt görünümü | `viewType 12`. Bağımlılık alanını kullanır. Ölçek: Gün/Hafta/Ay/Çeyrek/Yarıyıl |
| Kritik yol | Gantt seçeneği `showCriticalPath` |
| Bağımlı görevlerin otomatik kayması | Gantt seçeneği `dependencyShifting`: `none`, `maintain_buffer_all`, `maintain_buffer_downstream`, `consume_buffer` |
| Hiyerarşi | TASK tipi liste: Parent Task / Subtasks (sınırsız derinlik) |
| Başlangıç/bitiş eşlemesi | TASK listesinde `startDateFieldId` / `dueDateFieldId` |
| Yetkilendirme | Liste bazında: erişim, kayıt ekleme, silme, toplu güncelleme, export, import, görünüm oluşturma. **Kayıt filtresi** (ör. departman), **alan bazında** Editor/ReadOnly/Denied, **koşullu yetki grupları** (ör. "Sorumlu = ben ise şu alanlar düzenlenebilir") |
| Otomasyon | Kayıt bul (iç içe), kayıt oluştur/güncelle, **bağımlılık alanına ekleme (append)**, formül ile tarih hesabı, onay aksiyonu, zaman tetikleyici, bildirim |

---

## 2. Veri modeli

```
⚙️ Kütüphane (yalnızca PMO/Admin düzenler)
   Departmanlar ─┐
   Proje Şablonları ─┐
   Görev Kütüphanesi (TASK) ── Şablonlar ⇢ Proje Şablonları
                               Sorumlu Departman ⇢ Departmanlar
                               Öncüller (native dependency, kendi içinde)
                               Üst Öğe (Parent Task: Faz → Alt Faz → Görev → Alt Görev)

📁 Proje Yönetimi
   Projeler (TASK) ── Şablon ⇢ Proje Şablonları
   Görevler (TASK) ── Proje ⇢ Projeler
                      Şablon Öğesi ⇢ Görev Kütüphanesi   (izlenebilirlik + eşleştirme anahtarı)
                      Öncüller (native dependency), Parent Task
   Onay Geçmişi    ── Görev ⇢ Görevler
   Baseline Arşivi ── Görev ⇢ Görevler, Proje ⇢ Projeler
```

### 2.1 Departmanlar (DATA)
Departman Adı · Kod · Departman Yöneticisi (kullanıcı) · **Onaylayıcı** (kullanıcı) · Ekip Üyeleri (çoklu kullanıcı) · Açıklama

**Seed:** Proje Yönetimi, Formülasyon Geliştirme, Analitik Metot Geliştirme, Ruhsat, Kalite Güvence

### 2.2 Proje Şablonları (DATA)
Şablon Adı · Açıklama · Aktif

**Seed:** **Yeni Ürün** (38 kalem), **Alternatif Kaynak** (36 kalem; Excel'in 2. sayfasındaki gibi "DMF temini" ve "Referans ürün temini" yok)

### 2.3 Görev Kütüphanesi (TASK): MS Project şablonu gibi çalışır
| Alan | Tip | Not |
|---|---|---|
| Görev Adı | başlık | |
| WBS No | sayı | Excel'deki "No" |
| Tür | seçim | Faz / Alt Faz / Görev / Alt Görev / Kilometre Taşı |
| Şablonlar | link (çoklu) → Proje Şablonları | Bir kalem birden çok şablonda kullanılabilir |
| Sorumlu Departman | link → Departmanlar | |
| Başlangıç / Bitiş | tarih | Gantt eşlemesi. "Gün 0" = 01.01.2026 referans takvimi |
| Referans Tarih | tarih (gizli) | 01.01.2026 |
| **Başlangıç Ofseti (gün)** | formül | `Başlangıç − Referans Tarih` |
| **Süre (gün)** | formül | `Bitiş − Başlangıç` |
| **Öncüller** | **native bağımlılık** | Gantt'ta oklar görünür |
| Üst Öğe | Parent Task (sistem) | Faz/alt faz hiyerarşisi |
| Kilometre Taşı · Onay Gerekli | evet/hayır | |
| Onaylayıcı (özel) | kullanıcı | Boşsa departman onaylayıcısı kullanılır |
| Kabul Kriteri / Açıklama | çok satırlı metin | |
| Varsayım | evet/hayır | Excel'de süre/öncül tanımı olmayan kalemler (aşağıya bakın) |

**Görünümler:** "Yeni Ürün Şablonu" (Gantt, kritik yol açık, kaydırma modu: *maintain_buffer_downstream*), "Alternatif Kaynak Şablonu" (Gantt), "Kütüphane Tablosu" (Grid, WBS sıralı).

PMO kütüphane Gantt'ında bir görevin süresini uzattığında ardılları kayar ve ofset formülü kendiliğinden güncellenir. Bundan sonra açılan projeler yeni planla gelir.

### 2.4 Projeler (TASK): portföy Gantt'ı için TASK tipinde
Proje Adı · Proje Kodu (oto no) · Ürün/Molekül · **Şablon** · **Proje Yöneticisi** (atanan) · **Başlangıç Tarihi** · Hedef Bitiş · Durum · Plan Durumu (gizli, otomasyon adımı) · Baseline No · Baseline Tarihi · Proje Ekibi · Dokümanlar · Açıklama
Hesaplananlar: Toplam Görev · Tamamlanan Görev · **Tamamlanma %** · **Geciken Görev** · Plan Bitiş (görevlerin en geç bitişi)

**Durumlar:** Taslak → Planlanıyor → **Plan Onaylandı (Baseline)** → Devam Ediyor → Beklemede → Tamamlandı ✓ / İptal ✓

### 2.5 Görevler (TASK): tüm projelerin görevleri tek listede
| Alan | Tip | Kim düzenler |
|---|---|---|
| Görev Adı, WBS No, Tür | başlık / sayı / seçim | PM |
| Proje | link | PM (otomatik) |
| Sorumlu Departman | link | PM |
| **Sorumlu** | kullanıcı (atanan) | PM |
| Onaylayıcı | kullanıcı | PM (otomatik doldurulur) |
| **Başlangıç / Bitiş** | tarih (Gantt) | **PM** |
| Süre (gün) | formül | – |
| **Öncüller** | native bağımlılık | PM |
| Parent Task / Subtasks | sistem | PM |
| **Durum** | durum | **Sorumlu** (kurallara tabi) |
| **% Tamamlanma** | sayı 0–100 | **Sorumlu** |
| Gerçekleşen Başlangıç / Bitiş | tarih | Otomatik (Sorumlu düzeltebilir) |
| **Dokümanlar** (protokol, rapor…) | dosya | **Sorumlu** |
| **Notlar** | çok satırlı metin | **Sorumlu** |
| Kilometre Taşı, Onay Gerekli | evet/hayır | PM |
| Onay Durumu | seçim: Gerekmiyor / Bekliyor / Onaylandı / Reddedildi | Otomatik |
| Son Onay Notu | metin | Otomatik |
| Baseline Başlangıç / Bitiş | tarih | Otomatik |
| **Sapma (gün)** | formül: `Bitiş − Baseline Bitiş` | – |
| Gecikmede | evet/hayır | Otomatik |
| Kapalı (0/1), Açık Öncül Sayısı | sayı / rollup (gizli) | Otomatik |
| Şablon Öğesi | link → kütüphane | Otomatik |

**Durumlar:** Başlamadı → **Başlayabilir** → Devam Ediyor → **Onay Bekliyor** → Tamamlandı ✓ · Revizyon Gerekli · Beklemede · İptal ✓

**Görünümler:**
- **Proje Planı (Gantt):** tüm projeler, kritik yol, `maintain_buffer_downstream`; proje filtresi ile tek proje
- **Kilometre Taşları (Gantt)**
- **Görevlerim** (Grid)
- **Panolar** (Kanban, Durum'a göre)
- **Takvim** (Bitiş)
- **Geciken Görevler**, **Onay Bekleyenler**, **Bu Hafta Bitecekler** (Grid)

### 2.6 Onay Geçmişi (DATA)
Görev · Proje · Karar (Onaylandı/Reddedildi) · Onaylayan · Tarih · Not. Her onay kararı bir satır olarak kalır, GxP izlenebilirliği için.

### 2.7 Baseline Arşivi (DATA)
Proje · Görev · Baseline No · Baseline Tarihi · Planlanan Başlangıç · Planlanan Bitiş. Her baseline alınışında görev başına bir satır oluşur (Baseline 1, 2, …).

---

## 3. İş akışları (otomasyonlar)

| # | Tetikleyici | Ne olur |
|---|---|---|
| **A1** | Proje oluşturuldu (Şablon ve Başlangıç dolu) | Kütüphaneden şablona ait tüm kalemler WBS sırasıyla bulunur ve Görevler'e kopyalanır: ad, WBS, tür, departman, kilometre taşı, onay gerekli, onaylayıcı, **Başlangıç = Proje Başlangıç + Ofset**, **Bitiş = Başlangıç + Süre**. Sorumlu = departman yöneticisi (PM sonradan kişiye atar). Sonunda Plan Durumu "Görevler Oluşturuldu" olur. |
| **A2** | Plan Durumu → "Görevler Oluşturuldu" | **Hiyerarşi:** her görevin üst öğesi aynı projede şablon üst öğesine karşılık gelen kayda bağlanır. **Öncüller:** kütüphanedeki her öncül bağı, aynı projedeki karşılık gelen görevlere (Proje + Şablon Öğesi ile eşleşerek) native bağımlılık olarak eklenir. Sonra Plan Durumu "Hazır" olur ve PM'e "Plan hazır" bildirimi gider. |
| **A3** | Görev Durum değişti → Devam Ediyor / Onay Bekliyor / Tamamlandı | **Kilit:** Açık Öncül Sayısı > 0 ise durum "Başlamadı"ya geri alınır ve sorumluya "Öncül görevler tamamlanmadan başlatılamaz" bildirimi gider. (Ayrıca kayıt formunda aynı kural validasyon olarak tanımlanır, kullanıcı kaydedemeden uyarı görür.) |
| **A4** | Durum → Devam Ediyor | Gerçekleşen Başlangıç boşsa bugün yazılır. |
| **A5** | Durum → Onay Bekliyor | **Onay aksiyonu** (onaylayıcı = görevdeki Onaylayıcı). **Onay:** Onay Durumu = Onaylandı, Durum = Tamamlandı, Gerçekleşen Bitiş = bugün, % = 100, Onay Geçmişi'ne satır. **Red (gerekçe zorunlu):** Durum = Revizyon Gerekli, Onay Durumu = Reddedildi, gerekçe Son Onay Notu'na, sorumluya bildirim, Onay Geçmişi'ne satır. |
| **A6** | Durum → Tamamlandı | Onay Gerekli = Evet ve Onaylandı değilse durum "Onay Bekliyor"a çevrilir, yani onay atlanamaz. Değilse Kapalı = 1, % = 100, Gerçekleşen Bitiş = bugün. **Ardıllar:** bu görevi öncül olarak bekleyen görevler bulunur. Tüm öncülleri kapanmış olanlar **Başlayabilir** durumuna geçer ve sorumlusuna bildirim gider. |
| **A7** | Bitiş − 3 gün (zaman tetikleyici) | Sorumluya ve PM'e "yaklaşan son tarih" bildirimi gider. |
| **A8** | Bitiş + 1 gün, görev kapalı değil | Gecikmede = Evet, sorumlu + PM'e bildirim. Kapanınca bayrak "geç tamamlandı" bilgisi olarak kalır, dashboard açık gecikmeleri sayar. |
| **A9** | Proje Durum → Plan Onaylandı (Baseline) | Baseline No +1, Baseline Tarihi = bugün. Projenin tüm görevlerinde Baseline Başlangıç/Bitiş = mevcut plan, Baseline Arşivi'ne satır yazılır. Sapma (gün) bu andan itibaren hesaplanır. |

---

## 4. Rol ve yetki matrisi

| | PMO / Admin | **Proje Yöneticisi** | **Ekip Üyesi** (departman bazlı) | Yönetim (izleyici) |
|---|---|---|---|---|
| Kütüphane | Düzenler | Okur | Göremez | Okur |
| Projeler | Tam | Oluşturur, düzenler | Okur | Okur |
| Görevler: ekleme / silme | ✓ | ✓ | ✗ | ✗ |
| Görevler: tarih, süre, öncül, sorumlu, hiyerarşi | ✓ | ✓ | **Salt okunur** | Salt okunur |
| Görevler: Durum, %, Notlar, Dokümanlar | ✓ | ✓ | **Yalnızca Sorumlu = kendisi olan görevlerde** | ✗ |
| Görünürlük | Tümü | Tümü | **Kendi departmanının görevleri** (veya tümü salt okunur, müşteri seçer) | Tümü |
| Export (Excel) | ✓ | ✓ | Opsiyonel | ✓ |
| Görünüm oluşturma | ✓ | ✓ | Kapalı (plan yapısı korunur) | Kapalı |

Teknik karşılığı: rol başına liste izinleri (`createRecords`/`deleteRecords` = false), **kayıt filtresi** (Sorumlu Departman = X), **alan izinleri** (varsayılan ReadOnly) ve **koşullu yetki grubu** ("Sorumlu = mevcut kullanıcı" → Durum, %, Notlar, Dokümanlar = Editor). Departman başına bir ekip rolü açılır (Ekip – Formülasyon, Ekip – Analitik, Ekip – Ruhsat …). Roller Workiom'da merkezi olarak yönetilir.

---

## 5. Müşteri sorularına cevap haritası

✅ native · 🔧 bu kurguyla sağlanıyor · ⚠️ kısıt veya teyit gerekiyor

**1. Planlama & Gantt**
- Faz/alt faz/görev/alt görev hiyerarşisi: ✅ Parent/Subtask, Tür alanı
- Tarih, süre, kilometre taşı, ilerleme Gantt'ta: ✅ (ilerleme yüzdesi Gantt'ta salt okunur gösterilir)
- Bağımlılıklar Gantt'ta: ✅ FS/SS/FF/SF, kritik yol
- Süre değişince bağımlıların kayması: ✅ Gantt'ın "dependency shifting" modu. ⚠️ Kayma, tarih **Gantt üzerinde** değiştirildiğinde çalışır. Tablo/form üzerinden değişince ardıllar kendiliğinden kaymıyor olabilir, build sonrası test edip netleştireceğim.
- Çoklu proje ortak görünüm: ✅ Görevler Gantt'ı tüm projeleri gösterir, Projeler Gantt'ı portföy görünümüdür, dashboard ortaktır.

**2. Yetkilendirme:** ✅ / 🔧 Bölüm 4. Alan bazında, departman bazında, "sadece bana atanan" kuralları native izin modeliyle kuruluyor.

**3. Bağımlılık & iş akışı kontrolü**
- Öncül bitmeden başlatma/tamamlama engeli: 🔧 A3 (validasyon + geri alma otomasyonu). Bağımlılıklar sadece görsel değil, kural olarak işliyor.
- Tamamlanınca sonrakinin aktifleşmesi ve atanması: 🔧 A6 (Başlayabilir + bildirim; istenirse atama da yapılır)
- Sıralı yürütme: 🔧 A3 + A6

**4. Onay:** 🔧 A5/A6. Zorunlu onay, red durumunda gerekçe ve revizyona geri gönderme, onaysız sonraki görevin açılmaması (onaylanmayan görev Kapalı sayılmaz). Departman bazlı onaylayıcı, görev bazında özel onaylayıcı, proje bazında PM onayı tanımlanabilir. Çok aşamalı onay (ör. Departman → QA) ek otomasyonla eklenebilir.

**5. Gecikme & raporlama:** 🔧 A7/A8 bayrak ve bildirim. ✅ Dashboard: aktif proje, geciken görev, onay bekleyen, departmana göre iş yükü, proje bazında tamamlanma %, kilometre taşları tablosu. ✅ Excel export (liste/görünüm bazında; rol ile kısıtlanabilir).

**6. Doküman & geçmiş:** ✅ Görev ve proje üzerinde dosya alanı ✅ Kayıt bazında aktivite/değişiklik geçmişi (kim, ne zaman, hangi alan) + yorumlar. 🔧 Onay Geçmişi ve Baseline Arşivi kalıcı kayıt tutar. ⚠️ Kullanıcı bazlı merkezi audit log ekranının kapsamı ve lisans seviyesi Workiom ekibiyle teyit edilecek.

**7. Lisans:** ⚠️ Paket/fiyat bilgisini satış ekibi verecek, bu dokümanda tahmin yürütmüyorum. ✅ Excel planlarının aktarımı: kütüphane bu Excel'den üretildi. Mevcut projeler için ayrıca Excel import yapılabilir.

**Baseline (Cuma toplantısı için):** 🔧 A9. Birden çok baseline, plan ile baseline arasındaki sapma (gün) ve Gantt'ta karşılaştırma için "Baseline vs Plan" tablo görünümü. ⚠️ Gantt üzerinde baseline'ı ikinci bir gölge çubuk olarak gösterme (MS Project'teki gibi) native değil. Sapma kolon ve renk ile gösterilecek.

---

## 6. Demo senaryoları → nasıl gösterilecek

| # | Senaryo | Akış |
|---|---|---|
| 1 | PM planı kurar, ekip değiştiremez | PM "Projeler"den Yeni Ürün şablonuyla proje açar. 38 görev hiyerarşi, öncül ve tarihlerle Gantt'ta oluşur. Ekip kullanıcısıyla girilince tarih, öncül ve sorumlu alanları kilitlidir, ekle/sil butonu görünmez. |
| 2 | Sadece kendine atanan görevi günceller | Ekip üyesi kendi görevinde Durum ve % alanını değiştirir. Başkasının görevinde aynı alanlar salt okunurdur. |
| 3 | Öncül bitmeden tamamlanamaz | "Stress Çalışması" (öncül 9 ve 16) Devam Ediyor yapılmaya çalışılır, sistem geri alır ve uyarır. 16 tamamlanınca 17 "Başlayabilir" olur ve bildirim düşer. |
| 4 | Zorunlu onay | "Formülasyon Geliştirme Çalışmaları" Onay Bekliyor yapılır. Onaylayıcı reddeder (gerekçe yazar), görev Revizyon'a döner. Tekrar gönderilip onaylanınca Tamamlandı olur ve ardıllar açılır. |
| 5 | Süre değişince bağımlılar | Proje Gantt'ında "Seçilen API'nin Temini" 2 ay → 3 ay uzatılır. Geçimlilik, Formülasyon Geliştirme, Stabilite … zinciri kayar, kritik yol güncellenir, Sapma kolonu baseline'a göre +30 gün gösterir. |
| 6 | Çoklu proje | Calcium Carbonate (Yeni Ürün) + ikinci bir demo proje (Alternatif Kaynak). Portföy Gantt'ı, tüm görevler Gantt'ı ve dashboard birlikte gösterilir. |
| 7 | Değişiklik geçmişi | Görev kaydının aktivite sekmesinde tarih/durum değişikliği yapan kişi ve zaman, Onay Geçmişi listesi, Baseline Arşivi. |

Demo verisi: "Calcium Carbonate Tablet" (Yeni Ürün, başlangıç 02.06.2025, Excel'deki gerçek tarihlerle uyumlu) + "Demo – Alternatif Kaynak" projesi. Birkaç görev tamamlanmış, biri gecikmiş, biri onay bekler halde hazırlanır.

---

## 7. Excel'den kütüphaneye aktarım (varsayımlar)

- 1–26 numaralı kalemler: süre ve öncül **Excel'den birebir** alındı. "18.9" yazımı **18 ve 9** olarak yorumlandı.
- Süreler **takvim günü**: 1 hafta = 7, 1 ay = 30, 2 ay = 60, 4 ay = 120. (İş günü takvimi istenirse ayrıca konuşulmalı. Gantt hafta sonu atlamayı destekliyor mu, teyit edilecek.)
- 27–38 (Dosya Başvurusu ve Ruhsat Alımı fazları): Excel'de **No, süre ve öncül yok**. Hedef tarihlerden aşağıdaki şekilde türetildi ve kütüphanede **"Varsayım" işaretli**. Müşteriyle teyit edilmeli:

| No | Kalem | Öncül | Süre |
|---|---|---|---|
| 27 | TR&EU Dosya Hazırlığı | 23, 24 | 60 |
| 28 | PV Stabilite 3&6 Ay | 25 | 180 |
| 29 | Ruhsat ile dosya paylaşımı/kontrol | 27 | 15 |
| 30 | BE Sonucunun Alınması (KT) | 26 | 0 |
| 31 | Dosya Başvurusu (KT, onaylı) | 28, 29, 30 | 0 |
| 32 | Bakanlık İncelemesi / Eksiklik Yazıları | 31 | 90 |
| 33 | Teknik Komisyon Onayı | 32 | 270 |
| 34 | BE/BY Komisyon Onayı | 32 | 270 |
| 35 | KUB/KT Komisyon Onayı | 33 | 180 |
| 36 | Raf Ömrü Onayı | 32 | 270 |
| 37 | Ruhsat Alımı (KT) | 33, 34, 35, 36 | 0 |
| 38 | Geri Ödeme Başvurusu | 37 | 30 |

- **Departman**, Excel'de tarihin hangi "Zaman Bildirimi" kolonunda olduğuna göre atandı (Formülasyon / Analitik / Ruhsat). 1–2 ve 30 Proje Yönetimi'ne verildi.
- **Onay gerekli** (varsayılan): 3, 5, 18, 19, 22, 23, 27, 31. **Kilometre taşı:** 1, 30, 31, 37.
- Hesaplanan toplam süre ≈ **1006 gün (~33 ay)**. Excel'deki Haziran 2025 → Ocak 2028 aralığıyla uyumlu.

---

## 8. Teknik riskler (build'de test edilecek)

1. **Otomasyon sırası:** A1 tüm görevleri oluşturmadan A2 başlamamalı. Bu yüzden A2 ayrı bir alan değişikliğiyle tetikleniyor. Görevler dakikalar içinde değil, saniyeler içinde oluşmalı; 38 kayıtta test edilecek.
2. **"Açık Öncül Sayısı"**: native bağımlılık alanında rollup yapılamadığı için görevde gizli bir yardımcı link (Öncül Kayıtları) tutulup üzerinden rollup yapılıyor. Rollup'ın anlık güncellenmesi test edilecek. Gecikirse A6'da koşul doğrudan öncül kayıtları üzerinden kontrol edilecek.
3. **Kanban'da sürükle-bırak** validasyonu atlayabilir. A3 otomasyonu bu durumda da durumu geri alır (güvenlik ağı).
4. **Bağımlılık tipi:** otomasyonla eklenen bağlar FS olarak gelir (Excel'deki tüm bağlar FS). SS/FF gerekirse PM Gantt'ta değiştirir. Lag (öncül + n gün) native olarak yok gibi görünüyor, teyit edilecek.
5. **Rol izinleri API'si:** rol/yetki ağacı API ile kurulabiliyor. Koşullu yetki grubunun ("Sorumlu = ben") API'deki karşılığı build'de netleşecek, gerekirse bu adım UI'dan yapılacak.

---

## 9. Build planı (onaydan sonra)

1. `python main.py build farmatek_arge.py`: app, klasörler, listeler, alanlar, görünümler (Grid/Kanban/Takvim), formlar, raporlar, basit otomasyonlar
2. `python farmatek_ileri.py`: TASK tarih eşlemeleri, native bağımlılık alanları, Gantt görünümleri (kritik yol + kaydırma modu), formül/rollup alanları, iç içe otomasyonlar (A1, A2, A5, A6, A9), validasyonlar, roller
3. `python farmatek_seed.py`: departmanlar, 2 şablon, 38 kütüphane kalemi (tarihler + öncüller + hiyerarşi), demo projeler
4. Uçtan uca test: proje oluştur → hiyerarşi, öncül ve tarih kontrolü (öncüllerin proje dışına sızmadığı doğrulanır) → kilit → onay → kayma → baseline
5. Kısa test raporu + demo akış notu

Eski "Yalçın 2" app'ine dokunulmaz.

## 10. Senden beklenen kararlar

1. Ekip üyeleri **sadece kendi departmanlarının** görevlerini mi görsün, yoksa **hepsini salt okunur** mu görsün?
2. 27–38 varsayımları demo için yeterli mi?
3. Onay gerekli görev listesi (3, 5, 18, 19, 22, 23, 27, 31) uygun mu?
4. Kullanıcı/rol testleri için farmatek tenant'ında hangi kullanıcılar kullanılabilir (PM, ekip üyesi, onaylayıcı)?

---

## 11. Kurulum sonrası notlar (as-built, 16.10.2026)

**Kurulu:** app `Ar-Ge Proje Yönetimi` (7 liste, 2 klasör), 8 otomasyon (A1, A2, A2b, A3–A6, A6b, A7–A8, A8b, A9), 12 rapor, 3 rol, kütüphane (6 faz + 38 kalem, 2 şablon), 2 demo proje. Vibe app: `Ar-Ge Proje Merkezi`.

Tasarımdan sapmalar ve canlı testte bulunanlar:

| Konu | Sonuç |
|---|---|
| Otomasyon filtre operatörleri | `1 = Contains` (çoklu link/bağımlılık), `3 = Is` (tekil). Çoklu linkte `Is` yalnızca tek değerli kayıtları buluyor. |
| Tarih formülü | `DateAdd` otomasyon eşlemesinde boş dönüyor; `tarih + gün` çalışıyor. |
| Hiyerarşi | Sistem "Üst Görev" alanı otomasyonla yazılamıyor → üst kaydın "Alt Görevler" alanına append ile kuruluyor. Lookup alanı find filtresinde kaynak olarak çalışmıyor → kütüphanenin "Alt Öğeler" alanı kullanılıyor. |
| Ardılı açma | Rollup, aynı otomasyon içinde henüz güncellenmemiş olabiliyor → **A6b** eklendi: ardıl, kendi "Kapanan Öncül" rollup'ı değişince kendini "Başlayabilir"e alıyor (testte ~8 sn). |
| Gecikme | Zaman tetikleyicisi yerine günlük (06:00) zamanlanmış kontrol: geciken bayrağı + 3 gün kala hatırlatma. |
| "Yalnızca kendi görevini güncelle" | Workiom arayüzü koşullu yetki grubunu (permissionGroups) göndermiyor → rolde alan bazında kısıt var (ekip: yalnızca Durum, %, Notlar, Dokümanlar, gerçekleşen tarihler düzenlenebilir; ekleme/silme/görünüm oluşturma kapalı); "yalnızca bana atanan" kuralı vibe app'te uygulanıyor. Native arayüzde ekip üyesi başkasının görevinin durumunu değiştirebilir — Workiom ekibiyle teyit/yol haritası konusu. |
| A2 bölündü | Öncül döngüsü (42×20 iç içe adım) ile hiyerarşi döngüsü aynı otomasyonda olunca ikincisi hiç çalışmadı (çalıştırma başına adım limiti). Hiyerarşi **A2b**'ye taşındı (Plan Durumu = Hazır tetikler). Yeni projede tüm zincir ~80 sn: 44 görev, 37 öncül, 38 üst bağ. |
| WBS 37 adı | Faz "Ruhsat Alımı" ile çakıştığı için kalem adı "Ruhsatın Alınması". |
| Onay | Vibe app onay/redi doğrudan yapıyor (`AutomationApprovalRequest/Approve|Reject`); Workiom bildirimi üzerinden de yapılabiliyor. |

**Uçtan uca test (canlı, `akis_testi.py`):** proje oluşturma → 44 kayıt + hiyerarşi + 37 öncül bağı (proje dışına sızan bağ: 0) · öncülü açık görevi başlatma → geri alındı · tamamla → ardıllar Başlayabilir · onaylı görevi doğrudan tamamla → Onay Bekliyor · red (gerekçeli) → Revizyon · tekrar onay → Tamamlandı + Onay Geçmişi'nde 2 satır · baseline → 44 görevde baseline + 44 arşiv satırı · bitiş +30 gün → sapma +29.

**Rol atamaları yapılmadı** — roller kullanıcısız oluşturuldu; demo kullanıcıları Workiom > Ayarlar > Ekipler'den atanmalı.
