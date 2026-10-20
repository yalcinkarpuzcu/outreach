"""Performans Yönetimi — otomasyonlar (TASARIM.md bölüm 5).

    python3 apps/performans_automations.py            # hepsi (aynı ad varsa atlanır)
    python3 apps/performans_automations.py KRN OKR-02  # kod önekine göre

Notlar (API davranışı):
  • Hesaplanan alan (formül / rollup) değişimi kayıt güncelleme tetikleyicisi üretmez. Bu yüzden
    performans grubu (KRN-05) ve OKR rengi (OKR-04) gece çalışan zamanlanmış otomasyonla yazılır.
  • Arama filtresinde seçim / durum alanı kullanılamaz → arama geniş yapılır, durum kontrolü
    döngü içindeki koşulda yapılır.
  • Üst kayıt, alt kaydın id'si ile ters bağlantı üzerinden bulunur (Key Result'lar.Check-in'ler = trigger:_id).
  • Seçim alanları arasında değer kopyalanamaz (seçenek id'leri alana özgü) → etiket başına koşul.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from wk import client  # noqa: E402
from workiom.automation_builder import AutomationBuilder  # noqa: E402
from workiom.state import AppState  # noqa: E402

IK_APP = "9b672737-2465-4c5e-b41a-8a3db4f91d9b"
IK_CALISAN = "cc279e0f-af5a-4ff8-986f-a31793432ddf"
GRUPLAR = ["Beklentinin Çok Altında", "Beklenenin Altında", "Beklenen Performans",
           "Beklentinin Üstünde", "Beklentinin Çok Üstünde"]
TODAY = "formula:Today()"
K, H, YD = "Performans Karneleri", "KPI Hedefleri", "Yetkinlik Değerlendirmeleri"
O, KR, CI, D = "Objective'ler", "Key Result'lar", "Check-in'ler", "Dönemler"


# ─── kısa yardımcılar ─────────────────────────────────────────────────────────
def created(lst):
    return {"type": "record_created", "list": lst}


def updated(lst, field=None):
    t = {"type": "record_updated", "list": lst}
    if field:
        t["watch_field"] = field
    return t


def timed(lst, date_field, offset):
    return {"type": "time_trigger", "list": lst, "date_field": date_field, "offset": offset}


def cron(expr):
    return {"type": "cron", "cron": expr}


def cond(expr, then, else_=None):
    a = {"type": "condition", "if": expr, "then": then}
    if else_:
        a["else"] = else_
    return a


def upd(fields, target=None):
    a = {"type": "update_record", "fields": fields}
    if target:
        a["target"] = target
    return a


def find(lst, where, actions, mx=200, app_id=None):
    a = {"type": "find_records", "list": lst, "where": where, "actions": actions, "max": mx}
    if app_id:
        a["app_id"] = app_id
    return a


def w(field, value, op="equals"):
    return {"field": field, "op": op, "value": value}


def nf(field, msg):
    """Kullanıcı alanı boşsa bildirim atlanır (boş alana bildirim "Kullanıcı bulunamadı" hatası üretir)."""
    return cond("isNotBlank({{%s}})" % field, [{"type": "notify", "to_field": field, "message": msg}])


def nl(field, msg):
    """Döngüdeki kaydın kullanıcı alanına bildirim (alan boşsa atlanır)."""
    return cond("isNotBlank({{%s}})" % field, [{"type": "notify", "to_loop_field": field, "message": msg}])


def A(code, name, trigger, actions):
    return {"name": f"{code} · {name}", "trigger": trigger, "actions": actions}


def grup_kosullari(alan_puan="Toplam Puan", hedef="Performans Grubu"):
    """Puan eşiklerine göre performans grubunu yazan iç içe koşul (döngü kaydına)."""
    p = "{{%s}}" % alan_puan
    return [cond(f"{p} < 60", [upd({hedef: GRUPLAR[0]})], [
        cond(f"{p} < 90", [upd({hedef: GRUPLAR[1]})], [
            cond(f"{p} < 101", [upd({hedef: GRUPLAR[2]})], [
                cond(f"{p} < 111", [upd({hedef: GRUPLAR[3]})], [upd({hedef: GRUPLAR[4]})])])])])]


# ═══ Dönemler ═════════════════════════════════════════════════════════════════
DNM = [
    A("DNM-00a", "Tür kodu (yeni dönem)", created(D), [
        cond("{{Tür}} = 'Yıl'", [upd({"Tür Kodu": 1})], [upd({"Tür Kodu": 2})])]),
    A("DNM-00b", "Tür kodu (tür değişti)", updated(D, "Tür"), [
        cond("{{Tür}} = 'Yıl'", [upd({"Tür Kodu": 1})], [upd({"Tür Kodu": 2})])]),
    A("DNM-01", "Yıl aktif → tüm aktif çalışanlara karne aç", updated(D, "Durum"), [
        cond("{{Durum}} = 'Aktif' and {{Tür Kodu}} = 1", [
            find("Özlük Bilgileri", [], [
                cond("{{Fiili Görev Durumu}} = 'Aktif Çalışan'", [
                    {"type": "create_record", "list": K, "fields": {
                        "Karne": "formula:Concat({{Dönem Adı}}, ' – ', {{loop:İsim}})",
                        "Çalışan": "loop:_id", "Dönem": "trigger:_id",
                        # durum alanının varsayılanı otomasyonla açılan kayda uygulanmaz
                        "Durum": "Hedef Belirleme"}}])],
                 mx=500, app_id=IK_APP)])]),
    A("DNM-02", "Çeyrek kapanışı → aktif OKR'lar kapanışa", updated(D, "Durum"), [
        cond("{{Durum}} = 'Kapanış' and {{Tür Kodu}} = 2", [
            find(O, [w("Dönem", "trigger:_id")], [
                cond("{{Durum}} = 'Aktif'", [upd({"Durum": "Kapanış"})])])])]),
    A("DNM-03", "Yıl kapanışı → aktif karneler değerlendirmeye", updated(D, "Durum"), [
        cond("{{Durum}} = 'Kapanış' and {{Tür Kodu}} = 1", [
            find(K, [w("Dönem", "trigger:_id")], [
                cond("{{Durum}} = 'Aktif'", [upd({"Durum": "Değerlendirme"})])], mx=500)])]),
    A("DNM-04", "Çeyrek bitimine 7 gün → OKR sahiplerine hatırlatma", timed(D, "Bitiş", -7), [
        cond("{{Tür Kodu}} = 2", [
            find(O, [w("Dönem", "trigger:_id")], [
                cond("{{Durum}} = 'Aktif'", [
                    nl("Sahip", "Çeyrek 7 gün içinde bitiyor: KR'larını güncelle ve kapanışa hazırlan.")])])])]),
    A("DNM-05", "Hedef girişi son tarihine 3 gün → hatırlatma", timed(D, "Hedef Giriş Son Tarihi", -3), [
        cond("{{Tür Kodu}} = 1", [
            find(K, [w("Dönem", "trigger:_id")], [
                cond("{{Durum}} = 'Hedef Belirleme'", [
                    nl("Çalışan (kullanıcı)", "Hedef girişi için son 3 gün: karnendeki hedefleri tamamlayıp onaya gönder."),
                    nl("Yönetici (kullanıcı)", "Ekibinizde hedef girişini tamamlamamış karneler var.")])], mx=500)])]),
]

# ═══ Performans Karneleri ═════════════════════════════════════════════════════
KRN = [
    A("KRN-01", "Karne açıldı → kullanıcı, yönetici, form türü", created(K), [
        upd({"Çalışan (kullanıcı)": "trigger:Çalışan Hesabı", "Yönetici (kullanıcı)": "trigger:Yönetici Hesabı"}),
        cond("isBlank({{Form Türü}})", [upd({"Form Türü": "trigger:İK Form Türü"})]),
        nf("Çalışan (kullanıcı)", "Performans karnen açıldı: {{Karne}}. Hedeflerini girip yönetici onayına gönder."),
    ]),
    A("KRN-02", "Onaya gönderildi → ağırlık kontrolü + yönetici onayı", updated(K, "Durum"), [
        cond("{{Durum}} = 'Yönetici Onayında'", [
            cond("{{Ağırlık Hatası}} > 0 or {{Hedef Sayısı}} = 0", [
                upd({"Durum": "Hedef Belirleme"}),
                nf("Çalışan (kullanıcı)", "{{Karne}}: her hedef türünde ağırlık toplamı %100 olmalı. Karne düzenlemeye geri alındı."),
            ], [
                {"type": "approval", "title": "Karne onayı",
                 "subtitle": "{{Karne}} · KPI hedefleri onayınızı bekliyor",
                 "approver": "field:Yönetici (kullanıcı)", "timeout_days": 5,
                 "require_rejection_message": True,
                 "on_approve": [upd({"Durum": "Aktif", "Onay Tarihi": TODAY}),
                                nf("Çalışan (kullanıcı)", "{{Karne}} onaylandı, hedeflerin artık aktif.")],
                 "on_reject": [upd({"Durum": "Hedef Belirleme"}),
                               nf("Çalışan (kullanıcı)", "{{Karne}} reddedildi. Yöneticinin notuna göre hedefleri düzenle.")]},
            ]),
        ]),
    ]),
    A("KRN-03", "Karne aktif → hedefler kilitlenir", updated(K, "Durum"), [
        cond("{{Durum}} = 'Aktif'", [find(H, [w("Karne", "trigger:_id")], [upd({"Kilitli": 1})])])]),
    A("KRN-04", "Değerlendirme → yetkinlik formları oluşur", updated(K, "Durum"), [
        cond("{{Durum}} = 'Değerlendirme'", [
            # çoklu bağlantıda "equals" üyelik kontrolü yapar ("contains" sonuç döndürmüyor)
            find("Yetkinlikler", [w("Form Türleri", "trigger:Form Türü")], [
                cond("{{Aktif}} = 1", [
                    {"type": "create_record", "list": YD, "fields": {
                        "Değerlendirme": "loop:Yetkinlik", "Karne": "trigger:_id", "Yetkinlik": "loop:_id",
                        "Değerlendiren": "trigger:Yönetici (kullanıcı)"}}])], mx=50),
            nf("Çalışan (kullanıcı)", "{{Karne}}: yıl sonu gerçekleşen değerlerini gir."),
            nf("Yönetici (kullanıcı)", "{{Karne}}: yetkinlik değerlendirmesi bekliyor."),
        ]),
    ]),
    A("KRN-05", "Performans grubu (her gece)", cron("0 1 * * *"), [
        find(K, [], grup_kosullari(), mx=1000)]),
    A("KRN-06", "Karne tamamlandı → final grup", updated(K, "Durum"), [
        cond("{{Durum}} = 'Tamamlandı'", [
            cond("isNotBlank({{Kalibre Grup}})",
                 [cond(f"{{{{Kalibre Grup}}}} = '{g}'", [upd({"Final Performans Grubu": g})]) for g in GRUPLAR],
                 [cond(f"{{{{Performans Grubu}}}} = '{g}'", [upd({"Final Performans Grubu": g})]) for g in GRUPLAR]),
            nf("Çalışan (kullanıcı)", "{{Karne}} tamamlandı. Sonucunu karnende görebilirsin."),
        ]),
    ]),
]

# ═══ KPI Hedefleri ════════════════════════════════════════════════════════════
KPI = [
    A("KPI-02", "Gerçekleşen değişti → bağlı KR'ları besle", updated(H, "Gerçekleşen"), [
        upd({"Son Güncelleme": TODAY}),
        find(KR, [w("Kaynak KPI", "trigger:_id")],
             [upd({"Güncel Değer": "trigger:Gerçekleşen", "Son Check-in Tarihi": TODAY})]),
    ]),
]

# ═══ Objective'ler ════════════════════════════════════════════════════════════
OKR = [
    A("OKR-01", "Objective açıldı → seviye kodu, başarı eşiği, onaylayıcı, karne", created(O), [
        cond("{{Seviye}} = 'Şirket'", [upd({"Seviye Kodu": 1})]),
        cond("{{Seviye}} = 'Departman'", [upd({"Seviye Kodu": 2})]),
        cond("{{Seviye}} = 'Kişi'", [upd({"Seviye Kodu": 3})]),
        cond("{{OKR Türü}} = 'Zorunlu (Committed)'", [upd({"Başarı Eşiği": 1})], [upd({"Başarı Eşiği": 0.7})]),
        cond("isNotBlank({{Departman Yöneticisi}})", [upd({"Onaylayıcı": "trigger:Departman Yöneticisi"})]),
        cond("{{Seviye}} = 'Kişi' and isNotBlank({{Sahip Çalışan}})", [
            find(K, [w("Çalışan", "trigger:Sahip Çalışan"), w("Dönem", "trigger:Yıl")],
                 [upd({"Karne": "loop:_id"}, target="trigger")], mx=1)]),
    ]),
    A("OKR-02", "Onaya gönderildi → KR kontrolü + onay", updated(O, "Durum"), [
        cond("{{Durum}} = 'Onayda'", [
            cond("{{KR Sayısı}} < 2", [
                upd({"Durum": "Taslak"}),
                nf("Sahip", "{{Objective}}: onaya göndermek için en az 2 Key Result ekle."),
            ], [
                {"type": "approval", "title": "OKR onayı", "subtitle": "{{Objective}} onayınızı bekliyor",
                 "approver": "field:Onaylayıcı", "timeout_days": 3, "require_rejection_message": True,
                 "on_approve": [upd({"Durum": "Aktif"}), nf("Sahip", "{{Objective}} onaylandı ve aktif.")],
                 "on_reject": [upd({"Durum": "Taslak"}), nf("Sahip", "{{Objective}} reddedildi, notu inceleyip düzenle.")]},
            ]),
        ]),
    ]),
    A("OKR-03", "Objective aktif → KR'lar takipte", updated(O, "Durum"), [
        cond("{{Durum}} = 'Aktif'", [
            find(KR, [w("Objective", "trigger:_id")], [upd({"Takipte": 1})]),
            nf("Katkı Verenler", "{{Objective}} aktif oldu, haftalık check-in'lere katkı verebilirsin."),
        ]),
    ]),
    A("OKR-04", "OKR rengi (her gece)", cron("10 1 * * *"), [
        find(O, [], [
            cond("{{Durum}} = 'Kapandı'", [
                cond("{{İlerleme}} >= 0.7", [upd({"Renk": "Yeşil"})], [
                    cond("{{İlerleme}} >= 0.4", [upd({"Renk": "Sarı"})], [upd({"Renk": "Kırmızı"})])])]),
            cond("{{Durum}} != 'Kapandı'", [
                cond("{{İlerleme Farkı}} >= -0.05", [upd({"Renk": "Yeşil"})], [
                    cond("{{İlerleme Farkı}} >= -0.15", [upd({"Renk": "Sarı"})], [upd({"Renk": "Kırmızı"})])])]),
        ], mx=1000)]),
    A("OKR-05", "Kapanış → puan önerisi, KR takibi biter", updated(O, "Durum"), [
        cond("{{Durum}} = 'Kapanış'", [
            cond("isBlank({{Kapanış Puanı}})", [upd({"Kapanış Puanı": "trigger:İlerleme"})]),
            find(KR, [w("Objective", "trigger:_id")], [upd({"Takipte": 0})]),
            nf("Sahip", "{{Objective}} kapanışta: kapanış puanını teyit et ve retro notunu yaz."),
        ]),
    ]),
    A("OKR-06", "Kapandı → puan kontrolü", updated(O, "Durum"), [
        cond("{{Durum}} = 'Kapandı'", [
            cond("isBlank({{Kapanış Puanı}})", [
                upd({"Durum": "Kapanış"}),
                nf("Sahip", "{{Objective}}: kapatmadan önce kapanış puanını gir."),
            ], [upd({"Kapanış Tarihi": TODAY})]),
        ]),
    ]),
]

# ═══ Key Result'lar ═══════════════════════════════════════════════════════════
KRS = [
    A("KR-01", "KR açıldı → kilometre taşı değerleri, sahip, takip", created(KR), [
        cond("{{KR Tipi}} = 'Kilometre Taşı'",
             [upd({"Başlangıç Değeri": 0, "Hedef Değer": 1, "Güncel Değer": 0})]),
        cond("isBlank({{Güncel Değer}})", [upd({"Güncel Değer": "trigger:Başlangıç Değeri"})]),
        cond("isBlank({{Sahip}})", [upd({"Sahip": "trigger:Objective Sahibi"})]),
        # yalnızca Aktif objective'e eklenen KR takibe girer; diğerlerini OKR-03 aktifleşince açar
        find(O, [w("Key Result'lar", "trigger:_id")], [
            cond("{{Durum}} = 'Aktif'", [upd({"Takipte": 1}, target="trigger")])], mx=1),
    ]),
    A("KR-02", "Güven ≤ 4 → risk bildirimi", updated(KR, "Güven (1–10)"), [
        cond("{{Güven (1–10)}} <= 4", [
            nf("Objective Sahibi", "Risk: {{Key Result}} için güven {{Güven (1–10)}}/10'a düştü."),
            nf("Sahip", "{{Key Result}} riskte görünüyor; engeli check-in'de paylaş."),
        ]),
    ]),
    A("KR-03", "Haftalık check-in hatırlatması (pazartesi 09:00)", cron("0 6 * * 1"), [
        find(KR, [w("Takipte", 1, 0), w("Check-in Gecikti", 1, 0)],   # sayı eşitliği operatörü 0
             [nl("Sahip", "Bu haftanın check-in'i bekleniyor: KR değerini ve güven skorunu gir.")], mx=500)]),
]

# ═══ Check-in'ler ═════════════════════════════════════════════════════════════
CHK = [
    A("CHK-01", "Check-in → KR güncel değer, güven, tarih", created(CI), [
        upd({"Giren": "trigger:Oluşturan"}),
        cond("isBlank({{Tarih}})", [upd({"Tarih": TODAY})]),
        find(KR, [w("Check-in'ler", "trigger:_id")], [
            upd({"Güncel Değer": "trigger:Yeni Değer", "Güven (1–10)": "trigger:Güven (1–10)",
                 "Son Check-in Tarihi": "trigger:Tarih"})], mx=1),
    ]),
    A("CHK-02", "Engel bildirildi → KR sahibi", created(CI), [
        cond("isNotBlank({{Engel / İhtiyaç}})", [
            nf("KR Sahibi", "Engel bildirildi: {{Engel / İhtiyaç}}"),
        ]),
    ]),
]

# ═══ Geri Bildirim ════════════════════════════════════════════════════════════
G = "Geri Bildirim"
GBL = [
    A("GB-01", "Geri bildirim → tarih, gönderen, alıcıya bildirim", created(G), [
        cond("isBlank({{Tarih}})", [upd({"Tarih": TODAY})]),
        upd({"Gönderen (kullanıcı)": "trigger:Oluşturan"}),
        cond("{{Tür}} = 'Geri Bildirim Talebi'", [
            upd({"Durum": "Yanıt Bekliyor"}),
            nf("Kime Hesabı", "{{Geri Bildirim}}: senden geri bildirim isteniyor. {{Mesaj}}"),
        ], [
            upd({"Durum": "Gönderildi"}),
            nf("Kime Hesabı", "{{Geri Bildirim}}: {{Mesaj}}"),
        ]),
    ]),
    A("GB-02", "Talep yanıtlandı → durum, talep edene bildirim", updated(G, "Yanıt"), [
        cond("isNotBlank({{Yanıt}}) and {{Tür}} = 'Geri Bildirim Talebi'", [
            upd({"Durum": "Yanıtlandı"}),
            nf("Kimden Hesabı", "{{Geri Bildirim}}: geri bildirim talebin yanıtlandı. {{Yanıt}}"),
        ]),
    ]),
]

ALL = DNM + KRN + KPI + OKR + KRS + CHK + GBL

if __name__ == "__main__":
    only = sys.argv[1:]
    autos = [a for a in ALL if not only or any(a["name"].startswith(p) for p in only)]
    st = AppState("Performans Yönetimi")
    if not st.get_list_id("Özlük Bilgileri"):
        st.set_list_id("Özlük Bilgileri", IK_CALISAN)
    ab = AutomationBuilder(client(), st)
    ab.build_all(st.app_id, autos)
    print(f"\n{len(autos)} otomasyon")
