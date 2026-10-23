# Polifarma Ar-Ge Workiom
@sub Kullanım Kılavuzu
@meta Pilot ekip için · 23 Ekim 2026 · Hazırlayan: Workiom (Yalçın Karpuzcu)

## Başlarken

Ar-Ge projeleri, stok ve toplantılar artık tek bir yerde, Workiom'da takip edilir: **polifarma.workiom.com**. Bu kılavuz pilot ekip içindir; rolünüzü bulup ilgili bölümleri okumanız yeterli.

### Üç uygulama

| Uygulama | Ne için | En çok kim kullanır |
| --- | --- | --- |
| **Ar-Ge Proje Takibi** | Projeler, faz kapıları, denemeler, analitik, stabilite, görev ve sapmalar | Proje liderleri, uzmanlar, direktör, kalite |
| **Numune ve Hammadde Stok** | Malzemeler, lotlar, stok hareketleri, formül bileşenleri, numuneler, talepler | Stok sorumlusu, uzmanlar |
| **Toplantı Yönetimi** | Toplantılar, gündem, kararlar, aksiyonlar | Herkes |

Uygulamalar birbirine bağlıdır. Bir projeyi açtığınızda o projenin faz kapılarını, denemelerini, stok tüketimini, maliyetini ve toplantı kararlarını aynı kayıtta görürsünüz.

### Ekranı okumak

- **Liste:** Bir tablo gibidir (ör. Lotlar). Soldaki menüden uygulamayı, sonra listeyi seçersiniz.
- **Görünüm:** Aynı listenin farklı bakışıdır: tablo, kanban (kartlar), takvim, zaman çizelgesi. Listenin üstündeki sekmelerden geçersiniz; ör. "Faza Göre (Kanban)", "SKT Takvimi", "Onay Bekleyenler".
- **Kayıt:** Bir satıra tıklayınca açılır. Alanlar sekmelere ayrılmıştır (ör. "Proje Bilgileri", "Ekip ve Takvim"); alt kısımda bağlı kayıtlar listelenir.
- **Form:** Bazı işler için kısa giriş ekranları vardır: "Sapma / Görev Bildir", "Lot Girişi", "Stok Çıkışı", "Malzeme / Numune Talebi".
- **Bildirimler:** Sağ üstteki zil. Size atanan işler, onay istekleri ve uyarılar buraya düşer. Onay istekleri buradan onaylanır veya reddedilir.

### Bilmeniz gereken dört kural

1. **"Ad" alanını doldurmayın.** Her kaydın başlığı otomatik oluşur: proje için "PF-2026-001 — Ürün Adı", lot için Lot No, hareket için "Hareket #12" gibi.
2. **"Durum" alanı süreci yönetir.** Faz kapısı, talep, görev, toplantı ve aksiyonlarda işi ilerletmek için Durum'u değiştirirsiniz; onaylar ve bildirimler buna göre tetiklenir.
3. **Stok miktarı elle yazılmaz.** Kalan miktar ve toplam stok hareketlerden hesaplanır. Stok değişiyorsa bir hareket kaydı girersiniz.
4. **Projenin "Mevcut Faz" alanını değiştirmeyin.** Faz yalnızca faz kapısı iki onayı da alınca otomatik ilerler.

**Kodlama önerisi:** Proje Kodu her projede benzersiz olmalıdır (ör. PF-2026-001); faz ilerletme bu kodla çalışır. Lot No, Malzeme Kodu ve Deneme Kodu için de ekip içinde tek bir format belirleyin.

## Rolünüze göre ne yaparsınız

Her rolün düzenli işi birkaç kayıt türüyle sınırlıdır. Aşağıdaki tablo nereden başlayacağınızı gösterir; ayrıntılar ilgili bölümlerde.

| Rol | Her gün | Gerektiğinde | Haftalık | Bakılacak görünümler |
| --- | --- | --- | --- | --- |
| **Ar-Ge Direktörü** | Zildeki faz kapısı onay isteklerini onaylar / reddeder | Sapma ve CAPA bildirimlerini inceler; toplantıda karar girer | Dashboard'ları gözden geçirir | Faza Göre (Kanban), Onay Bekleyenler, Geciken Kapılar, Sapma ve CAPA |
| **Proje Lideri** | Kendi projelerinin görevlerini ve geciken işleri kontrol eder | Proje açar; faz kapısını onaya gönderir; görev atar; malzeme talebi açar | Toplantı açar, aksiyon atar | Aktif Projeler, Gecikenler, Açık Aksiyonlar |
| **Ar-Ge Uzmanı / Laborant** | Deneme, formül bileşeni, analitik ve stabilite sonuçlarını girer | Stok çıkışı girer; sapma bildirir | Kendi aksiyonlarını günceller | Deneme Takvimi, Ölçüm Takvimi, Planlanan Ölçümler |
| **Stok Sorumlusu** | Talepleri onaylar; lot girişi yapar | Sayım farkı, iade, imha girer; numune kararı verir | Kritik stok ve SKT listelerini kontrol eder | Bekleyen Talepler, Kritik Seviyedeki Malzemeler, 30 Gün İçinde SKT Dolan Lotlar, Karantinadaki Lotlar |
| **Kalite / Ruhsat** | Faz kapısı 2. onay isteklerini onaylar / reddeder | Lotları karantinadan çıkarır (Onaylı / Ret) | Sapma ve CAPA kayıtlarını izler | Karantinadaki Lotlar, Sapma ve CAPA, Onay Bekleyenler |

**Herkes için:** Size bir görev, aksiyon veya onay atandığında zile bildirim gelir. Bildirime tıklayınca ilgili kayıt açılır.

## Projeler ve faz kapıları

Bir proje **Ar-Ge Projeleri** listesinde açılır ve fazdan faza yalnızca **Faz Kapıları** üzerinden, Direktör ve QA onayıyla ilerler. Uygulama: Ar-Ge Proje Takibi.

### Yeni proje açmak (Proje Lideri)

1. Ar-Ge Projeleri → **+ Yeni kayıt**.
2. Zorunlu alanlar: **Proje Kodu** (benzersiz, ör. PF-2026-001) ve **Ürün Adı**.
3. Doldurun: Dozaj Formu, Proje Tipi, Referans Ürün, Başlangıç Tarihi, Hedef Ruhsat Tarihi, Bütçe, Risk Seviyesi, Durum = Aktif.
4. Kişileri seçin: **Proje Lideri**, **Ekip** (deneme girecek uzmanlar) ve **Ar-Ge Direktörü**. Bildirimler bu alanlara gider; boş bırakmayın.
5. **Mevcut Faz**'ı yalnızca proje açılışında seçin (genelde "1. Literatür ve Fizibilite"). Sonrasında bu alan elle değiştirilmez.

Proje kaydının altında bağlı tüm kayıtlar görünür: Faz Kapıları, Denemeler, Analitik ve Stabilite Çalışmaları, Görevler ve Sapmalar, Stok Tüketimi, Malzeme Talepleri, Numuneler, Toplantılar, Toplantı Kararları ve Aksiyonları. **Gerçekleşen Maliyet**, Deneme Sayısı, Görev / Sapma Sayısı ve Aksiyon Sayısı otomatik hesaplanır.

### Faz kapısı açmak ve onaya göndermek (Proje Lideri)

Her faz geçişi için bir faz kapısı kaydı açılır. Fazın başında açıp planlanan tarihleri girmeniz önerilir; gecikme takibi bu tarihlere göre yapılır.

1. Faz Kapıları → **+ Yeni kayıt** (veya proje kaydındaki Faz Kapıları bölümünden).
2. **Proje**'yi seçin. **Faz Adı** = kapanışı onaylanacak faz, **Sonraki Faz** = onaydan sonra projenin geçeceği faz.
3. Planlanan Başlangıç / Bitiş, Giriş ve Çıkış Kriterleri, Ekler (rapor, protokol).
4. **1. Onaylayan (Direktör)** ve **2. Onaylayan (QA/Ruhsat)** kişilerini seçin.
5. Çalışma sürerken Durum = **Devam Ediyor**.
6. Kriterler tamamlanınca Durum = **Direktör Onayı Bekliyor** yapın. Gerisi otomatiktir.

@img faz.png|Şekil 1 — Faz kapısı onay akışı: iki onay, iki red yolu

### Onay vermek (Direktör, QA / Ruhsat)

1. Zildeki **onay isteği** bildirimini açın (ör. "PF-2026-001 — … — 3. Formülasyon Geliştirme kapısı onayınızı bekliyor").
2. Kaydı ve eklerini inceleyin; gerekirse ilgili toplantı kararına bakın (kapı kaydındaki **Toplantı Kararları**).
3. **Onayla** veya **Reddet**. Reddederken açıklama yazmak zorunludur.
4. Onay isteği **5 gün** içinde yanıtlanmalıdır.

Direktör onaylayınca istek otomatik olarak QA'ya geçer. QA da onaylayınca kapı **Onaylandı** olur, Gerçekleşen Bitiş bugüne yazılır ve projenin Mevcut Faz'ı Sonraki Faz'a ilerler. Herhangi bir red kapıyı **Reddedildi** yapar; proje fazı değişmez. Yeniden değerlendirme için yeni bir kapı kaydı açılır.

### Görev, sapma ve CAPA

**Görevler ve Sapmalar** listesi üç tür kaydı tutar: Görev, Sapma, CAPA.

1. **Sapma / Görev Bildir** formunu veya listeye yeni kaydı kullanın.
2. Başlık (zorunlu), **Tip**, Proje, Atanan, Son Tarih, Öncelik, Açıklama, Ekler.
3. Durum: Açık → Devam Ediyor → Tamamlandı (veya İptal). Kapanışta **Kök Neden** ve **Kapanış Notu** doldurulur.

Tip **Sapma** veya **CAPA** seçilirse Proje Lideri ve Ar-Ge Direktörü anında bildirim alır; atanan kişiye de ayrıca bildirim gider. Son Tarih geçip kayıt kapanmamışsa Durum otomatik **Gecikmede** olur.

## Laboratuvar kayıtları

Deneme, analitik ve stabilite kayıtları Ar-Ge Proje Takibi'nde, denemede kullanılan hammaddeler ise Stok uygulamasındaki **Formül Bileşenleri**'nde tutulur. Her kayıt mutlaka bir projeye bağlanır.

### Formülasyon denemesi girmek (Uzman)

1. Formülasyon Denemeleri → **+ Yeni kayıt**.
2. **Deneme Kodu** (zorunlu), **Proje**, Batch No, Batch Büyüklüğü ve Batch Birimi, Sorumlu, Tarih.
3. **Proses Parametreleri**'ni yazın (karıştırma süresi, sıkıştırma kuvveti vb.).
4. Sonuç çıkana kadar Sonuç = **Devam Ediyor**; sonra **Uygun**, **Uygun Değil** veya **Tekrar** + Sonuç Notu + Ekler.

### Formül bileşenlerini girmek: stoktan düşme

Denemede kullanılan her hammadde, hangi lottan ne kadar alındığıyla birlikte bir **Formül Bileşeni** olarak girilir. Bileşen kaydı aynı miktarda **stok çıkışını otomatik yazar**; ayrıca stok çıkışı girmeyin.

1. Numune ve Hammadde Stok → Formül Bileşenleri → **+ Yeni kayıt**.
2. **Deneme** ve **İlgili Proje**'yi seçin (maliyetin projeye yazılması için ikisi de gerekli).
3. **Lot**'u seçin; Malzeme ve Birim lottan otomatik gelir. Lot **Onaylı** olmalıdır.
4. **Miktar** (zorunlu, lotun biriminde), Fonksiyon (Etken Madde, Dolgu, Bağlayıcı…), Formüldeki Oran (%).

Bir denemeyi açtığınızda altında **Formül Bileşenleri**, **Üretilen Numuneler**, **Stabilite** ve **Analitik Çalışmalar** listelenir. Böylece "bu batch'te hangi lottan ne kadar kullanıldı" sorusu tek ekranda cevaplanır.

### Analitik çalışma

Analitik Çalışmalar listesinde Test Tipi (Çözünürlük, Safsızlık, İçerik Tayini, Diğer), Metot, **Validasyon Durumu** (Planlandı → Geliştirmede → Validasyonda → Valide Edildi / Başarısız), Sonuç, Sorumlu, Tarih ve Ekler girilir. Proje zorunlu, Deneme isteğe bağlıdır.

### Stabilite çalışması ve ölçümleri

Her koşul için ayrı bir **Stabilite Çalışması** açılır; her zaman noktasının sonucu ise ayrı bir **Stabilite Ölçümü**'dür.

1. Stabilite Çalışmaları → **+ Yeni kayıt**: Proje, **Batch (Deneme)**, Koşul (25°C/%60, 30°C/%65, 40°C/%75 RH), Başlangıç Tarihi, Zaman Noktaları (0-1-3-6-9-12-18-24. ay), Sorumlu.
2. **Sonraki Ölçüm Tarihi**'ni girin. Sorumluya 7 gün önce hatırlatma gider. Her ölçümden sonra bu tarihi bir sonraki noktaya güncelleyin.
3. Her zaman noktası için çalışma kaydının altındaki **Ölçümler** bölümünden bir ölçüm açın: Zaman Noktası, Planlanan Tarih, Gerçekleşen Tarih, Sonuç (**Uygun**, **OOT (Trend)**, **OOS (Spek Dışı)**), Bulgular, Ekler. Planlanan Tarih'ten 7 gün önce de hatırlatma gider.
4. OOT veya OOS çıkarsa çalışmada **Sapma** kutusunu işaretleyin ve Görevler ve Sapmalar'da bir **Sapma** kaydı açın; lider ve direktör bilgilendirilir.

**Takvim görünümleri:** Ölçüm Takvimi (çalışmalar) ve Planlanan Ölçümler (ölçümler) yaklaşan noktaları ay görünümünde gösterir.

## Stok, numune ve talepler

Stokta hiçbir miktar elle yazılmaz: lotun **Kalan Miktar**'ı ve malzemenin **Toplam Stok**'u, girilen hareketlerden hesaplanır. Stok değişiyorsa bir hareket kaydı olmalıdır. Uygulama: Numune ve Hammadde Stok.

### Tanımlar: tedarikçi ve malzeme kartı (Stok Sorumlusu)

- **Tedarikçiler:** Tedarikçi Adı, İletişim Kişisi, E-Posta, Telefon, Onaylı Tedarikçi.
- **Malzeme Kartları:** Malzeme Kodu ve Adı (zorunlu), Tip (Etken Madde, Eksipiyan, Referans Ürün, Standart Madde, Çözücü, Ambalaj), **Birim** (g, kg, mg, mL, L, Adet), Depolama Koşulu, **Kritik Stok Seviyesi**, **Stok Sorumlusu**, Tedarikçi.
- Kritik Stok Seviyesi ve Stok Sorumlusu'nu mutlaka doldurun; günlük kritik stok uyarısı bu iki alana dayanır.
- Mevcut stok ilk kurulumda Excel'den toplu aktarılır (önce Malzeme Kartları, sonra Lotlar).

### Lot girişi (Stok Sorumlusu)

1. **Lot Girişi** formunu veya Lotlar → + Yeni kayıt'ı kullanın.
2. **Malzeme**, **Lot No** (zorunlu), Tedarikçi, Tedarikçi Lot No, Giriş Tarihi, Üretim Tarihi.
3. **SKT / Retest Tarihi** ve Tarih Tipi (Son Kullanma / Retest).
4. **Giriş Miktarı** (malzemenin biriminde) ve **Birim Maliyet** (proje maliyeti bununla hesaplanır).
5. Raf / Lokasyon, **CoA** dosyası, Stok Sorumlusu.

Kaydettikten sonra sistem lotu **Karantinada** yapar ve Giriş Miktarı kadar bir giriş hareketi yazar. Lotu kullanıma açmak için Kalite, Lot Durumu'nu **Onaylı** yapar.

@img lot.png|Şekil 2 — Lot yaşam döngüsü: yalnızca Onaylı lottan çıkış yapılır

### Stok hareketleri

Hareketlerin çoğu otomatik oluşur. Elle girmeniz gerekenler aşağıdadır.

| Durum | Kim girer | Nasıl |
| --- | --- | --- |
| Lot girişi | Otomatik | Lot kaydedilince giriş hareketi yazılır |
| Denemede kullanım | Otomatik | Formül Bileşeni girilince çıkış yazılır (Laboratuvar bölümü) |
| Talep teslimi | Otomatik | Talep onaylanınca çıkış yazılır |
| Analiz / diğer kullanım | Uzman | **Stok Çıkışı** formu: Hareket Tipi = Çıkış, Lot, Çıkış Miktarı, İlgili Proje, İlgili Deneme, Yapan Kişi |
| İade | Stok Sorumlusu | Hareket Tipi = İade, **Giriş Miktarı** |
| İmha | Stok Sorumlusu | Hareket Tipi = İmha, **Çıkış Miktarı** |
| Sayım farkı | Stok Sorumlusu | Sayım Fazlası → Giriş Miktarı, Sayım Eksiği → Çıkış Miktarı |

**Kurallar**

- Bir harekette ya **Giriş Miktarı** ya **Çıkış Miktarı** doldurulur; ikisi birden doldurulmaz, negatif sayı yazılmaz.
- Çıkışlarda **İlgili Proje**'yi her zaman seçin. Bu tüketim ve maliyet projeye yazılır.
- **Karantinadaki, reddedilmiş veya kullanılamaz lottan çıkış yapılmaz.** Yapılırsa Yapan Kişi'ye "lot onaylı değil, çıkış geçersiz" uyarısı gider; Stok Sorumlusu hareketi düzeltir.
- Yanlış girilen bir hareketi silmek yerine ters hareketle düzeltin (ör. yanlış çıkışı bir İade ile). Böylece geçmiş korunur.

### Malzeme veya numune talebi

**Talep eden (Proje Lideri / Uzman):**

1. **Malzeme / Numune Talebi** formunu açın.
2. Talep Tipi (Malzeme / Numune), İlgili Proje, İlgili Deneme, Malzeme veya Numune, **İstenen Miktar**, İstenen Tarih, Gerekçe.
3. Kayıt **Taslak** olarak açılır.

**Stok Sorumlusu:**

1. Talebi açıp **Onaylayıcı (Stok Sorumlusu)** alanına kendinizi seçin.
2. Malzeme talebinde verilecek **Lot**'u seçin (Onaylı bir lot).
3. Durum = **Onay Bekliyor** yapın. Zilinize onay isteği düşer; 2 gün içinde yanıtlayın.
4. **Onayla:** Durum Onaylandı olur, lot seçiliyse İstenen Miktar kadar çıkış otomatik yazılır ve talep edene bildirim gider. Malzemeyi teslim edince Durum = **Teslim Edildi** ve Teslim Tarihi.
5. **Reddet:** Gerekçe yazmak zorunlu; Durum Reddedildi olur, talep edene bildirim gider.

### Numuneler

Gelen (tedarikçi, referans ürün) ve üretilen (deneme batch'i) numuneler **Numuneler** listesinde tutulur: Numune Adı, Tip, Miktar, Birim, Saklama Koşulu, Lokasyon, **Saklama Bitiş Tarihi**, Durum (Saklamada, Analizde, Karar Bekliyor, Tüketildi, İmha), Sorumlu. Deneme batch'inden alınan numunede **İlgili Deneme**'yi seçin; numune denemenin altında görünür.

Saklama Bitiş Tarihi geldiğinde numune otomatik **Karar Bekliyor** olur ve Sorumlu'ya 7 gün süreli bir **Depo Görevi** açılır. Görevde **Karar** seçilir (İmha, Saklama Süresi Uzatıldı, Analize Gönderildi). Uzatıldıysa Yeni Saklama Bitiş Tarihi'ni numune kaydına da yazın; imha edildiyse numune Durum = İmha.

### Kritik stok ve SKT takibi (Stok Sorumlusu)

- Her iş günü saat 08:00'de Toplam Stok'u Kritik Stok Seviyesi'nin altına düşen her malzeme için bildirim gelir. Liste: **Kritik Seviyedeki Malzemeler**.
- SKT / Retest tarihine 30 gün kala bildirim gelir ve lot **30 Gün İçinde SKT Dolan Lotlar** görünümüne düşer. Tarih geldiğinde lot otomatik **Kullanılamaz** olur.
- Retest sonrası kullanım süresi uzayan lotta yeni tarihi girin ve Lot Durumu'nu yeniden **Onaylı** yapın.
- Sayım: sistemdeki Kalan Miktar ile fiziksel sayımı karşılaştırın, farkı Sayım Fazlası / Eksiği hareketiyle girin. PoC hedefi: fark %2'nin altında.

## Toplantılar, kararlar ve aksiyonlar

Her Ar-Ge toplantısı bir kayıttır. Toplantıda alınan kararlar ve verilen aksiyonlar o kayda ve ilgili projeye bağlanır; aksiyonlar sahibine ve son tarihine kadar otomatik takip edilir. Uygulama: Toplantı Yönetimi.

### Tekrarlayan toplantılar

**Toplantı Serileri** listesinde iki seri hazırdır: **Haftalık Ar-Ge Toplantısı** (Pazartesi 10:00, 60 dk) ve **PoC Geri Bildirim Toplantısı** (Cuma 15:00, 45 dk).

- Her Pazartesi 07:00'de, Periyot'u **Haftalık** olan her seri için o haftanın toplantı kaydı otomatik açılır. Katılımcılar, organizatör, saat ve yer seriden kopyalanır.
- Organizatör, serinin **Katılımcılar** ve **Yer / Online Link** alanlarını güncel tutar.
- Otomatik açılan kayıtta Tarih o günün (Pazartesi) tarihidir; toplantı başka bir günse Tarih'i düzeltin.
- Seriyi durdurmak için Periyot'u değiştirin veya seriyi silin.

### Tek seferlik toplantı açmak (Organizatör)

Toplantılar → **+ Yeni kayıt**: Başlık (zorunlu), **Tip** (Haftalık Ar-Ge, Proje Toplantısı, Faz Kapısı Değerlendirme, Tedarikçi, Yönetim), Tarih, Saat, Süre, Yer / Online Link, Organizatör, **Katılımcılar**, **İlgili Projeler**. Durum = **Planlandı**.

Tip **Haftalık Ar-Ge** olan bir toplantı açıldığında açık, devam eden ve geciken tüm aksiyonlar son tarih sırasıyla **Gündem Maddeleri**'ne otomatik eklenir (Kaynak = "Açık Aksiyon (otomatik)"). Diğer gündem maddelerini toplantı kaydının Gündem bölümünden ekleyin: Sıra, Konu, Sunan Kişi, Ayrılan Süre, İlgili Proje.

### Toplantı sırasında ve sonrasında

1. **Toplantı Notu**'nu toplantı kaydına yazın. Kayıt veya transkript varsa **Kayıt / Transkript** alanına yükleyin.
2. Her karar için kayıttaki **Kararlar** bölümünden bir karar ekleyin: Karar Metni (zorunlu), Karar Tipi, Karar Veren, Tarih, **İlgili Proje**. Faz kapısı değerlendirme toplantısıysa **İlgili Faz Kapısı**'nı da seçin; karar o kapının onay gerekçesi olarak kapı kaydında görünür.
3. Her aksiyon için **Aksiyonlar** bölümünden ekleyin: Aksiyon (zorunlu), **Sorumlu**, **Son Tarih**, Öncelik, İlgili Proje; aksiyon bir karardan doğduysa **Karar**'ı seçin.
4. **AI Özeti** alanına kısa bir özet yazın (Workiom AI ile transkriptten özet çıkarma kurulduktan sonra bu alan oradan doldurulacak).
5. Toplantı bitince Durum = **Yapıldı**. Tüm katılımcılara özetle birlikte "toplantı tamamlandı" bildirimi gider.

**Toplantı Tutanağı** görünümü başlık, tarih, katılımcılar, projeler, not ve özeti düzenli bir sayfa olarak gösterir; yazdırılabilir veya paylaşılabilir.

### Aksiyon takibi (Aksiyon sorumlusu)

- Size aksiyon atandığında bildirim gelir. Son tarihe **2 gün** kala hatırlatma gelir.
- İşe başlayınca Durum = **Devam Ediyor**, bitince **Tamamlandı** + **Kapanış Notu**.
- Son tarih geçip aksiyon tamamlanmamışsa Durum otomatik **Gecikmede** olur ve bildirim gelir. Gecikmedeki aksiyon, bir sonraki haftalık toplantının gündemine yine gelir.
- Kendi aksiyonlarınız için **Açık Aksiyonlar** görünümünü Sorumlu = kendi adınız diye filtreleyin. "Bana Atanan Açık Aksiyonlar" görünümü pilot başlamadan eklenecek.

## Bildirimler ve otomatik işler

Sistem 23 işi sizin yerinize yapar: bildirim gönderir, onay ister, stok hareketi yazar, durum değiştirir. Bunları bilmek, aynı işi elle tekrar yapmamanızı sağlar.

| Ne olunca | Sistem ne yapar | Kime gider |
| --- | --- | --- |
| Faz kapısı Durum = Direktör Onayı Bekliyor | Onay isteği (5 gün) | 1. Onaylayan (Direktör) |
| Direktör onaylar | Durum = QA Onayı Bekliyor, yeni onay isteği | 2. Onaylayan (QA/Ruhsat) |
| QA onaylar | Kapı Onaylandı, bitiş tarihi yazılır, projenin fazı ilerler | Proje Ekibi, Proje Lideri |
| Kapı reddedilir | Kapı Reddedildi | Proje Lideri |
| Kapının Planlanan Bitiş'i geçer (onaylanmamış) | Gecikmede işareti | Proje Lideri |
| Sapma veya CAPA açılır | Bildirim | Proje Lideri, Ar-Ge Direktörü |
| Görev / sapma oluşturulur | Bildirim | Atanan |
| Görevin Son Tarih'i geçer | Durum = Gecikmede | Atanan |
| Stabilite Sonraki Ölçüm Tarihi'ne 7 gün kalır | Hatırlatma | Sorumlu |
| Stabilite ölçümünün Planlanan Tarih'ine 7 gün kalır | Hatırlatma | Sorumlu |
| Lot kaydedilir | Lot Karantinada olur, giriş hareketi yazılır | — |
| Formül bileşeni girilir | Lottan çıkış hareketi yazılır (proje + deneme bağlı) | — |
| Onaylı olmayan lottan çıkış girilir | Uyarı | Yapan Kişi |
| Talep Durum = Onay Bekliyor | Onay isteği (2 gün) | Onaylayıcı (Stok Sorumlusu) |
| Talep onaylanır / reddedilir | Onayda çıkış hareketi yazılır; her iki durumda bildirim | Talep Eden |
| Lotun SKT / Retest tarihine 30 gün kalır | SKT Yaklaşıyor işareti + bildirim | Lotun Stok Sorumlusu |
| SKT / Retest tarihi gelir | Lot Kullanılamaz olur + bildirim | Lotun Stok Sorumlusu |
| Her iş günü 08:00 | Kritik seviyedeki her malzeme için uyarı | Malzemenin Stok Sorumlusu |
| Numunenin Saklama Bitiş Tarihi gelir | Numune Karar Bekliyor, 7 gün süreli Depo Görevi | Numunenin Sorumlusu |
| Depo görevi oluşturulur | Bildirim | Atanan |
| Her Pazartesi 07:00 | Haftalık serilerden toplantı kayıtları açılır | — |
| Haftalık Ar-Ge toplantısı açılır | Açık aksiyonlar gündeme eklenir | — |
| Toplantı Durum = Yapıldı | Özet bildirimi | Katılımcılar |
| Aksiyon oluşturulur | Bildirim | Sorumlu |
| Aksiyonun Son Tarih'ine 2 gün kalır | Hatırlatma (tamamlanmadıysa) | Sorumlu |
| Aksiyonun Son Tarih'i geçer | Durum = Gecikmede + bildirim | Sorumlu |

**Önemli:** Bildirim bir kişi alanına gider. Proje Lideri, Ekip, Ar-Ge Direktörü, Sorumlu, Atanan, Stok Sorumlusu ve Onaylayıcı alanları boş kalırsa bildirim kimseye gitmez. Kayıt açarken bu alanları doldurun.

## Dashboard ve raporlar

Her uygulamanın ana sayfasında o uygulamanın rapor kartları bulunur. Kartlar canlıdır: kayıt girildikçe güncellenir, bir karta tıklayınca arkasındaki kayıtlar açılır.

| Uygulama | Kartlar | Kim için |
| --- | --- | --- |
| Ar-Ge Proje Takibi | Aktif Projeler, Faza Göre Proje Dağılımı, Riske Göre Projeler, Toplam Bütçe, Toplam Gerçekleşen Maliyet, Faza Göre Maliyet | Direktör |
| Ar-Ge Proje Takibi | Geciken Faz Kapıları, Geciken Görevler, Açık Sapma / CAPA, Yaklaşan Stabilite Ölçümleri | Direktör, Proje Lideri, Kalite |
| Numune ve Hammadde Stok | Bekleyen Talepler, Kritik Seviyedeki Malzemeler, 30 Gün İçinde SKT Dolan Lotlar, Karantinadaki Lotlar | Stok Sorumlusu, Direktör, Kalite |
| Numune ve Hammadde Stok | Lot Durum Dağılımı, Hareket Tipine Göre, Numune Durumları, Malzeme Bazında Toplam Stok | Stok Sorumlusu |
| Toplantı Yönetimi | Açık Aksiyonlar, Geciken Aksiyonlar, Kişi Bazında Aksiyonlar, Aksiyon Durumları, Tipe Göre Toplantılar | Direktör, Proje Lideri |

**Haftalık kontrol önerisi (Direktör, 10 dakika):** Faza Göre Proje Dağılımı → Geciken Faz Kapıları ve Görevler → Kritik Seviyedeki Malzemeler ve SKT'si yaklaşan lotlar → Kişi Bazında Aksiyonlar. Üç uygulamanın kartlarını tek ekranda toplayan Direktör dashboard'u pilot süresince eklenecek.

**Proje bazında bakış:** Tek bir projenin durumu için dashboard yerine proje kaydını açın: faz kapıları, denemeler, stok tüketimi, Gerçekleşen Maliyet ve Bütçe, toplantı kararları ve aksiyonlar orada bir aradadır.

## Sık sorulan sorular ve sorun giderme

Sorunların çoğu boş bırakılmış bir kişi veya bağlantı alanından kaynaklanır. Çözülemeyen durumları Cuma günkü PoC Geri Bildirim Toplantısı'nda bir aksiyon olarak açın.

| Sorun | Neden | Ne yapılır |
| --- | --- | --- |
| Bildirim gelmedi | İlgili kişi alanı (Proje Lideri, Sorumlu, Atanan, Onaylayıcı…) boş | Alanı doldurun. Tarih tetiklemeli hatırlatmalar (SKT, stabilite, gecikme) tarih geldiğinde çalışır, anında değil. |
| Faz kapısını onaya gönderdim, onay isteği kimseye düşmedi | 1. Onaylayan veya 2. Onaylayan boş | Kişiyi seçin, Durum'u Devam Ediyor yapıp tekrar Direktör Onayı Bekliyor yapın. |
| Kapı onaylandı ama projenin fazı ilerlemedi | Sonraki Faz boş veya Proje Kodu başka projeyle aynı | Sonraki Faz'ı doldurun; Proje Kodu benzersiz olmalı. Projeyi düzeltmek için Workiom ekibine yazın. |
| Lotun Kalan Miktar'ı yanlış | Bir hareket yanlış lota bağlanmış veya miktar yanlış | Lot kaydındaki **Hareketler** listesini kontrol edin; yanlış hareketi ters hareketle düzeltin. |
| Projenin Gerçekleşen Maliyeti 0 | Çıkış hareketinde İlgili Proje boş veya lotun Birim Maliyet'i boş | Hareketlerde İlgili Proje'yi, lotta Birim Maliyet'i doldurun. |
| Formül bileşeni girdim, stoktan düşmedi | Lot seçilmemiş | Bileşende Lot'u seçin. Otomasyon yalnızca kayıt ilk açıldığında çalışır; sonradan lot eklenirse çıkışı Stok Çıkışı formuyla girin. |
| "Lot onaylı değil" uyarısı aldım | Karantinada / Ret / Kullanılamaz lottan çıkış | Onaylı bir lot kullanın; yanlış hareketi Stok Sorumlusu düzeltir. |
| Talep onaylanınca stok düşmedi | Talepte Lot seçilmemiş veya Talep Tipi = Numune | Malzeme taleplerinde onaydan önce Lot'u seçin. Numune teslimi stoktan otomatik düşmez. |
| "Ad" alanı karışık görünüyor | Ad, kaydın alanlarından otomatik oluşur | Ad'ı değil, kaynak alanı (Proje Kodu, Lot No, Başlık…) düzeltin. |
| Aksiyon tamamlandı ama gündeme yine geldi | Durum Tamamlandı yapılmamış | Aksiyonu Tamamlandı yapın; gündemdeki madde silinebilir. |
| Otomatik açılan toplantının tarihi yanlış | Seri toplantılar Pazartesi tarihiyle açılır | Tarih'i toplantının gerçek gününe düzeltin. |
| Yanlış bir kaydı sildim | — | Workiom ekibine yazın; tüm kayıtların değişiklik geçmişi tutulur. |

**Destek:** Workiom ekibi — Yalçın Karpuzcu. Bir hata bildirirken kaydın adını (ör. "Kapı #3", "Hareket #12") ve ne beklediğinizi yazın.
