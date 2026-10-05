---
format: 1920x1080
duration: 150s
message: "Her lead'i bir sonraki adıma en kısa sürede taşı: hızlı ara, önce dinle, çemberleri aç, ekranda kanıtla, hemen teklife geç — hepsini CRM'e yaz."
arc: Açılış → Kaynak → Hız → İlk arama → Kadans → Çemberler → Kanıt → Toplantı → Teklif → Disiplin/Kapanış
audience: Workiom satış ekibine yeni katılan full cycle satış temsilcisi
mode: collaborative
theme: "A — Kâğıt Masa"
tempo: 96 BPM (1 bar = 2.5 s) — her sahne bar katında başlar
---

# Message & tone

> Yeni gelen bir satışçıya, bir lead'in Workiom'a düştüğü ilk dakikadan teklifin
> imzalandığı ana kadar izlediği yolu **sıcak ve öğretici** bir tonla anlatmak
> istiyorum; izleyen **"yol belli, ritim belli — ben de yapabilirim"** hissetsin.

**Kahraman motifi (bilinçli tekrar — `motif:`):** "lead jetonu" — mor bir disk
(logodaki ok yönüyle). Her sahnede aynı jeton bir sonraki aşamaya taşınır;
izleyici yolu jetonu takip ederek okur.

**Tasarım:** krem kâğıt (#F5EFE4) + nokta dokusu, lacivert mürekkep (#221E52),
mor #8A3FFC (ana), pembe #F0287A (uyarı / vurgu), sarı #F6B71E (otomasyon / sistem).
Sesler: Fraunces (mentorun sesi — başlıklar, italik vurgular) · Rubik (süreç, etiket)
· JetBrains Mono (zaman / sayı / CRM alanları). Ekran metni sahne başına ≤ 7 kelime
ana satır.

# Ledger

| # | Sahne | Süre | Giriş (entrance) | Geçiş (transition_in) | Aile | Ease | Yön | Kamera | Bileşenler | Yeni bileşen | SFX | Not |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Açılış | 10 s | logo maske-wipe + başlık waterfall | — (soğuk açılış) | — | power3.out | sol→sağ | sabit, hafif drift | logo, jeton | — | kâğıt hışırtısı + yumuşak çan | logo gerçek (PDF'ten) |
| 2 | Kaynaklar | 12.5 s | 3 bulut spring-pop, çizgiler path-draw | mürekkep çizgisi wipe | örtme/maske | back.out(1.4) / sine | yukarı→aşağı | sabit | 3 kaynak, CRM tepsisi, Source çipi | Source çipi "flip" düzeltme | 3 tık (kaynaklar), "düşme" tok | Network kesikli yol: kendi ritmi |
| 3 | 15 dk kuralı | 12.5 s | kadran path-draw + ibre süpürme | ölçek-takas eşleşme kesmesi (jeton → kadran merkezi) | ölçek/morph | expo.out / linear ibre | merkezden | itme (push-in) | 15 dk kadranı, telefon | kadran-sayaç | saat tik-tak (ılık), telefon zili 2× | "ihtiyaç taze" tek satır |
| 4 | İlk arama | 12.5 s | ses dalgası 4 segmente bölünür, saat çipleri | yatay whip-pan | itme | power4.inOut | sağ→sol | yatay pan | arama dalgası, 2 saat çipi | "konuşma şeridi" (segmentli dalga) | whoosh, seçim "pop" | açık uçlu bitirme yok |
| 5 | Takip kadansı | 20 s | ip çizilir, 5 düğüm sırayla pop, mesaj balonları | odak çekme (blur crossfade) | bulanıklık | power2.inOut / back.out | sol→sağ | spatial-pan-stations | kadans ipi, mesaj balonları, görev rozeti | kadans ipi | düğüm başına tuned pluck (yükselen), mesaj "blip" | 3. düğüm sarı = otomasyon |
| 6 | Üç çember | 17.5 s | fidan büyür, dallar çizilir, halkalar genişler | radyal iris (tohumdan) | radyal | sine.out / power2.out | aşağı→yukarı | yavaş zoom-out | fidan-ağaç, 3 halka | **fidan → dallar ağacı** | toprak "tok", 3 yükselen nota | "Ekstra bütçe yok." damga |
| 7 | Söz'den Kanıt'a | 12.5 s | balon → ekran morph, 3 koşul tik | kart morph (balondan) | morph | power3.inOut | merkez | sabit | konuşma balonu, ekran çerçevesi, 3 koşul | balon→ekran morph | morph "swish", 3 tik, DEAL damga | |
| 8 | Toplantı + POC | 20 s | 5 blok orantılı genişlikle dolar, POC sapma yolu | kâğıt şerit blinds (4 yatay) | grid/şerit | power2.out / steps | sol→sağ | hafif push-in kalpte | toplantı şeridi, referans eko, POC sapması | POC "sapma döngüsü" | şerit flap'leri, kalp bloğunda pad yükselir | süreler PDF'ten |
| 9 | Teklif | 15 s | teklif kâğıdı kayarak gelir, tarih damgası, buhar soğuması | sayfa çevirme (3D) | 3D | power2.inOut | sağ kenar | hafif tilt | teklif kâğıdı, geçerlilik damgası, çay buharı | "soğuyan teklif" buharı | sayfa çevirme, damga "thunk" | indirim = taahhüt karşılığı |
| 10 | Disiplin + kapanış | 17.5 s | 3 altın kural damgası → tüm yol haritası zoom-out → logo | önceki sahne uzaklaşarak küçülür (recede) | ölçek | expo.inOut | dışarı | büyük zoom-out | 3 kural, harita, logo | yol haritası (tüm jetonlar) | 3 damga, final akor | kapanış logosu |

Transition aileleri: örtme/maske · ölçek-takas · itme (whip) · bulanıklık · radyal · morph · grid/şerit · 3D · ölçek (recede) → 8 aile, ardışık tekrar yok; sürprizler: 3 (eşleşme kesmesi, ~22 s), 6 (iris + büyüyen ağaç, ~67 s), 8 (POC sapması, ~102 s), 10 (zoom-out harita, ~132 s); aralarda 4–5 (whip + pan) ve 7 (morph) — ~15 s'de bir sürpriz.

## Frame 1 — Açılış

- scene: Krem kâğıt; resmi Workiom logosu mürekkep maskesiyle açılır, altında "Lead'den imzaya." ; mor lead jetonu masaya düşer.
- duration: 10s
- poster: 6s
- transition_in: cut
- status: animated
- src: index.html#s01-acilis.html
- blueprint: logo-assemble-lockup (wipe-reveal varyantı) + waterfall-entry
- onscreen: "SATIŞ PLAYBOOK'U" · "Lead'den imzaya." · "Full cycle — tek kişi, uçtan uca."

Mentor masaya oturur: bu video bir harita.

## Frame 2 — Lead nereden gelir?

- scene: Üç kaynak bulutu (Inbound / Outbound / Network) çizgilerle CRM tepsisine akar; LEAD kartı düşer; Source çipi Inbound→Outbound çevrilir.
- duration: 12.5s
- poster: 9s
- transition_in: ink-wipe
- status: animated
- src: index.html#s02-kaynaklar.html
- rules: spring-pop-entrance, svg-path-draw, center-outward-expansion (ters)
- onscreen: "INBOUND · OUTBOUND · NETWORK" · "Source = gerçek kaynak"

Inbound en sıcağı; Outbound'da ilgiyi biz yaratırız; Network kendi ritminde (kesikli yol yana ayrılır). Mailimizi görüp kendi hesap açan → Source Outbound'a çekilir.

## Frame 3 — 15 dakika kuralı

- scene: Jeton büyüyüp kadranın merkezine dönüşür; ibre 15 dakikayı süpürür, telefon çalar; "≤ 15 dk".
- duration: 12.5s
- poster: 8s
- transition_in: scale-swap match cut
- status: animated
- src: index.html#s03-15dk.html
- rules: scale-swap-transition, svg-path-draw (halka), counting-dynamic-scale
- onscreen: "≤ 15 dk" · "İhtiyaç henüz taze."

## Frame 4 — İlk arama

- scene: Arama, dört renkli segmente bölünmüş bir ses dalgası şeridi: Açılış 30 sn · Dinle 2–3 dk · Çemberler 2–3 dk · Kapat 1 dk; sonunda iki saat çipi (11:00 / 15:00), biri seçilir.
- duration: 12.5s
- poster: 9s
- transition_in: whip-pan
- status: animated
- src: index.html#s04-ilk-arama.html
- rules: stat-bars-and-fills (scaleX), press-release-spring
- onscreen: segment etiketleri · "Yarın 11:00 mı, 15:00 mü?"

Hedef satmak değil, toplantı almak.

## Frame 5 — Takip kadansı

- scene: Noktalı ip çizilir; kamera düğümden düğüme kayar: ≤15 dk → +2 saat → 1 gün (otomasyon, sarı) → ertesi gün → son deneme; Mesaj 1/2/3 balonları uçar; sonda kart "Unqualified · Non-responding"; görev rozeti "Hiçbir lead görevsiz kalmaz".
- duration: 20s
- poster: 14s
- transition_in: focus-pull
- status: animated
- src: index.html#s05-kadans.html
- blueprint: spatial-pan-stations
- onscreen: düğüm etiketleri · "Hiçbir lead görevsiz kalmaz."

## Frame 6 — Üç çember: fidandan ağaca

- scene: Tohumdan fidan çıkar (1. çember: Görev), dal verir (2: Proje · Müşteri), daha geniş dallar (3: Teklif · Masraf · Rapor); arkada üç halka genişler; damga "Ekstra bütçe yok."
- duration: 17.5s
- poster: 13s
- transition_in: radial-iris
- status: animated
- src: index.html#s06-cemberler.html
- rules: svg-path-draw, spring-pop-entrance, sine-wave-loop
- onscreen: halka etiketleri · "Ekstra bütçe yok."

## Frame 7 — Söz'den Kanıt'a

- scene: Konuşma balonu ("Bunu yapabilirsiniz") büyüyüp bir ekran çerçevesine dönüşür ("Evet, işte böyle"); üç koşul tiklenir → DEAL damgası.
- duration: 12.5s
- poster: 9s
- transition_in: card-morph
- status: animated
- src: index.html#s07-kanit.html
- rules: card-morph-anchor, spring-pop-entrance
- onscreen: "Söz → Kanıt" · Potansiyel · Platformu anladı · Acil ihtiyaç · "DEAL"

## Frame 8 — Toplantı akışı + POC

- scene: Toplantı şeridi süreleriyle orantılı 5 blokla dolar: Kısaca anlat 5 · Dinle 10–15 · Süreçlerimiz 5 · İhtiyaç üzerinden 20–25 · Sonraki adım 5 dk; kalp bloğu parlar; "Benzer bir müşterimiz var" ekosu; gerekirse POC sapma döngüsü (dar kapsam · tarihli) ana yola geri bağlanır.
- duration: 20s
- poster: 15s
- transition_in: paper-blinds
- status: animated
- src: index.html#s08-toplanti.html
- rules: stat-bars-and-fills, svg-path-draw, nudge-curve
- onscreen: blok etiketleri + dk · "POC: dar kapsam · tarihli"

## Frame 9 — Teklif

- scene: Teklif kâğıdı kayarak gelir; "Geçerlilik" tarih damgası; yanında çay bardağı — beklerse buharı söner (teklif soğur); "Neyi netleştirelim?" sorusu.
- duration: 15s
- poster: 10s
- transition_in: page-turn
- status: animated
- src: index.html#s09-teklif.html
- rules: card-morph-anchor (kâğıt), press-release-spring (damga), sine-wave-loop (buhar)
- onscreen: "En hızlı şekilde kapat." · "Geçerlilik: tarihli" · "Neyi netleştirirsek karar kolaylaşır?"

## Frame 10 — CRM disiplini + kapanış

- scene: Üç altın kural damga gibi basılır (15 dk · 5 temas · 0 görevsiz lead); kamera geri çekilir ve tüm yolculuk tek haritada görünür; logo + "Playbook'u masanda tut."
- duration: 17.5s
- poster: 14s
- transition_in: recede
- status: animated
- src: index.html#s10-kapanis.html
- blueprint: zoom-out-workspace-reveal + logo-assemble-lockup
- onscreen: "15 dk" · "5 temas" · "0 görevsiz lead" · "CRM tek doğruluk kaynağı." · logo

# Build notes

- Tek dosya (`index.html`) olarak kuruldu: sahneler arası geçişler iki sahnenin aynı DOM'da olmasını
  gerektirdiği ve "lead jetonu" motifi sahneden sahneye taşındığı için. Her sahne `<section id="sNN">`.
- Ses: `tools/make_audio.py` (96 BPM prosedürel skor + sıcak tonlu SFX) → `assets/audio/*.mp3`.
