/* Kütüphane — şablon planı (referans takvimde MS Project tarzı düzenleme) ve kütüphane tabloları */
"use strict";

VIEWS.kutuphane = { title: "Kütüphane", async mount(ctx) {
  const S = { tab: "plan", tpl: "", tpls: [], fk: [], kk: [], gk: [], depts: [], ref: null,
    rows: [], byId: new Map(), items: [], orig: new Map(), pending: new Set(), casc: true, edit: true, alive: true };
  const box = el("div", { class: "lib-page" });
  clear(ctx.main).append(box);
  let plan = null;
  const changed = t => { const o = S.orig.get(t.id); if (!o) return false; return o.start !== t.start || o.end !== t.end || depKey(o.deps) !== depKey(t.deps); };
  const depKey = ds => ds.map(d => d.id + ":" + (d.type || 1)).sort().join();
  const hasPending = () => [...S.pending].some(id => { const t = S.byId.get(id); return t && changed(t); });
  const inTpl = rec => !S.tpl || linkIds(rec[fid(rec.__l, "Şablonlar")]).includes(S.tpl);

  async function load() {
    stateLoading(box, "Kütüphane yükleniyor…");
    try {
      const [s, fk, kk, gk, d] = await Promise.all([fetchAll("S"), fetchAll("FK"), fetchAll("KK"), fetchAll("GK"), fetchAll("D")]);
      if (!S.alive) return;
      S.tpls = s; S.fk = fk.map(r => (r.__l = "FK", r)); S.kk = kk.map(r => (r.__l = "KK", r)); S.gk = gk.map(r => (r.__l = "GK", r)); S.depts = d;
      if (!S.tpl && s.length) S.tpl = s[0]._id;
      const refs = gk.map(r => toDay(v(r, "GK", "Referans Tarih"))).filter(x => x != null);
      S.ref = refs.length ? refs[0] : inputToDay("2026-01-01");
      draw();
    } catch (e) { stateError(box, e, load); }
  }

  /* ── şablon planı ───────────────────────────────────────────────── */
  function buildTpl() {
    const ref = S.ref;
    const phases = S.fk.filter(inTpl).map(r => {
      const s = ref + (Number(v(r, "FK", "Başlangıç Ofseti (gün)")) || 0);
      return { kind: "F", id: r._id, rec: r, name: v(r, "FK", "Faz") || "(faz)", order: Number(v(r, "FK", "Sıra")) || 0, summary: true, children: [], deps: [],
        recStart: s, recEnd: s + (Number(v(r, "FK", "Süre (gün)")) || 0), start: s, end: s + (Number(v(r, "FK", "Süre (gün)")) || 0) };
    }).sort((a, b) => a.order - b.order);
    const byPhase = new Map(phases.map(f => [f.id, f]));
    const orphan = { kind: "F", id: "__none", name: "Faza atanmamış", summary: true, children: [], deps: [], start: null, end: null };
    const tasks = S.gk.filter(inTpl).map(r => {
      const g = n => v(r, "GK", n);
      return { kind: "T", id: r._id, rec: r, name: g("Görev Adı") || "(adsız)", wbs: Number(g("WBS No")) || 0,
        start: toDay(g("Başlangıç")), end: toDay(g("Bitiş")) ?? toDay(g("Başlangıç")),
        deps: (g("Öncüller") || []).map(o => ({ id: o._id, type: o.dependencyType || 1, label: o.label })),
        phase: linkIds(g("Faz"))[0], dept: linkLabel(g("Sorumlu Departman")), deptId: linkIds(g("Sorumlu Departman"))[0] || "",
        approvalNeeded: !!g("Onay Gerekli"), assumed: !!g("Varsayım"), msIds: linkIds(g("Kilometre Taşları")), tpls: linkIds(g("Şablonlar")), pct: 0, status: "" };
    });
    const tIds = new Set(tasks.map(t => t.id));
    const mss = S.kk.filter(inTpl).map(r => {
      const d = ref + (Number(v(r, "KK", "Gün Ofseti")) || 0);
      return { kind: "K", id: r._id, rec: r, name: v(r, "KK", "Kilometre Taşı") || "(KT)", start: d, end: d, milestone: true, critical0: !!v(r, "KK", "Kritik"),
        phase: linkIds(v(r, "KK", "Faz"))[0], deps: tasks.filter(t => t.msIds.includes(r._id)).map(t => ({ id: t.id, type: 1, label: t.name })), status: "" };
    });
    for (const t of tasks.sort((a, b) => a.wbs - b.wbs)) (byPhase.get(t.phase) || orphan).children.push(t);
    for (const k of mss.sort((a, b) => a.start - b.start)) {
      const f = byPhase.get(k.phase) || orphan;
      let at = -1; f.children.forEach((c, i) => { if (k.deps.some(d => d.id === c.id)) at = i; });
      at < 0 ? f.children.push(k) : f.children.splice(at + 1, 0, k);
    }
    // öncül listesindeki şablon dışı kalemleri gizleme: yalnızca bu şablonda olanlar çizilir
    for (const t of tasks) t.depsAll = t.deps, t.deps = t.deps.filter(d => tIds.has(d.id));
    const top = { kind: "P", id: "__tpl", name: (S.tpls.find(t => t._id === S.tpl) && v(S.tpls.find(t => t._id === S.tpl), "S", "Şablon")) || "Tüm kütüphane", summary: true, deps: [],
      children: [...phases, ...(orphan.children.length ? [orphan] : [])] };
    top.children.forEach(rollup); rollup(top);
    S.rows = [top]; S.items = [...tasks, ...mss];
    let n = 0; const num = t => { if (t.kind !== "P") t.num = ++n; (t.children || []).forEach(num); }; num(top);
    S.byId = new Map(); const reg = t => { S.byId.set(t.id, t); (t.children || []).forEach(reg); }; reg(top);
    markCritical(S.items);
    S.orig = new Map(S.items.map(t => [t.id, { start: t.start, end: t.end, deps: t.deps.map(d => ({ ...d })) }]));
    S.pending.clear();
  }
  function relayout() {
    S.rows[0].children.forEach(rollup); rollup(S.rows[0]);
    markCritical(S.items);
    plan.setRows(S.rows); drawRibbon(); drawStatus();
  }
  function afterEdit(ids) { if (S.casc) cascadeSchedule(S.items, S.byId, ids, S.pending); relayout(); }
  function applyDates(t, s, e) {
    if (t.kind === "K") t.start = t.end = s; else { t.start = s; t.end = Math.max(s, e); }
    S.pending.add(t.id); afterEdit([t.id]);
  }
  function addLink(fromId, toId) {
    const from = S.byId.get(fromId), to = S.byId.get(toId);
    if (!from || !to || from.kind !== "T" || to.summary) return;
    if (to.deps.some(d => d.id === fromId)) { toast("Bu bağ zaten var."); return; }
    if (wouldCycle(S.items, fromId, toId)) { toast("Bu bağ döngü oluşturur.", "err"); return; }
    to.deps.push({ id: fromId, type: 1, label: from.name });
    S.pending.add(toId); afterEdit([fromId]);
    toast("Bağ eklendi: " + from.name + " → " + to.name + " (kaydedilmedi)");
  }
  const dayCol = t => t.start == null ? "" : "G" + (t.start - S.ref);
  const isT = t => t.kind === "T", isTK = t => t.kind === "T" || t.kind === "K";
  const COLS = [
    { key: "num", title: "#", w: 36, cls: "num", render: t => t.kind === "P" ? "0" : String(t.num) },
    { key: "name", title: "Kalem", w: 220, flex: true, edit: { type: "text", get: t => t.name }, editable: t => t.kind !== "P" && t.id !== "__none" },
    { key: "dur", title: "Süre", w: 58, cls: "r", render: t => t.start == null ? "" : (t.kind === "K" ? "0 g" : (t.end - t.start) + " g"), edit: { type: "number", get: t => t.end - t.start }, editable: isT },
    { key: "start", title: "Başl. günü", w: 76, cls: "r", render: dayCol, edit: { type: "number", min: "-9999", get: t => t.start - S.ref }, editable: isTK },
    { key: "end", title: "Bitiş günü", w: 76, cls: "r", render: t => t.end == null ? "" : "G" + (t.end - S.ref) },
    { key: "pred", title: "Öncüller", w: 74, render: t => isTK(t) ? predText(t, S.byId) : "", edit: { type: "text", get: t => predText(t, S.byId) }, editable: isTK },
    { key: "dept", title: "Departman", w: 150, render: t => t.dept || "", edit: { type: "select", get: t => t.deptId, options: () => [["", "—"], ...S.depts.map(d => [d._id, v(d, "D", "Departman")])] }, editable: isT },
    { key: "appr", title: "Onay", w: 56, render: t => isT(t) ? (t.approvalNeeded ? "✍ Evet" : "—") : "", edit: { type: "select", get: t => t.approvalNeeded ? "1" : "0", options: () => [["1", "Evet"], ["0", "Hayır"]] }, editable: isT }
  ];

  async function cellEdit(t, key, val) {
    try {
      if (key === "name") {
        const nm = String(val).trim(); if (!nm) { plan.render(); return; }
        const map = { T: ["GK", "Görev Adı"], F: ["FK", "Faz"], K: ["KK", "Kilometre Taşı"] }[t.kind];
        await updateRecord(map[0], t.id, { [fid(map[0], map[1])]: nm }); t.name = nm; toast("Ad kaydedildi", "ok"); plan.render(); return;
      }
      if (key === "dur") { const n = Math.round(Number(val)); if (!(n >= 0)) { plan.render(); return; } return applyDates(t, t.start, t.start + n); }
      if (key === "start") { const n = Math.round(Number(val)); if (!Number.isFinite(n)) { plan.render(); return; } const s = S.ref + n; return applyDates(t, s, t.kind === "K" ? s : s + (t.end - t.start)); }
      if (key === "pred") {
        const r = parsePreds(val); if (r.error) { toast(r.error, "err"); plan.render(); return; }
        const byNum = new Map([...S.byId.values()].filter(x => x.num).map(x => [x.num, x]));
        const deps = [];
        for (const { num, type } of r.list) {
          const p = byNum.get(num);
          if (!p || p.kind !== "T" || p.id === t.id) { toast(num + " geçerli bir kütüphane görevi değil.", "err"); plan.render(); return; }
          deps.push({ id: p.id, type: t.kind === "K" ? 1 : type, label: p.name });
        }
        const old = t.deps; t.deps = [];
        for (const d of deps) if (wouldCycle(S.items, d.id, t.id)) { t.deps = old; toast("Döngü oluşur: " + d.label, "err"); plan.render(); return; }
        t.deps = deps; S.pending.add(t.id); return afterEdit(deps.map(d => d.id));
      }
      if (key === "dept") { await updateRecord("GK", t.id, { [fid("GK", "Sorumlu Departman")]: val ? [val] : null }); toast("Departman kaydedildi", "ok"); return load(); }
      if (key === "appr") { await updateRecord("GK", t.id, { [fid("GK", "Onay Gerekli")]: val === "1" }); t.approvalNeeded = val === "1"; toast("Kaydedildi", "ok"); plan.render(); }
    } catch (e) { if (!(e instanceof SessionGone)) { toast(e.message, "err"); plan.render(); } }
  }

  async function saveAll() {
    const ch = [...S.pending].map(id => S.byId.get(id)).filter(t => t && changed(t));
    if (!ch.length) return;
    const ok = await confirmDialog("Şablon kaydedilsin mi?", ch.length + " kütüphane kalemi güncellenecek. Faz ofset ve süreleri görevlerden yeniden hesaplanır. Değişiklik yalnızca bundan sonra açılacak projeleri etkiler.", "Kaydet");
    if (!ok) return;
    const jobs = [];
    const msChanges = new Map();          // görev id → Kilometre Taşları yeni dizi
    for (const t of ch) {
      const o = S.orig.get(t.id);
      if (t.kind === "T") {
        const p = {};
        if (o.start !== t.start || o.end !== t.end) { p[fid("GK", "Başlangıç")] = dayToISO(t.start); p[fid("GK", "Bitiş")] = dayToISO(t.end); }
        if (depKey(o.deps) !== depKey(t.deps)) {
          const outside = (t.depsAll || []).filter(d => !S.byId.has(d.id));      // başka şablondaki öncüller korunur
          p[fid("GK", "Öncüller")] = [...t.deps, ...outside].map(d => ({ _id: d.id, dependencyType: d.type || 1 }));
        }
        if (Object.keys(p).length) jobs.push(["GK", t.id, p]);
      } else if (t.kind === "K") {
        if (o.start !== t.start) jobs.push(["KK", t.id, { [fid("KK", "Gün Ofseti")]: t.start - S.ref }]);
        if (depKey(o.deps) !== depKey(t.deps)) {
          const before = new Set(o.deps.map(d => d.id)), after = new Set(t.deps.map(d => d.id));
          for (const id of new Set([...before, ...after])) {
            const task = S.byId.get(id); if (!task) continue;
            const cur = msChanges.get(id) || [...task.msIds];
            const nx = after.has(id) ? [...new Set([...cur, t.id])] : cur.filter(x => x !== t.id);
            msChanges.set(id, nx);
          }
        }
      }
    }
    for (const [id, arr] of msChanges) jobs.push(["GK", id, { [fid("GK", "Kilometre Taşları")]: arr }]);
    for (const f of S.rows[0].children) if (f.id !== "__none" && f.start != null && (f.start !== f.recStart || f.end !== f.recEnd))
      jobs.push(["FK", f.id, { [fid("FK", "Başlangıç Ofseti (gün)")]: f.start - S.ref, [fid("FK", "Süre (gün)")]: f.end - f.start }]);
    setStatus(el("span", { class: "spinner sm" }), "Kaydediliyor… 0/" + jobs.length);
    try {
      const errs = await runPool(jobs, ([l, id, p]) => updateRecord(l, id, p), 4, (d, n) => setStatus(el("span", { class: "spinner sm" }), "Kaydediliyor… " + d + "/" + n));
      errs.length ? toast(errs.length + " kayıt yazılamadı: " + errs[0][1].message, "err", 7000) : toast("Şablon kaydedildi: " + jobs.length + " kayıt", "ok");
      await load();
    } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
  }

  function drawPlan(host) {
    if (plan) plan.destroy();
    plan = createPlan(host, {
      columns: COLS, leftWidth: Math.min(820, Math.round((innerWidth - (innerWidth > 900 ? 236 : 0)) * 0.55)), zoom: "ay", refDay: S.ref, showBaseline: false,
      canDrag: isTK, onDragEnd: applyDates, onLink: addLink, onCellEdit: cellEdit, pending: S.pending,
      onOpen: t => t.kind === "T" ? editLibTask(t) : t.kind === "K" ? editRecord("KK", t.rec) : t.kind === "F" && t.id !== "__none" ? editRecord("FK", t.rec) : null,
      onSelect: () => drawStatus(),
      onKey: (e, t) => { if (e.key === "Delete" && t) { e.preventDefault(); delRow(t); } },
      labelFor: t => t.kind === "T" ? t.dept : t.kind === "K" ? t.name : ""
    });
    buildTpl();
    plan.setRows(S.rows);
    plan.scrollToDay(S.ref);
  }
  function drawStatus() {
    if (S.tab !== "plan" || !S.rows[0]) return;
    const n = [...S.pending].filter(id => { const t = S.byId.get(id); return t && changed(t); }).length;
    const sel = plan && plan.selected();
    setStatus(S.items.filter(isT).length + " görev · " + S.items.filter(t => t.kind === "K").length + " kilometre taşı",
      "Toplam süre: " + (S.rows[0].end - S.rows[0].start) + " gün", "Kritik: " + S.items.filter(t => t.critical).length,
      n ? el("span", { class: "sb-pend", text: n + " kaydedilmemiş değişiklik" }) : null, el("span", { class: "spacer" }),
      sel ? "Seçili: " + (sel.num || "") + " · " + sel.name : "Referans takvim: Gün 0 = " + fmtDay(S.ref));
  }

  /* ── kütüphane görevi formu ─────────────────────────────────────── */
  function editLibTask(t) {
    const rec = t ? t.rec : null;
    const g = n => rec ? v(rec, "GK", n) : undefined;
    const m = openModal({ title: rec ? "Kütüphane görevi — " + t.name : "Kütüphaneye görev ekle", form: true, wide: true });
    const err = el("div", { class: "error-box", role: "alert" });
    const fName = el("input", { class: "input", value: g("Görev Adı") || "" });
    const fWbs = el("input", { class: "input", type: "number", step: "0.01", value: g("WBS No") ?? String(Math.max(0, ...S.gk.map(r => Number(v(r, "GK", "WBS No")) || 0)) + 1) });
    const fPhase = el("select", { class: "input" }, el("option", { value: "", text: "— faz —" }), ...S.fk.map(r => el("option", { value: r._id, text: v(r, "FK", "Faz"), selected: linkIds(g("Faz")).includes(r._id) || null })));
    const s0 = rec ? toDay(g("Başlangıç")) - S.ref : 0, d0 = rec ? toDay(g("Bitiş")) - toDay(g("Başlangıç")) : 7;
    const fOff = el("input", { class: "input", type: "number", value: String(s0) });
    const fDur = el("input", { class: "input", type: "number", min: "0", value: String(d0) });
    const fDept = el("select", { class: "input" }, el("option", { value: "", text: "— departman —" }), ...S.depts.map(d => el("option", { value: d._id, text: v(d, "D", "Departman"), selected: linkIds(g("Sorumlu Departman")).includes(d._id) || null })));
    const fOwner = userSelect(g("Varsayılan Sorumlu"), "— departman yöneticisi —");
    const tplBox = el("div", { class: "checks" }, ...S.tpls.map(s => el("label", { class: "check" }, el("input", { type: "checkbox", value: s._id, checked: (rec ? linkIds(g("Şablonlar")).includes(s._id) : s._id === S.tpl) || null }), " " + v(s, "S", "Şablon"))));
    const ktBox = el("div", { class: "checks" }, ...S.kk.map(k => el("label", { class: "check" }, el("input", { type: "checkbox", value: k._id, checked: linkIds(g("Kilometre Taşları")).includes(k._id) || null }), " ◆ " + v(k, "KK", "Kilometre Taşı"))));
    const fNeed = el("input", { type: "checkbox", checked: g("Onay Gerekli") || null });
    const fAss = el("input", { type: "checkbox", checked: g("Varsayım") || null });
    const fKab = el("textarea", { class: "input", rows: "2" }); fKab.value = g("Kabul Kriteri") || "";
    const ok = el("button", { class: "btn primary", type: "submit", text: rec ? "Kaydet" : "Ekle" });
    m.body.append(reqNote(), err, field("Görev adı", fName, { required: true, wide: true }),
      el("div", { class: "grid3" }, field("WBS No", fWbs), field("Başlangıç günü", fOff, { hint: "Gün 0 = proje başlangıcı" }), field("Süre (gün)", fDur)),
      el("div", { class: "grid3" }, field("Faz", fPhase), field("Sorumlu departman", fDept), field("Varsayılan sorumlu", fOwner)),
      el("div", { class: "field" }, el("span", { class: "lbl", text: "Şablonlar" }), tplBox),
      el("div", { class: "field" }, el("span", { class: "lbl", text: "Kilometre taşı koşulu" }), ktBox),
      el("label", { class: "check" }, fNeed, " Tamamlanması için onay gerekli"), el("label", { class: "check" }, fAss, " Varsayım (Excel'de süre/öncül tanımsızdı)"),
      field("Kabul kriteri", fKab, { wide: true }),
      el("p", { class: "hint", text: "Öncülleri şablon planında Öncüller sütunundan ya da Gantt'ta ok çekerek düzenleyin." }));
    m.foot.append(el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => m.close() }), ok);
    m.box.addEventListener("submit", async ev => {
      ev.preventDefault();
      const nameId = fid("GK", "Görev Adı");
      if (!checkRequired([{ id: nameId, name: "Görev adı", control: fName }], { [nameId]: fName.value }, err)) return;
      const off = Math.round(Number(fOff.value) || 0), dur = Math.max(0, Math.round(Number(fDur.value) || 0));
      const p = {
        [nameId]: fName.value.trim(), [fid("GK", "WBS No")]: Number(fWbs.value) || 0,
        [fid("GK", "Başlangıç")]: dayToISO(S.ref + off), [fid("GK", "Bitiş")]: dayToISO(S.ref + off + dur), [fid("GK", "Referans Tarih")]: dayToISO(S.ref),
        [fid("GK", "Onay Gerekli")]: fNeed.checked, [fid("GK", "Varsayım")]: fAss.checked,
        [fid("GK", "Şablonlar")]: [...tplBox.querySelectorAll("input:checked")].map(i => i.value),
        [fid("GK", "Kilometre Taşları")]: [...ktBox.querySelectorAll("input:checked")].map(i => i.value)
      };
      if (fPhase.value) p[fid("GK", "Faz")] = [fPhase.value]; else if (rec) p[fid("GK", "Faz")] = null;
      if (fDept.value) p[fid("GK", "Sorumlu Departman")] = [fDept.value]; else if (rec) p[fid("GK", "Sorumlu Departman")] = null;
      if (fOwner.value) p[fid("GK", "Varsayılan Sorumlu")] = fOwner.value;
      if (fKab.value.trim()) p[fid("GK", "Kabul Kriteri")] = fKab.value.trim(); else if (rec) p[fid("GK", "Kabul Kriteri")] = null;
      if (!rec) { for (const k of Object.keys(p)) if (isEmptyValue(p[k])) delete p[k]; }
      ok.disabled = true;
      try { rec ? await updateRecord("GK", rec._id, p) : await createRecord("GK", p); m.close(); toast(rec ? "Kütüphane görevi kaydedildi" : "Kütüphaneye eklendi", "ok"); load(); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; ok.disabled = false; }
    });
  }

  /* ── genel kayıt formu / tablo (Faz, KT, Şablon, Departman) ─────── */
  const TABLES = {
    FK: { title: "Faz kütüphanesi", cols: [["Faz", "text"], ["Sıra", "number"], ["Başlangıç Ofseti (gün)", "number"], ["Süre (gün)", "number"], ["Şablonlar", "link:S"], ["Açıklama", "longtext"]], sort: r => Number(v(r, "FK", "Sıra")) || 0 },
    KK: { title: "Kilometre taşı kütüphanesi", cols: [["Kilometre Taşı", "text"], ["Gün Ofseti", "number"], ["Faz", "link1:FK"], ["Kritik", "bool"], ["Şablonlar", "link:S"], ["Açıklama", "longtext"]], sort: r => Number(v(r, "KK", "Gün Ofseti")) || 0 },
    S: { title: "Proje şablonları", cols: [["Şablon", "text"], ["Toplam Süre (gün)", "number"], ["Aktif", "bool"], ["Açıklama", "longtext"]], sort: r => v(r, "S", "Şablon") || "" },
    D: { title: "Departmanlar", cols: [["Departman", "text"], ["Kod", "text"], ["Departman Yöneticisi", "user"], ["Onaylayıcı", "user"], ["Ekip Üyeleri", "users"], ["Açıklama", "longtext"]], sort: r => v(r, "D", "Departman") || "" }
  };
  const srcOf = key => ({ S: S.tpls, FK: S.fk, D: S.depts }[key] || []);
  const nameOf = (key, r) => v(r, key, { S: "Şablon", FK: "Faz", D: "Departman" }[key]);
  function cellText(list, r, [name, type]) {
    const x = v(r, list, name);
    if (type === "bool") return x ? "Evet" : "—";
    if (type === "user") return userName(x) || "—";
    if (type === "users") return (x || []).map(userName).join(", ") || "—";
    if (type.startsWith("link")) return linkLabel(x) || "—";
    return x == null || x === "" ? "—" : String(x);
  }
  function editRecord(list, rec) {
    const cfg = TABLES[list];
    const m = openModal({ title: (rec ? "Düzenle — " : "Yeni — ") + cfg.title, form: true, wide: true });
    const err = el("div", { class: "error-box", role: "alert" });
    const ctrls = [];
    m.body.append(reqNote(), err);
    for (const [name, type] of cfg.cols) {
      const f = L[list].f[name], cur = rec ? v(rec, list, name) : undefined;
      let c;
      if (type === "bool") c = el("input", { type: "checkbox", checked: (rec ? cur : name === "Aktif") || null });
      else if (type === "user") c = userSelect(cur, "— seçin —");
      else if (type === "users") c = multiUserSelect(cur || []);
      else if (type.startsWith("link")) {
        const key = type.split(":")[1], multi = type.startsWith("link:");
        c = el("select", { class: "input", multiple: multi || null, size: multi ? "3" : null }, multi ? null : el("option", { value: "", text: "—" }),
          ...srcOf(key).map(r => el("option", { value: r._id, text: nameOf(key, r), selected: linkIds(cur).includes(r._id) || (!rec && key === "S" && r._id === S.tpl) || null })));
      } else if (type === "longtext") { c = el("textarea", { class: "input", rows: "2" }); c.value = cur || ""; }
      else c = el("input", { class: "input", type: type === "number" ? "number" : "text", value: cur ?? "" });
      ctrls.push([name, type, c, f]);
      const req = !!(f.req || f.pri);
      m.body.append(type === "bool" ? el("label", { class: "check" }, c, " " + name) : field(name, c, { required: req, wide: type === "longtext" }));
    }
    const ok = el("button", { class: "btn primary", type: "submit", text: rec ? "Kaydet" : "Ekle" });
    m.foot.append(el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => m.close() }), ok);
    m.box.addEventListener("submit", async ev => {
      ev.preventDefault();
      const vals = {};
      for (const [name, type, c, f] of ctrls) {
        let x;
        if (type === "bool") x = c.checked;
        else if (type === "users" || type === "link:S" || type.startsWith("link:")) x = [...c.selectedOptions].map(o => o.value);
        else if (type.startsWith("link1")) x = c.value ? [c.value] : [];
        else if (type === "number") x = c.value === "" ? null : Number(c.value);
        else x = c.value.trim ? c.value.trim() : c.value;
        vals[String(f.id)] = x;
      }
      const reqs = ctrls.filter(([, , , f]) => f.req || f.pri).map(([name, , c, f]) => ({ id: f.id, name, control: c }));
      if (!checkRequired(reqs, vals, err)) return;
      const p = {};
      for (const [k, x] of Object.entries(vals)) {
        if (rec) p[k] = isEmptyValue(x) ? null : x;
        else if (!isEmptyValue(x)) p[k] = x;
      }
      if (rec) for (const [name, type, c, f] of ctrls) if (type === "user" && !c.value) delete p[String(f.id)];
      ok.disabled = true;
      try { rec ? await updateRecord(list, rec._id, p) : await createRecord(list, p); m.close(); toast("Kaydedildi", "ok"); load(); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; ok.disabled = false; }
    });
  }
  async function delRecord(list, rec, name) {
    if (!(await confirmDialog("Silinsin mi?", name + " kütüphaneden silinecek. Açılmış projeler etkilenmez; bu kaydı kullanan şablon kalemlerinin bağlantısı boşalır. Geri alınamaz.", "Sil", true))) return;
    try { await deleteRecord(list, rec._id); toast("Silindi", "ok"); load(); } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
  }
  async function delRow(t) {
    if (t.kind === "P" || t.id === "__none") return;
    if (hasPending()) { toast("Önce bekleyen değişiklikleri kaydedin ya da geri alın.", "err"); return; }
    if (t.kind === "F" && t.children.length) { toast("İçinde kalem olan faz silinemez.", "err"); return; }
    const list = { T: "GK", K: "KK", F: "FK" }[t.kind];
    if (t.kind === "T") {
      const succ = S.gk.filter(r => (v(r, "GK", "Öncüller") || []).some(o => o._id === t.id));
      if (!(await confirmDialog("Kütüphane görevi silinsin mi?", t.name + (succ.length ? " — " + succ.length + " kalemin öncül listesinden de çıkarılacak." : "") + " Açılmış projeler etkilenmez.", "Sil", true))) return;
      try {
        for (const r of succ) await updateRecord("GK", r._id, { [fid("GK", "Öncüller")]: (v(r, "GK", "Öncüller") || []).filter(o => o._id !== t.id).map(o => ({ _id: o._id, dependencyType: o.dependencyType || 1 })) });
        await deleteRecord("GK", t.id); toast("Silindi", "ok"); load();
      } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
      return;
    }
    delRecord(list, t.rec, t.name);
  }
  function drawTable(list) {
    const cfg = TABLES[list];
    const recs = [...({ FK: S.fk, KK: S.kk, S: S.tpls, D: S.depts }[list])].sort((a, b) => { const x = cfg.sort(a), y = cfg.sort(b); return typeof x === "number" ? x - y : String(x).localeCompare(String(y), "tr"); });
    const tbl = el("table", { class: "tbl" });
    tbl.append(el("thead", null, el("tr", null, ...cfg.cols.map(([n]) => el("th", { text: n })), el("th", { text: "" }))));
    const tb = el("tbody");
    for (const r of recs) tb.append(el("tr", { class: "click", onclick: () => editRecord(list, r) },
      ...cfg.cols.map(c => el("td", { class: c[1] === "longtext" ? "wrap" : "", text: cellText(list, r, c) })),
      el("td", null, el("button", { class: "icon-btn", type: "button", "aria-label": "Sil", title: "Sil", onclick: e => { e.stopPropagation(); delRecord(list, r, cellText(list, r, cfg.cols[0])); } }, icon("trash", 15)))));
    tbl.append(tb);
    setStatus(recs.length + " kayıt · " + cfg.title);
    return el("div", { class: "page" }, recs.length ? el("div", { class: "card tbl-wrap" }, tbl) : el("div", { class: "card" }, el("p", { class: "muted", text: "Kayıt yok." })));
  }

  /* ── çizim ──────────────────────────────────────────────────────── */
  function drawRibbon() {
    const n = [...S.pending].filter(id => { const t = S.byId.get(id); return t && changed(t); }).length;
    const tabSeg = rseg([["plan", "Şablon planı"], ["FK", "Fazlar"], ["KK", "Kilometre taşları"], ["S", "Şablonlar"], ["D", "Departmanlar"]], S.tab, async x => {
      if (hasPending() && !(await confirmDialog("Kaydedilmemiş değişiklikler", "Şablon planındaki değişiklikler atılsın mı?", "At", true))) { drawRibbon(); return; }
      S.tab = x; draw();
    }, "Kütüphane bölümü");
    const groups = [rgroup("Bölüm", tabSeg)];
    if (S.tab === "plan") {
      const ts = el("select", { class: "rsel", "aria-label": "Şablon" }, ...S.tpls.map(s => el("option", { value: s._id, text: v(s, "S", "Şablon"), selected: s._id === S.tpl || null })), el("option", { value: "", text: "Tüm kütüphane", selected: !S.tpl || null }));
      ts.addEventListener("change", async () => {
        if (hasPending() && !(await confirmDialog("Kaydedilmemiş değişiklikler", "Değişiklikler atılsın mı?", "At", true))) { ts.value = S.tpl; return; }
        S.tpl = ts.value; draw();
      });
      groups.push(
        rgroup("Şablon", ts),
        rgroup("Zamanlama", rbtn({ icon: "save", text: n ? "Kaydet (" + n + ")" : "Kaydet", big: true, cls: n ? "hot" : "", disabled: !n, onclick: saveAll }),
          el("div", { class: "rcol" }, rbtn({ icon: "undo", text: "Geri al", disabled: !n, onclick: () => { buildTpl(); plan.setRows(S.rows); drawRibbon(); drawStatus(); } }),
            rcheck("Otomatik zamanlama", S.casc, on => { S.casc = on; }))),
        rgroup("Ekle", rbtn({ icon: "plus", text: "Görev", big: true, onclick: () => editLibTask(null) }),
          el("div", { class: "rcol" }, rbtn({ icon: "ms", text: "Kilometre taşı", onclick: () => editRecord("KK", null) }), rbtn({ icon: "phase", text: "Faz", onclick: () => editRecord("FK", null) }),
            rbtn({ icon: "trash", text: "Sil", onclick: () => { const t = plan && plan.selected(); t ? delRow(t) : toast("Önce bir satır seçin"); } }))),
        rgroup("Görünüm", el("div", { class: "rcol" }, rseg([["hafta", "Hafta"], ["ay", "Ay"], ["ceyrek", "Çeyrek"], ["yil", "Yıl"]], "ay", z => plan.setZoom(z), "Ölçek"),
          rcheck("Kritik yol", true, on => plan.setOption("showCritical", on)))));
    } else groups.push(rgroup("Ekle", rbtn({ icon: "plus", text: "Yeni kayıt", big: true, onclick: () => editRecord(S.tab, null) })));
    groups.push(rgroup("Veri", rbtn({ icon: "refresh", text: "Yenile", onclick: load })));
    clear(ctx.ribbon).append(...groups);
  }
  function draw() {
    if (S.tab === "plan") {
      const host = el("div", { class: "plan-grid" });
      clear(box).append(el("div", { class: "lib-note" }, icon("info", 16),
        el("span", { text: "Şablon planı \"Gün 0\" referans takvimindedir. Burada yapılan değişiklikler yalnızca bundan sonra açılacak projelere uygulanır." })), host);
      drawRibbon();
      drawPlan(host);
      drawStatus();
    } else {
      if (plan) { plan.destroy(); plan = null; }
      drawRibbon();
      clear(box).append(drawTable(S.tab));
    }
  }

  drawRibbon();
  await load();
  return { dirty: hasPending, unmount() { S.alive = false; if (plan) plan.destroy(); } };
} };
