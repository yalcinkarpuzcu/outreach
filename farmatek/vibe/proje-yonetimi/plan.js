/* Proje Planı — MS Project deneyimi: proje özet satırı, fazlar (özet), görevler, ◆ kilometre taşları;
   satır içi düzenleme, sürükle-bırak, bağ çizme, otomatik zamanlama, Kaydet/Geri al, baseline, detay paneli */
"use strict";

/* ── genel zamanlama yardımcıları (Kütüphane de kullanır) ─────────── */
function successorsMap(items) {
  const succ = new Map();
  for (const t of items) for (const d of t.deps || []) { if (!succ.has(d.id)) succ.set(d.id, []); succ.get(d.id).push(t); }
  return succ;
}
/* öncülden sonra başla; tampon korunur, geri çekilmez */
function cascadeSchedule(items, byId, ids, pending) {
  const succ = successorsMap(items);
  const queue = [...ids];
  let guard = 0;
  while (queue.length && guard++ < 50000) {
    const id = queue.shift();
    for (const s of succ.get(id) || []) {
      if (s.summary || s.closed) continue;
      const dur = s.end - s.start;
      let need = -Infinity;
      for (const d of s.deps) {
        const p = byId.get(d.id); if (!p || p.start == null) continue;
        if (d.type === 2) need = Math.max(need, p.start);
        else if (d.type === 3) need = Math.max(need, p.end - dur);
        else if (d.type === 4) need = Math.max(need, p.start - dur);
        else need = Math.max(need, p.end);
      }
      if (need > s.start) { s.start = need; s.end = need + dur; pending.add(s.id); queue.push(s.id); }
    }
  }
}
function wouldCycle(items, fromId, toId) {
  const succ = successorsMap(items);
  const seen = new Set([toId]), stack = [toId];
  while (stack.length) {
    const x = stack.pop();
    if (x === fromId) return true;
    for (const n of succ.get(x) || []) if (!seen.has(n.id)) { seen.add(n.id); stack.push(n.id); }
  }
  return false;
}
const DEP_T = ["", "FS", "SS", "FF", "SF"];
function predText(t, byId) {
  return (t.deps || []).map(d => (byId.get(d.id)?.num ?? "?") + (d.type > 1 ? DEP_T[d.type] : "")).join(";");
}
/* "3;5SS, 7ff" → [{num, type}] ; hata metni döner */
function parsePreds(text) {
  const out = [];
  for (const raw of String(text || "").split(/[;,\s]+/).filter(Boolean)) {
    const m = /^(\d+)(FS|SS|FF|SF)?$/i.exec(raw.trim());
    if (!m) return { error: "Anlaşılmadı: \"" + raw + "\". Örnek: 3;5SS;7" };
    out.push({ num: Number(m[1]), type: m[2] ? DEP_T.indexOf(m[2].toUpperCase()) : 1 });
  }
  return { list: out };
}
function rollup(sum) {
  const kids = sum.children || [];
  kids.forEach(k => { if (k.summary) rollup(k); });
  const dated = kids.filter(k => k.start != null);
  if (dated.length) { sum.start = Math.min(...dated.map(k => k.start)); sum.end = Math.max(...dated.map(k => k.end)); }
  const work = [];
  const walk = x => (x.children && x.children.length) ? x.children.forEach(walk) : (x.kind === "G" || x.kind === "T") && work.push(x);
  walk(sum);
  const w = t => Math.max(1, (t.end ?? 0) - (t.start ?? 0));
  const tot = work.reduce((a, t) => a + w(t), 0);
  sum.pct = tot ? Math.round(work.reduce((a, t) => a + w(t) * (t.pct || 0), 0) / tot) : 0;
  sum.closed = work.length > 0 && work.every(t => t.closed);
  const bs = kids.map(k => k.baseStart).filter(x => x != null), be = kids.map(k => k.baseEnd).filter(x => x != null);
  if (sum.kind === "P" || sum.baseStart == null) { sum.baseStart = bs.length ? Math.min(...bs) : null; sum.baseEnd = be.length ? Math.max(...be) : null; }
}

/* ══════════════════════════════════════════════════════════════════ */
VIEWS.plan = { title: "Proje Planı", async mount(ctx) {
  const PID = ctx.arg;
  if (!PID) {
    stateEmpty(ctx.main, "Proje seçin", "Üstteki proje seçiciden ya da Portföy'den bir proje açın.",
      el("a", { class: "btn primary", href: "#/portfoy", text: "Portföye git" }), "portfolio");
    return {};
  }
  const S = {
    proj: null, phases: [], tasks: [], mss: [], depts: [], rows: [], items: [], byId: new Map(),
    orig: new Map(), pending: new Set(), edit: false, isPM: false,
    casc: true, filter: "all", fDept: "", fOwner: "", q: "", alive: true
  };
  const hasPending = () => [...S.pending].some(id => { const t = S.byId.get(id); return t && changed(t); });

  /* ── düzen ──────────────────────────────────────────────────────── */
  const head = el("div", { class: "plan-head" });
  const gHost = el("div", { class: "plan-grid" });
  const wrap = el("div", { class: "plan-wrap" }, head, gHost);
  clear(ctx.main).append(wrap);

  const IND = t => {
    const s = el("span", { class: "ind" });
    if (t.kind === "G") {
      if (t.late) s.append(el("span", { class: "i-late", title: "Gecikmede: plan bitişi geçti", text: "!" }));
      if (!t.closed && t.openPreds > 0 && ["Başlamadı", "Başlayabilir"].includes(t.status)) s.append(el("span", { class: "i-lock", title: t.openPreds + " açık öncül — başlatılamaz", text: "🔒" }));
      if (t.approvalNeeded) s.append(el("span", { class: "i-appr", title: "Onay gerekli" + (t.approvalState ? " · " + t.approvalState : ""), text: "✍" }));
      if (t.notes) s.append(el("span", { class: "i-note", title: t.notes, text: "✎" }));
      if (t.closed) s.append(el("span", { class: "i-done", title: "Kapandı", text: "✓" }));
    } else if (t.kind === "K") {
      if (t.status === "Ulaşıldı") s.append(el("span", { class: "i-done", title: "Ulaşıldı " + fmtDay(t.actual), text: "✓" }));
      if (t.status === "Gecikti") s.append(el("span", { class: "i-late", title: "Gecikti", text: "!" }));
      if (t.critical0) s.append(el("span", { class: "i-crit", title: "Kritik kilometre taşı", text: "★" }));
    }
    return s;
  };
  const isG = t => t.kind === "G", isGK = t => t.kind === "G" || t.kind === "K";
  const editable = f => t => S.edit && f(t);
  const COLS = [
    { key: "num", title: "#", w: 36, cls: "num", render: t => t.kind === "P" ? "0" : String(t.num) },
    { key: "ind", title: "", w: 40, cls: "ind-c", tip: "Göstergeler", render: IND },
    { key: "name", title: "Görev Adı", w: 160, flex: true, edit: { type: "text", get: t => t.name }, editable: editable(t => t.id !== "__none") },
    { key: "dur", title: "Süre", w: 58, cls: "r", render: t => t.start == null ? "" : (t.kind === "K" ? "0 g" : (t.end - t.start) + " g"),
      edit: { type: "number", get: t => t.end - t.start }, editable: editable(isG) },
    { key: "start", title: "Başlangıç", w: 100, render: t => fmtGrid(t.start), edit: { type: "date", get: t => t.start == null ? "" : dayToISO(t.start) }, editable: editable(isGK) },
    { key: "end", title: "Bitiş", w: 100, render: t => fmtGrid(t.end), edit: { type: "date", get: t => t.end == null ? "" : dayToISO(t.end) }, editable: editable(isG) },
    { key: "pred", title: "Öncüller", w: 74, render: t => isGK(t) ? predText(t, S.byId) : "", edit: { type: "text", get: t => predText(t, S.byId) }, editable: editable(isGK),
      tip: "Öncül satır numaraları; ör. 3;5SS. Kilometre taşında: bağlı görevler" },
    { key: "owner", title: "Sorumlu", w: 128, render: t => isG(t) ? el("span", { class: "who" }, avatar(t.owner, "xs"), el("span", { text: userName(t.owner) || "—" })) : "",
      edit: { type: "user" }, editable: editable(isG) },
    { key: "pct", title: "%", w: 46, cls: "r", render: t => t.kind === "K" ? "" : Math.round(t.pct || 0) + "%", edit: { type: "number", min: "0", max: "100", get: t => Math.round(t.pct || 0) }, editable: editable(isG) },
    { key: "status", title: "Durum", w: 122, render: t => t.status ? chip(t.status) : (t.summary ? el("span", { class: "muted", text: t.closed ? "Tamamlandı" : "" }) : ""),
      edit: t => t.kind === "G" ? { type: "select", get: x => x.status, options: x => { const lk = openPredecessors(x, S.byId).length > 0; return L.G.f["Durum"].opts.map(o => [o, o, lk && AKTIF_DURUMLAR.includes(o) && o !== x.status]); } }
        : t.kind === "K" ? { type: "select", get: x => x.status, options: () => L.K.f["KT Durumu"].opts.map(x => [x, x]) } : null,
      editable: editable(isGK) }
  ];
  const hidden = new Set();
  const visCols = () => COLS.filter(c => !hidden.has(c.key));
  const leftW = () => Math.min(visCols().reduce((a, c) => a + c.w, 0) + 60, Math.max(420, Math.round(innerWidth * 0.6)));

  const plan = createPlan(gHost, {
    columns: visCols(), leftWidth: leftW(), zoom: "ay",
    canDrag: t => S.edit && (t.kind === "G" || t.kind === "K"),
    onDragEnd: (t, s, e) => applyDates(t, s, e),
    onLink: (from, to) => addLink(from, to, 1),
    onSelect: () => drawStatus(),
    onOpen: t => openDetail(t),
    onCellEdit: cellEdit,
    onKey: (e, t) => { if (e.key === "Delete" && t && S.edit) { e.preventDefault(); removeRow(t); } else if (e.key === "Insert" && S.edit) { e.preventDefault(); addTask(); } },
    pending: S.pending,
    labelFor: t => t.kind === "G" ? userName(t.owner) : t.kind === "K" ? t.name : "",
    rowFilter: (t, isSummary) => {
      if (isSummary) return !S.q && S.filter === "all" && !S.fDept && !S.fOwner;
      if (S.q && !t.name.toLocaleLowerCase("tr").includes(S.q)) return false;
      if (S.fDept && t.kind === "G" && t.deptId !== S.fDept) return false;
      if (S.fDept && t.kind === "K") return false;
      if (S.fOwner && (t.kind !== "G" || String(t.owner?.id || "") !== S.fOwner)) return false;
      if (S.filter === "open") return !t.closed;
      if (S.filter === "late") return t.late || t.status === "Gecikti";
      if (S.filter === "crit") return !!t.critical;
      if (S.filter === "appr") return t.status === "Onay Bekliyor";
      if (S.filter === "ms") return t.kind === "K";
      return true;
    }
  });

  /* ── yükleme ve model ───────────────────────────────────────────── */
  async function load(keepSel) {
    if (!S.items.length) stateLoading(gHost, "Plan yükleniyor…");
    try {
      const [p, phases, tasks, mss, depts] = await Promise.all([
        getRecord("P", PID),
        fetchAll("F").then(rs => rs.filter(r => linkIds(v(r, "F", "Proje")).includes(PID))),
        fetchAll("G", { includeApprovalRequest: true }).then(rs => rs.filter(r => linkIds(v(r, "G", "Proje")).includes(PID))),
        fetchAll("K").then(rs => rs.filter(r => linkIds(v(r, "K", "Proje")).includes(PID))),
        S.depts.length ? S.depts : fetchAll("D").catch(() => [])
      ]);
      if (!S.alive) return;
      S.proj = p; S.depts = depts;
      S.isPM = sameUser(v(p, "P", "Proje Yöneticisi"), ME);
      if (!S.loadedOnce) { S.edit = S.isPM; S.loadedOnce = true; }
      S.phases = phases.map(phaseModel);
      S.tasks = tasks.map(taskModel);
      S.mss = mss.map(msModel);
      build();
      snapshot();
      drawHead();
      drawRibbon();
      const planState = lbl(v(p, "P", "Plan Durumu"));
      if (!S.tasks.length && planState && planState !== "Hazır") { buildingState(planState); return; }
      plan.setRows(S.rows);
      drawStatus();
      if (!keepSel) {
        const sec = ctx.q.get("sec");
        if (sec && S.byId.has(sec)) { plan.select(sec); setTimeout(() => openDetail(S.byId.get(sec)), 50); }
        else plan.scrollToToday();
      }
    } catch (e) { stateError(gHost, e, () => load()); }
  }

  function buildingState(state) {
    const steps = ["Bekliyor", "Fazlar Oluşturuldu", "Görevler Oluşturuldu", "Öncüller Bağlandı", "Hazır"];
    const i = steps.indexOf(state);
    clear(gHost).append(el("div", { class: "state" },
      el("div", { class: "spinner" }), el("h2", { text: "Plan kuruluyor…" }),
      el("ol", { class: "steps" }, ...["Fazlar", "Görevler", "Öncül bağları", "Kilometre taşları"].map((s, k) =>
        el("li", { class: k < i ? "done" : k === i ? "now" : "" }, el("span", { class: "dot" }), s))),
      el("p", { class: "muted", text: "Şablondan fazlar, görevler, öncüller ve kilometre taşları oluşturuluyor. Sayfa kendiliğinden yenilenir." })));
    setTimeout(() => S.alive && load(), 4000);
  }

  function build() {
    S.items = [...S.phases, ...S.tasks, ...S.mss];
    const phases = [...S.phases].sort((a, b) => a.order - b.order || (a.recStart ?? 0) - (b.recStart ?? 0));
    const orphan = { kind: "F", id: "__none", name: "Faza atanmamış", order: 999, deps: [], start: null, end: null, children: [], summary: true };
    const byPhase = new Map(phases.map(f => [f.id, f]));
    phases.forEach(f => { f.children = []; f.summary = true; });
    for (const t of [...S.tasks].sort((a, b) => a.wbs - b.wbs || (a.start ?? 0) - (b.start ?? 0))) (byPhase.get(t.phase) || orphan).children.push(t);
    for (const k of [...S.mss].sort((a, b) => (a.start ?? 0) - (b.start ?? 0))) {
      const f = byPhase.get(k.phase) || orphan;
      // MS Project gibi: bağlı görevlerin sonuncusundan hemen sonra
      let at = -1;
      f.children.forEach((c, i) => { if (k.deps.some(d => d.id === c.id)) at = i; });
      if (at < 0) f.children.push(k); else f.children.splice(at + 1, 0, k);
    }
    const proj = { kind: "P", id: "__proj", name: v(S.proj, "P", "Proje Adı") || "Proje", deps: [], summary: true, children: [...phases, ...(orphan.children.length ? [orphan] : [])] };
    proj.children.forEach(rollup); rollup(proj);
    S.rows = [proj];
    let n = 0;
    const num = t => { if (t.kind !== "P") t.num = ++n; (t.children || []).forEach(num); };
    num(proj);
    S.byId = new Map();
    const reg = t => { S.byId.set(t.id, t); (t.children || []).forEach(reg); };
    reg(proj);
    markCritical([...S.tasks, ...S.mss]);
  }
  function relayout() {
    for (const f of S.rows[0].children) rollup(f);
    rollup(S.rows[0]);
    markCritical([...S.tasks, ...S.mss]);
    plan.setRows(S.rows);
    drawStatus(); drawRibbon();
  }
  function snapshot() {
    S.orig = new Map([...S.tasks, ...S.mss].map(t => [t.id, { start: t.start, end: t.end, deps: t.deps.map(d => ({ ...d })) }]));
    S.pending.clear();
  }
  const changed = t => { const o = S.orig.get(t.id); if (!o) return false; return o.start !== t.start || o.end !== t.end || depKey(o.deps) !== depKey(t.deps); };
  const depKey = ds => ds.map(d => d.id + ":" + (d.type || 1) + (d.hard === false ? "s" : "")).sort().join();

  /* ── başlık şeridi ──────────────────────────────────────────────── */
  function drawHead() {
    const p = S.proj;
    const bno = Number(v(p, "P", "Baseline No")) || 0;
    const planState = lbl(v(p, "P", "Plan Durumu"));
    document.title = (v(p, "P", "Proje Adı") || "Proje") + " · Proje Planı";
    clear(head).append(
      el("div", { class: "ph-main" },
        el("h1", { text: v(p, "P", "Proje Adı") || "Proje" }),
        chip(lbl(v(p, "P", "Durum"))),
        el("span", { class: "ph-meta" }, "P" + (v(p, "P", "Proje Kodu") ?? "") + " · " + (linkLabel(v(p, "P", "Şablon")) || "şablonsuz")),
        el("span", { class: "ph-meta" }, avatar(v(p, "P", "Proje Yöneticisi"), "xs"), " PM: " + (userName(v(p, "P", "Proje Yöneticisi")) || "—")),
        el("span", { class: "ph-meta" }, bno ? "Baseline " + bno + " · " + fmtDay(toDay(v(p, "P", "Baseline Tarihi"))) : "Baseline alınmadı"),
        planState && planState !== "Hazır" ? el("span", { class: "tag warn", text: "Plan: " + planState }) : null),
      el("div", { class: "ph-mode" + (S.edit ? " on" : "") },
        rcheck(S.edit ? "Düzenleme modu" : "Salt okunur", S.edit, on => { S.edit = on; drawHead(); plan.render(); drawStatus(); }),
        el("span", { class: "muted", text: S.isPM ? "Bu projenin yöneticisisiniz" : "Değişiklikler Workiom yetkilerinize göre kaydedilir" })));
  }

  /* ── şerit ──────────────────────────────────────────────────────── */
  let zoom = "ay", showBase = true, showCrit = true, folded = false;
  function drawRibbon() {
    const nPend = [...S.pending].filter(id => { const t = S.byId.get(id); return t && changed(t); }).length;
    const deptOpts = S.depts.map(d => [d._id, v(d, "D", "Departman")]);
    const owners = new Map(); S.tasks.forEach(t => t.owner && owners.set(String(t.owner.id), userName(t.owner)));
    const sel = (opts, val, on, label, first) => {
      const s = el("select", { class: "rsel", "aria-label": label }, el("option", { value: "", text: first }), ...opts.map(([a, b]) => el("option", { value: a, text: b, selected: a === val || null })));
      s.addEventListener("change", () => on(s.value));
      return s;
    };
    const search = el("input", { class: "rsel search", type: "search", placeholder: "Görev ara…", value: S.q, "aria-label": "Görev ara" });
    search.addEventListener("input", () => { S.q = search.value.trim().toLocaleLowerCase("tr"); plan.render(); });
    const colMenu = el("details", { class: "rmenu" }, el("summary", { class: "rb" }, icon("list", 16), el("span", { text: "Sütunlar" })),
      el("div", { class: "rmenu-pop" }, ...COLS.filter(c => !["num", "name"].includes(c.key)).map(c => rcheck(c.title || "Göstergeler", !hidden.has(c.key), on => {
        on ? hidden.delete(c.key) : hidden.add(c.key);
        plan.setOption("columns", visCols()); plan.setOption("leftWidth", leftW());
        gHost.style.setProperty("--lw", leftW() + "px");
      }))));
    clear(ctx.ribbon).append(
      rgroup("Zamanlama",
        rbtn({ icon: "save", text: nPend ? "Kaydet (" + nPend + ")" : "Kaydet", big: true, cls: nPend ? "hot" : "", disabled: !nPend, onclick: saveAll, id: "rb-save" }),
        el("div", { class: "rcol" },
          rbtn({ icon: "undo", text: "Geri al", disabled: !nPend, onclick: undoAll }),
          rcheck("Otomatik zamanlama", S.casc, on => { S.casc = on; }, "chk-casc"))),
      rgroup("Ekle",
        rbtn({ icon: "plus", text: "Görev", big: true, disabled: !S.edit, onclick: () => addTask() }),
        el("div", { class: "rcol" },
          rbtn({ icon: "ms", text: "Kilometre taşı", disabled: !S.edit, onclick: () => addMilestone() }),
          rbtn({ icon: "phase", text: "Faz", disabled: !S.edit, onclick: () => addPhase() }),
          rbtn({ icon: "trash", text: "Sil", disabled: !S.edit, onclick: () => { const t = plan.selected(); t ? removeRow(t) : toast("Önce bir satır seçin"); } }))),
      rgroup("Görünüm",
        el("div", { class: "rcol" },
          rseg([["gun", "Gün"], ["hafta", "Hafta"], ["ay", "Ay"], ["ceyrek", "Çeyrek"], ["yil", "Yıl"]], zoom, z => { zoom = z; plan.setZoom(z); }, "Zaman ölçeği"),
          el("div", { class: "rrow" },
            rbtn({ icon: "today", text: "Bugün", onclick: () => plan.scrollToToday() }),
            rbtn({ icon: "plan", text: "Seçiliye git", onclick: () => { const t = plan.selected(); if (t && t.start != null) plan.scrollToDay(t.start); } }),
            rbtn({ icon: "collapse", text: folded ? "Fazları aç" : "Fazları daralt", onclick: () => { folded = !folded; plan.collapseAll(folded); S.rows[0] && folded && plan.render(); drawRibbon(); } })))),
      rgroup("Göster",
        el("div", { class: "rcol" },
          rcheck("Baseline", showBase, on => { showBase = on; plan.setOption("showBaseline", on); }),
          rcheck("Kritik yol", showCrit, on => { showCrit = on; plan.setOption("showCritical", on); }),
          colMenu)),
      rgroup("Filtre",
        el("div", { class: "rcol" },
          el("div", { class: "rrow" },
            sel([["open", "Açık işler"], ["late", "Gecikenler"], ["crit", "Kritik yol"], ["appr", "Onay bekleyen"], ["ms", "Kilometre taşları"]], S.filter === "all" ? "" : S.filter, x => { S.filter = x || "all"; plan.render(); }, "Filtre", "Tüm görevler"),
            sel(deptOpts, S.fDept, x => { S.fDept = x; plan.render(); }, "Departman", "Tüm departmanlar")),
          el("div", { class: "rrow" },
            sel([[String(ME.id), "Bana atananlar"], ...[...owners].filter(([id]) => id !== String(ME.id)).sort((a, b) => a[1].localeCompare(b[1], "tr"))], S.fOwner, x => { S.fOwner = x; plan.render(); }, "Sorumlu", "Tüm sorumlular"),
            search))),
      rgroup("Proje",
        rbtn({ icon: "baseline", text: "Baseline al", big: true, disabled: !S.edit, onclick: takeBaseline }),
        el("div", { class: "rcol" },
          rbtn({ icon: "info", text: "Proje bilgileri", onclick: () => openDetail(S.rows[0]) }),
          rbtn({ icon: "excel", text: "Excel'e aktar", onclick: exportCSV }),
          rbtn({ icon: "refresh", text: "Yenile", onclick: async () => { if (hasPending() && !(await confirmDialog("Yenile", "Kaydedilmemiş değişiklikler atılsın mı?", "At ve yenile", true))) return; load(true); } }))));
  }

  function drawStatus() {
    const tasks = S.tasks, P = S.rows[0];
    if (!P) return;
    const nPend = [...S.pending].filter(id => { const t = S.byId.get(id); return t && changed(t); }).length;
    const bEnd = P.baseEnd, sap = P.end != null && bEnd != null ? P.end - bEnd : null;
    const sel = plan.selected();
    setStatus(
      el("span", { class: "sb-mode" + (S.edit ? " on" : ""), text: S.edit ? "Düzenleme" : "Salt okunur" }),
      tasks.length + " görev · " + S.mss.length + " kilometre taşı",
      "%" + Math.round(P.pct || 0) + " tamamlandı",
      "Bitiş: " + fmtDay(P.end) + (sap != null ? " (baseline " + (sap > 0 ? "+" : "") + sap + " g)" : ""),
      "Kritik: " + tasks.filter(t => t.critical).length,
      "Geciken: " + tasks.filter(t => t.late).length,
      nPend ? el("span", { class: "sb-pend", text: nPend + " kaydedilmemiş değişiklik" }) : null,
      el("span", { class: "spacer" }),
      sel ? "Seçili: " + (sel.num ? sel.num + " · " : "") + sel.name : "Satır seçin · çift tık: ayrıntı · F2: adı düzenle · Ins: görev ekle · Del: sil");
  }

  /* ── düzenleme ──────────────────────────────────────────────────── */
  function afterPlanEdit(ids) {
    if (S.casc) cascadeSchedule([...S.tasks, ...S.mss], S.byId, ids, S.pending);
    relayout();
  }
  function applyDates(t, s, e) {
    if (!S.edit) return;
    if (t.kind === "K") { t.start = t.end = s; }
    else { t.start = s; t.end = Math.max(s, e); }
    S.pending.add(t.id);
    afterPlanEdit([t.id]);
  }
  function addLink(fromId, toId, type, hard) {
    const from = S.byId.get(fromId), to = S.byId.get(toId);
    if (!from || !to || !S.edit) return;
    if (from.kind !== "G") { toast("Bağ yalnızca bir görevden başlayabilir.", "err"); return; }
    if (to.summary) { toast("Faz satırına bağ kurulamaz; bir göreve ya da kilometre taşına bırakın.", "err"); return; }
    if (to.kind === "K") type = 1;
    if (to.deps.some(d => d.id === fromId)) { toast("Bu bağ zaten var."); return; }
    if (wouldCycle([...S.tasks, ...S.mss], fromId, toId)) { toast("Bu bağ döngü oluşturur: " + to.name + " zaten " + from.name + " görevinden önce geliyor.", "err", 5000); return; }
    to.deps.push({ id: fromId, type: type || 1, label: from.name, hard: hard !== false });
    S.pending.add(toId);
    afterPlanEdit([fromId]);
    toast((to.kind === "K" ? "Kilometre taşına bağlandı: " : "Bağımlılık eklendi: ") + from.name + " → " + to.name + " (kaydedilmedi)");
  }
  async function cellEdit(t, key, val) {
    try {
      if (key === "name") {
        const nm = String(val).trim();
        if (!nm) { toast("Ad boş olamaz.", "err"); plan.render(); return; }
        const map = { G: ["G", "Görev Adı"], F: ["F", "Faz"], K: ["K", "Kilometre Taşı"], P: ["P", "Proje Adı"] }[t.kind];
        await updateRecord(map[0], t.kind === "P" ? PID : t.id, { [fid(map[0], map[1])]: nm });
        t.name = nm;
        toast("Ad kaydedildi", "ok"); plan.render(); if (t.kind === "P") { S.proj[fid("P", "Proje Adı")] = nm; drawHead(); loadProjects(); }
        return;
      }
      if (key === "dur") {
        const n = Math.round(Number(val));
        if (!Number.isFinite(n) || n < 0) { toast("Süre 0 veya daha büyük bir tam sayı olmalı.", "err"); plan.render(); return; }
        return applyDates(t, t.start, t.start + n);
      }
      if (key === "start") {
        const d = inputToDay(val); if (d == null) { plan.render(); return; }
        return applyDates(t, d, t.kind === "K" ? d : d + (t.end - t.start));
      }
      if (key === "end") {
        const d = inputToDay(val); if (d == null) { plan.render(); return; }
        if (d < t.start) { toast("Bitiş başlangıçtan önce olamaz.", "err"); plan.render(); return; }
        return applyDates(t, t.start, d);
      }
      if (key === "pred") {
        const r = parsePreds(val);
        if (r.error) { toast(r.error, "err", 5000); plan.render(); return; }
        const byNum = new Map([...S.byId.values()].filter(x => x.num).map(x => [x.num, x]));
        const deps = [];
        for (const { num, type } of r.list) {
          const p = byNum.get(num);
          if (!p) { toast(num + " numaralı satır yok.", "err"); plan.render(); return; }
          if (p.kind !== "G") { toast(num + " · " + p.name + " bir görev değil; öncül yalnızca görev olabilir.", "err", 5000); plan.render(); return; }
          if (p.id === t.id) { toast("Bir görev kendi öncülü olamaz.", "err"); plan.render(); return; }
          deps.push({ id: p.id, type: t.kind === "K" ? 1 : type, label: p.name, hard: t.deps.find(x => x.id === p.id)?.hard ?? true });
        }
        const old = t.deps; t.deps = [];
        for (const d of deps) if (wouldCycle([...S.tasks, ...S.mss], d.id, t.id)) { t.deps = old; toast("Döngü oluşur: " + d.label, "err", 5000); plan.render(); return; }
        t.deps = deps;
        S.pending.add(t.id);
        return afterPlanEdit(deps.map(d => d.id));
      }
      if (key === "owner") {
        if (!val) { plan.render(); return; }
        await updateRecord("G", t.id, { [fid("G", "Sorumlu")]: val });
        toast("Sorumlu atandı — kişiye Workiom bildirimi gider.", "ok");
        return softReload();
      }
      if (key === "pct") {
        const n = Math.max(0, Math.min(100, Math.round(Number(val))));
        if (!Number.isFinite(n)) { plan.render(); return; }
        await updateRecord("G", t.id, { [fid("G", "% Tamamlanma")]: n });
        t.pct = n; relayout(); toast("% tamamlanma kaydedildi", "ok");
        return;
      }
      if (key === "status") return setStatusOf(t, val);
    } catch (e) { if (!(e instanceof SessionGone)) { toast(e.message, "err", 5000); plan.render(); } }
  }
  async function setStatusOf(t, val) {
    if (t.kind === "K") {
      await updateRecord("K", t.id, { [fid("K", "KT Durumu")]: val });
      toast("Kilometre taşı durumu: " + val, "ok");
      return softReload();
    }
    const open = openPredecessors(t, S.byId);
    if (AKTIF_DURUMLAR.includes(val) && open.length) { blockDialog(t, open, val); plan.render(); return false; }
    await updateRecord("G", t.id, { [fid("G", "Durum")]: val });
    toast(val === "Tamamlandı" && t.approvalNeeded ? "Onay gerekli: görev onaylayıcıya gönderiliyor…" : "Durum: " + val + " — otomasyonlar çalışıyor…", "ok", 4000);
    setTimeout(() => S.alive && softReload(), 3500);
    return softReload();
  }
  async function softReload() {
    if (hasPending()) { toast("Kaydedilmemiş plan değişiklikleri var; görünüm kaydettikten sonra yenilenecek."); return; }
    const sel = plan.selected();
    await load(true);
    if (sel && S.byId.has(sel.id)) plan.select(sel.id);
  }

  function undoAll() {
    for (const t of [...S.tasks, ...S.mss]) { const o = S.orig.get(t.id); if (o) { t.start = o.start; t.end = o.end; t.deps = o.deps.map(d => ({ ...d })); } }
    S.pending.clear();
    relayout();
    toast("Değişiklikler geri alındı");
  }

  async function saveAll() {
    const ch = [...S.pending].map(id => S.byId.get(id)).filter(t => t && changed(t));
    if (!ch.length) return;
    const P = S.rows[0];
    const oldEnd = Math.max(...[...S.orig.values()].map(o => o.end ?? -Infinity));
    const ok = await confirmDialog("Plan kaydedilsin mi?",
      ch.length + " satır güncellenecek. Proje bitişi " + fmtDay(oldEnd) + (P.end !== oldEnd ? " → " + fmtDay(P.end) + " (" + (P.end > oldEnd ? "+" : "") + (P.end - oldEnd) + " gün)" : " (değişmiyor)") + ". Fazların tarihleri görevlerden yeniden hesaplanıp kaydedilir.",
      "Kaydet");
    if (!ok) return;
    const jobs = [];
    for (const t of ch) {
      const o = S.orig.get(t.id), p = {};
      if (t.kind === "G") {
        if (o.start !== t.start || o.end !== t.end) { p[fid("G", "Başlangıç")] = dayToISO(t.start); p[fid("G", "Bitiş")] = dayToISO(t.end); }
        if (depKey(o.deps) !== depKey(t.deps)) {
          p[fid("G", "Öncüller")] = t.deps.map(d => ({ _id: d.id, dependencyType: d.type || 1 }));
          p[fid("G", "Öncül Kayıtları")] = t.deps.filter(d => d.hard !== false).map(d => d.id);   // kilit otomasyonu yalnızca zorunlu bağları kullanır
        }
        jobs.push(["G", t.id, p]);
      } else {
        if (o.start !== t.start) p[fid("K", "Hedef Tarih")] = dayToISO(t.start);
        if (depKey(o.deps) !== depKey(t.deps)) p[fid("K", "Bağlı Görevler")] = t.deps.map(d => d.id);
        jobs.push(["K", t.id, p]);
      }
    }
    for (const f of S.phases) if (f.start != null && (f.start !== f.recStart || f.end !== f.recEnd))
      jobs.push(["F", f.id, { [fid("F", "Başlangıç")]: dayToISO(f.start), [fid("F", "Bitiş")]: dayToISO(f.end) }]);
    const btn = document.getElementById("rb-save");
    if (btn) btn.disabled = true;
    setStatus(el("span", { class: "spinner sm" }), "Kaydediliyor… 0/" + jobs.length);
    try {
      const errors = await runPool(jobs, ([l, id, p]) => updateRecord(l, id, p), 4, (d, n) => setStatus(el("span", { class: "spinner sm" }), "Kaydediliyor… " + d + "/" + n));
      if (errors.length) toast(errors.length + " kayıt yazılamadı: " + errors[0][1].message, "err", 7000);
      else toast("Plan kaydedildi: " + jobs.length + " kayıt", "ok");
      S.pending.clear();
      await load(true);
    } catch (e) { if (!(e instanceof SessionGone)) { toast(e.message, "err"); drawRibbon(); drawStatus(); } }
  }

  /* ── ekle / sil ─────────────────────────────────────────────────── */
  function guardPending() {
    if (hasPending()) { toast("Önce bekleyen plan değişikliklerini kaydedin ya da geri alın.", "err", 4500); return false; }
    return true;
  }
  const phaseOptions = cur => [...S.phases].sort((a, b) => a.order - b.order).map(f => el("option", { value: f.id, text: f.name, selected: f.id === cur || null }));
  function selPhaseId() {
    const t = plan.selected();
    if (!t) return S.phases[0]?.id;
    if (t.kind === "F") return t.id === "__none" ? S.phases[0]?.id : t.id;
    return t.phase || S.phases[0]?.id;
  }

  function addTask() {
    if (!S.edit || !guardPending()) return;
    const sel = plan.selected();
    const after = sel && sel.kind === "G" ? sel : null;
    const m = openModal({ title: after ? "Görev ekle — \"" + after.name + "\" sonrasına" : "Görev ekle", form: true });
    const err = el("div", { class: "error-box", role: "alert" });
    const fName = el("input", { class: "input", placeholder: "ör. Çözünürlük profili karşılaştırması" });
    const fPhase = el("select", { class: "input" }, ...phaseOptions(selPhaseId()));
    const s0 = after ? after.end : (S.byId.get(selPhaseId())?.start ?? todayDay());
    const fStart = el("input", { class: "input", type: "date", value: dayToISO(s0) });
    const fDur = el("input", { class: "input", type: "number", min: "0", value: "7" });
    const fOwner = userSelect(null, "— sorumlu seçin —");
    const fDept = el("select", { class: "input" }, el("option", { value: "", text: "— departman —" }),
      ...S.depts.map(d => el("option", { value: d._id, text: v(d, "D", "Departman"), selected: after && after.deptId === d._id || null })));
    const fPred = el("input", { type: "checkbox", checked: after ? true : null });
    const fNeed = el("input", { type: "checkbox" });
    const ok = el("button", { class: "btn primary", type: "submit", text: "Görevi ekle" });
    m.body.append(reqNote(), err,
      field("Görev adı", fName, { required: true, wide: true }),
      el("div", { class: "grid2" }, field("Faz", fPhase), field("Departman", fDept)),
      el("div", { class: "grid2" }, field("Başlangıç", fStart), field("Süre (gün)", fDur)),
      field("Sorumlu", fOwner, { hint: "Boş bırakılırsa görev sırası geldiğinde (Başlayabilir) departman yöneticisine otomatik atanır." }),
      after ? el("label", { class: "check" }, fPred, " \"" + after.name + "\" görevinin ardılı olsun (FS, zorunlu: o bitmeden başlatılamaz)") : null,
      el("label", { class: "check" }, fNeed, " Tamamlanması için onay gerekli"));
    m.foot.append(el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => m.close() }), ok);
    fName.focus();
    m.box.addEventListener("submit", async ev => {
      ev.preventDefault();
      const nameId = fid("G", "Görev Adı");
      if (!checkRequired([{ id: nameId, name: "Görev adı", control: fName }], { [nameId]: fName.value }, err)) return;
      const s = inputToDay(fStart.value), d = Math.max(0, Math.round(Number(fDur.value) || 0));
      if (s == null) { err.textContent = "Geçerli bir başlangıç tarihi girin."; fStart.focus(); return; }
      const sameP = S.tasks.filter(x => x.phase === fPhase.value).sort((a, b) => a.wbs - b.wbs);
      let wbs;
      if (after && after.phase === fPhase.value) {
        const nxt = S.tasks.filter(x => x.wbs > after.wbs).sort((a, b) => a.wbs - b.wbs)[0];
        wbs = nxt ? Math.round(((after.wbs + nxt.wbs) / 2) * 1000) / 1000 : after.wbs + 1;
      } else wbs = sameP.length ? sameP[sameP.length - 1].wbs + 0.5 : Math.max(0, ...S.tasks.map(x => x.wbs)) + 1;
      const p = {
        [nameId]: fName.value.trim(), [fid("G", "Proje")]: [PID], [fid("G", "Faz")]: [fPhase.value],
        [fid("G", "Durum")]: "Başlamadı", [fid("G", "Başlangıç")]: dayToISO(s), [fid("G", "Bitiş")]: dayToISO(s + d),
        [fid("G", "WBS No")]: wbs, [fid("G", "Kapalı")]: 0, [fid("G", "% Tamamlanma")]: 0, [fid("G", "Onay Gerekli")]: fNeed.checked
      };
      if (fOwner.value) p[fid("G", "Sorumlu")] = fOwner.value;
      if (fDept.value) {
        p[fid("G", "Sorumlu Departman")] = [fDept.value];
        const dep = S.depts.find(x => x._id === fDept.value);
        const appr = dep && v(dep, "D", "Onaylayıcı");
        if (appr?.emailAddress) p[fid("G", "Onaylayıcı")] = appr.emailAddress;
      }
      if (!p[fid("G", "Onaylayıcı")]) { const pm = v(S.proj, "P", "Proje Yöneticisi"); if (pm?.emailAddress) p[fid("G", "Onaylayıcı")] = pm.emailAddress; }
      if (after && fPred.checked) { p[fid("G", "Öncüller")] = [{ _id: after.id, dependencyType: 1 }]; p[fid("G", "Öncül Kayıtları")] = [after.id]; }
      ok.disabled = true;
      try {
        const r = await createRecord("G", p);
        m.close(); toast("Görev eklendi: " + fName.value.trim(), "ok");
        await load(true);
        const nid = r?.id || r?._id; if (nid) plan.select(nid);
      } catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; }
      finally { ok.disabled = false; }
    });
  }

  function addMilestone() {
    if (!S.edit || !guardPending()) return;
    const sel = plan.selected();
    const m = openModal({ title: "Kilometre taşı ekle", form: true });
    const err = el("div", { class: "error-box", role: "alert" });
    const fName = el("input", { class: "input", placeholder: "ör. Pilot seri tamamlandı" });
    const fPhase = el("select", { class: "input" }, ...phaseOptions(selPhaseId()));
    const fDate = el("input", { class: "input", type: "date", value: dayToISO(sel && sel.kind === "G" ? sel.end : todayDay()) });
    const fCrit = el("input", { type: "checkbox" });
    const fLink = el("input", { type: "checkbox", checked: sel && sel.kind === "G" ? true : null });
    const ok = el("button", { class: "btn primary", type: "submit", text: "Ekle" });
    m.body.append(reqNote(), err, field("Kilometre taşı", fName, { required: true, wide: true }),
      el("div", { class: "grid2" }, field("Faz", fPhase), field("Hedef tarih", fDate)),
      el("label", { class: "check" }, fCrit, " Kritik kilometre taşı"),
      sel && sel.kind === "G" ? el("label", { class: "check" }, fLink, " \"" + sel.name + "\" tamamlanınca ulaşılsın (bağlı görev)") : null,
      el("p", { class: "hint", text: "Bağlı görevlerin tamamı kapandığında kilometre taşı kendiliğinden \"Ulaşıldı\" olur. Bağlı görevleri sonradan Öncüller sütunundan ya da Gantt'ta ok çekerek ekleyebilirsiniz." }));
    m.foot.append(el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => m.close() }), ok);
    fName.focus();
    m.box.addEventListener("submit", async ev => {
      ev.preventDefault();
      const nameId = fid("K", "Kilometre Taşı");
      if (!checkRequired([{ id: nameId, name: "Kilometre taşı", control: fName }], { [nameId]: fName.value }, err)) return;
      const d = inputToDay(fDate.value);
      if (d == null) { err.textContent = "Geçerli bir hedef tarih girin."; fDate.focus(); return; }
      const p = { [nameId]: fName.value.trim(), [fid("K", "Proje")]: [PID], [fid("K", "Faz")]: [fPhase.value], [fid("K", "Hedef Tarih")]: dayToISO(d),
        [fid("K", "KT Durumu")]: "Bekleniyor", [fid("K", "Kritik")]: fCrit.checked };
      if (sel && sel.kind === "G" && fLink.checked) p[fid("K", "Bağlı Görevler")] = [sel.id];
      ok.disabled = true;
      try { await createRecord("K", p); m.close(); toast("Kilometre taşı eklendi", "ok"); await load(true); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; }
      finally { ok.disabled = false; }
    });
  }

  function addPhase() {
    if (!S.edit || !guardPending()) return;
    const m = openModal({ title: "Faz ekle", form: true });
    const err = el("div", { class: "error-box", role: "alert" });
    const fName = el("input", { class: "input" });
    const last = [...S.phases].sort((a, b) => b.order - a.order)[0];
    const fOrder = el("input", { class: "input", type: "number", value: String((last?.order || 0) + 1) });
    const fStart = el("input", { class: "input", type: "date", value: dayToISO(last?.end ?? todayDay()) });
    const fEnd = el("input", { class: "input", type: "date", value: dayToISO((last?.end ?? todayDay()) + 30) });
    const ok = el("button", { class: "btn primary", type: "submit", text: "Ekle" });
    m.body.append(reqNote(), err, field("Faz adı", fName, { required: true, wide: true }),
      el("div", { class: "grid3" }, field("Sıra", fOrder), field("Başlangıç", fStart), field("Bitiş", fEnd)),
      el("p", { class: "hint", text: "Faza görev ekledikçe tarihleri görevlerden hesaplanır." }));
    m.foot.append(el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => m.close() }), ok);
    fName.focus();
    m.box.addEventListener("submit", async ev => {
      ev.preventDefault();
      const nameId = fid("F", "Faz");
      if (!checkRequired([{ id: nameId, name: "Faz adı", control: fName }], { [nameId]: fName.value }, err)) return;
      const p = { [nameId]: fName.value.trim(), [fid("F", "Proje")]: [PID], [fid("F", "Sıra")]: Number(fOrder.value) || 0 };
      if (fStart.value) p[fid("F", "Başlangıç")] = fStart.value;
      if (fEnd.value) p[fid("F", "Bitiş")] = fEnd.value;
      ok.disabled = true;
      try { await createRecord("F", p); m.close(); toast("Faz eklendi", "ok"); await load(true); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; }
      finally { ok.disabled = false; }
    });
  }

  async function removeRow(t) {
    if (!S.edit || !guardPending()) return;
    if (t.kind === "P" || t.id === "__none") { toast("Bu satır silinemez."); return; }
    if (t.kind === "F" && t.children.length) { toast("İçinde görev olan faz silinemez; önce görevleri başka faza taşıyın ya da silin.", "err", 5000); return; }
    const succ = [...S.tasks, ...S.mss].filter(x => x.deps.some(d => d.id === t.id));
    const what = { G: "Görev", K: "Kilometre taşı", F: "Faz" }[t.kind];
    const ok = await confirmDialog(what + " silinsin mi?", t.name + (succ.length ? " — bağlı " + succ.length + " satırdaki bağ da kaldırılacak: " + succ.map(s => s.name).join(", ") : "") + ". Bu işlem geri alınamaz.", "Sil", true);
    if (!ok) return;
    try {
      for (const s of succ) {
        const deps = s.deps.filter(d => d.id !== t.id);
        if (s.kind === "K") await updateRecord("K", s.id, { [fid("K", "Bağlı Görevler")]: deps.map(d => d.id) });
        else await updateRecord("G", s.id, { [fid("G", "Öncüller")]: deps.map(d => ({ _id: d.id, dependencyType: d.type || 1 })), [fid("G", "Öncül Kayıtları")]: deps.map(d => d.id) });
      }
      await deleteRecord(t.kind, t.id);
      closeDetail(); toast(what + " silindi", "ok"); await load(true);
    } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
  }

  /* ── baseline ───────────────────────────────────────────────────── */
  async function takeBaseline() {
    if (!guardPending()) return;
    const no = Number(v(S.proj, "P", "Baseline No")) || 0;
    const ok = await confirmDialog("Baseline " + (no + 1) + " alınsın mı?",
      "Tüm görevlerin, fazların ve kilometre taşlarının mevcut tarihleri Baseline " + (no + 1) + " olarak kaydedilir ve arşive yazılır. Sapma bundan sonra bu plana göre hesaplanır. Proje durumu 'Devam Ediyor' olur.", "Baseline al");
    if (!ok) return;
    setStatus(el("span", { class: "spinner sm" }), "Baseline alınıyor… (otomasyon çalışıyor)");
    try {
      await updateRecord("P", PID, { [fid("P", "Durum")]: "Plan Onaylandı (Baseline)" });
      const t0 = Date.now();
      while (Date.now() - t0 < 180000 && S.alive) {
        await new Promise(r => setTimeout(r, 4000));
        const p = await getRecord("P", PID);
        if ((Number(v(p, "P", "Baseline No")) || 0) > no) break;
      }
      await new Promise(r => setTimeout(r, 4000));
      toast("Baseline " + (no + 1) + " alındı", "ok");
      load(true);
    } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
  }

  /* ── Excel ──────────────────────────────────────────────────────── */
  function exportCSV() {
    const rows = [["#", "Tür", "Ad", "Faz", "Departman", "Sorumlu", "Başlangıç", "Bitiş", "Süre (gün)", "Öncüller", "Durum", "% Tamamlanma",
      "Baseline Başlangıç", "Baseline Bitiş", "Sapma (gün)", "Kritik yol", "Gecikmede", "Onay Gerekli"]];
    const walk = (t, depth) => {
      if (t.kind !== "P") rows.push([t.num, { F: "Faz", G: "Görev", K: "Kilometre taşı" }[t.kind], "  ".repeat(Math.max(0, depth - 1)) + t.name, t.phaseName || "", t.dept || "", userName(t.owner),
        t.start != null ? dayToISO(t.start) : "", t.end != null ? dayToISO(t.end) : "", t.start != null ? t.end - t.start : "", (t.kind !== "F" ? predText(t, S.byId) : ""), t.status || "", Math.round(t.pct || 0),
        t.baseStart != null ? dayToISO(t.baseStart) : "", t.baseEnd != null ? dayToISO(t.baseEnd) : "", t.summary ? "" : (t.variance || 0),
        t.critical ? "Evet" : "", t.late ? "Evet" : "", t.approvalNeeded ? "Evet" : ""]);
      (t.children || []).forEach(c => walk(c, depth + 1));
    };
    walk(S.rows[0], 0);
    downloadCSV((v(S.proj, "P", "Proje Adı") || "proje").replace(/[^\p{L}\p{N}]+/gu, "_") + "_plan.csv", rows);
  }

  /* ── detay paneli ───────────────────────────────────────────────── */
  let drawer = null;
  function closeDetail() { if (drawer) { drawer.remove(); drawer = null; } }
  function openDetail(t, tab) {
    closeDetail();
    if (!t || t.id === "__none") return;
    const body = el("div", { class: "dr-body" });
    const tabs = el("div", { class: "dr-tabs", role: "tablist" });
    const kindTxt = { P: "Proje", F: "Faz", G: "Görev", K: "Kilometre taşı" }[t.kind];
    drawer = el("aside", { class: "drawer", role: "dialog", "aria-modal": "false", "aria-labelledby": "dr-t" },
      el("header", null,
        el("div", { class: "dr-top" }, el("span", { class: "tag", text: kindTxt + (t.num ? " · #" + t.num : "") }),
          t.status ? chip(t.status) : null, t.critical ? el("span", { class: "tag crit", text: "Kritik yol" }) : null,
          t.late ? el("span", { class: "tag late", text: "Gecikmede" }) : null, S.pending.has(t.id) && changed(t) ? el("span", { class: "tag warn", text: "kaydedilmedi" }) : null,
          el("span", { class: "spacer" }), el("button", { class: "icon-btn", type: "button", "aria-label": "Kapat", onclick: closeDetail }, icon("x", 16))),
        el("h2", { id: "dr-t", text: t.name }), tabs),
      body);
    ctx.main.append(drawer);
    const panes = {};
    if (t.kind === "G") Object.assign(panes, { "Genel": () => taskGeneral(t, body), "Öncüller": () => depPane(t, body), "Notlar & Dokümanlar": () => notesPane(t, body), "Yorumlar": () => renderComments(body, "G", t.id), "Geçmiş": () => renderHistory(body, "G", t.id) });
    else if (t.kind === "K") Object.assign(panes, { "Genel": () => msGeneral(t, body), "Bağlı görevler": () => depPane(t, body), "Geçmiş": () => renderHistory(body, "K", t.id) });
    else if (t.kind === "F") Object.assign(panes, { "Genel": () => phaseGeneral(t, body), "Geçmiş": () => renderHistory(body, "F", t.id) });
    else Object.assign(panes, { "Proje": () => projectGeneral(body), "Yorumlar": () => renderComments(body, "P", PID), "Geçmiş": () => renderHistory(body, "P", PID) });
    const show = name => {
      tabs.querySelectorAll("button").forEach(b => b.setAttribute("aria-selected", b.textContent === name ? "true" : "false"));
      clear(body); panes[name]();
    };
    Object.keys(panes).forEach(n => tabs.append(el("button", { type: "button", role: "tab", text: n, onclick: () => show(n) })));
    show(tab && panes[tab] ? tab : Object.keys(panes)[0]);
  }
  const kv = rows => el("dl", { class: "kv" }, ...rows.filter(Boolean).flatMap(([k, val]) => [el("dt", { text: k }), el("dd", null, val)]));
  const saveBar = (err, btn) => el("div", { class: "dr-actions" }, err, btn);

  function taskGeneral(t, body) {
    body.append(kv([
      ["Plan", fmtDay(t.start) + " → " + fmtDay(t.end) + " (" + (t.end - t.start) + " gün)"],
      ["Faz", t.phaseName || "—"], ["Departman", t.dept || "—"],
      ["Gerçekleşen", (t.actualStart != null ? fmtDay(t.actualStart) : "—") + " → " + (t.actualEnd != null ? fmtDay(t.actualEnd) : "—")],
      ["Baseline", t.baseStart != null ? fmtDay(t.baseStart) + " → " + fmtDay(t.baseEnd) + (t.variance ? " (sapma " + (t.variance > 0 ? "+" : "") + t.variance + " gün)" : "") : "alınmadı"],
      ["Onay", t.approvalNeeded ? "Gerekli · " + (userName(t.approver) || "—") + (t.approvalState ? " · " + t.approvalState : "") : "Gerekmiyor"],
      t.openPreds > 0 && !t.closed ? ["Kilit", t.openPreds + " açık öncül"] : null,
      t.desc ? ["Kabul kriteri", t.desc] : null
    ]));
    // durum düğmeleri (MS Project'teki "Görev" sekmesi gibi hızlı işlemler)
    const acts = el("div", { class: "quick" });
    const qb = (txt, st, cls) => acts.append(el("button", { class: "btn sm " + (cls || ""), type: "button", text: txt, onclick: async () => { try { if (await setStatusOf(t, st) !== false) closeDetail(); } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); } } }));
    if (!t.closed) {
      if (t.status !== "Devam Ediyor") qb("▶ Başlat", "Devam Ediyor");
      qb(t.approvalNeeded ? "✍ Onaya gönder" : "✓ Tamamla", t.approvalNeeded ? "Onay Bekliyor" : "Tamamlandı", "primary");
      if (t.status !== "Beklemede") qb("⏸ Beklemeye al", "Beklemede");
    }
    body.append(el("div", { class: "section-t", text: "Hızlı işlem" }), acts);
    workflowSection(t, body);

    const err = el("div", { class: "error-box", role: "alert" });
    const fName = el("input", { class: "input", value: t.name });
    const fPhase = el("select", { class: "input" }, ...phaseOptions(t.phase));
    const fDept = el("select", { class: "input" }, el("option", { value: "", text: "— departman —" }), ...S.depts.map(d => el("option", { value: d._id, text: v(d, "D", "Departman"), selected: d._id === t.deptId || null })));
    const fOwner = userSelect(t.owner, "— sorumlu —");
    const fAppr = userSelect(t.approver, "— onaylayıcı —");
    const fNeed = el("input", { type: "checkbox", checked: t.approvalNeeded || null });
    const fDesc = el("textarea", { class: "input", rows: "3" }); fDesc.value = t.desc || "";
    const btn = el("button", { class: "btn primary", type: "button", text: "Kaydet", disabled: !S.edit || null });
    body.append(el("div", { class: "section-t", text: "Görev bilgileri" }), reqNote(),
      field("Görev adı", fName, { required: true }),
      el("div", { class: "grid2" }, field("Faz", fPhase), field("Departman", fDept)),
      el("div", { class: "grid2" }, field("Sorumlu", fOwner), field("Onaylayıcı", fAppr)),
      el("label", { class: "check" }, fNeed, " Tamamlanması için onay gerekli"),
      field("Açıklama / kabul kriteri", fDesc), saveBar(err, btn));
    if (!S.edit) body.append(el("p", { class: "hint", text: "Düzenlemek için üstteki 'Düzenleme modu'nu açın." }));
    btn.addEventListener("click", async () => {
      const nameId = fid("G", "Görev Adı");
      if (!checkRequired([{ id: nameId, name: "Görev adı", control: fName }], { [nameId]: fName.value }, err)) return;
      const p = {};
      if (fName.value.trim() !== t.name) p[nameId] = fName.value.trim();
      if (fPhase.value && fPhase.value !== t.phase) p[fid("G", "Faz")] = [fPhase.value];
      if (fDept.value !== (t.deptId || "")) p[fid("G", "Sorumlu Departman")] = fDept.value ? [fDept.value] : null;
      if (fOwner.value && fOwner.value !== (t.owner?.emailAddress || "")) p[fid("G", "Sorumlu")] = fOwner.value;
      if (fAppr.value && fAppr.value !== (t.approver?.emailAddress || "")) p[fid("G", "Onaylayıcı")] = fAppr.value;
      if (fNeed.checked !== !!t.approvalNeeded) p[fid("G", "Onay Gerekli")] = fNeed.checked;
      if ((fDesc.value || "") !== (t.desc || "")) p[fid("G", "Açıklama")] = fDesc.value || null;
      if (!Object.keys(p).length) { toast("Değişiklik yok"); return; }
      btn.disabled = true;
      try { await updateRecord("G", t.id, p); toast("Görev kaydedildi", "ok"); closeDetail(); softReload(); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; btn.disabled = false; }
    });
  }

  /* İş akışı: neyi bekliyor, tamamlanınca ne olur, ardılın sorumlusunu ata */
  function workflowSection(t, body) {
    const open = openPredecessors(t, S.byId);
    body.append(el("div", { class: "section-t", text: "İş akışı" }));
    const box = el("div", { class: "wf-box" });
    if (t.closed) box.append(el("p", { class: "wf-ok", text: "✓ Görev kapandı; ardılları açıldı." }));
    else if (open.length) box.append(el("p", { class: "wf-lock" }, "🔒 Bekliyor: ", ...open.map((p, i) => [i ? ", " : "", el("b", { text: p.name })]).flat(),
      ". Bunlar tamamlanmadan başlatılamaz."));
    else box.append(el("p", { class: "wf-ok", text: "▶ Tüm zorunlu öncüller tamam; görev başlatılabilir." }));
    const succ = [...S.tasks, ...S.mss].filter(x => x.deps.some(d => d.id === t.id));
    if (!succ.length) box.append(el("p", { class: "muted", text: "Bu görevi bekleyen başka görev yok." }));
    else {
      box.append(el("p", { class: "muted", text: "Bu görev tamamlanınca:" }));
      const ul = el("ul", { class: "wf-next" });
      for (const s of succ) {
        const dep = s.deps.find(d => d.id === t.id);
        const others = s.kind === "G" ? openPredecessors(s, S.byId).filter(p => p.id !== t.id) : s.deps.map(d => S.byId.get(d.id)).filter(p => p && p.id !== t.id && !p.closed);
        const what = s.kind === "K" ? (others.length ? "kilometre taşı " + others.length + " görev daha bekleyecek" : "◆ kilometre taşına ulaşılır, PM'e bildirim gider")
          : dep.hard === false ? "görsel bağ; etkilenmez"
          : s.closed ? "zaten kapandı"
          : others.length ? "açılmaz, " + others.length + " öncül daha bekleyecek"
          : "\"Başlayabilir\" olur" + (s.owner ? ", " + userName(s.owner) + " kişisine bildirim gider" : ", departman yöneticisine atanır");
        const li = el("li", null, el("span", { class: "pn" }, s.kind === "K" ? "◆ " : "", el("b", { text: s.name })), el("small", { text: what }));
        if (s.kind === "G" && !s.closed && S.edit) {
          const us = userSelect(s.owner, "— sorumlu yok —");
          us.classList.add("narrow-sel");
          us.setAttribute("aria-label", s.name + " sorumlusu");
          us.addEventListener("change", async () => {
            if (!us.value) return;
            try { await updateRecord("G", s.id, { [fid("G", "Sorumlu")]: us.value }); toast(s.name + " atandı", "ok"); softReload(); }
            catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
          });
          li.append(us);
        }
        ul.append(li);
      }
      box.append(ul);
    }
    body.append(box);
  }

  function depPane(t, body) {
    const isK = t.kind === "K";
    body.append(el("p", { class: "hint", text: isK ? "Bu görevlerin hepsi kapandığında kilometre taşına ulaşılır." : "Zorunlu öncüller bitmeden bu görev başlatılamaz ya da tamamlanamaz (Workiom öncül kilidi). Görsel bağ yalnızca Gantt'ta ok olarak görünür, kilitlemez." }));
    const ul = el("ul", { class: "pred-list" });
    if (!t.deps.length) ul.append(el("li", { class: "muted", text: isK ? "Bağlı görev yok" : "Öncül yok" }));
    for (const d of t.deps) {
      const p = S.byId.get(d.id);
      ul.append(el("li", null,
        el("span", { class: "pn" }, el("b", { text: "#" + (p?.num ?? "?") + " " }), p ? p.name : d.label, isK ? "" : " (" + DEP_T[d.type || 1] + ")"),
        p ? chip(p.status) : null,
        isK ? null : el("button", { class: "dep-kind" + (d.hard === false ? " soft" : ""), type: "button", disabled: !S.edit || null,
          title: d.hard === false ? "Yalnızca görsel: kilitlemez. Zorunlu yapmak için tıklayın." : "Zorunlu: tamamlanmadan bu görev başlatılamaz. Görsel yapmak için tıklayın.",
          onclick: () => { d.hard = d.hard === false; S.pending.add(t.id); relayout(); openDetail(t, (t.kind === "K" ? "Bağlı görevler" : "Öncüller")); toast("Bağ türü: " + (d.hard ? "zorunlu" : "yalnızca görsel") + " (kaydedilmedi)"); } },
          d.hard === false ? "Görsel" : "🔒 Zorunlu"),
        S.edit ? el("button", { class: "icon-btn", type: "button", "aria-label": "Kaldır", title: "Kaldır", onclick: () => {
          t.deps = t.deps.filter(x => x.id !== d.id); S.pending.add(t.id); relayout(); openDetail(t, (t.kind === "K" ? "Bağlı görevler" : "Öncüller"));
          toast("Bağ kaldırıldı (kaydedilmedi)");
        } }, icon("x", 14)) : null));
    }
    body.append(ul);
    if (S.edit) {
      const cand = S.tasks.filter(x => x.id !== t.id && !t.deps.some(d => d.id === x.id)).sort((a, b) => a.num - b.num);
      const sel = el("select", { class: "input", "aria-label": isK ? "Bağlı görev ekle" : "Öncül ekle" }, el("option", { value: "", text: isK ? "Görev seçin…" : "Öncül seçin…" }),
        ...cand.map(x => el("option", { value: x.id, text: "#" + x.num + " · " + x.name })));
      const typ = el("select", { class: "input narrow", "aria-label": "Bağ türü", disabled: isK || null }, ...[[1, "FS"], [2, "SS"], [3, "FF"], [4, "SF"]].map(([n, l]) => el("option", { value: String(n), text: l })));
      const kind = el("select", { class: "input narrow", "aria-label": "Zorunluluk", disabled: isK || null }, el("option", { value: "1", text: "Zorunlu" }), el("option", { value: "0", text: "Görsel" }));
      body.append(el("div", { class: "inline-row" }, sel, typ, kind, el("button", { class: "btn sm", type: "button", text: "Ekle", onclick: () => { if (sel.value) { addLink(sel.value, t.id, Number(typ.value), kind.value === "1"); openDetail(t, (t.kind === "K" ? "Bağlı görevler" : "Öncüller")); } } })));
    }
    if (!isK) {
      const succ = [...S.tasks, ...S.mss].filter(x => x.deps.some(d => d.id === t.id));
      body.append(el("div", { class: "section-t", text: "Ardıllar" }));
      const sl = el("ul", { class: "pred-list" });
      if (!succ.length) sl.append(el("li", { class: "muted", text: "Ardıl yok" }));
      succ.forEach(s => sl.append(el("li", null, el("span", { class: "pn" }, el("b", { text: "#" + s.num + " " }), s.kind === "K" ? "◆ " + s.name : s.name), chip(s.status))));
      body.append(sl);
    }
    if (S.pending.size) body.append(el("p", { class: "hint", text: "Değişiklikler şeritteki Kaydet ile yazılır." }));
  }

  function notesPane(t, body) {
    const ta = el("textarea", { class: "input", rows: "6" }); ta.value = t.notes || "";
    const err = el("div", { class: "error-box", role: "alert" });
    const btn = el("button", { class: "btn primary", type: "button", text: "Notu kaydet" });
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try { await updateRecord("G", t.id, { [fid("G", "Notlar")]: ta.value.trim() || null }); t.notes = ta.value.trim(); toast("Not kaydedildi", "ok"); plan.render(); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; }
      finally { btn.disabled = false; }
    });
    body.append(field("Notlar", ta), saveBar(err, btn), el("div", { class: "section-t", text: "Dokümanlar" }),
      fileEditor(t.files, async next => {
        await updateRecord("G", t.id, { [fid("G", "Dokümanlar")]: next });
        t.files = next; toast("Doküman yüklendi", "ok"); clear(body); notesPane(t, body);
      }));
  }

  function msGeneral(t, body) {
    body.append(kv([
      ["Hedef tarih", fmtDay(t.start)], ["Durum", t.status], ["Gerçekleşen", t.actual != null ? fmtDay(t.actual) : "—"],
      ["Baseline", t.baseStart != null ? fmtDay(t.baseStart) + (t.variance ? " (sapma " + (t.variance > 0 ? "+" : "") + t.variance + " gün)" : "") : "alınmadı"],
      ["Bağlı görev", t.deps.length + " (" + t.openLinked + " açık)"], ["Faz", t.phaseName || "—"]
    ]));
    const err = el("div", { class: "error-box", role: "alert" });
    const fName = el("input", { class: "input", value: t.name });
    const fPhase = el("select", { class: "input" }, ...phaseOptions(t.phase));
    const fSt = el("select", { class: "input" }, ...L.K.f["KT Durumu"].opts.map(x => el("option", { value: x, text: x, selected: x === t.status || null })));
    const fCrit = el("input", { type: "checkbox", checked: t.critical0 || null });
    const fDesc = el("textarea", { class: "input", rows: "3" }); fDesc.value = t.desc || "";
    const btn = el("button", { class: "btn primary", type: "button", text: "Kaydet", disabled: !S.edit || null });
    body.append(el("div", { class: "section-t", text: "Bilgiler" }), reqNote(), field("Kilometre taşı", fName, { required: true }),
      el("div", { class: "grid2" }, field("Faz", fPhase), field("Durum", fSt)),
      el("label", { class: "check" }, fCrit, " Kritik kilometre taşı"), field("Açıklama", fDesc), saveBar(err, btn),
      el("p", { class: "hint", text: "Hedef tarihi Gantt'ta ◆ simgesini sürükleyerek ya da Başlangıç hücresinden değiştirin." }));
    btn.addEventListener("click", async () => {
      const nameId = fid("K", "Kilometre Taşı");
      if (!checkRequired([{ id: nameId, name: "Kilometre taşı", control: fName }], { [nameId]: fName.value }, err)) return;
      const p = {};
      if (fName.value.trim() !== t.name) p[nameId] = fName.value.trim();
      if (fPhase.value !== t.phase) p[fid("K", "Faz")] = [fPhase.value];
      if (fSt.value !== t.status) p[fid("K", "KT Durumu")] = fSt.value;
      if (fCrit.checked !== !!t.critical0) p[fid("K", "Kritik")] = fCrit.checked;
      if ((fDesc.value || "") !== (t.desc || "")) p[fid("K", "Açıklama")] = fDesc.value || null;
      if (!Object.keys(p).length) { toast("Değişiklik yok"); return; }
      btn.disabled = true;
      try { await updateRecord("K", t.id, p); toast("Kilometre taşı kaydedildi", "ok"); closeDetail(); softReload(); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; btn.disabled = false; }
    });
  }

  function phaseGeneral(t, body) {
    const work = t.children.filter(c => c.kind === "G");
    body.append(kv([
      ["Tarihler", fmtDay(t.start) + " → " + fmtDay(t.end) + (t.start != null ? " (" + (t.end - t.start) + " gün)" : "")],
      ["İlerleme", "%" + Math.round(t.pct || 0) + " · " + work.filter(x => x.closed).length + "/" + work.length + " görev kapandı"],
      ["Kilometre taşı", String(t.children.filter(c => c.kind === "K").length)],
      ["Baseline", t.baseStart != null ? fmtDay(t.baseStart) + " → " + fmtDay(t.baseEnd) : "alınmadı"]
    ]));
    const err = el("div", { class: "error-box", role: "alert" });
    const fName = el("input", { class: "input", value: t.name });
    const fOrder = el("input", { class: "input", type: "number", value: String(t.order || 0) });
    const fDesc = el("textarea", { class: "input", rows: "3" }); fDesc.value = t.desc || "";
    const btn = el("button", { class: "btn primary", type: "button", text: "Kaydet", disabled: !S.edit || null });
    body.append(el("div", { class: "section-t", text: "Faz bilgileri" }), reqNote(), field("Faz adı", fName, { required: true }), field("Sıra", fOrder), field("Açıklama", fDesc), saveBar(err, btn),
      el("p", { class: "hint", text: "Faz tarihleri içindeki görevlerden hesaplanır ve plan kaydedilirken Fazlar listesine yazılır." }));
    btn.addEventListener("click", async () => {
      const nameId = fid("F", "Faz");
      if (!checkRequired([{ id: nameId, name: "Faz adı", control: fName }], { [nameId]: fName.value }, err)) return;
      const p = {};
      if (fName.value.trim() !== t.name) p[nameId] = fName.value.trim();
      if (Number(fOrder.value) !== t.order) p[fid("F", "Sıra")] = Number(fOrder.value) || 0;
      if ((fDesc.value || "") !== (t.desc || "")) p[fid("F", "Açıklama")] = fDesc.value || null;
      if (!Object.keys(p).length) { toast("Değişiklik yok"); return; }
      btn.disabled = true;
      try { await updateRecord("F", t.id, p); toast("Faz kaydedildi", "ok"); closeDetail(); softReload(); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; btn.disabled = false; }
    });
  }

  function projectGeneral(body) { projectForm(S.proj, body, () => { closeDetail(); load(true); loadProjects(); }); }

  /* ── başlat ─────────────────────────────────────────────────────── */
  await load();
  return {
    dirty: hasPending,
    unmount() { S.alive = false; closeDetail(); plan.destroy(); }
  };
} };

/* Proje bilgileri formu (Plan ve Portföy ortak) */
function projectForm(rec, body, onSaved) {
  const g = n => v(rec, "P", n);
  const err = el("div", { class: "error-box", role: "alert" });
  const fName = el("input", { class: "input", value: g("Proje Adı") || "" });
  const fProd = el("input", { class: "input", value: g("Ürün / Molekül") || "" });
  const fPM = userSelect(g("Proje Yöneticisi"), "— proje yöneticisi —");
  const fSt = el("select", { class: "input" }, ...L.P.f["Durum"].opts.map(x => el("option", { value: x, text: x, selected: x === lbl(g("Durum")) || null })));
  const fEnd = el("input", { class: "input", type: "date", value: toDay(g("Hedef Bitiş")) != null ? dayToISO(toDay(g("Hedef Bitiş"))) : "" });
  const fTeam = multiUserSelect(g("Proje Ekibi"));
  const fDesc = el("textarea", { class: "input", rows: "3" }); fDesc.value = g("Proje Açıklaması") || "";
  const btn = el("button", { class: "btn primary", type: "button", text: "Kaydet" });
  body.append(el("dl", { class: "kv" },
      el("dt", { text: "Proje kodu" }), el("dd", { text: "P" + (g("Proje Kodu") ?? "") }),
      el("dt", { text: "Şablon" }), el("dd", { text: linkLabel(g("Şablon")) || "—" }),
      el("dt", { text: "Başlangıç" }), el("dd", { text: fmtDay(toDay(g("Başlangıç Tarihi"))) }),
      el("dt", { text: "Plan durumu" }), el("dd", { text: lbl(g("Plan Durumu")) || "—" }),
      el("dt", { text: "Baseline" }), el("dd", { text: g("Baseline No") ? "Baseline " + g("Baseline No") + " · " + fmtDay(toDay(g("Baseline Tarihi"))) : "alınmadı" })),
    reqNote(), err,
    field("Proje adı", fName, { required: true }),
    el("div", { class: "grid2" }, field("Durum", fSt, { required: true }), field("Hedef bitiş", fEnd)),
    el("div", { class: "grid2" }, field("Proje yöneticisi", fPM), field("Ürün / Molekül", fProd)),
    field("Proje ekibi", fTeam, { hint: "Ctrl/⌘ ile birden çok kişi seçin" }),
    field("Açıklama", fDesc),
    el("div", { class: "dr-actions" }, btn),
    el("p", { class: "hint", text: "Durumu 'Plan Onaylandı (Baseline)' yapmak baseline alır. Şablon ve başlangıç tarihi plan kurulduktan sonra değiştirilmez." }));
  btn.addEventListener("click", async () => {
    const nameId = fid("P", "Proje Adı"), stId = fid("P", "Durum");
    if (!checkRequired([{ id: nameId, name: "Proje adı", control: fName }, { id: stId, name: "Durum", control: fSt }], { [nameId]: fName.value, [stId]: fSt.value }, err)) return;
    const p = {};
    if (fName.value.trim() !== (g("Proje Adı") || "")) p[nameId] = fName.value.trim();
    if (fSt.value !== lbl(g("Durum"))) p[stId] = fSt.value;
    if (fEnd.value !== (toDay(g("Hedef Bitiş")) != null ? dayToISO(toDay(g("Hedef Bitiş"))) : "")) p[fid("P", "Hedef Bitiş")] = fEnd.value || null;
    if (fPM.value && fPM.value !== (g("Proje Yöneticisi")?.emailAddress || "")) p[fid("P", "Proje Yöneticisi")] = fPM.value;
    if ((fProd.value || "") !== (g("Ürün / Molekül") || "")) p[fid("P", "Ürün / Molekül")] = fProd.value || null;
    const team = [...fTeam.selectedOptions].map(o => o.value);
    const cur = (g("Proje Ekibi") || []).map(u => u.emailAddress).filter(Boolean);
    if (!fTeam.disabled && fTeam.options.length && team.sort().join() !== cur.sort().join()) p[fid("P", "Proje Ekibi")] = team;
    if ((fDesc.value || "") !== (g("Proje Açıklaması") || "")) p[fid("P", "Proje Açıklaması")] = fDesc.value || null;
    if (!Object.keys(p).length) { toast("Değişiklik yok"); return; }
    btn.disabled = true;
    try { await updateRecord("P", rec._id, p); toast("Proje kaydedildi", "ok"); onSaved && onSaved(); }
    catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; btn.disabled = false; }
  });
}
