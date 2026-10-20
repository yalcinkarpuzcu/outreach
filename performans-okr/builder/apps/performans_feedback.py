"""Performans Yönetimi — Geri Bildirim listesi (OKR klasörü) + demo verisi.

    python3 apps/performans_feedback.py          # liste + alanlar + görünümler + demo verisi
    python3 apps/performans_feedback.py nodata   # yalnızca liste

Takdir, gelişim önerisi ve geri bildirim talebi tek listede tutulur. Kimden / Kime İK'daki
Özlük Bilgileri'ne bağlanır (kullanıcı hesabı olmayan çalışanlar da geri bildirim alabilsin diye).
Takdir bir yetkinliğe, geri bildirim bir Objective'e iliştirilebilir.
"""
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps"))
from wk import client  # noqa: E402
from workiom.builder import Builder  # noqa: E402
from workiom.constants import F, V  # noqa: E402
from workiom.resolver import Resolver  # noqa: E402
from workiom.state import AppState  # noqa: E402
from performans_yonetimi import IK_APP, IK_CALISAN, link, sel, txt, date as dt, user  # noqa: E402

GB = "Geri Bildirim"
TURLER = ["Takdir", "Gelişim Önerisi", "Geri Bildirim Talebi"]
SPEC = {
    "name": "Performans Yönetimi",
    "folders": [{"name": "OKR", "lists": [
        {"name": GB, "icon": "far fa-comments",
         "fields": [
             txt(GB, required=True),
             sel("Tür", TURLER, ["#5bd77e", "#4e86f7", "#f5c044"]),
             txt("Mesaj", multiline=True),
             txt("Yanıt", multiline=True),
             sel("Durum", ["Gönderildi", "Yanıt Bekliyor", "Yanıtlandı"], ["#5bd7d0", "#ffa979", "#5bd77e"]),
             sel("Görünürlük", ["Herkese Açık", "Özel"], ["#7942e3", "#8ed6ff"]),
             dt("Tarih"),
             user("Gönderen (kullanıcı)"),
             link("Kimden", IK_CALISAN, IK_APP),
             link("Kime", IK_CALISAN, IK_APP),
             link("İlgili Objective", "Objective'ler"),
             link("Yetkinlik", "Yetkinlikler"),
         ],
         "views": [
             {"name": "Tüm Geri Bildirimler", "type": V.GRID},
             {"name": "Türe Göre", "type": V.KANBAN, "group_by": "Tür"},
         ]},
    ]}],
    "lists": [],
}


def fix_primary(c, st):
    lid = st.get_list_id(GB)
    fs = c.get("/api/services/app/Fields/GetAll", {"listId": lid, "withSystemFields": "true"})
    fs = fs.get("items", fs) if isinstance(fs, dict) else fs
    prim = next(f for f in fs if f.get("isPrimary"))
    dup = next((f for f in fs if f["name"] == GB and not f.get("isPrimary")), None)
    if dup:
        c.delete("/api/services/app/Fields/Delete", {"listId": lid, "id": dup["id"]})
    if prim["name"] != GB:
        c.put("/api/services/app/Fields/Update", {**prim, "name": GB, "isRequired": False, "isVisible": True},
              {"listId": lid, "id": prim["id"]})
    print(f"  birincil = {GB} ({prim['id']})" + (" · kopya silindi" if dup else ""))


# ─── demo verisi ────────────────────────────────────────────────────────────
TAKDIR = [
    ("Selin Aydın", "Gülşen Yılmaz", "Performans sisteminin dijitalleşmesi projesinde ekibi çok iyi yönettin. Takvimde bir gün bile kayma olmadı.", "Sonuç Odaklılık"),
    ("Murat Koç", "Burak Çelik", "Ödeme modülündeki kritik hatayı gece yarısı çözdüğün için teşekkürler, müşteri kaybını önledin.", "Sonuç Odaklılık"),
    ("Hakan Bulut", "Seda Güneş", "Depo yerleşim pilotunda sahadan getirdiğin veriler kararımızı netleştirdi.", "Problem Çözme"),
    ("Aylin Kılıç", "Cansu Yavuz", "Şikayetçi müşteriyi sadık müşteriye çeviren görüşmen ekip toplantısında örnek oldu.", "Müşteri Odaklılık"),
    ("Burak Çelik", "Zeynep Öztürk", "Kod gözden geçirmelerinde bıraktığın açıklamalar çok öğretici, teşekkürler.", "Takım Çalışması"),
    ("Gülşen Yılmaz", "Merve Kurt", "Yetenek havuzu sunumun yönetim kurulunda çok beğenildi.", "İletişim"),
    ("Kerem Yıldız", "Murat Koç", "Q3 OKR'larında riskleri erken paylaşman sayesinde kapsamı zamanında daralttık.", "OKR Davranışı"),
    ("Serkan Uçar", "Volkan Sarı", "Portföy panosunu tek başına ayağa kaldırdın, PMO'nun işi çok kolaylaştı.", "Sonuç Odaklılık"),
    ("Defne Arslan", "Kaan Aslan", "Ay sonu kapanışını ilk kez 5 günün altına indirdik, emeğine sağlık.", "Sonuç Odaklılık"),
    ("Onur Aksoy", "Tolga Özdemir", "Bordro hatalarını kök nedenine kadar takip ettin, bu ay sıfır hata.", "Problem Çözme"),
    ("Cansu Yavuz", "Barış Doğan", "Yoğun günde vardiyamı devraldığın için teşekkürler.", "Takım Çalışması"),
    ("Nazlı Ekinci", "Esra Turan", "Müşteri kabul toplantısını çok iyi hazırladın, tek seferde onay aldık.", "Müşteri Odaklılık"),
    ("Ece Şahin", "Emre Kaya", "Test kapsamını %70'e taşıyan çalışman sprint hedefini kurtardı.", "OKR Davranışı"),
    ("Hakan Bulut", "Okan Tekin", "Enerji tüketimi verisini haftalık check-in'lere düzenli girmen OKR'ı görünür kıldı.", "OKR Davranışı"),
]
GELISIM = [
    ("Murat Koç", "Emre Kaya", "Sprint planlamasında tahminlerini biraz daha temkinli yapabilirsin; son iki sprintte taşma oldu."),
    ("Aylin Kılıç", "Furkan Özkan", "Geri arama notlarını CRM'e aynı gün girersen ekip devri çok daha kolay olur."),
    ("Gülşen Yılmaz", "Onur Aksoy", "Bağlılık anketi sonuçlarını birimlere dönerken aksiyon önerisi de eklersek etkisi artar."),
    ("Serkan Uçar", "Nazlı Ekinci", "Bütçe sapması raporunda trend grafiği olursa yönetim daha hızlı karar verir."),
    ("Kerem Yıldız", "Ece Şahin", "Teknik borç listesini çeyreklik OKR'lara bağlarsan önceliklendirme kolaylaşır."),
    ("Hakan Bulut", "Pınar Acar", "Fire oranı check-in'lerinde güven skorunu daha gerçekçi verebilirsin; iki hafta 8 dedin ama hedefin gerisindeydik."),
]
TALEP = [  # kimden (talep eden), kime (yanıtlayacak), mesaj, yanıt (None = bekliyor)
    ("Merve Kurt", "Gülşen Yılmaz", "Yetenek havuzu sunumumu nasıl buldunuz? Bir sonraki sunumda neyi farklı yapmalıyım?",
     "İçerik çok güçlüydü. Bir sonrakinde ilk slayta tek cümlelik bir özet koy, yönetim hızlı okuyor."),
    ("Zeynep Öztürk", "Murat Koç", "Mobil v2'deki rolüm hakkında geri bildirim alabilir miyim?", None),
    ("Barış Doğan", "Aylin Kılıç", "Müşteri görüşmelerimde ses tonum hakkında ne düşünüyorsunuz?", None),
    ("Volkan Sarı", "Serkan Uçar", "Portföy panosu için önceliklerim doğru mu?",
     "Doğru. Sadece kaynak planlaması sekmesini Q1'e bırakalım."),
    ("İrem Demir", "Burak Çelik", "Kod gözden geçirmede neyi geliştirmeliyim?", None),
    ("Melis Ateş", "Defne Arslan", "Nakit akış modelinde varsayımlarım yeterince açık mı?", None),
]


def seed(c, st):
    sys.argv = ["x", "none"]
    import performans_seed as S
    S.REG[GB] = st.get_list_id(GB)
    S._F.pop(GB, None)
    mevcut = S.records(GB)
    if mevcut:
        print(f"  demo verisi zaten var ({len(mevcut)} kayıt)")
        return
    isim = S.F("Özlük Bilgileri", "İsim")
    cal = {r.get(isim): r["_id"] for r in S.records("Özlük Bilgileri")}
    yet = {r.get(S.F("Yetkinlikler", "Yetkinlik")): r["_id"] for r in S.records("Yetkinlikler")}
    rnd = random.Random(7)
    bugun = date(2026, 10, 20)

    def gun():
        return (bugun - timedelta(days=rnd.randint(0, 40))).isoformat()

    n = 0
    for kimden, kime, mesaj, y in TAKDIR:
        S.create(GB, {GB: f"Takdir · {kimden} → {kime}", "Tür": "Takdir", "Mesaj": mesaj, "Durum": "Gönderildi",
                      "Görünürlük": "Herkese Açık", "Tarih": gun(), "Gönderen (kullanıcı)": S.user(),
                      "Kimden": S.link(cal[kimden]), "Kime": S.link(cal[kime]), "Yetkinlik": S.link(yet.get(y))})
        n += 1
    for kimden, kime, mesaj in GELISIM:
        S.create(GB, {GB: f"Gelişim · {kimden} → {kime}", "Tür": "Gelişim Önerisi", "Mesaj": mesaj,
                      "Durum": "Gönderildi", "Görünürlük": "Özel", "Tarih": gun(), "Gönderen (kullanıcı)": S.user(),
                      "Kimden": S.link(cal[kimden]), "Kime": S.link(cal[kime])})
        n += 1
    for kimden, kime, mesaj, yanit in TALEP:
        S.create(GB, {GB: f"Talep · {kimden} → {kime}", "Tür": "Geri Bildirim Talebi", "Mesaj": mesaj,
                      "Yanıt": yanit, "Durum": "Yanıtlandı" if yanit else "Yanıt Bekliyor", "Görünürlük": "Özel",
                      "Tarih": gun(), "Gönderen (kullanıcı)": S.user(),
                      "Kimden": S.link(cal[kimden]), "Kime": S.link(cal[kime])})
        n += 1
    print(f"  {n} geri bildirim oluşturuldu")


if __name__ == "__main__":
    c = client()
    st = AppState("Performans Yönetimi")
    Builder(c, st, Resolver(c)).build(SPEC)
    fix_primary(c, st)
    if "nodata" not in sys.argv:
        seed(c, st)
