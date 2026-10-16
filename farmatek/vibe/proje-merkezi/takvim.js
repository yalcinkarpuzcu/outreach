/* Takvim — aylık görünüm: görev bitişleri / başlangıçları ve ◆ kilometre taşları */
"use strict";

VIEWS.takvim = { title: "Takvim", async mount(ctx) {
  const t0 = dayToDate(todayDay());
  const S = { y: t0.getUTCFullYear(), m: t0.getUTCMonth(), scope: "all", proj: "", starts: true, tasks: [], mss: [], alive: true };
  const box = el("div", { class: "page cal-page" });
  clear(ctx.main).append(box);

  async function load() {
    stateLoading(box, "Takvim yükleniyor…");
    try {
      const [g, k] = await Promise.all([fetchAll("G"), fetchAll("K")]);
      if (!S.alive) return;
      S.tasks = g.map(taskModel); S.mss = k.map(msModel);
      draw();
    } catch (e) { stateError(box, e, load); }
  }
  function events() {
    const ev = new Map();
    const add = (d, item) => { if (d == null) return; if (!ev.has(d)) ev.set(d, []); ev.get(d).push(item); };
    for (const t of S.tasks) {
      if (S.proj && t.project !== S.proj) continue;
      if (S.scope === "mine" && !sameUser(t.owner, ME)) continue;
      add(t.end, { kind: "end", t });
      if (S.starts && t.start !== t.end && !t.closed) add(t.start, { kind: "start", t });
    }
    if (S.scope !== "mine") for (const k of S.mss) { if (!S.proj || k.project === S.proj) add(k.start, { kind: "ms", t: k }); }
    for (const list of ev.values()) list.sort((a, b) => ({ ms: 0, end: 1, start: 2 }[a.kind] - { ms: 0, end: 1, start: 2 }[b.kind]));
    return ev;
  }
  function chipFor(e) {
    const t = e.t;
    const cls = e.kind === "ms" ? "ev evms" + (t.closed ? " done" : t.start < todayDay() ? " late" : "")
      : e.kind === "start" ? "ev start" : "ev end" + (t.closed ? " done" : t.late ? " late" : "");
    const txt = (e.kind === "ms" ? "◆ " : e.kind === "start" ? "▶ " : "") + t.name;
    return el("button", { class: cls, type: "button", title: txt + " · " + (t.projectName || "") + (t.status ? " · " + t.status : ""),
      onclick: ev => { ev.stopPropagation(); go("plan", t.project, { sec: t.id }); } }, txt);
  }
  function dayModal(d, list) {
    const m = openModal({ title: fmtDay(d) + " · " + list.length + " kayıt" });
    m.body.append(el("div", { class: "day-list" }, ...list.map(e => el("div", { class: "day-i" }, chipFor(e),
      el("small", { class: "muted", text: (e.t.projectName || "") + (e.t.owner ? " · " + userName(e.t.owner) : "") })))));
    m.foot.append(el("button", { class: "btn", type: "button", text: "Kapat", onclick: () => m.close() }));
  }
  function drawRibbon() {
    const projs = [...new Map(S.tasks.map(t => [t.project, t.projectName])).entries()].filter(([id]) => id);
    const ps = el("select", { class: "rsel", "aria-label": "Proje" }, el("option", { value: "", text: "Tüm projeler" }), ...projs.map(([id, n]) => el("option", { value: id, text: n, selected: id === S.proj || null })));
    ps.addEventListener("change", () => { S.proj = ps.value; draw(); });
    const step = n => { S.m += n; if (S.m < 0) { S.m = 11; S.y--; } if (S.m > 11) { S.m = 0; S.y++; } draw(); };
    clear(ctx.ribbon).append(
      rgroup("Ay", el("div", { class: "rrow" },
        rbtn({ icon: "left", text: "Önceki", onclick: () => step(-1) }),
        el("b", { class: "cal-month", text: ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][S.m] + " " + S.y }),
        rbtn({ icon: "right", text: "Sonraki", onclick: () => step(1) }),
        rbtn({ icon: "today", text: "Bugün", onclick: () => { S.y = t0.getUTCFullYear(); S.m = t0.getUTCMonth(); draw(); } }))),
      rgroup("Kapsam", el("div", { class: "rrow" }, rseg([["all", "Tümü"], ["mine", "Bana atananlar"]], S.scope, x => { S.scope = x; draw(); }, "Kapsam"), ps,
        rcheck("Başlangıçları göster", S.starts, on => { S.starts = on; draw(); }))),
      rgroup("Veri", rbtn({ icon: "refresh", text: "Yenile", onclick: load })));
  }
  function draw() {
    drawRibbon();
    const ev = events();
    const first = Math.round(Date.UTC(S.y, S.m, 1) / 864e5);
    const dim = new Date(Date.UTC(S.y, S.m + 1, 0)).getUTCDate();
    const lead = (dayToDate(first).getUTCDay() + 6) % 7;          // Pazartesi başlangıç
    const grid = el("div", { class: "cal", role: "grid", "aria-label": "Aylık takvim" },
      ...["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"].map(d => el("div", { class: "cal-h", role: "columnheader", text: d })));
    const td = todayDay();
    let nMonth = 0;
    for (let i = 0; i < 42; i++) {
      const d = first - lead + i;
      const dt = dayToDate(d), inM = dt.getUTCMonth() === S.m;
      if (i % 7 === 0 && d > first + dim - 1) break;
      const list = ev.get(d) || [];
      if (inM) nMonth += list.length;
      const cell = el("div", { class: "cal-d" + (inM ? "" : " out") + (d === td ? " today" : "") + ([5, 6].includes(i % 7) ? " we" : ""), role: "gridcell" },
        el("div", { class: "cal-n", text: String(dt.getUTCDate()) }));
      list.slice(0, 3).forEach(e => cell.append(chipFor(e)));
      if (list.length > 3) cell.append(el("button", { class: "ev more", type: "button", text: "+" + (list.length - 3) + " daha", onclick: () => dayModal(d, list) }));
      if (list.length) cell.addEventListener("dblclick", () => dayModal(d, list));
      grid.append(cell);
    }
    clear(box).append(el("div", { class: "cal-legend" },
      el("span", { class: "lg" }, el("i", { class: "sw ev-ms" }), "Kilometre taşı"), el("span", { class: "lg" }, el("i", { class: "sw ev-end" }), "Görev bitişi"),
      el("span", { class: "lg" }, el("i", { class: "sw ev-start" }), "Görev başlangıcı"), el("span", { class: "lg" }, el("i", { class: "sw ev-late" }), "Geciken"),
      el("span", { class: "lg" }, el("i", { class: "sw ev-done" }), "Tamamlandı")),
      el("div", { class: "card flush cal-wrap" }, grid));
    setStatus(nMonth + " kayıt bu ay", "Bir kayda tıklayınca planda açılır", "Güne çift tık: günün listesi");
  }
  drawRibbon();
  await load();
  return { unmount() { S.alive = false; } };
} };
