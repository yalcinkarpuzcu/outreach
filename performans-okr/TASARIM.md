# Performans Yönetimi (KPI Karnesi + OKR) · Workiom Tasarım Dokümanı

**Yeni app adı:** `Performans Yönetimi` · **Bağlandığı app:** müşterinin merkezi İK uygulaması (`İK`)
**Durum:** Taslak, onay bekliyor (K1 ve K6 onaylandı, 20.10.2026). Onay gelmeden build yapılmayacak.
**Kaynaklar:** `Performans Kartı Hesaplama – Örnek.xlsx` (müşterinin mevcut KPI karnesi), "Performans Kartı Hesaplama Metodolojisi" analiz dokümanı, "KPI + OKR Performans Sistemi – Workiom Tasarım Önerisi", müşteri görüşmesi (20.10.2026: kalan %10 = yetkinlik, OKR takibi isteniyor, çalışanlar merkezi İK app'inde).

---

## 0. Özet

Excel'deki KPI karnesi Workiom'a **birebir** taşınır ve yıllık performans puanının tek kaynağı olarak kalır: **Toplam Puan = KPI Skoru (%90) + Yetkinlik Skoru × %10**. Yanına **çeyreklik OKR** katmanı eklenir: Şirket → Departman → Kişi hizalaması, 0–1,0 ilerleme, 1–10 güven skoru, haftalık check-in.

Çalışan ve departman bilgisi **ayrı tutulmaz**; tüm kayıtlar merkezi İK uygulamasındaki `Çalışanlar` ve `Departmanlar` listelerine **uygulamalar arası bağlantı** ile bağlanır. Ünvan, departman, yönetici ve Workiom kullanıcısı oradan lookup ile gelir.

KPI ile OKR üç noktada bağlanır:
1. **Objective → İyileştirdiği KPI**: OKR'ın hangi KPI'ı iyileştirmek için açıldığı (Perdoo modeli).
2. **Key Result → Kaynak KPI**: KR'ın güncel değeri KPI'ın gerçekleşen değerinden otomatik akar.
3. **Kişisel Objective → Karne**: OKR kapanış puanları karnede **bilgi olarak** görünür, **puana girmez** (K1, onaylandı 20.10.2026).

Kapsam: 1 yeni app, 3 klasör, **10 liste**, İK app'ine **2 uygulamalar arası bağlantı hedefi**, **27 otomasyon**, 4 rol, 2 pano.

---

## 1. Platform kısıtları ve tasarımdaki karşılıkları

Farmatek ve İleri Acoustic kurulumlarında canlı testle doğrulanan kısıtlar. Tasarım bunlara göre kuruldu.

| Kısıt | Bu tasarımdaki çözüm |
|---|---|
| **Filtreli rollup yok** (ör. "sadece Operasyonel hedeflerin toplamı" alınamaz) | KPI hedefinde **gösterge formülleri** (`Op Katkısı = If(Tür Kodu = 1, Ağırlıklı Skor, 0)`), karnede bunların **SUM** rollup'ı. Excel'deki pivotun yerini tutar. |
| Rollup yalnızca sayısal alanlarda | Tüm toplanacak/ortalaması alınacak alanlar sayı veya formül. |
| Formül alanı yalnızca **aynı listedeki** alanları görür | Başka listeden gereken değerler önce **lookup** ile listeye alınır (oranlar, tür kodu, karne durumu). |
| Formül **metin döndüremez** | Performans grubu, OKR rengi gibi metin sonuçlar otomasyonla **seçim** alanına yazılır. |
| Formülde seçim alanı karşılaştırması güvenilir değil; **arama (find) filtresinde seçim / onay kutusu desteklenmiyor**, sayı eşitliği destekleniyor | Hedef türü ayrı bir referans listeye bağlanır ve **Tür Kodu (1/2/3)** lookup ile gelir. Yönelim, durum gibi seçimler için otomasyonla doldurulan gizli **sayı kodu** alanları (`Yön Kodu`, `Takipte`, `Kilitli`) tutulur. |
| `_id` ile doğrudan arama yok | Üst kayıt **ters bağlantı** üzerinden aranır (`Karneler.KPI Hedefleri = trigger:_id`). |
| Bir koşul dalında yalnızca **ilk** `find_records` çalışır | Her find kendi üst seviye koşuluna alınır (`flatten_finds`). |
| Lookup'tan gelen kullanıcı alanı yetki filtresinde kullanılamayabilir | Karne ve Objective'de `Çalışan (kullanıcı)`, `Yönetici (kullanıcı)`, `Onaylayıcı` **gerçek kullanıcı alanı** olarak tutulur, otomasyonla lookup'tan kopyalanır. |
| Formül motorunda `Ceiling`, `Max/Min` yok varsayılır | Sınırlama (0–1, 0–120) iç içe `If` ile yazılır. |
| API ile açılan kayıtta birincil alan dolu olmalı | Otomasyonla oluşturulan her kayıtta birincil alan (ad) doldurulur. |
| Pivot görünümü API'de hatalı | Pivot kullanılmaz; rollup + rapor widget'ları yeterli. |

---

## 2. Veri modeli

```
🏢 İK (mevcut merkezi app — dokunulacak tek yer: Çalışanlar'a 1 alan, K6 onaylandı)
   Çalışanlar ── Departman ⇢ Departmanlar
                 Yönetici (kullanıcı), Workiom Kullanıcısı (kullanıcı)
                 [+ Performans Form Türü ⇢ Performans Yönetimi.Form Türleri]   (önerilen)
   Departmanlar ── Departman Yöneticisi (kullanıcı)

📁 Performans Yönetimi
 ⚙️ Klasör 1 · Tanımlar (yalnızca İK düzenler)
   Dönemler ── Yıl ⇢ Dönemler (çeyreğin bağlı olduğu yıl, kendi içinde)
   Form Türleri
   Hedef Türleri
   Yetkinlikler ── Form Türleri ⇢⇢ Form Türleri (çoklu)

 📊 Klasör 2 · KPI Karnesi
   Performans Karneleri (PROCESS) ── Çalışan ⇢ İK.Çalışanlar
                                     Dönem ⇢ Dönemler (Yıl)
                                     Form Türü ⇢ Form Türleri
   KPI Hedefleri ── Karne ⇢ Performans Karneleri
                    Hedef Türü ⇢ Hedef Türleri
   Yetkinlik Değerlendirmeleri ── Karne ⇢ Performans Karneleri
                                  Yetkinlik ⇢ Yetkinlikler

 🎯 Klasör 3 · OKR
   Objective'ler (PROCESS) ── Dönem ⇢ Dönemler (Çeyrek)
                              Departman ⇢ İK.Departmanlar
                              Katkı Veren Departmanlar ⇢⇢ İK.Departmanlar (çoklu)
                              Sahip Çalışan ⇢ İK.Çalışanlar
                              Üst Objective ⇢ Objective'ler (kendi içinde, hizalama)
                              İyileştirdiği KPI ⇢ KPI Hedefleri          ← KPI↔OKR köprüsü 1
                              Karne ⇢ Performans Karneleri (bilgi)       ← KPI↔OKR köprüsü 3
   Key Result'lar ── Objective ⇢ Objective'ler
                     Kaynak KPI ⇢ KPI Hedefleri                          ← KPI↔OKR köprüsü 2
   Check-in'ler ── Key Result ⇢ Key Result'lar

⇢ tekli bağlantı · ⇢⇢ çoklu bağlantı · her bağlantının karşı listede ters bağlantısı (back-link) açılır
```

**İlişki özeti**

| Bağlantı | Tür | Ters bağlantı (karşı listede) | Not |
|---|---|---|---|
| Karne → İK.Çalışanlar | N:1, **uygulamalar arası** | Çalışanlar.Performans Karneleri | Çalışan başına yılda 1 karne |
| Karne → Dönemler | N:1 | Dönemler.Karneler | Yalnızca Tür = Yıl |
| Karne → Form Türleri | N:1 | Form Türleri.Karneler | Karne açılınca sabitlenir, yıl içinde terfi karneyi değiştirmez |
| KPI Hedefi → Karne | N:1 | **Karneler.KPI Hedefleri** (rollup kaynağı) | Hedef karnenin içinden eklenir |
| KPI Hedefi → Hedef Türleri | N:1 | – | Tür Kodu lookup'ı için |
| Yetkinlik Değ. → Karne | N:1 | **Karneler.Yetkinlik Değerlendirmeleri** (rollup kaynağı) | |
| Yetkinlik Değ. → Yetkinlikler | N:1 | – | |
| Yetkinlikler → Form Türleri | **N:N (çoklu)** | Form Türleri.Yetkinlikler | Hangi yetkinlik hangi kademede değerlendirilir |
| Dönemler (Çeyrek) → Dönemler (Yıl) | N:1, kendi içinde | Dönemler.Çeyrekler | |
| Objective → Dönemler | N:1 | Dönemler.Objective'ler | Yalnızca Tür = Çeyrek |
| Objective → İK.Departmanlar | N:1, **uygulamalar arası** | – | Departman/Kişi seviyesinde |
| Objective → İK.Departmanlar (Katkı Veren) | **N:N (çoklu)**, uygulamalar arası | – | Ortak OKR'larda |
| Objective → İK.Çalışanlar (Sahip Çalışan) | N:1, uygulamalar arası | – | Kişi seviyesinde |
| Objective → Objective (Üst) | N:1, kendi içinde | Objective'ler.Alt Objective'ler | Hizalama ağacı |
| Objective → KPI Hedefleri | N:1 (opsiyonel) | **KPI Hedefleri.İyileştiren OKR'lar** | Köprü 1 |
| Objective → Karne | N:1 (opsiyonel, otomatik) | **Karneler.OKR'lar** (rollup kaynağı) | Köprü 3 |
| Key Result → Objective | N:1 | **Objective'ler.Key Result'lar** (rollup kaynağı) | |
| Key Result → KPI Hedefleri (Kaynak) | N:1 (opsiyonel) | **KPI Hedefleri.Beslediği KR'lar** | Köprü 2 |
| Check-in → Key Result | N:1 | **Key Result'lar.Check-in'ler** | |

---

## 3. İK app'ine bağımlılık (müşteri ile teyit)

| İK.Çalışanlar alanı | Tip | Bu app'te kullanımı | Durum |
|---|---|---|---|
| Ad Soyad (birincil) | metin | Bağlantı etiketi | Var sayıldı |
| Workiom Kullanıcısı | kullanıcı | Kendi karnesini görme, check-in, bildirim | **Zorunlu** — yoksa eklenmeli |
| Yönetici | kullanıcı | Karne onayı, ekip görünürlüğü | **Zorunlu** — kullanıcı tipinde olmalı |
| Departman | bağlantı → İK.Departmanlar | Lookup, rapor kırılımı | Var sayıldı |
| Ünvan | metin / bağlantı | Lookup | Var sayıldı |
| Aktif / Çalışma Durumu | onay kutusu / seçim | Toplu karne açmada filtre (find'da seçim desteklenmediği için sayı göstergesi gerekebilir) | Teyit |
| **Performans Form Türü** | bağlantı → Performans Yönetimi.Form Türleri | Karne açılınca otomatik dolar | **Eklenecek (K6 onaylandı)** |

| İK.Departmanlar alanı | Tip | Kullanımı |
|---|---|---|
| Departman Adı | metin | Bağlantı etiketi |
| Departman Yöneticisi | kullanıcı | Departman OKR onayı, düşük güven bildirimi |

**Yetki şartı:** Performans rollerinin İK.Çalışanlar ve İK.Departmanlar listelerinde **okuma** yetkisi olmalı (bağlantı seçimi ve lookup için). Maaş, TC kimlik, adres gibi hassas alanlar bu rollere **alan bazında Denied** yapılır (bölüm 6).

---

## 4. Listeler ve alanlar

Gösterim: **kalın** = zorunlu (formda) · *(gizli)* = kullanıcı formunda görünmez, otomasyon/formül yardımcısı · `{Alan}` = formül referansı.

### Klasör 1 · Tanımlar

#### 4.1 Dönemler (DATA)
| Alan | Tip | Not |
|---|---|---|
| **Dönem Adı** | metin (birincil) | "2026", "2026-Ç1" |
| **Tür** | seçim: Yıl / Çeyrek | |
| Tür Kodu *(gizli)* | sayı | 1 = Yıl, 2 = Çeyrek (DNM-00) — find filtresi için |
| Yıl | bağlantı → Dönemler | Yalnızca Çeyrek'te dolu |
| **Başlangıç** · **Bitiş** | tarih | Takvim görünümü |
| Hedef Giriş Son Tarihi | tarih | Yıl: karne onayı için son gün; Çeyrek: OKR yazımı için son gün |
| **Durum** | seçim: Planlama / Aktif / Kapanış / Kapalı | Durum değişimi DNM-01/02/03'ü tetikler |
| Çeyrekler · Karneler · Objective'ler | ters bağlantı | |

**Seed:** 2026 (Yıl), 2026-Ç1…Ç4; 2027 ve çeyrekleri.

#### 4.2 Form Türleri (DATA) — Excel'deki VERİ sayfası
| Alan | Tip | Not |
|---|---|---|
| **Form Türü** | metin (birincil) | |
| Operasyonel Oranı · Proje Oranı · Kurumsal Oranı · Yetkinlik Oranı | sayı (%) | |
| Toplam Oran | formül | `{Op} + {Proje} + {Kurumsal} + {Yetkinlik}` → 100 olmalı |
| Yetkinlikler · Karneler | ters bağlantı | |

**Seed:**

| Form Türü | Op. | Proje | Kurumsal | Yetkinlik |
|---|---|---|---|---|
| Yönetici ve Uzman | 50 | 30 | 10 | 10 |
| Müdür | 45 | 25 | 20 | 10 |
| GM, Başkan, Direktör | 35 | 25 | 30 | 10 |

#### 4.3 Hedef Türleri (DATA)
Hedef Türü (birincil) · **Kod** (sayı) · Açıklama
**Seed:** Operasyonel Hedef = 1 · Proje Hedefi = 2 · Kurumsal Hedef = 3

#### 4.4 Yetkinlikler (DATA)
| Alan | Tip | Not |
|---|---|---|
| **Yetkinlik** | metin (birincil) | |
| Tanım / Davranış Göstergeleri | çok satırlı metin | Değerlendiren için rehber |
| **Form Türleri** | **çoklu bağlantı** → Form Türleri | Hangi kademelerde değerlendirileceği |
| Aktif | sayı (1/0) | Find filtresi onay kutusunu desteklemediği için sayı |
| Sıra | sayı | |

**Seed:** müşterinin yetkinlik listesi (K4) + önerilen **"OKR Davranışı"** (iddialı hedef alma, düzenli check-in, sorunları erken bildirme), tüm form türlerinde.

### Klasör 2 · KPI Karnesi

#### 4.5 Performans Karneleri (PROCESS) — Excel'deki PVT + FİNAL TABLOSU
**Durumlar:** Hedef Belirleme → Yönetici Onayında → Aktif → Değerlendirme → Kalibrasyon → Tamamlandı ✓ · İptal ✓

| Alan | Tip | Hesaplama / not |
|---|---|---|
| Karne No | otomatik numara | |
| Karne | metin (birincil) | "2026 – Ad Soyad" (KRN-01) |
| **Çalışan** | bağlantı → **İK.Çalışanlar** | |
| **Dönem** | bağlantı → Dönemler | Filtre: Tür = Yıl |
| **Form Türü** | bağlantı → Form Türleri | KRN-01 İK'dan kopyalar; boşsa İK seçer |
| Ünvan · Departman | lookup (Çalışan) | |
| Çalışan Kullanıcısı (lookup) · Yönetici (lookup) | lookup (Çalışan) | |
| Çalışan (kullanıcı) *(gizli)* | kullanıcı | KRN-01 kopyalar → yetki filtresi, bildirim |
| Yönetici (kullanıcı) *(gizli)* | kullanıcı | KRN-01 kopyalar → yetki filtresi, onaylayıcı |
| Op. Oranı · Proje Oranı · Kurumsal Oranı · Yetkinlik Oranı | lookup (Form Türü) | |
| KPI Hedefleri | ters bağlantı (çoklu) | Karne formunda alt tablo |
| Hedef Sayısı | sayım | |
| Operasyonel Skor | rollup SUM ← KPI Hedefleri.Op Katkısı | Excel pivotu |
| Proje Skoru | rollup SUM ← KPI Hedefleri.Proje Katkısı | |
| Kurumsal Skor | rollup SUM ← KPI Hedefleri.Kurumsal Katkısı | |
| Op. Ağırlık Toplamı · Proje Ağ. Toplamı · Kurumsal Ağ. Toplamı | rollup SUM ← KPI Hedefleri.(tür) Ağırlık Göstergesi | |
| Ağırlık Hatası | formül | `If({Op Ağ} = 100, 0, 1) + If({Proje Ağ} = 100, 0, 1) + If({Kurumsal Ağ} = 100, 0, 1)` → 0 olmalı |
| **KPI Skoru** | formül | `{Op Skor} * {Op Oranı} / 100 + {Proje Skoru} * {Proje Oranı} / 100 + {Kurumsal Skor} * {Kurumsal Oranı} / 100` |
| Yetkinlik Değerlendirmeleri | ters bağlantı (çoklu) | |
| Yetkinlik Skoru | rollup AVG ← Yetkinlik Değ.Puan (0–100) | |
| **Toplam Puan** | formül | `{KPI Skoru} + {Yetkinlik Skoru} * {Yetkinlik Oranı} / 100` |
| Performans Grubu | seçim (KRN-05) | Beklentinin Çok Altında / Beklenenin Altında / Beklenen Performans / Beklentinin Üstünde / Beklentinin Çok Üstünde |
| Kalibre Grup | seçim (aynı 5 değer) | Yalnızca İK |
| Kalibrasyon Notu | çok satırlı metin | Yalnızca İK |
| Final Performans Grubu | seçim (KRN-06) | |
| Onay Tarihi · Red Notu | tarih · metin | KRN-02 |
| OKR'lar | ters bağlantı ← Objective'ler.Karne | |
| OKR Sayısı · OKR Ortalaması | sayım · rollup AVG ← Objective'ler.Kapanış Puanı | **Bilgi, puana girmez** (K1) |

#### 4.6 KPI Hedefleri (DATA) — Excel'deki BİREYSEL HEDEF LİSTESİ
| Alan | Tip | Hesaplama / not |
|---|---|---|
| Hedef No | otomatik numara | |
| **Hedef** | metin (birincil) | |
| Açıklama / Ölçüm Yöntemi | çok satırlı metin | |
| **Karne** | bağlantı → Performans Karneleri | |
| Çalışan · Dönem · Karne Durumu | lookup (Karne) | |
| **Hedef Türü** | bağlantı → Hedef Türleri | |
| Tür Kodu *(gizli)* | lookup (Hedef Türü.Kod) | |
| **Hedef Yönelimi** | seçim: Artan / Azalan | |
| Yön Kodu *(gizli)* | sayı | KPI-01: 1 = Artan, 2 = Azalan |
| Birim | seçim (17) | %, Puan, Skor, Adet, Yıl, Ay, Hafta, Gün, Tutar, Ton, Dakika, KWH/M², PPM, TL/KG, TL/M², M², Metre |
| **Hedef Ağırlığı (%)** | sayı | Tür içinde toplam 100 |
| **Hedeflenen** · Gerçekleşen | sayı | |
| Gerçekleşme Oranı | formül | `If({Yön Kodu} = 1, If({Hedeflenen} = 0, 0, {Gerçekleşen} / {Hedeflenen}), If({Gerçekleşen} = 0, 0, {Hedeflenen} / {Gerçekleşen}))` — sıfır durumu Excel'deki gibi 0; teyit sorusu 3'e göre güncellenir |
| Hedef Puanı | formül | `If({Oran} < 0.8, 0, If({Oran} <= 1, 60 + ({Oran} - 0.8) * 200, If({Oran} < 1.2, 100 + ({Oran} - 1) * 100, 120)))` |
| Ağırlıklı Skor | formül | `{Hedef Puanı} * {Hedef Ağırlığı} / 100` |
| Op Katkısı · Proje Katkısı · Kurumsal Katkısı *(gizli)* | formül | `If({Tür Kodu} = 1, {Ağırlıklı Skor}, 0)` (2, 3 için aynı) |
| Op · Proje · Kurumsal Ağırlık Göstergesi *(gizli)* | formül | `If({Tür Kodu} = 1, {Hedef Ağırlığı}, 0)` (2, 3 için aynı) |
| Kilitli *(gizli)* | sayı (0/1) | KRN-03: karne Aktif olunca 1 → hedef tanımı salt okunur |
| Son Güncelleme | tarih | KPI-02 |
| İyileştiren OKR'lar · Beslediği KR'lar | ters bağlantı | Köprü 1 ve 2 |
| İyileştiren OKR Sayısı | sayım | |

> Formül alanının başka bir formül alanını referans alması build'de test edilecek. Desteklenmezse `Hedef Puanı` içindeki `{Oran}` yerine Gerçekleşme Oranı ifadesi açık yazılır.

#### 4.7 Yetkinlik Değerlendirmeleri (DATA)
| Alan | Tip | Not |
|---|---|---|
| Değerlendirme | metin (birincil) | "{Yetkinlik} – {Karne}" (KRN-04) |
| **Karne** | bağlantı → Performans Karneleri | |
| **Yetkinlik** | bağlantı → Yetkinlikler | |
| Tanım | lookup (Yetkinlik) | Değerlendirene rehber |
| **Puan (1–5)** | sayı | Ölçek K4 ile netleşir |
| Puan (0–100) | formül | `({Puan} - 1) * 25` |
| Değerlendiren | kullanıcı | KRN-04: karnedeki Yönetici |
| Açıklama | çok satırlı metin | |

### Klasör 3 · OKR

#### 4.8 Objective'ler (PROCESS)
**Durumlar:** Taslak → Onayda → Aktif → Kapanış → Kapandı ✓ · İptal ✓

| Alan | Tip | Not |
|---|---|---|
| OKR No | otomatik numara | |
| **Objective** | metin (birincil) | Niteliksel, ilham veren cümle |
| Açıklama / Neden | çok satırlı metin | |
| **Dönem** | bağlantı → Dönemler | Filtre: Tür = Çeyrek |
| Yıl | lookup (Dönem.Yıl) | OKR-01'de karne eşleştirme |
| **Seviye** | seçim: Şirket / Departman / Kişi | |
| Seviye Kodu *(gizli)* | sayı | OKR-01: 1 / 2 / 3 |
| Departman | bağlantı → **İK.Departmanlar** | Departman ve Kişi seviyesinde zorunlu (validasyon) |
| Katkı Veren Departmanlar | **çoklu bağlantı** → **İK.Departmanlar** | Ortak OKR'lar |
| **Sahip** | kullanıcı | |
| Sahip Çalışan | bağlantı → **İK.Çalışanlar** | Kişi seviyesinde zorunlu |
| Katkı Verenler | **çoklu kullanıcı** | Check-in girebilir, bildirim alır |
| Onaylayıcı *(gizli)* | kullanıcı | OKR-01: Departman Yöneticisi (lookup'tan); Şirket seviyesinde Üst Yönetim rolü |
| Üst Objective | bağlantı → Objective'ler | Hizalama; Şirket seviyesinde boş |
| Alt Objective'ler | ters bağlantı | |
| Hizalanan OKR Sayısı | sayım | |
| **OKR Türü** | seçim: Zorunlu (Committed) / İddialı (Aspirational) | |
| Başarı Eşiği | sayı | OKR-01: Zorunlu 1,0 · İddialı 0,7 |
| İyileştirdiği KPI | bağlantı → KPI Hedefleri | **Köprü 1** (opsiyonel) |
| Karne | bağlantı → Performans Karneleri | **Köprü 3** — OKR-01 kişisel OKR'da otomatik |
| Key Result'lar | ters bağlantı (çoklu) | Form alt tablosu |
| KR Sayısı | sayım | Validasyon: Onaya göndermek için 2–5 |
| **İlerleme** | rollup AVG ← Key Result'lar.İlerleme | 0–1,0 |
| Ortalama Güven | rollup AVG ← Key Result'lar.Güven | 1–10 |
| Renk | seçim: Yeşil / Sarı / Kırmızı (OKR-04) | 0,7+ / 0,4–0,69 / 0,4 altı |
| Kapanış Puanı | sayı (0–1) | OKR-05 önerir (= İlerleme), sahip düzeltebilir |
| Retro Notu | çok satırlı metin | Ne öğrendik, sonraki çeyreğe ne taşınıyor |
| Kapanış Tarihi | tarih | |
| Red Notu | metin | OKR-02 |

#### 4.9 Key Result'lar (DATA)
| Alan | Tip | Not |
|---|---|---|
| KR No | otomatik numara | |
| **Key Result** | metin (birincil) | Ölçülebilir sonuç |
| **Objective** | bağlantı → Objective'ler | |
| Dönem · Objective Sahibi · Objective Durumu | lookup (Objective) | |
| **Sahip** | kullanıcı | Varsayılan: Objective sahibi (KR-01) |
| **KR Tipi** | seçim: Metrik / Kilometre Taşı | Kilometre taşında Başlangıç 0, Hedef 1 (KR-01) |
| **Başlangıç Değeri** · **Hedef Değer** · Güncel Değer | sayı | Güncel değer check-in'den gelir |
| Birim | seçim (17) | |
| İlerleme | formül | `If({Hedef} = {Başlangıç}, If({Güncel} = {Hedef}, 1, 0), If(({Güncel} - {Başlangıç}) / ({Hedef} - {Başlangıç}) < 0, 0, If(({Güncel} - {Başlangıç}) / ({Hedef} - {Başlangıç}) > 1, 1, ({Güncel} - {Başlangıç}) / ({Hedef} - {Başlangıç}))))` — azalan hedefte (hedef < başlangıç) de doğru çalışır |
| Güven (1–10) | sayı | Son check-in'den |
| Kaynak KPI | bağlantı → KPI Hedefleri | **Köprü 2** (opsiyonel) |
| Kaynak KPI Gerçekleşen | lookup (Kaynak KPI.Gerçekleşen) | Kontrol için |
| Son Check-in Tarihi | tarih | |
| Check-in Gecikti *(gizli)* | formül | `If(SubtractDate(Today(), {Son Check-in Tarihi}) > 7, 1, 0)` — KR-03 filtresi |
| Takipte *(gizli)* | sayı (0/1) | OKR-03/OKR-05: Objective Aktif iken 1 |
| Check-in'ler | ters bağlantı | |
| Check-in Sayısı | sayım | |

#### 4.10 Check-in'ler (DATA)
| Alan | Tip | Not |
|---|---|---|
| Check-in | metin (birincil) | "{KR No} – {Tarih}" (CHK-01) |
| **Key Result** | bağlantı → Key Result'lar | |
| Objective · KR Sahibi | lookup (Key Result) | |
| **Tarih** | tarih | Varsayılan bugün |
| **Yeni Değer** | sayı | |
| **Güven (1–10)** | sayı | Validasyon 1–10 |
| Bu Hafta Yapılan | çok satırlı metin | |
| Engel / İhtiyaç | çok satırlı metin | Doluysa KR-02 bildirimi |
| Giren | kullanıcı | CHK-01: kaydı oluşturan |

---

## 5. Otomasyonlar

Kodlar: DNM = Dönemler · KRN = Karneler · KPI = KPI Hedefleri · YTK = Yetkinlik · OKR = Objective'ler · KR = Key Result'lar · CHK = Check-in'ler. Tüm otomasyonlar `Performans Yönetimi` app'inde kurulur; İK listelerine yalnızca **find** ve **lookup** ile erişilir, İK'da kayıt değiştirilmez.

| # | Tetikleyici | Koşul | Aksiyon |
|---|---|---|---|
| **DNM-00** | Dönemler: oluşturuldu / Tür değişti | – | Tür Kodu = 1 (Yıl) / 2 (Çeyrek) |
| **DNM-01** | Dönemler: Durum → Aktif | Tür Kodu = 1 | *(opsiyonel, K7)* **Toplu karne açma:** find İK.Çalışanlar (Aktif) → her biri için Performans Karneleri'nde kayıt oluştur (Çalışan, Dönem = trigger, durum Hedef Belirleme). KRN-01 her kayıt için çalışır. |
| **DNM-02** | Dönemler: Durum → Kapanış | Tür Kodu = 2 | find Objective'ler (`Dönemler.Objective'ler = trigger:_id`) → döngüde Durum = Aktif olanları **Kapanış**'a al (OKR-05 tetiklenir) |
| **DNM-03** | Dönemler: Durum → Kapanış | Tür Kodu = 1 | find Performans Karneleri (Dönem = trigger) → Durum Aktif olanları **Değerlendirme**'ye al (KRN-04 tetiklenir) |
| **DNM-04** | Dönemler: zaman tetikleyici, Bitiş − 7 gün | Tür Kodu = 2 | find Objective'ler (bu dönem) → Sahip'lere "Çeyrek bitiyor: KR'larını güncelle, kapanışa hazırlan" bildirimi |
| **KRN-01** | Karne: oluşturuldu | – | Çalışan (kullanıcı) = lookup Çalışan Kullanıcısı · Yönetici (kullanıcı) = lookup Yönetici · Form Türü boşsa = İK.Çalışanlar.Performans Form Türü · Karne = "{Dönem} – {Çalışan}" · Çalışana "Karnen açıldı, hedeflerini gir" bildirimi |
| **KRN-02** | Karne: Durum → Yönetici Onayında | Ağırlık Hatası > 0 **veya** Hedef Sayısı = 0 | **Evet:** Durum → Hedef Belirleme, çalışana "Her hedef türünde ağırlık toplamı %100 olmalı" bildirimi. **Hayır:** **Onay aksiyonu** (onaylayıcı = Yönetici (kullanıcı), 5 gün, red gerekçesi zorunlu). Onay → Durum Aktif, Onay Tarihi = bugün, çalışana bildirim. Red → Durum Hedef Belirleme, Red Notu, çalışana bildirim. |
| **KRN-03** | Karne: Durum → Aktif | – | find KPI Hedefleri (`Karneler.KPI Hedefleri = trigger:_id`) → Kilitli = 1 |
| **KRN-04** | Karne: Durum → Değerlendirme | – | find Yetkinlikler (Aktif = 1, Form Türleri içerir trigger.Form Türü) → her biri için Yetkinlik Değerlendirmeleri kaydı (Karne, Yetkinlik, Değerlendiren = Yönetici). Çalışana "Yıl sonu gerçekleşenlerini gir", yöneticiye "Yetkinlik değerlendirmesi bekliyor" bildirimi. |
| **KRN-05** | Karne: güncellendi (izlenen alan: Toplam Puan) | Toplam Puan eşikleri | < 60 Beklentinin Çok Altında · < 90 Beklenenin Altında · < 101 Beklenen Performans · < 111 Beklentinin Üstünde · diğer Beklentinin Çok Üstünde → Performans Grubu (eşikler teyit sorusu 7) |
| **KRN-06** | Karne: Durum → Tamamlandı | Kalibre Grup dolu mu | Evet: Final = Kalibre Grup · Hayır: Final = Performans Grubu. Çalışana ve yöneticiye "Karnen tamamlandı" bildirimi. |
| **KRN-07** | Karne: zaman tetikleyici, Dönem.Hedef Giriş Son Tarihi − 3 gün | Durum = Hedef Belirleme | Çalışana ve yöneticiye hatırlatma |
| **KPI-01** | KPI Hedefi: oluşturuldu / Hedef Yönelimi değişti | Yönelim = Artan | Yön Kodu = 1, değilse 2 |
| **KPI-02** | KPI Hedefi: güncellendi (izlenen alan: Gerçekleşen) | – | Son Güncelleme = bugün · find Key Result'lar (`KPI Hedefleri.Beslediği KR'lar = trigger:_id`) → Güncel Değer = trigger.Gerçekleşen, Son Check-in Tarihi = bugün (**Köprü 2**) |
| **KPI-03** | KPI Hedefi: oluşturuldu | Karne Durumu ≠ Hedef Belirleme | Kilitli = 1 ve İK'ya "Onaylı karneye yeni hedef eklendi" bildirimi (yetki ile de engellenir, bu güvenlik ağı) |
| **YTK-01** | Yetkinlik Değ.: güncellendi (Puan) | Puan < 1 veya > 5 | Puan temizlenir, değerlendirene uyarı (form validasyonu da tanımlanır) |
| **OKR-01** | Objective: oluşturuldu | – | Seviye Kodu = 1/2/3 · Başarı Eşiği = 1,0 (Zorunlu) / 0,7 (İddialı) · Onaylayıcı = Departman.Departman Yöneticisi (Şirket seviyesinde Üst Yönetim rolündeki kullanıcı) · **Seviye Kodu = 3 ise** find Performans Karneleri (Çalışan = Sahip Çalışan ve Dönem = Yıl) → Karne bağlantısı (**Köprü 3**) |
| **OKR-02** | Objective: Durum → Onayda | KR Sayısı < 2 | **Evet:** Durum → Taslak, sahibe "En az 2 KR ekle" bildirimi. **Hayır:** **Onay aksiyonu** (onaylayıcı = Onaylayıcı, 3 gün, red gerekçesi zorunlu). Onay → Durum Aktif. Red → Taslak, Red Notu, sahibe bildirim. |
| **OKR-03** | Objective: Durum → Aktif | – | find Key Result'lar (`Objective'ler.Key Result'lar = trigger:_id`) → Takipte = 1. Katkı Verenler'e "OKR aktif" bildirimi. |
| **OKR-04** | Objective: güncellendi (izlenen alan: İlerleme) | İlerleme eşikleri | ≥ 0,7 Yeşil · ≥ 0,4 Sarı · diğer Kırmızı → Renk |
| **OKR-05** | Objective: Durum → Kapanış | – | Kapanış Puanı boşsa = İlerleme · find Key Result'lar → Takipte = 0 · Sahibe "Kapanış puanını teyit et, retro notunu yaz" bildirimi |
| **OKR-06** | Objective: Durum → Kapandı | Kapanış Puanı boş | Durum → Kapanış'a geri, sahibe uyarı. Değilse Kapanış Tarihi = bugün. |
| **KR-01** | Key Result: oluşturuldu | KR Tipi = Kilometre Taşı | Başlangıç = 0, Hedef = 1, Güncel = 0 · Sahip boşsa = Objective Sahibi · Objective Aktif ise Takipte = 1 |
| **KR-02** | Key Result: güncellendi (izlenen alan: Güven) | Güven ≤ 4 | Objective Sahibi ve Departman Yöneticisine "KR riskte" bildirimi |
| **KR-03** | Zamanlanmış: her pazartesi 09:00 | – | find Key Result'lar (Takipte = 1 **ve** Check-in Gecikti = 1) → Sahip'e "Bu haftanın check-in'i bekleniyor" bildirimi |
| **CHK-01** | Check-in: oluşturuldu | – | Check-in = "{KR No} – {Tarih}" · Giren = oluşturan kullanıcı · find Key Result (`Key Result'lar.Check-in'ler = trigger:_id`) → Güncel Değer = Yeni Değer, Güven = trigger.Güven, Son Check-in Tarihi = Tarih |
| **CHK-02** | Check-in: oluşturuldu | Engel / İhtiyaç dolu | Objective Sahibi ve Departman Yöneticisine "Engel bildirildi" bildirimi |

**Zincirler:** DNM-03 → KRN-04 · DNM-02 → OKR-05 · CHK-01 → (İlerleme rollup) → OKR-04 · KPI-02 → (İlerleme rollup) → OKR-04 · KRN-04 + yetkinlik puanları → Toplam Puan → KRN-05.

---

## 6. Roller ve yetkiler

Roller: **İK / Performans Yöneticisi** (admin) · **Üst Yönetim** · **Yönetici** (ekibi olan herkes) · **Çalışan**.
Teknik karşılık: rol başına liste izinleri (erişim, ekleme, silme, toplu güncelleme, export, görünüm oluşturma), **kayıt filtresi**, **alan izinleri** (Editor / ReadOnly / Denied) ve **koşullu yetki grupları** (ör. "Sahip = mevcut kullanıcı ise şu alanlar düzenlenebilir").

### 6.1 Liste bazında matris

| Liste | İK | Üst Yönetim | Yönetici | Çalışan |
|---|---|---|---|---|
| Tanımlar (Dönemler, Form Türleri, Hedef Türleri, Yetkinlikler) | Tam | Okur | Okur | Okur (Yetkinlikler) / Görmez (diğerleri) |
| Performans Karneleri | Tam | Okur (tümü) | **Kayıt filtresi:** Yönetici (kullanıcı) = ben **veya** Çalışan (kullanıcı) = ben | **Kayıt filtresi:** Çalışan (kullanıcı) = ben · ekleme/silme ✗ |
| KPI Hedefleri | Tam | Okur | Ekibinin hedefleri (Karne üzerinden filtre) · ekler/düzenler | Kendi hedefleri · **Kilitli = 0 iken** ekler/düzenler, **Kilitli = 1 iken** yalnızca Gerçekleşen (K3) · silme ✗ |
| Yetkinlik Değerlendirmeleri | Tam | Okur | Değerlendiren = ben → Puan, Açıklama düzenler | **Görmez** (karne Tamamlandı olunca okur — K8) |
| Objective'ler | Tam | Tümü okur, **Şirket** seviyesini oluşturur | Tümü okur, **Departman** seviyesini oluşturur | Tümü okur, **Kişi** seviyesini oluşturur |
| Key Result'lar | Tam | Tümü okur | Tümü okur | Tümü okur |
| Check-in'ler | Tam | Okur | Okur, oluşturur | Okur, oluşturur |
| İK.Çalışanlar / İK.Departmanlar (diğer app) | – | Okur | Okur | Okur |
| Export | ✓ | ✓ | ✓ (kendi kapsamı) | ✗ |
| Görünüm oluşturma | ✓ | ✗ | ✗ | ✗ |

### 6.2 Alan bazında kurallar

| Liste | Alan(lar) | Kural |
|---|---|---|
| Karneler | Kalibre Grup, Kalibrasyon Notu, Final Performans Grubu | Yalnızca İK: Editor · Diğer roller: Durum = Tamamlandı ise ReadOnly, değilse **Denied** |
| Karneler | Performans Grubu, Toplam Puan, Yetkinlik Skoru | Çalışan: Durum Tamamlandı olana kadar Denied (K8) |
| Karneler | Çalışan, Dönem, Form Türü | Yalnızca İK düzenler |
| KPI Hedefleri | Hedef, Hedef Türü, Yönelim, Ağırlık, Hedeflenen | Koşullu grup: **Kilitli = 0** → Çalışan + Yönetici Editor; **Kilitli = 1** → ReadOnly (İK hariç) |
| KPI Hedefleri | Gerçekleşen | Kilitli = 1 iken Çalışan (veya Yönetici, K3) Editor |
| Objective'ler | Tüm içerik alanları | Koşullu grup: **Sahip = ben** → Editor; diğerleri ReadOnly. Durum Aktif sonrası Dönem, Seviye, Üst Objective yalnızca İK |
| Key Result'lar | Başlangıç, Hedef, KR Tipi | Objective Durumu Aktif sonrası ReadOnly (hedef çeyrek ortasında değişmez) |
| Key Result'lar | Güncel Değer, Güven | Doğrudan düzenlenmez; check-in ile güncellenir (herkes için ReadOnly, otomasyon yazar) |
| Check-in'ler | Tüm alanlar | Koşullu grup: **Giren = ben** → Editor (24 saat içinde düzeltme, K9) |
| İK.Çalışanlar (diğer app) | Maaş, TC, adres, iletişim vb. hassas alanlar | Performans rollerine **Denied** — yalnızca Ad Soyad, Ünvan, Departman, Yönetici, Workiom Kullanıcısı görünür |

> **OKR şeffaflığı:** Objective / KR / Check-in'ler şirket içinde herkese açık (OKR ilkesi). Karneler ve yetkinlik puanları gizli.

---

## 7. Görünümler ve formlar

| Liste | Görünüm | Tip | Kim için |
|---|---|---|---|
| Karneler | Benim Karnem | Tablo (filtre: Çalışan = ben) | Çalışan |
| Karneler | Ekibimin Karneleri | **Kanban** (Durum) | Yönetici |
| Karneler | Kalibrasyon | Tablo, Departman + Performans Grubu'na göre gruplu, Kalibre Grup düzenlenebilir | İK |
| Karneler | Tüm Karneler | Tablo | İK, Üst Yönetim |
| KPI Hedefleri | Hedeflerim | Tablo (Karne'ye göre gruplu) | Çalışan |
| KPI Hedefleri | Gerçekleşen Girişi | Tablo, yalnızca Hedef / Hedeflenen / Gerçekleşen / Birim kolonları | Çalışan, veri sahibi |
| Yetkinlik Değ. | Değerlendirmelerim | Tablo (Değerlendiren = ben) | Yönetici |
| Objective'ler | OKR Ağacı | **Org Chart** (Üst Objective hiyerarşisi) | Herkes |
| Objective'ler | Bu Çeyrek | **Kanban** (Renk) | Herkes |
| Objective'ler | Departman OKR'ları | Tablo (Departman'a göre gruplu) | Herkes |
| Objective'ler | Takvim | **Timeline** (Dönem Başlangıç–Bitiş) | Üst Yönetim |
| Key Result'lar | KR'larım | Tablo (Sahip = ben, Takipte = 1) | Herkes |
| Check-in'ler | Son Check-in'ler | Tablo (Tarih azalan) | Herkes |
| Dönemler | Takvim | **Takvim** (Başlangıç) | İK |

| Form | Liste | İçerik |
|---|---|---|
| Karne | Performans Karneleri | Üst bilgi + **KPI Hedefleri alt tablosu** + skor özeti (layout sekmeleri: Hedefler / Yetkinlik / OKR / Kalibrasyon) |
| Haftalık Check-in | Check-in'ler | KR seçimi (filtre: KR'larım), Yeni Değer, Güven, Yapılan, Engel — tek ekran |
| Yeni OKR | Objective'ler | Objective + **Key Result'lar alt tablosu** (2–5 KR) |

**Validasyonlar:** Hedef Ağırlığı 0–100 · Güven 1–10 · Yetkinlik Puanı 1–5 · Objective'de Seviye Departman/Kişi ise Departman zorunlu · Seviye Kişi ise Sahip Çalışan zorunlu · Dönem tür filtresi (Karne: Yıl, Objective: Çeyrek).

---

## 8. Raporlar (pano)

**Pano 1 · Performans Karnesi (İK, Üst Yönetim)**
- KPI: Açık karne sayısı · Onay bekleyen karne · Ağırlık Hatası > 0 olan karne · Ortalama Toplam Puan
- Pasta: Performans Grubu dağılımı · Final Performans Grubu dağılımı
- Çubuk: Departmana göre ortalama Toplam Puan · Durumlara göre karne sayısı

**Pano 2 · OKR (herkes)**
- KPI: Aktif Objective · Ortalama İlerleme · Ortalama Güven · Bu hafta check-in girilmeyen KR (Check-in Gecikti = 1)
- Pasta: Renk dağılımı (bu çeyrek)
- Çubuk: Departmana göre ortalama İlerleme · Seviyeye göre Objective sayısı · KPI'a bağlı Objective sayısı (köprü kullanımı)

---

## 9. Teknik riskler (build'de test edilecek)

1. **Uygulamalar arası bağlantı + lookup:** İK.Çalışanlar'dan Workiom Kullanıcısı ve Yönetici lookup'larının kullanıcı tipinde gelip otomasyonla kullanıcı alanına kopyalanabildiği test edilecek. Gelmiyorsa KRN-01, İK kaydını find ile bulup değeri oradan alır.
2. **Formül → formül referansı** (Hedef Puanı → Gerçekleşme Oranı; gösterge formülleri → Ağırlıklı Skor). Desteklenmezse ifadeler açık yazılır (uzun ama çalışır).
3. **Rollup anlık güncelleme:** KPI gerçekleşeni değişince karne skorlarının ve KRN-05'in aynı anda güncellendiği; check-in sonrası Objective İlerleme ve OKR-04 zinciri test edilecek.
4. **Çoklu bağlantıda "içerir" filtresi** (KRN-04: Yetkinlikler.Form Türleri içerir X). Farmatek'te `contains` çalıştı; burada tekrar doğrulanacak.
5. **Koşullu yetki grupları** (Kilitli = 0/1, Sahip = ben) API'de kurulamazsa UI'dan yapılacak.
6. **DNM-01 toplu karne açma** cross-app find + create; çalışan sayısı yüksekse döngü limiti (max_records) nedeniyle parçalı çalıştırma gerekebilir.
7. **Lookup'lar geriye dönük hesaplanmaz:** Form Türleri oranı değişirse açık karnelerdeki lookup'lar bağlantı yeniden yazılarak güncellenir (yıl içinde oran değişmemesi önerilir).

---

## 10. Build planı (onaydan sonra)

1. İK app'inin listelerini ve alan ID'lerini okuma; Workiom Kullanıcısı ve Yönetici alanlarının kullanıcı tipinde olduğunu doğrulama. Form Türleri listesi kurulduktan sonra **İK.Çalışanlar'a "Performans Form Türü" alanı eklenir** (uygulamalar arası bağlantı → Form Türleri) ve mevcut çalışanlara form türü atanır (müşterinin vereceği ünvan → form türü eşleşmesiyle toplu güncelleme).
2. `python main.py build apps/performans_yonetimi.py`: app, 3 klasör, 10 liste, düz alanlar, uygulamalar arası bağlantılar, görünümler, formlar.
3. `python apps/upgrade_performans_computed.py`: formüller → ters bağlantılar + rollup/sayım → lookup'lar.
4. `python apps/performans_seed.py`: dönemler, form türleri, hedef türleri, yetkinlikler; Excel'deki 3 örnek çalışanın karnesi ve 27 hedefi.
5. **Doğrulama:** Workiom'daki KPI Skorları Excel ile birebir: A **63,10** · B **85,91** · C **70,05** (yetkinlik hariç).
6. `python apps/performans_roles.py`: 4 rol, kayıt filtreleri, alan izinleri.
7. `python apps/performans_build_automations.py`: 27 otomasyon.
8. `python apps/performans_reports.py`: 2 pano.
9. Uçtan uca test: dönem aç → karne → hedef gir (ağırlık hatası) → onay/red → gerçekleşen → yetkinlik → kalibrasyon → final; OKR yaz → onay → check-in → düşük güven → KPI'dan KR besleme → kapanış.

---

## 11. Senden (ve müşteriden) beklenen kararlar

| # | Karar | Önerim |
|---|---|---|
| **K1** | OKR performans puanına girsin mi? | ✅ **Karar: Girmeyecek.** Karnede bilgi olarak görünür; yetkinliklerde "OKR Davranışı" kalemi. |
| K2 | OKR seviyeleri | İlk yıl Şirket + Departman; Kişi opsiyonel |
| K3 | KPI gerçekleşenini kim girer? | Çalışan girer, yönetici görür. (Alternatif: yalnızca yönetici / veri sahibi) |
| K4 | Yetkinlik listesi ve ölçeği | Müşteriden; 1–5 varsayıldı |
| K5 | Takvim ve check-in sıklığı | Takvim yılı, 4 çeyrek, haftalık check-in |
| **K6** | İK.Çalışanlar'a "Performans Form Türü" alanı eklensin mi? | ✅ **Karar: Eklenecek.** Karne açılınca KRN-01 form türünü buradan otomatik doldurur. |
| K7 | Karneler toplu mu açılsın (DNM-01) yoksa İK tek tek mi açsın? | Toplu (yıl Aktif olunca) |
| K8 | Çalışan puanını / grubunu ne zaman görsün? | Karne Tamamlandı olduktan sonra (kalibrasyon bitince) |
| K9 | Check-in düzeltme süresi | 24 saat, sonra salt okunur |

**Müşteriden beklenen veri:** ünvan → form türü eşleşme listesi (İK.Çalışanlar'daki yeni alanı doldurmak için).

**İlk analiz dokümanından açık kalanlar:** sıfır değerlerin puanlanması (soru 3), performans grubu sınırları (soru 7; artık Toplam Puan üzerinden). Kalan %10'un yetkinlik olduğu cevaplandı.

---

## 12. Kurulum sonrası notlar (as-built, 20.10.2026)

**Tenant:** `faydasicok` · **App:** [`Performans Yönetimi`](https://faydasicok.workiom.com/app/apps/11c4b539-f3f5-41e0-a4e5-82b5cd906840) · **İK app:** `İnsan Kaynakları`

**Kurulu:** 3 klasör, 10 liste, 12 üst-alt ilişki (ters bağlantılı), 25 lookup, 18 formül, 16 rollup/sayım, 25 otomasyon, 4 rol, 15 pano widget'ı.
**Demo verisi:** İK'ya 30 yeni çalışan (toplam 37 aktif) · 8 dönem · 3 form türü · 3 hedef türü · 8 yetkinlik · 52 karne (2025: 15 tamamlanmış, 2026: 37) · 340 KPI hedefi · 94 yetkinlik değerlendirmesi · 28 Objective (2026-Ç3 kapanmış, 2026-Ç4 aktif; şirket / departman / kişi) · 66 KR · 223 check-in.

### İK eşlemesi (tasarımdaki genel adların karşılığı)
| Tasarım | İK app'te |
|---|---|
| İK.Çalışanlar | **Özlük Bilgileri** (birincil: İsim) |
| İK.Departmanlar | **Organizasyon** (pozisyon bazlı birim ağacı: CEO, CTO, Yazılım Müdürü …) |
| Workiom Kullanıcısı | Özlük Bilgileri · **Workiom Hesabı** |
| Yönetici | Özlük Bilgileri · **Birim Yöneticisi** (kullanıcı) |
| Departman Yöneticisi | Organizasyon · **Birim Yöneticisi Hesabı** |
| Performans Form Türü | Özlük Bilgileri'ne eklendi (K6) |

Demo verisinde bildirim yalnızca tenant sahibine gitsin diye tüm yönetici/sahip alanları Yalçın'dır; "Benim karnem" demosu için Gülşen Yılmaz'ın Workiom Hesabı = Yalçın.

### Doğrulama
- **Excel ile birebir:** 2025 karnelerinde Excel'in A / B / C örnekleri girildi → KPI Skoru **63,10 / 85,91 / 70,05** (OPS_Dummy 01, Hakan Bulut, Defne Arslan).
- **Canlı test edilen otomasyonlar:** CHK-01 (check-in → KR değeri, güven, tarih, giren), CHK-02, KPI-02 (KPI gerçekleşeni → bağlı KR), KRN-01 (yönetici + form türü İK'dan), KRN-02 (ağırlık hatasında geri alma), KRN-04 (form türüne göre yetkinlik formları: Müdür için 7), KRN-06 (kalibre grup → final), OKR-01 (seviye kodu, başarı eşiği, kişisel OKR → 2026 karnesi)., KRN-02 onay → Aktif + Onay Tarihi + KRN-03 hedef kilidi (otomasyonun yaptığı durum değişikliği diğer otomasyonları tetikliyor) / red (gerekçe zorunlu) → Hedef Belirleme, OKR-02 KR < 2 → Taslak / onay → Aktif / red → Taslak, KR-01 (yalnızca Aktif objective'e eklenen KR Takipte = 1), OKR-03 (Taslak → Aktif olunca KR'lar takibe girer), DNM-01 (2027 Aktif → 37 aktif çalışana 20 sn içinde "Hedef Belirleme" durumunda karne; KRN-01 37'sinde form türü ve yöneticiyi doldurdu). Test kayıtları silindi, 2027 Planlama'ya geri alındı.
- **Testte düzeltilenler:** DNM-01 karneyi Durum boş açıyordu (durum alanının varsayılanı otomasyonla açılan kayda uygulanmıyor) → Durum açıkça yazılıyor. KR-01 Takipte'yi koşulsuz 1 yapıyordu → Objective ters bağlantıyla bulunup Durum = Aktif ise 1. Bildirim adımları kullanıcı alanı boşsa atlanıyor (Workiom hesabı olmayan çalışanda "Kullanıcı bulunamadı" hatası oluşmaz).
- **Test edilmedi:** zamanlanmış otomasyonlar (KRN-05, OKR-04, KR-03 ilk gece / pazartesi çalışacak), DNM-04/05 zaman tetikleyicileri.

### Tasarımdan farklar
| Konu | Tasarım | Kurulan | Neden |
|---|---|---|---|
| Gerçekleşme | Gerçekleşme Oranı (0–1) | **Gerçekleşme (%)** + ölçekli formüller | Workiom formülünde **bölme sonucu 3 ondalığa yuvarlanıyor** (540/590 → 0,915). Oran 100.000 ile ölçeklendi, eşikler bu ölçekte yazıldı; Excel ile birebir. |
| Yönelim | Yön Kodu (gizli sayı) + KPI-01 | Formül seçim alanını doğrudan okuyor (`{{Hedef Yönelimi=Azalan}}`) | Seçim karşılaştırması formülde çalışıyor; alan ve otomasyon gereksiz. |
| OKR rengi | İlerleme ≥ 0,7 / ≥ 0,4 | Aktif: **İlerleme − Beklenen İlerleme** ≥ −0,05 yeşil, ≥ −0,15 sarı · Kapanmış: 0,7 / 0,4 | Çeyrek ortasında ham ilerleme her şeyi kırmızı gösteriyordu. Beklenen İlerleme = geçen gün / çeyrek günü (Objective'e 2 lookup + 2 formül eklendi). |
| KRN-05, OKR-04 | Alan değişince | **Her gece** (01:00 / 01:10 UTC) | Formül/rollup değişimi kayıt güncelleme tetikleyicisi üretmiyor. |
| KR-03 | pazartesi 09:00 | `0 6 * * 1` (UTC = 09:00 TR) | Sayı eşitliği filtresinde operatör 0 kullanılıyor. |
| KRN-07 | Karne zaman tetikleyicisi | **DNM-05** (Dönemler · Hedef Giriş Son Tarihi − 3 gün) | Tarih, karnede değil dönemde. |
| DNM-00 | Tek otomasyon | 00a (oluşturuldu) + 00b (Tür değişti) | |
| KPI-03, YTK-01 | Otomasyon | Kurulmadı → yetki (Kilitli) ve form validasyonu ile | Kural yetkiyle zaten sağlanıyor. |
| KRN-04 filtresi | "içerir" | Çoklu bağlantıda **"eşittir"** | `contains` sonuç döndürmüyor; `equals` çoklu bağlantıda üyelik kontrolü yapıyor. |
| Yetki filtresi | Karne üzerinden | KPI Hedefleri ve Yetkinlik Değ.'de **Karne Sahibi / Karne Yöneticisi** lookup'ları | "Kendim" kayıt filtresi listenin kendi kullanıcı alanında çalışır. |
| Red Notu | Onay redinde doldurulur | Alan var, otomatik dolmuyor | Ret gerekçesi onay kaydında kalıyor; alana yazılamıyor. |

### Arayüzden tamamlanacaklar
1. **Koşullu yetki grupları:** KPI Hedefleri'nde *Kilitli = 1* iken Hedef / Tür / Yönelim / Ağırlık / Hedeflenen salt okunur (Çalışan, Yönetici); Objective'de *Sahip = ben* → düzenler. API'de kurulmadı.
2. **Rollere kullanıcı atama:** 4 rol kullanıcısız açıldı (Performans – İK / Üst Yönetim / Yönetici / Çalışan). Alan izin kodları (0 görmez, 1 salt okunur, 2 düzenler) tenant'taki mevcut rolden çıkarıldı; arayüzde bir kez kontrol edilmeli.
3. **Formlar ve kayıt düzeni:** Karne formunda Hedefler / Yetkinlik / OKR / Kalibrasyon sekmeleri, Haftalık Check-in formu, Yeni OKR formu (KR alt tablosu).
4. **Validasyonlar:** Hedef Ağırlığı 0–100, Güven 1–10, Yetkinlik Puanı 1–5, Seviye'ye göre zorunlu Departman / Sahip Çalışan.
5. **OKR Ağacı** (Org Chart görünümü, Üst Objective) ve **Objective takvimi** (Timeline) görünümleri.

### Kurulum dosyaları
`performans-okr/builder/` — `apps/performans_yonetimi.py` (spec) → `performans_fix_primary.py` → `performans_computed.py` → `performans_seed.py` → `performans_automations.py` → `performans_roles.py` → `performans_reports.py`. Ayrıntı: `builder/README.md`.

## 13. Geri Bildirim listesi ve vibe app (20.10.2026)

**Geri Bildirim** (OKR klasörü, `apps/performans_feedback.py`): Tür (Takdir / Gelişim Önerisi / Geri Bildirim Talebi), Mesaj, Yanıt, Durum, Görünürlük (Herkese Açık / Özel), Tarih, Kimden / Kime → İK.Özlük Bilgileri, İlgili Objective, Yetkinlik (takdir rozeti); lookup'lar: Kimden Hesabı, Kime Hesabı, Kime Yöneticisi. 26 demo kaydı.

| # | Tetikleyici | Aksiyon |
|---|---|---|
| **GB-01** | Geri bildirim oluşturuldu | Tarih boşsa bugün · Gönderen = oluşturan · Talep ise Durum = Yanıt Bekliyor, değilse Gönderildi · Kime Hesabı'na bildirim |
| **GB-02** | Yanıt güncellendi (Talep) | Durum = Yanıtlandı · Kimden Hesabı'na bildirim |

Canlı test edildi (talep → bildirim, yanıt → Yanıtlandı + bildirim).

**Vibe app** `performans-okr` → https://faydasicok.workiom.com/vibe/performans-okr (kaynak: `vibe/performans-okr/`). Üstte persona seçici (Çalışan / Yönetici / İK) ve "kim olarak bakıyorum"; görünürlük demo içindir, gerçek erişimi Workiom rolleri belirler.
- **Çalışan:** özet + yapılacaklar, karnem (ağırlık göstergeleri, gerçekleşen girişi, hedef ekle / onaya gönder), OKR'larım (bugün beklenen değer + sapma ile check-in, haftalık toplu güncelleme, yeni OKR), geri bildirim (takdir duvarı, rozetler, talep / yanıt).
- **Yönetici:** ekip tablosu + benimseme kutucukları, karne / OKR onayı (AutomationApprovalRequest Approve / Reject), check-in akışı (takdir, yorum), takım OKR'ları (ekibe OKR atama, departman KR check-in'i), yetkinlik puanlama; "kendi hedeflerim" ile çalışan görünümü.
- **İK:** dönem durumu yönetimi (otomasyon etkisi gösterilerek), faz çubuğu, departman × aşama ısı haritası, "kimde bekliyor" + hatırlatma, OKR çeyreği check-in uyumu, kalibrasyon (sürükle-bırak, hedef dağılım; kalibrasyon aşamasında değilse senaryo modu, kaydedilmez), şirket skoru, parametreler (form türü oranları, yetkinlik aktifliği).
- Ekip = yöneticinin biriminin alt birimlerindeki çalışanlar (Organizasyon.Üst Birimi). Arayüz araştırması: Lattice, Perdoo, Tability, 15Five, Leapsome, Culture Amp, Profit.co, Quantive.
- Yazma izin listesi 10 liste için tanımlı; API yalnızca oluşturma iznini açıyor (canUpdate = 0), yazma proxy'si devreye girince güncelleme izni Workiom tarafında açılmalı.
- Demo için: Zeynep / İrem / Furkan 2026 karneleri Yönetici Onayında, Tolga / Pınar / Gizem Hedef Belirleme; Onayda bekleyen iki OKR yeniden gönderildi (gerçek onay isteği oluştu).
