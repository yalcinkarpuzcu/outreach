"""
İleri Acoustic — 73 otomasyon (doküman 6.1–6.5, kodlar CRM/PRJ/HSP/URT/STN).

Kurulum: python3 apps/ileri_build_automations.py
Her otomasyon tetikleyici listenin bulunduğu uygulamada kurulur (6.0).

Uygulama notları (API kısıtları):
  • "find_records(Liste; _id = trigger:Bağlantı)" → üst listedeki TERS BAĞLANTI üzerinden
    aranır (ör. Projeler.Teklifler = trigger:_id). İki adım uzaktaki kayıtlar iç içe arama.
  • send_email → aynı alıcılara uygulama içi bildirim (konu + gövde). CRM-13 (dış müşteriye
    e-posta) yöneticiye bildirim olarak kurulur; gerçek e-posta aksiyonu arayüzden eklenmeli.
  • Webhook (CRM-14/15) tetikleyicileri oluşturulur; payload alan eşlemesi ilk test
    mesajından sonra arayüzde tamamlanır.
  • [… – Sx] yer tutucuları: S4 = 5/10 gün, S6 = 50.000 TL / 1.500 USD / 1.500 EUR,
    S11 = varsayılan temsilci (DEFAULT_USER).
"""

DEFAULT_USER = "161973"      # S11 – yurt içi / yurt dışı / EPART / varsayılan temsilci
ESIK_TL, ESIK_USD, ESIK_EUR = 50000, 1500, 1500    # S6
TAKIP_1, TAKIP_2 = 5, 10                            # S4

YON, SAT, IMP, STN_R, OPR, MON = ("Yönetici", "Satış Temsilcisi", "İmalat Planlama",
                                  "Satınalma", "İmalat Şefi / Operatör", "Montaj Ekibi")


# ─── kısa yardımcılar ─────────────────────────────────────────────────────────
def created(lst):
    return {"type": "record_created", "list": lst}


def updated(lst, field=None):
    t = {"type": "record_updated", "list": lst}
    if field:
        t["watch_field"] = field
    return t


def deleted(lst):
    return {"type": "record_deleted", "list": lst}


def timed(lst, date_field, offset):
    return {"type": "time_trigger", "list": lst, "date_field": date_field, "offset": offset}


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


def find(lst, where, actions=None, no_results=None, sort=None, mx=200):
    a = {"type": "find_records", "list": lst, "where": where, "actions": actions or [], "max": mx}
    if no_results:
        a["no_results"] = no_results
    if sort:
        a["sort_by"] = sort
    return a


def w(field, value, op="equals"):
    return {"field": field, "op": op, "value": value}


def create(lst, fields):
    return {"type": "create_record", "list": lst, "fields": fields}


def nf(field, msg):
    return {"type": "notify", "to_field": field, "message": msg}


def nr(roles, msg):
    return {"type": "notify", "to_roles": list(roles), "message": msg}


def email(subject, body, roles=(), fields=()):
    """send_email → aynı alıcılara bildirim (konu + gövde)."""
    out = []
    if roles:
        out.append({"type": "send_email", "to_roles": list(roles), "subject": subject, "body": body})
    for f in fields:
        out.append({"type": "send_email", "to_field": f, "subject": subject, "body": body})
    return out


def gorev(baslik, tur, sorumlu, son, ilgili, oncelik=None):
    f = {"Görev": "formula:" + baslik, "Görev Türü": tur, "Sorumlu": sorumlu,
         "Son Tarih": son, "Durum": "Açık", **ilgili}
    if oncelik:
        f["Öncelik"] = oncelik
    return create("Görevler", f)


def A(code, name, trigger, actions):
    return {"name": f"{code} · {name}", "trigger": trigger, "actions": actions}


TODAY, NOW = "formula:Today()", "formula:Now()"
PLUS = lambda n: f"formula:Today() + {n}"  # noqa: E731


# ═════════════════════════════════════════════════════════════════════════════
# A1 · CRM (16)
# ═════════════════════════════════════════════════════════════════════════════
def _ilk_yanit_gorevi():
    return [
        gorev("Concat('İlk yanıt – ', {{Firma}}, ' / ', {{Talep No}})", "İlk Yanıt",
              "trigger:Sorumlu", PLUS(1), {"İlgili Talep": "trigger:_id"}, "Yüksek"),
        nf("Sorumlu", "Yeni talep {{Talep No}}: {{Firma}} ({{Kaynak}}). 1 iş günü içinde yanıtlayın."),
    ]


def _kisi_eslestir(alan_talep, alan_kisi):
    return find("Kişiler", w(alan_kisi, f"trigger:{alan_talep}"), mx=1, actions=[
        upd({"Yetkili": "loop:_id", "Firma": "loop:Firma", "Sorumlu": "loop:Firma Sorumlusu"},
            target="trigger")])


CRM = [
    A("CRM-01", "Yeni talep – ilk yanıt görevi", created("Talepler"), [
        cond("isBlank({{Talep Tarihi}})", [upd({"Talep Tarihi": NOW})]),
        cond("isBlank({{Durum}})", [upd({"Durum": "Yeni"})]),
        cond("isNotBlank({{Sorumlu}})", _ilk_yanit_gorevi()),
    ]),
    A("CRM-02", "İlk yanıt zamanını yaz", updated("Talepler", "Durum"), [
        cond("{{Durum}} != 'Yeni' and isBlank({{İlk Yanıt Tarihi}})", [
            upd({"İlk Yanıt Tarihi": NOW}),
            find("Görevler", w("İlgili Talep", "trigger:_id"), [
                cond("{{Görev Türü}} = 'İlk Yanıt' and {{Durum}} != 'Tamamlandı'",
                     [upd({"Durum": "Tamamlandı", "Tamamlanma Tarihi": NOW})])]),
        ]),
    ]),
    A("CRM-03", "Yanıtsız talep uyarısı", timed("Talepler", "Talep Tarihi", 1), [
        cond("{{Durum}} = 'Yeni' and isBlank({{İlk Yanıt Tarihi}})", [
            nf("Sorumlu", "{{Talep No}} ({{Firma}}) 24 saattir yanıtsız."),
            nr([YON], "{{Talep No}} ({{Firma}}) 24 saattir yanıtsız."),
        ]),
    ]),
    A("CRM-04", "Talebi projeye dönüştür", updated("Talepler", "Durum"), [
        cond("{{Durum}} = 'Projeye Dönüştü' and isBlank({{Proje}})", [
            cond("isBlank({{Firma}})", [
                upd({"Durum": "Analizde"}),
                nf("Sorumlu", "Projeye dönüştürmek için önce Firma seçin."),
            ], [
                create("Projeler", {
                    "Proje Adı": "formula:Concat({{Firma}}, ' – ', {{Talep No}})",
                    "Firma": "trigger:Firma", "Yetkili": "trigger:Yetkili",
                    "Sorumlu Satış Temsilcisi": "trigger:Sorumlu",
                    "Sistem(ler)": "trigger:İlgilenilen Sistem",
                    "Proje Yeri (Şehir/Ülke)": "formula:Concat({{Ülke}})",
                    "Proje Aşaması": "Analiz", "Kaynak Talep": "trigger:_id",
                    "Notlar": "trigger:Talep İçeriği"}),
                nf("Sorumlu", "{{Talep No}} projeye dönüştürüldü; proje adını ve yerini güncelleyin."),
            ]),
        ]),
    ]),
    A("CRM-05", "Uygun değil nedeni", updated("Talepler", "Durum"), [
        cond("{{Durum}} = 'Uygun Değil' and isBlank({{Uygun Değil Nedeni}})",
             [nf("Sorumlu", "{{Talep No}} için Uygun Değil Nedeni seçin.")]),
    ]),
    A("CRM-06", "Portföy değişikliği", updated("Firmalar", "Satış Temsilcisi"), [
        cond("isNotBlank({{Satış Temsilcisi}})",
             [nf("Satış Temsilcisi", "{{Firma Adı}} portföyünüze atandı.")]),
    ]),
    A("CRM-07a", "Görev atandı", created("Görevler"), [
        cond("isNotBlank({{Sorumlu}})", [nf("Sorumlu", "Size görev atandı: {{Görev}} – son tarih {{Son Tarih}}.")]),
    ]),
    A("CRM-07b", "Görev yeniden atandı", updated("Görevler", "Sorumlu"), [
        cond("isNotBlank({{Sorumlu}})", [nf("Sorumlu", "Size görev atandı: {{Görev}} – son tarih {{Son Tarih}}.")]),
    ]),
    A("CRM-08", "Görev son gün hatırlatması", timed("Görevler", "Son Tarih", -1), [
        cond("{{Durum}} in ('Açık','Devam Ediyor')", [nf("Sorumlu", "Yarın son gün: {{Görev}}.")]),
    ]),
    A("CRM-09", "Görev tamamlandı", updated("Görevler", "Durum"), [
        cond("{{Durum}} = 'Tamamlandı' and isBlank({{Tamamlanma Tarihi}})",
             [upd({"Tamamlanma Tarihi": NOW})]),
    ]),
    A("CRM-10", "Geciken görev", timed("Görevler", "Son Tarih", 1), [
        cond("{{Durum}} in ('Açık','Devam Ediyor')", [
            upd({"Öncelik": "Yüksek"}),
            nf("Sorumlu", "Geciken görev: {{Görev}} ({{Sorumlu}}), son tarih {{Son Tarih}}."),
            nr([YON], "Geciken görev: {{Görev}} ({{Sorumlu}}), son tarih {{Son Tarih}}."),
        ]),
    ]),
    A("CRM-11", "Kanal talebi – eşleştirme ve atama", created("Talepler"), [
        cond("isBlank({{Sorumlu}})", [
            cond("isNotBlank({{Gönderen Telefon}})", [_kisi_eslestir("Gönderen Telefon", "Telefon")]),
            cond("isBlank({{Yetkili}}) and isNotBlank({{Gönderen E-posta}})",
                 [_kisi_eslestir("Gönderen E-posta", "E-posta")]),
            cond("isBlank({{Sorumlu}})", [
                # Atama Kuralları 2–5 (S11): EPART-DOORSON → yurt içi → yurt dışı → varsayılan
                cond("{{İlgilenilen Sistem}} = 'EPART-DOORSON'", [upd({"Sorumlu": DEFAULT_USER})], [
                    cond("{{Ülke}} = 'Türkiye'", [upd({"Sorumlu": DEFAULT_USER})], [
                        cond("isNotBlank({{Ülke}})", [upd({"Sorumlu": DEFAULT_USER})],
                             [upd({"Sorumlu": DEFAULT_USER})])])]),
            ]),
            # Atama aynı çalıştırmada yapıldığı için talep yeniden okunur (güncel Sorumlu ile görev + bildirim)
            find("Talepler", w("Talep No (sayı)", "trigger:Talep No (sayı)", 0), mx=1, actions=[
                gorev("Concat('İlk yanıt – ', {{loop:Firma}}, ' / ', {{loop:Talep No}})", "İlk Yanıt",
                      "loop:Sorumlu", PLUS(1), {"İlgili Talep": "loop:_id"}, "Yüksek"),
                nf("loop:Sorumlu", "Yeni talep {{loop:Talep No}}: {{loop:Firma}} ({{loop:Kaynak}}). "
                                   "1 iş günü içinde yanıtlayın."),
            ]),
        ]),
    ]),
    A("CRM-12", "Mükerrer talep kontrolü", created("Talepler"), [
        cond("isNotBlank({{Gönderen Telefon}}) or isNotBlank({{Gönderen E-posta}})", [
            cond("isNotBlank({{Gönderen Telefon}})", [
                find("Talepler", w("Gönderen Telefon", "trigger:Gönderen Telefon"), sort="Talep Tarihi DESC",
                     mx=5, actions=[
                    cond("{{Talep No (sayı)}} != {{trigger:Talep No (sayı)}} and {{Durum}} in ('Yeni','Analizde')", [
                        upd({"Mükerrer Şüphesi": "true"}, target="trigger"),
                        nf("loop:Sorumlu", "{{Talep No}}, açık {{loop:Talep No}} talebiyle mükerrer olabilir."),
                    ])])]),
            cond("isNotBlank({{Gönderen E-posta}})", [
                find("Talepler", w("Gönderen E-posta", "trigger:Gönderen E-posta"), sort="Talep Tarihi DESC",
                     mx=5, actions=[
                    cond("{{Talep No (sayı)}} != {{trigger:Talep No (sayı)}} and {{Durum}} in ('Yeni','Analizde')", [
                        upd({"Mükerrer Şüphesi": "true"}, target="trigger"),
                        nf("loop:Sorumlu", "{{Talep No}}, açık {{loop:Talep No}} talebiyle mükerrer olabilir."),
                    ])])]),
        ]),
    ]),
    A("CRM-13", "Web formu alındı e-postası", created("Talepler"), [
        cond("{{Kaynak}} = 'Web' and isNotBlank({{Gönderen E-posta}})", email(
            "Talebiniz alındı / We received your request – {{Talep No}}",
            "Sayın {{Gönderen Adı}} ({{Gönderen E-posta}}), talebiniz kayıt altına alınmıştır; satış ekibimiz "
            "en kısa sürede dönüş yapacaktır. / Dear {{Gönderen Adı}}, your request has been recorded; "
            "our sales team will get back to you shortly.", roles=[YON])),
    ]),
    {"name": "CRM-14 · E-postadan talep oluştur", "trigger": {"type": "webhook", "list": None},
     "actions": [create("Talepler", {"Talep Konusu": "E-posta talebi", "Kaynak": "E-posta",
                                     "Talep Tarihi": NOW, "Durum": "Yeni"})]},
    {"name": "CRM-15 · WhatsApp'tan talep oluştur", "trigger": {"type": "webhook", "list": None},
     "actions": [create("Talepler", {"Talep Konusu": "WhatsApp talebi", "Kaynak": "WhatsApp",
                                     "Talep Tarihi": NOW, "Durum": "Yeni"})]},
]

# ═════════════════════════════════════════════════════════════════════════════
# A2 · Proje & Teklif (19)
# ═════════════════════════════════════════════════════════════════════════════
def _gecerli_tek(trig):
    return A(*trig, [
        cond("{{Geçerli mi}} = true", [
            # Döngüdeki kaydın bağlantısına trigger:_id yazılamıyor (API) → Kayıt No yazılır, PRJ-04c bağlar
            find("Teklifler", w("Revizyonlar", "trigger:_id"),
                 [upd({"Geçerli Revizyon Kayıt No": "trigger:Kayıt No (sayı)"})]),
            find("Teklif Revizyonları", w("Teklif", "trigger:Teklif"), [
                cond("{{Kayıt No (sayı)}} != {{trigger:Kayıt No (sayı)}} and {{Geçerli mi}} = true",
                     [upd({"Geçerli mi": "false"})])]),
        ]),
    ])


def _takip_hatirlat(code, gun, oncelik, ek_rol):
    msg = ("{{Teklif No}} ({{Firma}}) " + str(gun) + " gündür takip edilmedi." if not ek_rol else
           "{{Teklif No}} ({{Firma}}, {{Geçerli Tutar}} {{Para Birimi}}) " + str(gun) + " gündür takipsiz.")
    acts = [
        gorev("Concat('Teklif takibi – bu müşteri ne oldu? ', {{Firma}}, ' / ', {{Teklif Başlığı}})",
              "Teklif Takibi", "trigger:Sorumlu Satış Temsilcisi", PLUS(1), {"İlgili Teklif": "trigger:_id"},
              oncelik),
        nf("Sorumlu Satış Temsilcisi", msg),
    ]
    if ek_rol:
        acts.append(nr([YON], msg))
    name = "5 günlük takip hatırlatması" if not ek_rol else "Kademeli hatırlatma (10 gün)"
    return A(code, name, timed("Teklifler", "Son Gönderim Tarihi", gun), [
        cond("{{Teklif Durumu}} = 'Gönderildi' and (isBlank({{Son Takip Tarihi}}) or "
             "{{Son Takip Tarihi}} < {{Son Gönderim Tarihi}})", acts)])


PRJ = [
    A("PRJ-01", "Yeni proje", created("Projeler"), [
        cond("isBlank({{Proje Aşaması}})", [upd({"Proje Aşaması": "Analiz"})]),
        nf("Sorumlu Satış Temsilcisi", "Yeni proje: {{Proje No}} {{Proje Adı}} ({{Firma}})."),
        cond("isBlank({{Arşiv Linki}})", [
            gorev("Concat('Drive arşiv klasörünü açıp linki girin – ', {{Proje Adı}})", "Genel",
                  "trigger:Sorumlu Satış Temsilcisi", PLUS(2), {"İlgili Proje": "trigger:_id"})]),
    ]),
    A("PRJ-02", "Teklif açıldı – ilk revizyon", created("Teklifler"), [
        cond("isBlank({{Teklif Durumu}})", [upd({"Teklif Durumu": "Hazırlanıyor"})]),
        create("Teklif Revizyonları", {
            "Revizyon Kodu": "formula:Concat({{Teklif No}}, '-R0')", "Teklif": "trigger:_id",
            "Revizyon No": "0", "Geçerli mi": "true", "Para Birimi": "USD", "Hazırlayan": "trigger:Oluşturan"}),
        find("Projeler", w("Teklifler", "trigger:_id"), [
            cond("{{Proje Aşaması}} = 'Analiz'", [upd({"Proje Aşaması": "Teklif"})])]),
    ]),
    A("PRJ-03", "Revizyon numarası", created("Teklif Revizyonları"), [
        cond("isBlank({{Revizyon No}})", [
            cond("isBlank({{Hazırlayan}})", [upd({"Hazırlayan": "trigger:Oluşturan"})]),
            find("Teklifler", w("Revizyonlar", "trigger:_id"), [
                upd({"Revizyon No": "formula:{{loop:Revizyon Sayısı}} - 1",
                     "Revizyon Kodu": "formula:Concat({{loop:Teklif No}}, '-R', {{loop:Revizyon Sayısı}} - 1)"},
                    target="trigger")]),
        ]),
    ]),
    _gecerli_tek(("PRJ-04a", "Tek geçerli revizyon (yeni)", created("Teklif Revizyonları"))),
    _gecerli_tek(("PRJ-04b", "Tek geçerli revizyon (işaretlendi)", updated("Teklif Revizyonları", "Geçerli mi"))),
    A("PRJ-04c", "Geçerli revizyon bağlantısını yaz (PRJ-04 yardımcı)",
      updated("Teklifler", "Geçerli Revizyon Kayıt No"), [
        cond("isNotBlank({{Geçerli Revizyon Kayıt No}})", [
            find("Teklif Revizyonları", w("Teklif", "trigger:_id"), [
                cond("{{Kayıt No (sayı)}} = {{trigger:Geçerli Revizyon Kayıt No}}",
                     [upd({"Geçerli Revizyon": "loop:_id"}, target="trigger")])])]),
    ]),
    A("PRJ-05", "Teklif gönderildi", updated("Teklifler", "Teklif Durumu"), [
        cond("{{Teklif Durumu}} = 'Gönderildi'", [
            cond("isBlank({{Gönderim Tarihi}})", [upd({"Gönderim Tarihi": TODAY})]),
            upd({"Son Gönderim Tarihi": TODAY}),
            find("Teklif Revizyonları", w("Teklif", "trigger:_id"), [
                cond("{{Geçerli mi}} = true",
                     [upd({"Gönderilen Tutar": "loop:Teklif Tutarı", "Gönderim Tarihi": TODAY})])]),
            find("Projeler", w("Teklifler", "trigger:_id"), [
                upd({"Para Birimi": "trigger:Para Birimi"}),
                cond("{{Proje Aşaması}} in ('Analiz','Teklif')", [upd({"Proje Aşaması": "Takipte"})])]),
        ]),
    ]),
    _takip_hatirlat("PRJ-06", TAKIP_1, "Orta", False),
    _takip_hatirlat("PRJ-07", TAKIP_2, "Yüksek", True),
    A("PRJ-08", "Takip sonucunu işle", created("Teklif Takipleri"), [
        cond("isBlank({{Yapan}})", [upd({"Yapan": "trigger:Oluşturan"})]),
        cond("isBlank({{Takip Tarihi}})", [upd({"Takip Tarihi": TODAY})]),
        find("Teklifler", w("Takipler", "trigger:_id"),
             [upd({"Son Takip Tarihi": "formula:Coalesce({{trigger:Takip Tarihi}}, Today())"})]),
        cond("{{Sonuç}} = 'Revize İstedi'", [
            find("Teklifler", w("Takipler", "trigger:_id"), [upd({"Teklif Durumu": "Revizyonda"})]),
            gorev("Concat('Revizyon hazırla – ', {{Teklif}})", "Revizyon", "trigger:Yapan", PLUS(2),
                  {"İlgili Teklif": "trigger:Teklif"}),
        ]),
        cond("{{Sonuç}} = 'Onay Verecek'", [
            find("Teklifler", w("Takipler", "trigger:_id"), [
                find("Projeler", w("Teklifler", "loop:_id"), [upd({"Proje Aşaması": "Potansiyel"})])])]),
        cond("{{Sonuç}} = 'Reddetti'", [
            find("Teklifler", w("Takipler", "trigger:_id"), [upd({"Teklif Durumu": "Kaybedildi"})])]),
        cond("{{Sonuç}} = 'Ertelendi'", [
            find("Teklifler", w("Takipler", "trigger:_id"), [
                find("Projeler", w("Teklifler", "loop:_id"), [
                    upd({"Proje Aşaması": "Ertelendi", "Ertelenme Tarihi": "trigger:Sonraki Takip Tarihi"})])])]),
    ]),
    A("PRJ-09", "Planlı takip günü", timed("Teklif Takipleri", "Sonraki Takip Tarihi", 0), [
        cond("{{Sonuç}} != 'Ertelendi' and {{Teklif Durumu}} in ('Gönderildi','Revizyonda')", [
            gorev("Concat('Planlı takip – ', {{Teklif}})", "Teklif Takibi", "trigger:Yapan", TODAY,
                  {"İlgili Teklif": "trigger:Teklif"}),
            nf("Yapan", "Bugün planlı takip: {{Teklif}}."),
        ]),
    ]),
    A("PRJ-10", "Ertelenen proje geri gelir", timed("Projeler", "Ertelenme Tarihi", 0), [
        cond("{{Proje Aşaması}} = 'Ertelendi'", [
            upd({"Proje Aşaması": "Takipte"}),
            gorev("Concat('Ertelenen proje yeniden aranacak – ', {{Firma}}, ' / ', {{Proje Adı}})",
                  "Teklif Takibi", "trigger:Sorumlu Satış Temsilcisi", TODAY, {"İlgili Proje": "trigger:_id"}),
            nf("Sorumlu Satış Temsilcisi", "Ertelenen proje bugün aranacak: {{Proje Adı}}."),
        ]),
    ]),
    A("PRJ-11", "Potansiyel iş bildirimi", updated("Projeler", "Proje Aşaması"), [
        cond("{{Proje Aşaması}} = 'Potansiyel'", [
            *email("Potansiyel iş: {{Proje Adı}} – {{Firma}}",
                   "Proje No {{Proje No}} · Firma {{Firma}} · Yer {{Proje Yeri (Şehir/Ülke)}} · Sistem "
                   "{{Sistem(ler)}} · Toplam Panel {{Toplam Panel}} · Toplam m² {{Toplam m²}} · Tutar "
                   "{{Geçerli Teklif Tutarı}} {{Para Birimi}} · Beklenen onay {{Beklenen Onay Tarihi}} · "
                   "Hedef teslim {{Hedef Teslim Tarihi}} · Arşiv {{Arşiv Linki}} · Sorumlu "
                   "{{Sorumlu Satış Temsilcisi}}. Özel üretim malzemeleri için ön sipariş gerekiyorsa "
                   "Satınalma Talebi (Kaynak: Potansiyel İş Ön Siparişi) açın.",
                   roles=[IMP, STN_R], fields=["Sorumlu Satış Temsilcisi"]),
            nr([IMP, STN_R], "Potansiyel iş: {{Proje Adı}} ({{Firma}})."),
            cond("isBlank({{Beklenen Onay Tarihi}})", [
                nf("Sorumlu Satış Temsilcisi", "Planlama için Beklenen Onay Tarihi'ni girin – {{Proje Adı}}.")]),
        ]),
    ]),
    A("PRJ-12", "Teklif kazanıldı – sözleşme aç", updated("Teklifler", "Teklif Durumu"), [
        cond("{{Teklif Durumu}} = 'Kazanıldı'", [
            create("Sözleşmeler", {
                "Sözleşme Başlığı": "formula:Concat({{Firma}}, ' – ', {{Teklif No}})",
                "Proje": "trigger:Proje", "Teklif": "trigger:_id", "Esas Revizyon": "trigger:Geçerli Revizyon",
                "Sözleşme Bedeli": "trigger:Geçerli Tutar", "Teslim Tarihi": "trigger:Hedef Teslim Tarihi",
                "İmza Durumu": "Hazırlanıyor"}),
            gorev("Concat('Sözleşmeyi hazırlayıp müşteriye gönderin – ', {{Firma}})", "Sözleşme",
                  "trigger:Sorumlu Satış Temsilcisi", PLUS(2), {"İlgili Teklif": "trigger:_id"}),
            nf("Sorumlu Satış Temsilcisi", "Teklif kazanıldı: {{Teklif No}} – {{Firma}}, {{Geçerli Tutar}} "
                                           "{{Para Birimi}}. Sözleşme kaydı açıldı."),
            nr([YON], "Teklif kazanıldı: {{Teklif No}} – {{Firma}}, {{Geçerli Tutar}} {{Para Birimi}}. "
                      "Sözleşme kaydı açıldı."),
        ]),
    ]),
    A("PRJ-13", "Teklif kaybedildi / iptal", updated("Teklifler", "Teklif Durumu"), [
        cond("{{Teklif Durumu}} in ('Kaybedildi','İptal')", [
            find("Projeler", w("Teklifler", "trigger:_id"), [
                cond("{{Açık Teklif Sayısı}} = 0 and {{Kazanılan Teklif Sayısı}} = 0", [
                    cond("{{trigger:Teklif Durumu}} = 'Kaybedildi'",
                         [upd({"Proje Aşaması": "Kaybedildi", "Kapanış Tarihi": TODAY})],
                         [upd({"Proje Aşaması": "İptal", "Kapanış Tarihi": TODAY})]),
                    cond("isBlank({{Kayıp Nedeni}})", [
                        gorev("Concat('Kayıp nedeni ve rakip bilgisini girin – ', {{loop:Proje Adı}})", "Genel",
                              "trigger:Sorumlu Satış Temsilcisi", PLUS(1), {"İlgili Proje": "loop:_id"}),
                        nf("Sorumlu Satış Temsilcisi", "{{loop:Proje Adı}} kapatıldı; kayıp nedenini girin."),
                    ]),
                ])]),
        ]),
    ]),
    A("PRJ-14", "Sözleşme müşteriye gönderildi", updated("Sözleşmeler", "İmza Durumu"), [
        cond("{{İmza Durumu}} = 'Müşteride'", [upd({"Müşteriye Gönderim Tarihi": TODAY})]),
    ]),
    A("PRJ-15", "İmza takibi (3 gün)", timed("Sözleşmeler", "Müşteriye Gönderim Tarihi", 3), [
        cond("{{İmza Durumu}} = 'Müşteride'",
             [nf("Sorumlu Satış Temsilcisi", "{{Sözleşme No}} ({{Firma}}) 3 gündür imza bekliyor.")]),
    ]),
    A("PRJ-16", "Sözleşme yönetici onayı", updated("Sözleşmeler", "İmza Durumu"), [
        cond("{{İmza Durumu}} = 'İmzalandı'", [
            cond("isBlank({{Sözleşme Dosyası}})", [
                upd({"İmza Durumu": "Müşteride"}),
                nf("Sorumlu Satış Temsilcisi", "İmzalı sözleşme dosyasını yükleyin."),
            ], [
                {"type": "approval", "title": "Sözleşme onayı",
                 "subtitle": "{{Sözleşme No}} – {{Firma}} · {{Sözleşme Bedeli}} {{Para Birimi}} · teslim "
                             "{{Teslim Tarihi}} · montaj: {{Montaj Var mı}}",
                 "approver": f"roles:{YON}", "timeout_days": 2, "require_rejection_message": True,
                 "on_approve": [upd({"İmza Durumu": "Onaylandı", "Onay Tarihi": TODAY})],
                 "on_reject": [upd({"İmza Durumu": "Hazırlanıyor"}),
                               nf("Sorumlu Satış Temsilcisi",
                                  "Sözleşme reddedildi: {{Sözleşme No}}. Ret gerekçesi onay kaydında.")]},
            ]),
        ]),
    ]),
    A("PRJ-17", "Sözleşme onaylandı – üretime aktar", updated("Sözleşmeler", "İmza Durumu"), [
        cond("{{İmza Durumu}} = 'Onaylandı'", [
            find("Projeler", w("Sözleşmeler", "trigger:_id"), [
                upd({"Proje Aşaması": "Sözleşmeli"}),
                find("Firmalar", w("Projeler", "loop:_id"), [
                    cond("isBlank({{Müşteri Durumu}}) or {{Müşteri Durumu}} in ('Aday','Pasif')",
                         [upd({"Müşteri Durumu": "Aktif"})])]),
            ]),
            create("Üretim Planları", {
                "Plan Adı": "formula:Concat({{Sözleşme Başlığı}})", "Sözleşme": "trigger:_id",
                "Proje": "trigger:Proje", "Esas Revizyon": "trigger:Esas Revizyon",
                "Satış Sorumlusu": "trigger:Sorumlu Satış Temsilcisi", "Durum": "Planlandı",
                "Hedef Bitiş Tarihi": "trigger:Teslim Tarihi",
                "Teknik Resim / Arşiv Linki": "trigger:Proje Arşiv Linki"}),
            *email("Sözleşme onaylandı – {{Proje}} ({{Firma}})",
                   "Sözleşme {{Sözleşme No}} · {{Sözleşme Bedeli}} {{Para Birimi}} · Teslim {{Teslim Tarihi}} · "
                   "Montaj {{Montaj Var mı}} · Esas Revizyon {{Esas Revizyon}} · Arşiv {{Proje Arşiv Linki}}. "
                   "Üretim planı açıldı; imalat talimatı plan kaydına girilecektir. Eksik malzemeleri önceden "
                   "kontrol edin.", roles=[IMP, STN_R, YON], fields=["Sorumlu Satış Temsilcisi"]),
        ]),
    ]),
    A("PRJ-18", "Teslime 7 gün kaldı", timed("Sözleşmeler", "Teslim Tarihi", -7), [
        cond("{{Proje Aşaması}} in ('Sözleşmeli','Üretimde')", [
            nf("Sorumlu Satış Temsilcisi", "{{Proje}} ({{Firma}}) teslimine 7 gün kaldı; proje hâlâ {{Proje Aşaması}}."),
            nr([IMP], "{{Proje}} ({{Firma}}) teslimine 7 gün kaldı; proje hâlâ {{Proje Aşaması}}."),
        ]),
    ]),
]

# ═════════════════════════════════════════════════════════════════════════════
# A3 · Teknik Hesaplama (8)
# ═════════════════════════════════════════════════════════════════════════════
def _receteyi_uret():
    return find("Reçete Şablonu", w("Sistem", "trigger:Sistem"), sort="Sıra ASC", actions=[
        cond("{{Aktif mi}} = true", [create("Reçete Kalemleri", {
            "Kalem": "loop:Şablon Kodu", "Duvar Kalemi": "trigger:_id", "Kaynak": "Şablon",
            "Reçete Şablonu": "loop:_id", "Liste Türü": "loop:Liste Türü",
            "Malzeme": "loop:Malzeme", "İstasyon": "loop:İstasyon"})])],
        no_results=[nr([IMP], "{{Sistem}} için reçete şablonu tanımlı değil; {{Duvar No}} no'lu duvarın "
                              "reçetesi üretilemedi.")])


DUVAR_KOPYA = ["Duvar", "Duvar No", "Sistem", "Uzunluk L (cm)", "Yükseklik H (cm)", "Sistem Adedi",
               "Makara Düzeni", "Makara Tipi", "Ray Tipi", "Akıstik", "Yüzey", "Yüzey Kodu/Adı",
               "Yüzey Kalınlığı (mm)", "Yüzey İşlemleri", "Alüminyum Boya Tipi", "Alüminyum RAL Kodu",
               "Ray Boya Tipi", "Ray RAL Kodu",
               *[f"{k} {s}" for k in ("Tek Kanat Kapı", "Çift Kanat Kapı", "İnce Kapı TK", "İnce Kapı ÇK")
                 for s in ("Adedi", "En (cm)", "Boy (cm)")],
               "Teleskopik Panel", "Paspileta", "Sabit Parça", "Ambalaj", "Notlar"]


def _manuel_kalem(miktar):
    return create("Reçete Kalemleri", {
        "Kalem": "formula:Concat('Düzeltme: ', {{Açıklama / Gerekçe}})",
        "Duvar Kalemi": "trigger:Duvar Kalemi", "Kaynak": "Manuel Düzeltme", "Reçete Düzeltmesi": "trigger:_id",
        "Liste Türü": "trigger:Liste Türü", "Malzeme": "trigger:Malzeme", "İstasyon": "trigger:İstasyon",
        "Manuel Miktar": miktar})


HSP = [
    A("HSP-01", "Duvar kalemi – reçeteyi üret", created("Duvar Kalemleri"), [
        cond("isNotBlank({{Sistem}})", [_receteyi_uret()]),
    ]),
    A("HSP-02", "Sistem değişti – reçeteyi yenile", updated("Duvar Kalemleri", "Sistem"), [
        find("Reçete Kalemleri", w("Duvar Kalemi", "trigger:_id"),
             [cond("{{Kaynak}} = 'Şablon'", [{"type": "delete_record"}])]),
        cond("isNotBlank({{Sistem}})", [_receteyi_uret()]),
    ]),
    A("HSP-03", "Duvar silindi – reçeteyi sil", deleted("Duvar Kalemleri"), [
        find("Reçete Kalemleri", w("Duvar Kalemi", "trigger:_id"), [{"type": "delete_record"}]),
        find("Reçete Düzeltmeleri", w("Duvar Kalemi", "trigger:_id"), [{"type": "delete_record"}]),
    ]),
    A("HSP-04", "Yeni revizyona duvarları kopyala", updated("Teklif Revizyonları", "Revizyon No"), [
        cond("{{Revizyon No}} >= 1 and {{Duvar Kalemi Sayısı}} = 0", [
            find("Teklif Revizyonları", w("Teklif", "trigger:Teklif"), [
                cond("{{Revizyon No}} = {{trigger:Revizyon No}} - 1", [
                    find("Duvar Kalemleri", w("Teklif Revizyonu", "loop:_id"), sort="Duvar No ASC", actions=[
                        create("Duvar Kalemleri", {"Teklif Revizyonu": "trigger:_id",
                                                   **{f: f"loop:{f}" for f in DUVAR_KOPYA}})])])]),
            nf("Hazırlayan", "{{Revizyon Kodu}} oluşturuldu; önceki revizyonun duvarları kopyalandı, "
                             "değişiklikleri girebilirsiniz."),
        ]),
    ]),
    A("HSP-05", "Manuel düzeltme – reçeteye ekle", created("Reçete Düzeltmeleri"), [
        cond("isBlank({{Giren}})", [upd({"Giren": "trigger:Oluşturan", "Tarih": NOW})]),
        cond("{{Düzeltme Türü}} in ('İlave Kalem','Eksiltme') and isNotBlank({{Malzeme}})", [
            cond("{{Düzeltme Türü}} = 'İlave Kalem'", [_manuel_kalem("trigger:Adet")],
                 [_manuel_kalem("formula:0 - {{Adet}}")]),
            nr([IMP, STN_R], "Manuel reçete düzeltmesi: {{Duvar Kalemi}} – {{Düzeltme Türü}} {{Adet}} × "
                             "{{Malzeme}}. Gerekçe: {{Açıklama / Gerekçe}}."),
        ]),
    ]),
    A("HSP-06", "Özellik değişikliği (renk vb.)", created("Reçete Düzeltmeleri"), [
        cond("{{Düzeltme Türü}} = 'Özellik Değişikliği'", [
            cond("isNotBlank({{Üretim Planı}})", [
                find("İş Emirleri", w("Üretim Planı", "trigger:Üretim Planı"), [
                    upd({"Not": "formula:Concat({{loop:Not}}, ' | Düzeltme: ', {{Açıklama / Gerekçe}})"})])]),
            nr([IMP, OPR], "Özellik değişikliği: {{Duvar Kalemi}} – {{Açıklama / Gerekçe}}."),
        ]),
    ]),
    A("HSP-07", "Fiyat parametresi değişti", updated("Hesap Parametreleri", "Değer"), [
        upd({"Son Güncelleme": NOW}),
        nr([YON, SAT], "{{Parametre}} ({{Parametre Kodu}}) yeni değer: {{Değer}} {{Para Birimi}}/{{Birim}}. "
                       "Gönderilmiş tekliflerin Gönderilen Tutarı değişmez; hazırlanan teklifler yeni değerle "
                       "hesaplanır."),
    ]),
    A("HSP-08", "Fiyat geçerliliği bitiyor", timed("Hesap Parametreleri", "Geçerlilik Tarihi", -7), [
        cond("isNotBlank({{Geçerlilik Tarihi}})",
             [nr([YON], "{{Parametre}} fiyatının geçerliliği 7 gün içinde bitiyor ({{Geçerlilik Tarihi}}).")]),
    ]),
]

# ═════════════════════════════════════════════════════════════════════════════
# A4 · Planlama & Üretim (16)
# ═════════════════════════════════════════════════════════════════════════════
def _sonraki_asama(grup):
    return find("İş Emirleri", w("Üretim Planı", "trigger:Üretim Planı"), [
        cond(f"{{{{Aşama Grubu}}}} = '{grup}' and {{{{Durum}}}} = 'Bekliyor'", [
            upd({"Durum": "Hazır"}),
            nf("loop:İstasyon Sorumlusu", "{{Üretim Planı}} [{{İş Rengi}}] istasyonunuzda hazır."),
        ])])


def _plan_gorevini_kapat(tur):
    return find("Görevler", w("İlgili Üretim Planı", "trigger:_id"),
                [cond(f"{{{{Görev Türü}}}} = '{tur}'", [upd({"Durum": "Tamamlandı"})])])


def _montaj_gorevi():
    return [gorev("Concat('Montaj – ', {{Plan Adı}}, ' (', {{Proje Yeri}}, ')')", "Montaj",
                  "trigger:Montaj Sorumlusu", "trigger:Montaj Tarihi", {"İlgili Üretim Planı": "trigger:_id"}),
            nf("Montaj Sorumlusu", "Montaj atandı: {{Plan Adı}}, {{Proje Yeri}}, {{Montaj Tarihi}}.")]


URT = [
    A("URT-01", "Yeni üretim planı", created("Üretim Planları"), [
        gorev("Concat('İmalat talimatını hazırla – ', {{Plan Adı}})", "İmalat Talimatı",
              "trigger:Satış Sorumlusu", PLUS(2), {"İlgili Üretim Planı": "trigger:_id"}),
        nr([IMP], "Yeni üretim planı {{Plan No}} – {{Proje}} ({{Firma}}), hedef {{Hedef Bitiş Tarihi}}. "
                  "İmalat sorumlusu, iş rengi ve başlangıç tarihini girin."),
    ]),
    A("URT-02", "İmalata sunuldu – iş emirleri ve resmi bildirim", updated("Üretim Planları", "Durum"), [
        cond("{{Durum}} = 'İmalata Sunuldu'", [
            cond("isBlank({{İmalat Talimatı}}) or isBlank({{İş Rengi}}) or isBlank({{İmalat Sorumlusu}}) or "
                 "isBlank({{Başlangıç Tarihi}})", [
                upd({"Durum": "Planlandı"}),
                nf("Satış Sorumlusu", "İmalata sunmak için İmalat Talimatı, İş Rengi, İmalat Sorumlusu ve "
                                      "Başlangıç Tarihi zorunludur."),
            ], [
                upd({"İmalata Sunma Tarihi": TODAY}),
                find("İstasyonlar", w("İstasyon Adı", None, "is_not_blank"), sort="Sıra ASC", actions=[
                    cond("{{Aktif mi}} = true and {{Aşama Grubu}} = 'Hazırlık'", [
                        create("İş Emirleri", {"İş Emri": "loop:İstasyon Adı", "Üretim Planı": "trigger:_id",
                                               "İstasyon": "loop:_id", "Durum": "Hazır",
                                               "Planlanan Tarih": "trigger:Başlangıç Tarihi"})], [
                      cond("{{Aktif mi}} = true", [
                        create("İş Emirleri", {"İş Emri": "loop:İstasyon Adı", "Üretim Planı": "trigger:_id",
                                               "İstasyon": "loop:_id", "Durum": "Bekliyor",
                                               "Planlanan Tarih": "trigger:Başlangıç Tarihi"})])])]),
                find("Projeler", w("Üretim Planları", "trigger:_id"), [upd({"Proje Aşaması": "Üretimde"})]),
                _plan_gorevini_kapat("İmalat Talimatı"),
                *email("İMALAT BAŞLADI – {{Plan No}} {{Proje}} [{{İş Rengi}}]",
                       "Firma {{Firma}} · Yer {{Proje Yeri}} · {{Başlangıç Tarihi}} – {{Hedef Bitiş Tarihi}} "
                       "({{İş Günü Sayısı}} iş günü) · Panel {{Toplam Panel}} / Teleskop {{Toplam Teleskop}} / "
                       "Kapı {{Toplam Kapı}} · İş rengi {{İş Rengi}} · Montaj {{Montaj Var mı}} · Teknik resim "
                       "{{Teknik Resim / Arşiv Linki}} · İMALAT TALİMATI: {{İmalat Talimatı}}",
                       roles=[IMP, STN_R, OPR, YON], fields=["Satış Sorumlusu", "İmalat Sorumlusu"]),
            ]),
        ]),
    ]),
    A("URT-03", "Planlanmış ama sunulmamış plan", timed("Üretim Planları", "Oluşturulma Tarihi", 3), [
        cond("{{Durum}} = 'Planlandı'", [
            nr([IMP], "{{Plan No}} ({{Proje}}) 3 gündür imalata sunulmadı."),
            nf("Satış Sorumlusu", "{{Plan No}} ({{Proje}}) 3 gündür imalata sunulmadı."),
        ]),
    ]),
    A("URT-04", "Üretime alındı", updated("Üretim Planları", "Durum"), [
        cond("{{Durum}} = 'Üretimde' and isBlank({{İmalata Alınma Tarihi}})",
             [upd({"İmalata Alınma Tarihi": TODAY})]),
    ]),
    A("URT-05", "İş emri başladı", updated("İş Emirleri", "Durum"), [
        cond("{{Durum}} = 'Devam Ediyor'", [
            upd({"Başlama Zamanı": NOW}),
            cond("isBlank({{Operatör}})", [upd({"Operatör": "trigger:Son Değiştiren"})]),
            find("Üretim Planları", w("İş Emirleri", "trigger:_id"), [
                cond("{{Durum}} = 'İmalata Sunuldu'", [upd({"Durum": "Üretimde"})])]),
        ]),
    ]),
    A("URT-06", "İş emri bitti – sıradaki aşamayı aç", updated("İş Emirleri", "Durum"), [
        cond("{{Durum}} in ('Tamamlandı','Gerekmiyor')", [
            cond("{{Durum}} = 'Tamamlandı'", [upd({"Tamamlanma Zamanı": NOW})]),
            find("Üretim Planları", w("İş Emirleri", "trigger:_id"), [
                cond("{{Açık İş Emri Sayısı}} = 0", [upd({"Durum": "Kalite Kontrol"})], [
                    cond("{{trigger:Aşama Grubu}} = 'Hazırlık' and {{Açık Hazırlık İş Emri}} = 0",
                         [_sonraki_asama("Toplama")], [
                        cond("{{trigger:Aşama Grubu}} = 'Toplama' and {{Açık Toplama İş Emri}} = 0",
                             [_sonraki_asama("Paketleme")])])]),
            ]),
            nr([IMP], "{{İstasyon}} {{Durum}} – {{Üretim Planı}}."),
        ]),
    ]),
    A("URT-07", "Kalite kontrol", updated("Üretim Planları", "Durum"), [
        cond("{{Durum}} = 'Kalite Kontrol'", [
            gorev("Concat('Kalite kontrol ve sevke hazırlık – ', {{Plan No}})", "Kalite",
                  "trigger:İmalat Sorumlusu", PLUS(1), {"İlgili Üretim Planı": "trigger:_id"}),
            nf("İmalat Sorumlusu", "{{Plan No}} tüm istasyonları tamamladı; kalite kontrolü yapın."),
        ]),
    ]),
    A("URT-08", "Sevke hazır", updated("Üretim Planları", "Durum"), [
        cond("{{Durum}} = 'Sevke Hazır'", [
            cond("{{Tamamlanma (%)}} < 100", [
                upd({"Durum": "Kalite Kontrol"}),
                nf("İmalat Sorumlusu", "Biten adetler toplamla eşleşmiyor ({{Tamamlanma (%)}}); sevke hazır "
                                       "yapılamaz."),
            ], [
                _plan_gorevini_kapat("Kalite"),
                gorev("Concat('Sevkiyatı planla – ', {{Plan Adı}})", "Sevkiyat", "trigger:Satış Sorumlusu",
                      PLUS(1), {"İlgili Üretim Planı": "trigger:_id"}),
                nf("Satış Sorumlusu", "Sevke hazır: {{Proje}} ({{Firma}}). Sevkiyat tarihini planlayın."),
                nr([YON], "Sevke hazır: {{Proje}} ({{Firma}}). Sevkiyat tarihini planlayın."),
            ]),
        ]),
    ]),
    A("URT-09", "Sevk edildi", updated("Üretim Planları", "Durum"), [
        cond("{{Durum}} = 'Sevk Edildi'", [
            cond("isBlank({{Sevk Tarihi}})", [upd({"Sevk Tarihi": TODAY})]),
            find("Projeler", w("Üretim Planları", "trigger:_id"), [upd({"Proje Aşaması": "Sevk/Montaj"})]),
            _plan_gorevini_kapat("Sevkiyat"),
            *email("Sevk edildi – {{Proje}} ({{Firma}})",
                   "Plan {{Plan No}} · Sevk {{Sevk Tarihi}} · Yer {{Proje Yeri}} · Panel {{Toplam Panel}} / Kapı "
                   "{{Toplam Kapı}} · Montaj {{Montaj Var mı}}", roles=[YON], fields=["Satış Sorumlusu"]),
            cond("{{Montaj Var mı}} = true", [upd({"Durum": "Montaj Bekliyor"})], [upd({"Durum": "Montaj Yok"})]),
        ]),
    ]),
    A("URT-10a", "Montaj planlama", updated("Üretim Planları", "Durum"), [
        cond("{{Durum}} = 'Montaj Bekliyor'", [
            cond("isBlank({{Montaj Sorumlusu}}) or isBlank({{Montaj Tarihi}})", [
                nr([MON, IMP], "{{Plan Adı}} için Montaj Sorumlusu ve Montaj Tarihi atanmalı.")],
                _montaj_gorevi()),
        ]),
    ]),
    A("URT-10b", "Montaj sorumlusu atandı", updated("Üretim Planları", "Montaj Sorumlusu"), [
        cond("{{Durum}} = 'Montaj Bekliyor' and isNotBlank({{Montaj Tarihi}}) and isNotBlank({{Montaj Sorumlusu}})", [
            find("Görevler", [w("İlgili Üretim Planı", "trigger:_id"), w("Görev", "Montaj –", "contains")],
                 no_results=_montaj_gorevi()),
        ]),
    ]),
    A("URT-11", "Montaj günü hatırlatması", timed("Üretim Planları", "Montaj Tarihi", -1), [
        cond("{{Durum}} = 'Montaj Bekliyor'", [
            nf("Montaj Sorumlusu", "Yarın montaj: {{Plan Adı}} ({{Proje Yeri}})."),
            nf("Satış Sorumlusu", "Yarın montaj: {{Plan Adı}} ({{Proje Yeri}})."),
        ]),
    ]),
    A("URT-12", "Plan kapandı – proje tamamlandı", updated("Üretim Planları", "Durum"), [
        cond("{{Durum}} in ('Montaj Tamamlandı','Montaj Yok')", [
            find("Görevler", w("İlgili Üretim Planı", "trigger:_id"), [
                cond("{{Durum}} in ('Açık','Devam Ediyor')", [upd({"Durum": "Tamamlandı"})])]),
            find("Projeler", w("Üretim Planları", "trigger:_id"), [
                cond("{{Açık Üretim Planı Sayısı}} = 0",
                     [upd({"Proje Aşaması": "Tamamlandı", "Kapanış Tarihi": TODAY})])]),
            nf("Satış Sorumlusu", "{{Proje}} ({{Firma}}) tamamlandı; fatura ve tahsilat sürecini başlatın."),
            nr([YON], "{{Proje}} ({{Firma}}) tamamlandı; fatura ve tahsilat sürecini başlatın."),
        ]),
    ]),
    A("URT-13", "Termin riski", timed("Üretim Planları", "Hedef Bitiş Tarihi", -2), [
        cond("{{Durum}} in ('İmalata Sunuldu','Üretimde','Kalite Kontrol') and {{Tamamlanma (%)}} < 80", [
            nf("İmalat Sorumlusu", "Termin riski: {{Plan No}} % {{Tamamlanma (%)}} tamam, hedef {{Hedef Bitiş Tarihi}}."),
            nf("Satış Sorumlusu", "Termin riski: {{Plan No}} % {{Tamamlanma (%)}} tamam, hedef {{Hedef Bitiş Tarihi}}."),
            nr([IMP], "Termin riski: {{Plan No}} % {{Tamamlanma (%)}} tamam, hedef {{Hedef Bitiş Tarihi}}."),
        ]),
    ]),
    A("URT-14", "Termin geçti", timed("Üretim Planları", "Hedef Bitiş Tarihi", 1), [
        cond("{{Durum}} in ('Planlandı','İmalata Sunuldu','Üretimde','Kalite Kontrol','Sevke Hazır')", [
            nr([YON, IMP], "Termin geçti: {{Plan No}} – {{Proje}}, hedef {{Hedef Bitiş Tarihi}}, durum {{Durum}}."),
            nf("Satış Sorumlusu", "Termin geçti: {{Plan No}} – {{Proje}}, hedef {{Hedef Bitiş Tarihi}}, durum {{Durum}}."),
        ]),
    ]),
    A("URT-15", "Biten adet kontrolü", updated("Üretim Planları", "Biten Panel"), [
        cond("{{Biten Panel}} > {{Toplam Panel}} or {{Biten Kapı}} > {{Toplam Kapı}}",
             [nf("İmalat Sorumlusu", "{{Plan No}}: biten adet toplamdan fazla girildi, kontrol edin.")]),
    ]),
]

# ═════════════════════════════════════════════════════════════════════════════
# A5 · Satınalma & Stok (14)
# ═════════════════════════════════════════════════════════════════════════════
EKSIK = "Min({{trigger:İhtiyaç Miktarı}}, Max(0, 0 - {{loop:Net Durum}}))"


def _stok_hareketi(tur, miktar):
    return create("Stok Hareketleri", {
        "Açıklama": "Otomatik üretim tüketimi", "Malzeme": "loop:Malzeme", "Hareket Türü": tur,
        "Miktar": miktar, "Tarih": TODAY, "İlgili Üretim Planı": "trigger:_id", "Not": "Otomatik üretim tüketimi"})


def _ihtiyac(miktar):
    return create("Malzeme İhtiyaçları", {
        "İhtiyaç": "formula:Concat('Düzeltme: ', {{Açıklama / Gerekçe}})", "Üretim Planı": "trigger:Üretim Planı",
        "Malzeme": "trigger:Malzeme", "Reçete Düzeltmesi": "trigger:_id", "İhtiyaç Miktarı": miktar,
        "Durum": "Açık"})


STN = [
    A("STN-01", "Malzeme ihtiyaçlarını oluştur", updated("Üretim Planları", "Durum"), [
        # URT-02 ile aynı zorunlu alan kontrolü: eksik bilgiyle sunulan (geri çevrilen) planda ihtiyaç açılmaz
        cond("{{Durum}} = 'İmalata Sunuldu' and {{Malzeme İhtiyacı Sayısı}} = 0 and isNotBlank({{İmalat Talimatı}})"
             " and isNotBlank({{İş Rengi}}) and isNotBlank({{İmalat Sorumlusu}}) and isNotBlank({{Başlangıç Tarihi}})", [
            find("Duvar Kalemleri", w("Teklif Revizyonu", "trigger:Esas Revizyon"), mx=500, actions=[
                find("Reçete Kalemleri", w("Duvar Kalemi", "loop:_id"), mx=500, actions=[
                    cond("isNotBlank({{Malzeme}}) and {{Toplam İhtiyaç}} != 0", [
                        create("Malzeme İhtiyaçları", {
                            "İhtiyaç": "loop:Kalem", "Üretim Planı": "trigger:_id", "Malzeme": "loop:Malzeme",
                            "Reçete Kalemi": "loop:_id", "İhtiyaç Miktarı": "loop:Toplam İhtiyaç",
                            "Durum": "Açık"})])])]),
        ]),
    ]),
    A("STN-02", "Eksik hesapla – otomatik satınalma talebi", created("Malzeme İhtiyaçları"), [
        cond("{{İhtiyaç Miktarı}} > 0", [
            find("Malzemeler", w("Malzeme İhtiyaçları", "trigger:_id"), [
                upd({"Eksik Miktar": "formula:" + EKSIK}, target="trigger"),
                cond("0 - {{Net Durum}} > 0", [
                    create("Satınalma Talepleri", {
                        "Açıklama": "formula:Concat('Eksik: ', {{loop:Malzeme Adı}})",
                        "Malzeme": "trigger:Malzeme", "Miktar": "formula:" + EKSIK,
                        "Kaynak": "Otomatik (eksik)", "İlgili Üretim Planı": "trigger:Üretim Planı",
                        "İlgili Proje": "trigger:İlgili Proje", "Malzeme İhtiyacı": "trigger:_id",
                        "Tedarikçi": "loop:Varsayılan Tedarikçi", "Durum": "Talep",
                        "Gerekli Tarih": "trigger:Plan Başlangıç Tarihi"}),
                    nr([STN_R], "Eksik malzeme: {{Malzeme}} {{Eksik Miktar}} {{Birim}} – {{Üretim Planı}}, "
                                "gerekli {{Plan Başlangıç Tarihi}}."),
                ]),
                cond("isNotBlank({{trigger:Plan Başlangıç Tarihi}}) and "
                     "SubtractDate({{trigger:Plan Başlangıç Tarihi}}, Today()) < Coalesce({{Tedarik Süresi (gün)}}, 0)",
                     [nr([IMP, STN_R], "{{Malzeme}} tedarik süresi ({{Tedarik Süresi (gün)}} gün) plan "
                                       "başlangıcına yetmeyebilir – {{Üretim Planı}}.")]),
            ]),
        ]),
    ]),
    A("STN-03", "Plan sonrası manuel düzeltme", created("Reçete Düzeltmeleri"), [
        cond("isNotBlank({{Üretim Planı}}) and {{Düzeltme Türü}} in ('İlave Kalem','Eksiltme') and "
             "isNotBlank({{Malzeme}})", [
            cond("{{Düzeltme Türü}} = 'İlave Kalem'", [_ihtiyac("trigger:Adet")],
                 [_ihtiyac("formula:0 - {{Adet}}")]),
        ]),
    ]),
    A("STN-04", "Manuel / ön sipariş talebi", created("Satınalma Talepleri"), [
        cond("{{Kaynak}} in ('Manuel','Potansiyel İş Ön Siparişi')", [
            cond("isBlank({{Talep Eden}})", [upd({"Talep Eden": "trigger:Oluşturan"})]),
            cond("isBlank({{Durum}})", [upd({"Durum": "Talep"})]),
            cond("{{Kaynak}} = 'Potansiyel İş Ön Siparişi' and isBlank({{İlgili Proje}})",
                 [nf("Oluşturan", "Ön sipariş talebinde İlgili Proje zorunludur.")]),
            nr([STN_R], "Yeni satınalma talebi {{Talep No}}: {{Malzeme}} {{Miktar}} {{Birim}}, gerekli "
                        "{{Gerekli Tarih}} ({{Kaynak}})."),
        ]),
    ]),
    A("STN-05", "Tedarikçi teklifi – eşik kontrolü", updated("Satınalma Talepleri", "Teklif Tutarı"), [
        cond("isNotBlank({{Teklif Tutarı}}) and isNotBlank({{Para Birimi}}) and {{Durum}} in ('Talep','Teklif')", [
            cond(f"({{{{Para Birimi}}}} = 'TL' and {{{{Teklif Tutarı}}}} > {ESIK_TL}) or "
                 f"({{{{Para Birimi}}}} = 'USD' and {{{{Teklif Tutarı}}}} > {ESIK_USD}) or "
                 f"({{{{Para Birimi}}}} = 'EUR' and {{{{Teklif Tutarı}}}} > {ESIK_EUR})",
                 [upd({"Durum": "Onay Bekliyor"})],
                 [upd({"Durum": "Onaylandı", "Onaylayan": "trigger:Son Değiştiren", "Onay Tarihi": TODAY})]),
        ]),
    ]),
    A("STN-06", "Yönetici onayı", updated("Satınalma Talepleri", "Durum"), [
        cond("{{Durum}} = 'Onay Bekliyor'", [
            {"type": "approval", "title": "Satınalma onayı",
             "subtitle": "{{Talep No}} – {{Malzeme}} · {{Miktar}} {{Birim}} · {{Teklif Tutarı}} {{Para Birimi}} · "
                         "{{Tedarikçi}} · gerekli {{Gerekli Tarih}} · {{İlgili Üretim Planı}}",
             "approver": f"roles:{YON}", "timeout_days": 2, "require_rejection_message": True,
             "on_approve": [upd({"Durum": "Onaylandı", "Onay Tarihi": TODAY})],
             "on_reject": [upd({"Durum": "Reddedildi"})]},
        ]),
    ]),
    A("STN-07", "Onaylandı – sipariş ver", updated("Satınalma Talepleri", "Durum"), [
        cond("{{Durum}} = 'Onaylandı'",
             [nr([STN_R], "Onaylandı, sipariş verin: {{Talep No}} – {{Malzeme}} {{Miktar}} {{Birim}}, {{Tedarikçi}}.")]),
    ]),
    A("STN-08", "Sipariş verildi", updated("Satınalma Talepleri", "Durum"), [
        cond("{{Durum}} = 'Sipariş Verildi'", [
            upd({"Sipariş Tarihi": TODAY}),
            cond("isBlank({{Beklenen Teslim}})", [nr([STN_R], "{{Talep No}} için Beklenen Teslim tarihini girin.")]),
        ]),
    ]),
    A("STN-09", "Teslim alındı – stok girişi", updated("Satınalma Talepleri", "Durum"), [
        cond("{{Durum}} = 'Teslim Alındı'", [
            upd({"Teslim Tarihi": TODAY}),
            create("Stok Hareketleri", {
                "Açıklama": "formula:Concat('Satınalma girişi – ', {{Talep No}})", "Malzeme": "trigger:Malzeme",
                "Hareket Türü": "Giriş", "Miktar": "trigger:Miktar", "Tarih": TODAY,
                "İlgili Satınalma Talebi": "trigger:_id", "İlgili Üretim Planı": "trigger:İlgili Üretim Planı",
                "Yapan": "trigger:Son Değiştiren"}),
            cond("isNotBlank({{İlgili Üretim Planı}})",
                 [nr([IMP], "Malzeme geldi: {{Malzeme}} {{Miktar}} {{Birim}} – {{İlgili Üretim Planı}}.")]),
        ]),
    ]),
    A("STN-10", "Geciken teslimat", timed("Satınalma Talepleri", "Beklenen Teslim", 1), [
        cond("{{Durum}} = 'Sipariş Verildi'", [nr([STN_R, IMP], "Teslimat gecikti: {{Talep No}} – {{Malzeme}}, "
                                                               "beklenen {{Beklenen Teslim}}, {{Tedarikçi}}.")]),
    ]),
    A("STN-11", "Gerekli tarih riski", timed("Satınalma Talepleri", "Gerekli Tarih", -3), [
        cond("{{Durum}} in ('Talep','Teklif','Onay Bekliyor','Onaylandı')",
             [nr([STN_R, YON], "{{Talep No}} ({{Malzeme}}) için 3 gün kaldı, sipariş hâlâ verilmedi ({{Durum}}).")]),
    ]),
    A("STN-12", "Üretim başladı – stoktan düş", updated("Üretim Planları", "Durum"), [
        cond("{{Durum}} = 'Üretimde'", [
            find("Malzeme İhtiyaçları", w("Üretim Planı", "trigger:_id"), mx=1000, actions=[
                cond("{{Durum}} = 'Açık'", [
                    cond("{{İhtiyaç Miktarı}} > 0", [_stok_hareketi("Çıkış", "loop:İhtiyaç Miktarı")],
                         [_stok_hareketi("Giriş", "formula:0 - {{loop:İhtiyaç Miktarı}}")]),
                    upd({"Durum": "Tüketildi"}),
                ])]),
        ]),
    ]),
    A("STN-13", "Kritik stok uyarısı", created("Stok Hareketleri"), [
        find("Malzemeler", w("Stok Hareketleri", "trigger:_id"), [
            cond("isNotBlank({{Minimum Stok}}) and {{Stok Bakiyesi}} < {{Minimum Stok}}", [
                nr([STN_R], "Kritik stok: {{loop:Malzeme Adı}} bakiye {{loop:Stok Bakiyesi}} {{loop:Birim}}, "
                            "minimum {{loop:Minimum Stok}}.")])]),
    ]),
    A("STN-14", "Talep reddedildi", updated("Satınalma Talepleri", "Durum"), [
        cond("{{Durum}} = 'Reddedildi'", [
            nr([STN_R], "{{Talep No}} reddedildi: {{Ret Nedeni}}."),
            cond("isNotBlank({{Talep Eden}})", [nf("Talep Eden", "{{Talep No}} reddedildi: {{Ret Nedeni}}.")]),
            cond("isNotBlank({{İlgili Üretim Planı}})",
                 [nr([IMP], "Plan için gereken malzeme talebi reddedildi: {{Malzeme}} – {{İlgili Üretim Planı}}.")]),
        ]),
    ]),
]

BY_APP = {"CRM": CRM, "Proje & Teklif": PRJ, "Teknik Hesaplama": HSP,
          "Planlama & Üretim": URT, "Satınalma & Stok": STN}
