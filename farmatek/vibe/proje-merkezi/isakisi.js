/* İş Akışı — bağımlılık kuralları: aktif kurallar, sıralı yürütme zinciri, kilitli görevler (neyi bekliyor),
   sıradaki görevler, engellenen denemeler. Kurallar Workiom otomasyonlarıdır; hangi ekrandan güncellenirse güncellensin çalışır. */
"use strict";

const IS_KURALLARI = [
  ["🔒", "Öncül kilidi (zorunlu bağ)", "Zorunlu öncülü tamamlanmamış görev \"Devam Ediyor\", \"Onay Bekliyor\" ya da \"Tamamlandı\" yapılamaz. Bu uygulama isteği göndermeden durdurur; başka bir ekrandan denenirse Workiom durumu \"Başlamadı\"ya geri alır ve sorumluya bildirir."],
  ["▶️", "Otomatik aktifleştirme", "Bir görev tamamlanınca, tüm zorunlu öncülleri kapanmış ardılları kendiliğinden \"Başlayabilir\" olur ve sorumlusuna bildirim gider."],
  ["👤", "Otomatik atama", "\"Başlayabilir\" olan görevin sorumlusu yoksa görev departman yöneticisine atanır ve kişiye bildirim gider."],
  ["✍", "Zorunlu onay adımı", "Onay gereken görev \"Tamamlandı\" yapılınca onaylayıcıya gider; onaylanmadan kapanmaz, ardılları da açılmaz. Red gerekçesiyle sorumluya döner."],
  ["◆", "Kilometre taşı", "Bağlı görevlerin hepsi kapanınca kilometre taşı \"Ulaşıldı\" olur ve proje yöneticisine bildirim gider."],
  ["⏰", "Gecikme ve hatırlatma", "Her sabah bitişi geçen açık görevler işaretlenir, bitişine 3 gün kalan görevler için sorumluya ve proje yöneticisine hatırlatma gider."],
  ["🧩", "Plan kurulum sırası", "Proje açılınca sırayla fazlar, görevler, öncül bağları ve kilometre taşları şablondan kurulur."]
];

VIEWS.isakisi = { title: "İş Akışı", async mount(ctx) {
  const S = { tasks: [], byId: new Map(), proj: "", alive: true };
  const box = el("div", { class: "page wf-page" });
  clear(ctx.main).append(box);

  async function load() {
    stateLoading(box, "İş akışı yükleniyor…");
    try {
      const g = await fetchAll("G");
      if (!S.alive) return;
      S.tasks = g.map(taskModel);
      S.byId = new Map(S.tasks.map(t => [t.id, t]));
      draw();
    } catch (e) { stateError(box, e, load); }
  }
  function drawRibbon() {
    const projs = [...new Map(S.tasks.map(t => [t.project, t.projectName])).entries()].filter(([id]) => id);
    const ps = el("select", { class: "rsel", "aria-label": "Proje" }, el("option", { value: "", text: "Tüm projeler" }), ...projs.map(([id, n]) => el("option", { value: id, text: n, selected: id === S.proj || null })));
    ps.addEventListener("change", () => { S.proj = ps.value; draw(); });
    clear(ctx.ribbon).append(rgroup("Kapsam", ps), rgroup("Veri", rbtn({ icon: "refresh", text: "Yenile", onclick: load })));
  }
  const taskBtn = t => el("button", { class: "lnk", type: "button", onclick: () => go("plan", t.project, { sec: t.id }) }, t.name);
  function draw() {
    drawRibbon();
    const ts = S.tasks.filter(t => !S.proj || t.project === S.proj);
    const locked = ts.filter(t => !t.closed && openPredecessors(t, S.byId).length);
    const ready = ts.filter(t => t.status === "Başlayabilir");
    const blocked = NOTIF.items.filter(n => notifKind(n)[0] === "lock").slice(0, 15);

    const flow = el("div", { class: "wf-flow", role: "img", "aria-label": "Sıralı yürütme zinciri" },
      ...[["Başlamadı", "öncüller bekleniyor", "bekle"], ["Başlayabilir", "otomatik · atanır · bildirilir", "hazir"], ["Devam Ediyor", "sorumlu başlatır", "devam"],
        ["Onay Bekliyor", "onay gerekiyorsa", "onay"], ["Tamamlandı", "ardıllar açılır", "tamam"]]
        .flatMap(([s, sub, c], i) => [i ? el("span", { class: "wf-arr", "aria-hidden": "true", text: "→" }) : null,
          el("div", { class: "wf-step st-" + c }, el("b", { text: s }), el("small", { text: sub }))]).filter(Boolean));

    const rules = el("section", { class: "card" }, el("h2", { class: "card-h", text: "Aktif iş akışı kuralları" }),
      el("p", { class: "muted", text: "Bu kurallar Workiom otomasyonu olarak sunucuda çalışır: görev bu uygulamadan, Workiom ekranından, mobilden ya da bildirimden güncellense de uygulanır." }),
      flow,
      el("ul", { class: "wf-rules" }, ...IS_KURALLARI.map(([ic, n, d]) => el("li", null, el("span", { class: "wf-ic", "aria-hidden": "true", text: ic }),
        el("div", null, el("b", { text: n }), el("p", { text: d })), el("span", { class: "chip st-tamam", text: "Aktif" })))),
      el("p", { class: "hint", text: "Bağ türleri: \"Zorunlu\" bağ kilitler ve sırayı belirler; \"Yalnızca görsel\" bağ Gantt'ta kesikli çizilir, kilitlemez. Bağ türünü plandaki görev panelinin Öncüller sekmesinden değiştirebilirsiniz." }));

    const lockedTbl = el("table", { class: "tbl" }, el("thead", null, el("tr", null, ...["Görev", "Proje", "Sorumlu", "Beklediği zorunlu öncüller"].map(h => el("th", { text: h })))),
      el("tbody", null, ...locked.slice(0, 60).map(t => el("tr", null, el("td", null, taskBtn(t)), el("td", { text: t.projectName }), el("td", { text: userName(t.owner) || "—" }),
        el("td", null, el("div", { class: "wf-wait" }, ...openPredecessors(t, S.byId).map(p => el("span", { class: "wf-p" }, chip(p.status), " " + p.name + (p.owner ? " · " + userName(p.owner) : "")))))))));
    const readyTbl = el("table", { class: "tbl" }, el("thead", null, el("tr", null, ...["Görev", "Proje", "Sorumlu", "Plan başlangıç"].map(h => el("th", { text: h })))),
      el("tbody", null, ...ready.map(t => el("tr", null, el("td", null, taskBtn(t)), el("td", { text: t.projectName }), el("td", { text: userName(t.owner) || "atanacak" }), el("td", { text: fmtDay(t.start) })))));

    clear(box).append(rules,
      el("div", { class: "wf-grid" },
        el("section", { class: "card" }, el("h2", { class: "card-h" }, "Sıradaki görevler ", el("span", { class: "cnt", text: String(ready.length) })),
          el("p", { class: "muted", text: "Öncülleri tamamlandığı için otomatik olarak açılan görevler." }),
          ready.length ? el("div", { class: "tbl-wrap" }, readyTbl) : el("p", { class: "muted", text: "Şu an sırası gelen görev yok." })),
        el("section", { class: "card" }, el("h2", { class: "card-h" }, "Engellenen denemeler ", el("span", { class: "cnt", text: String(blocked.length) })),
          el("p", { class: "muted", text: "Öncülü bitmeden başlatılmak istenen ve Workiom'un geri aldığı görevler (bildirimlerinizden)." }),
          blocked.length ? el("ul", { class: "wf-log" }, ...blocked.map(n => el("li", null, el("span", { text: notifText(n) }), el("small", { class: "muted", text: relTime(n.notification?.creationTime) }))))
            : el("p", { class: "muted", text: "Engellenen deneme yok." }))),
      el("section", { class: "card" }, el("h2", { class: "card-h" }, "Kilitli görevler ", el("span", { class: "cnt", text: String(locked.length) })),
        el("p", { class: "muted", text: "Zorunlu öncülleri tamamlanmadığı için başlatılamayan görevler ve bekledikleri." }),
        locked.length ? el("div", { class: "tbl-wrap" }, lockedTbl) : el("p", { class: "muted", text: "Kilitli görev yok." })));
    setStatus(locked.length + " kilitli görev", ready.length + " sıradaki görev", blocked.length + " engellenen deneme");
  }
  const off = NOTIF.on(() => S.alive && S.tasks.length && draw());
  drawRibbon();
  await load();
  return { unmount() { S.alive = false; off(); } };
} };
