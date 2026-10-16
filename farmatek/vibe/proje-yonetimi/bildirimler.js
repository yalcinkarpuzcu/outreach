/* Bildirim merkezi — Workiom bildirimleri (bu uygulamaya ait), canlı uyarılar, bildirim kuralları */
"use strict";

const NOTIF_RULES = [
  ["Proje planı kuruldu", "Proje yöneticisi", "plan"],
  ["Öncülü açık görev başlatıldı/kapatıldı (kilit)", "Görev sorumlusu", "lock"],
  ["Görev onaya gönderildi", "Onaylayıcı (onay talebi)", "onay"],
  ["Onay reddedildi", "Görev sorumlusu", "rev"],
  ["Görevin öncülleri tamamlandı → Başlayabilir", "Ardıl görevin sorumlusu", "go"],
  ["Kilometre taşına ulaşıldı", "Proje yöneticisi", "ms"],
  ["Görev gecikti (her sabah 06:00)", "Sorumlu + proje yöneticisi", "late"],
  ["Bitişe 3 gün kaldı (her sabah)", "Sorumlu + proje yöneticisi", "soon"],
  ["Kilometre taşı gecikti (her sabah 06:05)", "Proje yöneticisi", "late"],
  ["Baseline alındı", "Proje yöneticisi", "base"],
  ["Görev size atandı", "Yeni sorumlu (Workiom)", "info"]
];

VIEWS.bildirimler = { title: "Bildirimler", async mount(ctx) {
  const S = { filter: "unread", kind: "", alive: true, tasks: [], mss: [], projs: [] };
  const left = el("section", { class: "card n-list" });
  const right = el("aside", { class: "n-side" });
  clear(ctx.main).append(el("div", { class: "page n-page" }, left, right));

  const KINDS = [["", "Tümü"], ["onay", "Onay"], ["rev", "Red"], ["go", "Başlayabilir"], ["late", "Gecikme"], ["soon", "Yaklaşan"], ["ms", "Kilometre taşı"], ["lock", "Kilit"], ["plan", "Plan"], ["base", "Baseline"]];
  const shown = () => NOTIF.items.filter(n => (S.filter === "all" || n.state === 0) && (!S.kind || notifKind(n)[0] === S.kind));

  function drawRibbon() {
    const unreadShown = shown().filter(n => n.state === 0).length;
    clear(ctx.ribbon).append(
      rgroup("Göster", el("div", { class: "rcol" },
        rseg([["unread", "Okunmamış (" + NOTIF.unread + ")"], ["all", "Tümü (" + NOTIF.items.length + ")"]], S.filter, x => { S.filter = x; drawList(); }, "Okunma"),
        (() => { const s = el("select", { class: "rsel", "aria-label": "Tür" }, ...KINDS.map(([k, t]) => el("option", { value: k, text: t, selected: k === S.kind || null }))); s.addEventListener("change", () => { S.kind = s.value; drawList(); }); return s; })())),
      rgroup("İşlem",
        rbtn({ icon: "check", text: "Görünenleri okundu işaretle", disabled: !unreadShown, onclick: markShown }),
        rbtn({ icon: "refresh", text: "Yenile", onclick: async () => { await NOTIF.refresh(true); await loadAlerts(); } })));
  }

  function drawList() {
    drawRibbon();
    const list = shown();
    setStatus(NOTIF.unread + " okunmamış", NOTIF.items.length + " bildirim (bu uygulama)", "Her 60 sn'de bir kendiliğinden yenilenir");
    clear(left).append(el("header", { class: "n-h" }, el("h2", { text: "Bildirimler" }), el("span", { class: "muted", text: "Workiom bildirimlerinizden Proje Yönetimi'ne ait olanlar" })));
    if (!NOTIF.loaded) { left.append(el("div", { class: "state slim" }, el("div", { class: "spinner" }))); return; }
    if (!list.length) {
      left.append(el("div", { class: "state slim" }, el("div", { class: "state-ic" }, icon("bell", 26)), el("h2", { text: S.filter === "unread" ? "Okunmamış bildirim yok" : "Bildirim yok" }),
        el("p", { text: "Görev atandığında, başlayabilir olduğunda, onaya geldiğinde, geciktiğinde ve kilometre taşına ulaşıldığında burada görünür." })));
      return;
    }
    let lastDay = "";
    const ul = el("div", { class: "n-items" });
    for (const n of list) {
      const day = new Date(n.notification?.creationTime).toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long" });
      if (day !== lastDay) { ul.append(el("div", { class: "n-day", text: day })); lastDay = day; }
      const row = notifRow(n, false);
      const wrap = el("div", { class: "n-wrap" }, row);
      if (n.state === 0) wrap.append(el("button", { class: "icon-btn", type: "button", title: "Okundu işaretle", "aria-label": "Okundu işaretle",
        onclick: async e => { e.stopPropagation(); try { await NOTIF.markRead(n); } catch (er) { if (!(er instanceof SessionGone)) toast(er.message, "err"); } } }, icon("check", 15)));
      ul.append(wrap);
    }
    left.append(ul);
  }

  async function markShown() {
    const list = shown().filter(n => n.state === 0).slice(0, 300);
    if (!list.length) return;
    setStatus(el("span", { class: "spinner sm" }), "İşaretleniyor…");
    const errs = await runPool(list, n => NOTIF.markRead(n), 4).catch(e => { if (!(e instanceof SessionGone)) toast(e.message, "err"); return []; });
    toast(list.length - errs.length + " bildirim okundu işaretlendi", "ok");
    drawList();
  }

  /* ── canlı uyarılar (veriden hesaplanır) ────────────────────────── */
  async function loadAlerts() {
    stateLoading(right, "Uyarılar hesaplanıyor…");
    try {
      const [g, k, p] = await Promise.all([fetchAll("G", { includeApprovalRequest: true }), fetchAll("K"), fetchAll("P")]);
      if (!S.alive) return;
      S.tasks = g.map(taskModel); S.mss = k.map(msModel); S.projs = p;
      drawAlerts();
    } catch (e) { stateError(right, e, loadAlerts); }
  }
  function drawAlerts() {
    const td = todayDay();
    const pmOf = new Set(S.projs.filter(r => sameUser(v(r, "P", "Proje Yöneticisi"), ME)).map(r => r._id));
    const mine = S.tasks.filter(t => sameUser(t.owner, ME) && !t.closed);
    const groups = [
      ["Onayımı bekleyenler", "onay", S.tasks.filter(t => t.approvalRequest && t.approvalRequest.status === 0 && (t.approvalRequest.usersIds || []).map(String).includes(String(ME.id))), t => go("onaylar")],
      ["Geciken görevlerim", "late", mine.filter(t => t.late), t => go("plan", t.project, { sec: t.id })],
      ["Başlayabileceğim görevler", "go", mine.filter(t => t.status === "Başlayabilir"), t => go("plan", t.project, { sec: t.id })],
      ["7 gün içinde bitecek görevlerim", "soon", mine.filter(t => t.end != null && t.end >= td && t.end <= td + 7), t => go("plan", t.project, { sec: t.id })],
      ["Revizyon istenen görevlerim", "rev", mine.filter(t => t.status === "Revizyon Gerekli"), t => go("plan", t.project, { sec: t.id })],
      ["Yönettiğim projelerde geciken görevler", "late", S.tasks.filter(t => pmOf.has(t.project) && t.late && !sameUser(t.owner, ME)), t => go("plan", t.project, { sec: t.id })],
      ["Yaklaşan / geciken kilometre taşları (14 gün)", "ms", S.mss.filter(k => !k.closed && k.start != null && k.start <= td + 14 && (pmOf.has(k.project) || !pmOf.size)), k => go("plan", k.project, { sec: k.id })]
    ];
    clear(right).append(el("div", { class: "card" }, el("header", { class: "n-h" }, el("h2", { text: "Uyarılar" }), el("span", { class: "muted", text: "Güncel verilerden" })),
      ...groups.map(([title, k, items, open]) => {
        const det = el("details", { class: "al-g", open: items.length && items.length <= 6 ? true : null },
          el("summary", null, el("span", { class: "nk k-" + k }), el("span", { class: "al-t", text: title }), el("span", { class: "cnt" + (items.length ? " on" : ""), text: String(items.length) })));
        if (!items.length) det.append(el("p", { class: "muted sm", text: "Yok" }));
        for (const t of items.slice(0, 30)) det.append(el("button", { class: "al-i", type: "button", onclick: () => open(t) },
          el("span", { class: "al-n", text: (t.kind === "K" ? "◆ " : "") + t.name }),
          el("span", { class: "al-m", text: (t.projectName || "") + " · " + (t.kind === "K" ? "hedef " : "bitiş ") + fmtShort(t.end) + (t.end != null && t.end < td ? " · " + (td - t.end) + " g gecikti" : "") })));
        return det;
      })),
      el("div", { class: "card" }, el("header", { class: "n-h" }, el("h2", { text: "Kime ne zaman bildirim gider?" })),
        el("ul", { class: "rules" }, ...NOTIF_RULES.map(([e, who, k]) => el("li", null, el("span", { class: "nk k-" + k }), el("span", null, el("b", { text: e }), el("small", { text: who })))))));
  }

  const off = NOTIF.on(() => S.alive && drawList());
  drawList();
  NOTIF.refresh(true);
  await loadAlerts();
  return { unmount() { S.alive = false; off(); } };
} };
