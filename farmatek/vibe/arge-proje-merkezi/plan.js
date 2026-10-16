/* Proje planı: MS Project tarzı Gantt — PM sürükle-bırak (taşı / süre / bağ), bağımlı kaydırma,
   öncül ve görev düzenleme, baseline, Excel, departman filtresi, değişiklik geçmişi */
"use strict";

const PID = new URLSearchParams(location.search).get("id");
let ME = null, PROJ = null, TASKS = [], BYID = new Map(), IS_PM = false, DEPTS = [];
let ORIG = new Map();            // id → {start, end, deps}  (son kaydedilmiş hâl)
const PENDING = new Set();       // tarih ya da öncülü değişen görevler
const host = document.getElementById("gantt");
const kpiBox = document.getElementById("kpis");
const pendBox = document.getElementById("pending");
const casc = document.getElementById("chk-casc");
const fDept = document.getElementById("f-dept");
const fMine = document.getElementById("f-mine");

const gantt = createGantt(host, {
  zoom: "ay", onSelect: openTask,
  editable: () => IS_PM,
  onDragEnd: (t, s, e) => applyChange(t.id, s, e),
  onLink: (from, to) => addLink(from, to),
  pending: PENDING,
  rowFilter: t => (!fDept.value || t.dept === fDept.value) && (!fMine.checked || (t.owner && String(t.owner.id) === String(ME.id)))
});

function kpi(label, value, sub) {
  return el("div", { class: "card kpi" }, el("div", { class: "label", text: label }), el("div", { class: "value", text: String(value) }), el("div", { class: "sub", text: sub || "" }));
}
const leaves = () => TASKS.filter(t => !t.summary);

function renderHead() {
  const ad = v(PROJ, "P", "Proje Adı") || "Proje";
  document.title = ad + " · Proje Planı";
  document.getElementById("p-title").textContent = ad;
  const sub = document.getElementById("p-sub");
  clear(sub).append(chip(lbl(v(PROJ, "P", "Durum"))), " ",
    "P" + (v(PROJ, "P", "Proje Kodu") ?? "") + " · " + lbl((v(PROJ, "P", "Şablon") || [])[0]) +
    " · PM: " + (userName(v(PROJ, "P", "Proje Yöneticisi")) || "—") +
    (v(PROJ, "P", "Baseline No") ? " · Baseline " + v(PROJ, "P", "Baseline No") + " (" + fmtDay(toDay(v(PROJ, "P", "Baseline Tarihi"))) + ")" : " · baseline alınmadı"));
  document.getElementById("btn-baseline").hidden = !IS_PM;
  document.getElementById("btn-add").hidden = !IS_PM;
  document.getElementById("pm-hint").textContent = IS_PM
    ? "Proje yöneticisi olarak: çubuğu sürükleyerek taşıyın, sağ ucundan çekerek süreyi değiştirin, çubuğun yanındaki noktadan başka bir göreve sürükleyerek bağımlılık ekleyin. Değişiklikler 'Kaydet' deyinceye kadar taslak kalır."
    : "Plan yapısı (tarih, süre, öncül, sorumlu) yalnızca proje yöneticisi tarafından değiştirilebilir. Size atanan görevleri Görevlerim sayfasından güncelleyebilirsiniz.";
}

function renderKPIs() {
  const ls = leaves();
  const w = t => Math.max(1, t.end - t.start);
  const tot = ls.reduce((a, t) => a + w(t), 0);
  const pct = tot ? Math.round(ls.reduce((a, t) => a + w(t) * (t.pct || 0), 0) / tot) : 0;
  const end = ls.length ? Math.max(...ls.map(t => t.end)) : null;
  const bEnds = ls.map(t => t.baseEnd).filter(x => x != null);
  const bEnd = bEnds.length ? Math.max(...bEnds) : null;
  const sapma = end != null && bEnd != null ? end - bEnd : null;
  clear(kpiBox).append(
    kpi("Tamamlanma", "%" + pct, ls.filter(t => t.closed).length + "/" + ls.length + " görev kapandı"),
    kpi("Planlanan bitiş", fmtDay(end), bEnd != null ? "Baseline: " + fmtDay(bEnd) : "Baseline yok"),
    kpi("Bitiş sapması", sapma == null ? "—" : (sapma > 0 ? "+" : "") + sapma + " gün", sapma > 0 ? "baseline'a göre gecikme" : sapma < 0 ? "baseline'dan önde" : ""),
    kpi("Geciken görev", ls.filter(t => t.late).length, ls.filter(t => t.late && t.critical).length + " tanesi kritik yolda"),
    kpi("Onay bekleyen", ls.filter(t => t.status === "Onay Bekliyor").length, "zorunlu onay adımı"));
}

function snapshot() {
  ORIG = new Map(TASKS.map(t => [t.id, { start: t.start, end: t.end, deps: t.deps.map(d => ({ ...d })) }]));
  PENDING.clear();
}

async function load(keepSel) {
  if (!TASKS.length) stateLoading(host, "Plan yükleniyor…");
  try {
    const [p, all, depts] = await Promise.all([getRecord("P", PID), fetchAll("G"), fetchAll("D").catch(() => [])]);
    PROJ = p; DEPTS = depts;
    IS_PM = (v(p, "P", "Proje Yöneticisi")?.id || "") === String(ME.id);
    TASKS = all.filter(r => linkIds(v(r, "G", "Proje")).includes(PID)).map(r => taskModel(r, "G"));
    BYID = new Map(TASKS.map(t => [t.id, t]));
    renderHead();
    const cur = fDept.value;
    clear(fDept).append(el("option", { value: "", text: "Tüm departmanlar" }),
      ...[...new Set(TASKS.map(t => t.dept).filter(Boolean))].sort((a, b) => a.localeCompare(b, "tr")).map(d => el("option", { value: d, text: d, selected: d === cur || null })));
    if (!TASKS.length) {
      stateEmpty(host, "Bu projede görev yok", lbl(v(p, "P", "Plan Durumu")) && lbl(v(p, "P", "Plan Durumu")) !== "Hazır"
        ? "Plan otomasyonla kuruluyor (" + lbl(v(p, "P", "Plan Durumu")) + "). Birkaç dakika sonra yenileyin."
        : "Proje bir şablonla oluşturulmamış olabilir.", el("button", { class: "btn", type: "button", onclick: () => load(), text: "↻ Yenile" }));
      clear(kpiBox);
      return;
    }
    snapshot();
    gantt.setTasks(TASKS);
    renderKPIs(); renderPending();
    if (!keepSel) gantt.scrollToToday();
  } catch (e) {
    stateError(host, e, () => load());
  }
}

/* ── bağımlılık kaydırma (öncülden sonra başla; tampon korunur, geri çekilmez) ── */
function cascadeFrom(ids) {
  const succ = new Map();
  for (const t of leaves()) for (const d of t.deps) {
    if (!succ.has(d.id)) succ.set(d.id, []);
    succ.get(d.id).push(t);
  }
  const queue = [...ids];
  let guard = 0;
  while (queue.length && guard++ < 20000) {
    const id = queue.shift();
    for (const s of succ.get(id) || []) {
      const dur = s.end - s.start;
      let need = -Infinity;
      for (const d of s.deps) {
        const p = BYID.get(d.id); if (!p) continue;
        if (d.type === 2) need = Math.max(need, p.start);              // SS
        else if (d.type === 3) need = Math.max(need, p.end - dur);      // FF
        else if (d.type === 4) need = Math.max(need, p.start - dur);    // SF
        else need = Math.max(need, p.end);                              // FS
      }
      if (need > s.start) { s.start = need; s.end = need + dur; PENDING.add(s.id); queue.push(s.id); }
    }
  }
}

function refreshAfterEdit() {
  gantt.setTasks(TASKS);     // özetleri ve kritik yolu yeniden hesaplar
  renderKPIs(); renderPending();
}

function applyChange(id, start, end) {
  const t = BYID.get(id);
  if (!t || !IS_PM) return;
  t.start = start; t.end = Math.max(start, end);
  PENDING.add(id);
  if (casc.checked) cascadeFrom([id]);
  refreshAfterEdit();
}

function wouldCycle(fromId, toId) {           // to → … → from yolu varsa from→to bağı döngü yaratır
  const succ = new Map();
  for (const t of leaves()) for (const d of t.deps) { if (!succ.has(d.id)) succ.set(d.id, []); succ.get(d.id).push(t.id); }
  const seen = new Set([toId]), stack = [toId];
  while (stack.length) {
    const x = stack.pop();
    if (x === fromId) return true;
    for (const n of succ.get(x) || []) if (!seen.has(n)) { seen.add(n); stack.push(n); }
  }
  return false;
}

function addLink(fromId, toId, type) {
  const from = BYID.get(fromId), to = BYID.get(toId);
  if (!from || !to || !IS_PM) return;
  if (from.summary || to.summary) { toast("Bağımlılık yalnızca görevler arasında kurulabilir (faz satırı değil).", "err"); return; }
  if (to.deps.some(d => d.id === fromId)) { toast("Bu bağımlılık zaten var.", ""); return; }
  if (wouldCycle(fromId, toId)) { toast("Bu bağ döngü oluşturur: " + to.name + " zaten " + from.name + " görevinden önce gelmeli.", "err", 5000); return; }
  to.deps.push({ id: fromId, type: type || 1, label: from.name });
  PENDING.add(toId);
  if (casc.checked) cascadeFrom([fromId]);
  refreshAfterEdit();
  toast("Bağımlılık eklendi: " + from.name + " → " + to.name + " (kaydedilmedi)");
}

function removeLink(toId, fromId) {
  const to = BYID.get(toId);
  to.deps = to.deps.filter(d => d.id !== fromId);
  PENDING.add(toId);
  refreshAfterEdit();
}

function depsChanged(t) {
  const o = ORIG.get(t.id);
  const a = o.deps.map(d => d.id + ":" + d.type).sort().join(), b = t.deps.map(d => d.id + ":" + d.type).sort().join();
  return a !== b;
}
function datesChanged(t) { const o = ORIG.get(t.id); return o.start !== t.start || o.end !== t.end; }

function renderPending() {
  const ch = [...PENDING].map(id => BYID.get(id)).filter(t => t && (datesChanged(t) || depsChanged(t)));
  if (!ch.length) { PENDING.clear(); pendBox.hidden = true; clear(pendBox); return; }
  const oldEnd = Math.max(...leaves().map(t => ORIG.get(t.id).end));
  const newEnd = Math.max(...leaves().map(t => t.end));
  const nDates = ch.filter(datesChanged).length, nDeps = ch.filter(depsChanged).length;
  const save = el("button", { class: "btn primary", type: "button", text: "Kaydet" });
  const undo = el("button", { class: "btn", type: "button", text: "Geri al", onclick: undoAll });
  const detail = el("details", null, el("summary", { text: "Ayrıntı" }),
    el("ul", { style: "margin:6px 0 0;padding-inline-start:18px;max-height:140px;overflow:auto;font-size:12.5px" },
      ...ch.map(t => { const o = ORIG.get(t.id); const dd = t.start - o.start;
        return el("li", { text: t.name + ": " + (datesChanged(t) ? fmtShort(o.start) + "–" + fmtShort(o.end) + " → " + fmtShort(t.start) + "–" + fmtShort(t.end) + (dd ? " (" + (dd > 0 ? "+" : "") + dd + " g)" : "") : "") + (depsChanged(t) ? " · öncüller değişti" : "") }); })));
  clear(pendBox).append(
    el("div", { class: "grow" },
      el("b", { text: "Kaydedilmemiş plan değişikliği: " }),
      (nDates ? nDates + " görevin tarihi" : "") + (nDates && nDeps ? ", " : "") + (nDeps ? nDeps + " görevin öncülü" : "") +
      " · proje bitişi " + fmtDay(oldEnd) + (newEnd !== oldEnd ? " → " + fmtDay(newEnd) + " (" + (newEnd > oldEnd ? "+" : "") + (newEnd - oldEnd) + " gün)" : " (değişmedi)"),
      detail),
    undo, save);
  pendBox.hidden = false;
  save.addEventListener("click", () => saveAll(ch, save, undo));
}

function undoAll() {
  for (const t of TASKS) { const o = ORIG.get(t.id); if (o) { t.start = o.start; t.end = o.end; t.deps = o.deps.map(d => ({ ...d })); } }
  PENDING.clear();
  refreshAfterEdit();
  toast("Değişiklikler geri alındı");
}

/* faz (özet) kayıtlarının tarihleri: çocuklardan hesaplanan aralık kayıttakinden farklıysa yaz */
function summaryWrites() {
  return TASKS.filter(t => t.summary).map(t => [t, toDay(v(t.rec, "G", "Başlangıç")), toDay(v(t.rec, "G", "Bitiş"))])
    .filter(([t, s, e]) => t.start !== s || t.end !== e).map(([t]) => t);
}

async function saveAll(ch, save, undo) {
  save.disabled = true; undo.disabled = true;
  const jobs = [];
  for (const t of ch) {
    const p = {};
    if (datesChanged(t)) { p[fid("G", "Başlangıç")] = dayToISO(t.start); p[fid("G", "Bitiş")] = dayToISO(t.end); }
    if (depsChanged(t)) {
      p[fid("G", "Öncüller")] = t.deps.map(d => ({ _id: d.id, dependencyType: d.type || 1 }));
      p[fid("G", "Öncül Kayıtları")] = t.deps.map(d => d.id);
    }
    jobs.push([t.id, p]);
  }
  for (const t of summaryWrites()) jobs.push([t.id, { [fid("G", "Başlangıç")]: dayToISO(t.start), [fid("G", "Bitiş")]: dayToISO(t.end) }]);
  save.textContent = "Kaydediliyor… 0/" + jobs.length;
  try {
    const errors = await runPool(jobs, ([id, p]) => updateRecord("G", id, p), 4, (d, n) => { save.textContent = "Kaydediliyor… " + d + "/" + n; });
    if (errors.length) toast(errors.length + " kayıt yazılamadı: " + errors[0][1].message, "err", 6000);
    else toast("Plan kaydedildi: " + jobs.length + " kayıt. Workiom'un Gantt'ı ve bildirimleri güncellendi.", "ok", 4500);
    await load(true);
  } catch (e) {
    if (!(e instanceof SessionGone)) { toast(e.message, "err"); save.disabled = false; undo.disabled = false; save.textContent = "Kaydet"; }
  }
}

/* ── görev çekmecesi ──────────────────────────────────────────────── */
let drawerEls = null;
function closeDrawer() { if (drawerEls) { drawerEls.forEach(x => x.remove()); drawerEls = null; } }

function openTask(t) {
  closeDrawer();
  const back = el("div", { class: "drawer-back", onclick: closeDrawer });
  const body = el("div", { class: "body" });
  const foot = el("footer");
  const tabs = el("div", { class: "tabs", role: "tablist", style: "margin:12px 0 0" });
  const dr = el("aside", { class: "drawer", role: "dialog", "aria-modal": "true", "aria-labelledby": "dr-t" },
    el("header", null,
      el("div", { style: "display:flex;gap:6px;flex-wrap:wrap" }, t.summary ? el("span", { class: "tag", text: t.type || "Özet" }) : chip(t.status),
        t.critical ? el("span", { class: "tag crit", text: "Kritik yol" }) : null, t.late ? el("span", { class: "tag late", text: "Gecikti" }) : null,
        t.milestone ? el("span", { class: "tag", text: "◆ Kilometre taşı" }) : null, t.approvalNeeded ? el("span", { class: "tag", text: "✍ Onay gerekli" }) : null,
        PENDING.has(t.id) ? el("span", { class: "tag", text: "kaydedilmedi" }) : null),
      el("h2", { id: "dr-t", text: t.name }),
      el("div", { class: "meta", style: "color:var(--text-secondary);font-size:12.5px", text: "WBS " + (t.wbs || "") + (t.dept ? " · " + t.dept : "") }),
      tabs),
    body, foot);
  drawerEls = [back, dr];
  document.body.append(back, dr);
  document.addEventListener("keydown", function esc(e) { if (e.key === "Escape") { closeDrawer(); document.removeEventListener("keydown", esc); } });

  const panes = { "Ayrıntı": () => detailPane(t, body, foot), "Geçmiş": () => { clear(foot).append(el("button", { class: "btn", type: "button", text: "Kapat", onclick: closeDrawer })); renderHistory(body, "G", t.id); } };
  const show = name => {
    tabs.querySelectorAll("button").forEach(b => b.setAttribute("aria-selected", b.textContent === name ? "true" : "false"));
    clear(body); clear(foot); panes[name]();
  };
  Object.keys(panes).forEach(n => tabs.append(el("button", { type: "button", role: "tab", text: n, onclick: () => show(n) })));
  show("Ayrıntı");
}

function detailPane(t, body, foot) {
  const kv = el("dl", { class: "kv" });
  const row = (k, val) => kv.append(el("dt", { text: k }), el("dd", null, val));
  row("Plan", fmtDay(t.start) + " → " + fmtDay(t.end) + " (" + (t.end - t.start) + " gün)");
  if (!t.summary) {
    row("Sorumlu", userName(t.owner) || "—");
    if (t.approvalNeeded) row("Onaylayıcı", userName(t.approver) || "—");
    row("İlerleme", "%" + Math.round(t.pct || 0));
    row("Gerçekleşen", (t.actualStart != null ? fmtDay(t.actualStart) : "—") + " → " + (t.actualEnd != null ? fmtDay(t.actualEnd) : "—"));
    row("Baseline", t.baseStart != null ? fmtDay(t.baseStart) + " → " + fmtDay(t.baseEnd) + (t.variance ? " (sapma " + (t.variance > 0 ? "+" : "") + t.variance + " gün)" : "") : "alınmadı");
  } else row("İlerleme", "%" + Math.round(t.pct || 0) + " (alt görevlerden)");
  body.append(kv);

  if (!t.summary) {
    body.append(el("div", { class: "section-t", text: "Öncüller" }));
    const pl = el("ul", { class: "pred-list" });
    if (!t.deps.length) pl.append(el("li", { text: "Öncül yok" }));
    for (const d of t.deps) {
      const p = BYID.get(d.id);
      pl.append(el("li", null, el("span", { text: (p ? p.name : d.label) + " (" + ["", "FS", "SS", "FF", "SF"][d.type || 1] + ")" }),
        el("span", { class: "inline-row" }, p ? chip(p.status) : "",
          IS_PM ? el("button", { class: "x", type: "button", "aria-label": "Öncülü kaldır", title: "Öncülü kaldır", text: "×", onclick: () => { removeLink(t.id, d.id); openTask(t); } }) : null)));
    }
    body.append(pl);
    if (IS_PM) {
      const cand = leaves().filter(x => x.id !== t.id && !t.deps.some(d => d.id === x.id)).sort((a, b) => a.wbs - b.wbs);
      const sel = el("select", { class: "input", id: "add-pred", "aria-label": "Öncül ekle" }, el("option", { value: "", text: "Öncül ekle…" }),
        ...cand.map(x => el("option", { value: x.id, text: x.wbs + " · " + x.name })));
      const typ = el("select", { class: "input", id: "add-type", style: "flex:0 0 76px;min-width:76px", "aria-label": "Bağ türü" },
        ...[[1, "FS"], [2, "SS"], [3, "FF"], [4, "SF"]].map(([n, l]) => el("option", { value: String(n), text: l })));
      const add = el("button", { class: "btn sm", type: "button", text: "Ekle", onclick: () => { if (sel.value) { addLink(sel.value, t.id, Number(typ.value)); openTask(t); } } });
      body.append(el("div", { class: "inline-row", style: "margin-top:8px" }, sel, typ, add));
    }
    const succ = leaves().filter(x => x.deps.some(d => d.id === t.id));
    if (succ.length) {
      body.append(el("div", { class: "section-t", text: "Ardıllar" }));
      const sl = el("ul", { class: "pred-list" });
      succ.forEach(s => sl.append(el("li", null, el("span", { text: s.name }), chip(s.status))));
      body.append(sl);
    }
    if (t.notes) body.append(el("div", { class: "section-t", text: "Notlar" }), el("p", { style: "white-space:pre-wrap;margin:0", text: t.notes }));
    if (t.files.length) body.append(el("div", { class: "section-t", text: "Dokümanlar" }), el("p", { style: "margin:0", text: t.files.map(f => f.FileName).join(", ") }));
  }

  if (IS_PM) pmEditor(t, body, foot);
  else {
    if (!t.summary && t.owner && String(t.owner.id) === String(ME.id))
      foot.append(el("a", { class: "btn primary", href: "gorevlerim.html#" + encodeURIComponent(t.id), text: "Görevlerim'de güncelle →" }));
    body.append(el("p", { style: "color:var(--text-muted);font-size:12.5px", text: "Plan yapısı (tarih, süre, öncül, sorumlu) yalnızca proje yöneticisi tarafından değiştirilebilir." }));
    foot.append(el("button", { class: "btn", type: "button", text: "Kapat", onclick: closeDrawer }));
  }
}

function pmEditor(t, body, foot) {
  const err = el("div", { class: "error-box", role: "alert" });
  body.append(el("div", { class: "section-t", text: "Planı değiştir" }), err);
  if (!t.summary) {
    const fStart = el("input", { class: "input", type: "date", id: "e-start", value: dayToISO(t.start) });
    const fDur = el("input", { class: "input", type: "number", id: "e-dur", min: "0", step: "1", value: String(t.end - t.start) });
    const apply = el("button", { class: "btn sm", type: "button", text: "Plana uygula" });
    apply.addEventListener("click", () => {
      const s = toDay(fStart.value + "T00:00:00"), d = Math.round(Number(fDur.value));
      if (s == null || !Number.isFinite(d) || d < 0) { err.textContent = "Geçerli bir başlangıç tarihi ve 0 veya daha büyük bir süre girin."; return; }
      applyChange(t.id, s, s + d);
      toast("Plana uygulandı (kaydedilmedi). Üstteki çubuktan kaydedin.");
      closeDrawer();
    });
    body.append(el("div", { class: "grid2" },
      el("div", { class: "field" }, el("label", { for: "e-start", text: "Başlangıç" }), fStart),
      el("div", { class: "field" }, el("label", { for: "e-dur", text: "Süre (gün)" }), fDur)), apply);

    // görev bilgileri (anında kaydedilir)
    const fName = el("input", { class: "input", id: "e-name", value: t.name, required: true, "aria-required": "true" });
    const fOwner = userSelect("e-owner", t.owner, "— sorumlu seçin —");
    const fAppr = userSelect("e-appr", t.approver, "— onaylayıcı seçin —");
    const fNeed = el("input", { type: "checkbox", id: "e-need", checked: t.approvalNeeded || null });
    body.append(el("div", { class: "section-t", text: "Görev bilgileri" }),
      el("div", { class: "field" }, el("label", { for: "e-name" }, "Görev adı", el("span", { class: "req", "aria-hidden": "true", text: "*" })), fName),
      el("div", { class: "grid2" },
        el("div", { class: "field" }, el("label", { for: "e-owner", text: "Sorumlu" }), fOwner),
        el("div", { class: "field" }, el("label", { for: "e-appr", text: "Onaylayıcı" }), fAppr)),
      el("label", { style: "display:flex;gap:8px;align-items:center;font-size:13px" }, fNeed, "Tamamlanması için onay gerekli"));
    const saveInfo = el("button", { class: "btn primary", type: "button", text: "Bilgileri kaydet" });
    saveInfo.addEventListener("click", async () => {
      clear(err); fName.removeAttribute("aria-invalid");
      if (!fName.value.trim()) { err.textContent = "Eksik alan: Görev adı"; fName.setAttribute("aria-invalid", "true"); fName.focus(); return; }
      const p = {};
      if (fName.value.trim() !== t.name) p[fid("G", "Görev Adı")] = fName.value.trim();
      if (fOwner.value && fOwner.value !== (t.owner?.emailAddress || "")) p[fid("G", "Sorumlu")] = fOwner.value;
      if (fAppr.value && fAppr.value !== (t.approver?.emailAddress || "")) p[fid("G", "Onaylayıcı")] = fAppr.value;
      if (fNeed.checked !== !!t.approvalNeeded) p[fid("G", "Onay Gerekli")] = fNeed.checked;
      if (!Object.keys(p).length) { toast("Değişiklik yok"); return; }
      saveInfo.disabled = true;
      try { await updateRecord("G", t.id, p); toast("Görev bilgileri kaydedildi", "ok"); closeDrawer(); load(true); }
      catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; saveInfo.disabled = false; }
    });
    foot.append(el("button", { class: "btn danger", type: "button", text: "Görevi sil", onclick: () => confirmDelete(t) }));
    foot.append(el("button", { class: "btn", type: "button", text: "＋ Alt görev", onclick: () => { closeDrawer(); openAdd(t); } }));
    foot.append(saveInfo);
  } else {
    body.append(el("p", { style: "font-size:13px;color:var(--text-secondary);margin:0 0 8px", text: "Faz tarihleri alt görevlerden hesaplanır. Bu faza görev ekleyebilirsiniz." }));
    foot.append(el("button", { class: "btn primary", type: "button", text: "＋ Bu faza görev ekle", onclick: () => { closeDrawer(); openAdd(t); } }));
  }
  foot.prepend(el("button", { class: "btn", type: "button", text: "Kapat", onclick: closeDrawer }));
}

/* ── görev ekle / sil (PM) ────────────────────────────────────────── */
function openAdd(parent) {
  if (PENDING.size) { toast("Önce bekleyen plan değişikliklerini kaydedin ya da geri alın.", "err", 4500); return; }
  const back = el("div", { class: "modal-back" });
  const err = el("div", { class: "error-box", role: "alert" });
  const parents = TASKS.filter(t => t.type === "Faz" || t.type === "Alt Faz" || !t.summary).sort((a, b) => a.wbs - b.wbs);
  const fName = el("input", { class: "input", id: "n-name", required: true, "aria-required": "true", placeholder: "ör. Çözünürlük profili karşılaştırması" });
  const fPar = el("select", { class: "input", id: "n-par" }, ...parents.map(p => el("option", { value: p.id, text: (p.summary ? "▸ " : "   ") + (p.type === "Faz" ? "F" + Math.round(p.wbs / 100) : p.wbs) + " · " + p.name, selected: parent && p.id === parent.id || null })));
  const fTur = el("select", { class: "input", id: "n-tur" }, ...["Görev", "Alt Görev", "Alt Faz", "Kilometre Taşı"].map(x => el("option", { value: x, text: x, selected: (parent && !parent.summary && x === "Alt Görev") || null })));
  const base = parent ? Math.max(parent.start ?? todayDay(), todayDay() - 3650) : todayDay();
  const fStart = el("input", { class: "input", type: "date", id: "n-start", value: dayToISO(parent && !parent.summary ? parent.end : base) });
  const fDur = el("input", { class: "input", type: "number", id: "n-dur", min: "0", value: "7" });
  const fOwner = userSelect("n-owner", null, "— sorumlu seçin —");
  const fDept = el("select", { class: "input", id: "n-dept" }, el("option", { value: "", text: "— departman —" }),
    ...DEPTS.map(d => el("option", { value: d._id, text: v(d, "D", "Departman") })));
  const fPred = el("select", { class: "input", id: "n-pred" }, el("option", { value: "", text: "— öncül yok —" }),
    ...leaves().sort((a, b) => a.wbs - b.wbs).map(x => el("option", { value: x.id, text: x.wbs + " · " + x.name })));
  const fNeed = el("input", { type: "checkbox", id: "n-need" });
  const ok = el("button", { class: "btn primary", type: "submit", text: "Görevi ekle" });
  const form = el("form", { class: "card modal", novalidate: true, "aria-labelledby": "n-t" },
    el("h2", { id: "n-t", text: parent && !parent.summary ? "Alt görev ekle" : "Görev ekle" }),
    el("p", { class: "req-note" }, el("span", { class: "req", "aria-hidden": "true", text: "*" }), " Zorunlu"), err,
    el("div", { class: "field" }, el("label", { for: "n-name" }, "Görev adı", el("span", { class: "req", "aria-hidden": "true", text: "*" })), fName),
    el("div", { class: "grid2" },
      el("div", { class: "field" }, el("label", { for: "n-par", text: "Üst öğe (faz / görev)" }), fPar),
      el("div", { class: "field" }, el("label", { for: "n-tur", text: "Tür" }), fTur)),
    el("div", { class: "grid2" },
      el("div", { class: "field" }, el("label", { for: "n-start", text: "Başlangıç" }), fStart),
      el("div", { class: "field" }, el("label", { for: "n-dur", text: "Süre (gün)" }), fDur)),
    el("div", { class: "grid2" },
      el("div", { class: "field" }, el("label", { for: "n-owner", text: "Sorumlu" }), fOwner),
      el("div", { class: "field" }, el("label", { for: "n-dept", text: "Departman" }), fDept)),
    el("div", { class: "field" }, el("label", { for: "n-pred", text: "Öncül (FS)" }), fPred),
    el("label", { style: "display:flex;gap:8px;align-items:center;font-size:13px;margin-bottom:10px" }, fNeed, "Tamamlanması için onay gerekli"),
    el("div", { class: "actions" }, el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => back.remove() }), ok));
  form.addEventListener("submit", async ev => {
    ev.preventDefault(); clear(err); fName.removeAttribute("aria-invalid");
    if (!fName.value.trim()) { err.textContent = "Eksik alan: Görev adı"; fName.setAttribute("aria-invalid", "true"); fName.focus(); return; }
    const s = toDay(fStart.value + "T00:00:00"), d = Math.max(0, Math.round(Number(fDur.value) || 0));
    if (s == null) { err.textContent = "Geçerli bir başlangıç tarihi girin."; return; }
    const par = BYID.get(fPar.value);
    const sib = TASKS.filter(x => x.parent === par?.id);
    const isSub = par && !par.summary;
    const wbs = isSub ? Math.round((Math.max(par.wbs, ...sib.map(x => x.wbs)) + 0.1) * 10) / 10 : Math.floor(Math.max(0, ...leaves().map(x => x.wbs))) + 1;
    const tur = fTur.value;
    const p = {
      [fid("G", "Görev Adı")]: fName.value.trim(), [fid("G", "Proje")]: [PID], [fid("G", "Durum")]: "Başlamadı",
      [fid("G", "Başlangıç")]: dayToISO(s), [fid("G", "Bitiş")]: dayToISO(s + d), [fid("G", "WBS No")]: wbs, [fid("G", "Tür")]: tur,
      [fid("G", "Kapalı")]: 0, [fid("G", "% Tamamlanma")]: 0, [fid("G", "Onay Gerekli")]: fNeed.checked, [fid("G", "Kilometre Taşı")]: tur === "Kilometre Taşı"
    };
    if (par) p[fid("G", "Üst Görev")] = [par.id];
    if (fOwner.value) p[fid("G", "Sorumlu")] = fOwner.value;
    if (fDept.value) p[fid("G", "Sorumlu Departman")] = [fDept.value];
    if (fPred.value) { p[fid("G", "Öncüller")] = [{ _id: fPred.value, dependencyType: 1 }]; p[fid("G", "Öncül Kayıtları")] = [fPred.value]; }
    const pm = v(PROJ, "P", "Proje Yöneticisi");
    if (pm?.emailAddress) p[fid("G", "Onaylayıcı")] = pm.emailAddress;
    ok.disabled = true;
    try { await createRecord("G", p); back.remove(); toast("Görev eklendi: " + fName.value.trim(), "ok"); await load(true); }
    catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; ok.disabled = false; }
  });
  back.addEventListener("click", e => { if (e.target === back) back.remove(); });
  back.append(form);
  document.body.append(back);
  fName.focus();
}

function confirmDelete(t) {
  if (t.children.length) { toast("Alt görevi olan bir görev silinemez; önce alt görevleri silin.", "err", 4500); return; }
  const succ = leaves().filter(x => x.deps.some(d => d.id === t.id));
  const back = el("div", { class: "modal-back" });
  const go = el("button", { class: "btn danger", type: "button", text: "Sil" });
  back.append(el("div", { class: "card modal", role: "dialog", "aria-modal": "true" },
    el("h2", { text: "Görev silinsin mi?" }),
    el("p", { class: "lead", text: t.name + (succ.length ? " — " + succ.length + " görev bu göreve bağlı; bağları kaldırılacak: " + succ.map(s => s.name).join(", ") : "") }),
    el("div", { class: "actions" }, el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => back.remove() }), go)));
  document.body.append(back);
  go.addEventListener("click", async () => {
    go.disabled = true;
    try {
      for (const s of succ) {
        const deps = s.deps.filter(d => d.id !== t.id);
        await updateRecord("G", s.id, { [fid("G", "Öncüller")]: deps.map(d => ({ _id: d.id, dependencyType: d.type || 1 })), [fid("G", "Öncül Kayıtları")]: deps.map(d => d.id) });
      }
      await api("DELETE", "/api/services/app/Data/Delete?listId=" + encodeURIComponent(L.G.id) + "&id=" + encodeURIComponent(t.id));
      back.remove(); closeDrawer(); toast("Görev silindi", "ok"); load(true);
    } catch (e) { if (!(e instanceof SessionGone)) { toast(e.message, "err"); go.disabled = false; } }
  });
}

/* ── baseline ─────────────────────────────────────────────────────── */
async function takeBaseline() {
  if (PENDING.size) { toast("Önce bekleyen plan değişikliklerini kaydedin.", "err"); return; }
  const no = Number(v(PROJ, "P", "Baseline No")) || 0;
  const back = el("div", { class: "modal-back" });
  const ok = el("button", { class: "btn primary", type: "button", text: "Baseline " + (no + 1) + " al" });
  back.append(el("div", { class: "card modal", role: "dialog", "aria-modal": "true" },
    el("h2", { text: "Baseline alınsın mı?" }),
    el("p", { class: "lead", text: "Tüm görevlerin mevcut başlangıç/bitiş tarihleri Baseline " + (no + 1) + " olarak kaydedilir ve arşive yazılır. Sapma bundan sonra bu plana göre hesaplanır. Proje durumu 'Devam Ediyor' olur." }),
    el("div", { class: "actions" }, el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => back.remove() }), ok)));
  document.body.append(back);
  ok.addEventListener("click", async () => {
    ok.disabled = true; ok.textContent = "Baseline alınıyor…";
    try {
      await updateRecord("P", PID, { [fid("P", "Durum")]: "Plan Onaylandı (Baseline)" });
      const t0 = Date.now();
      while (Date.now() - t0 < 180000) {
        await new Promise(r => setTimeout(r, 4000));
        const p = await getRecord("P", PID);
        if ((Number(v(p, "P", "Baseline No")) || 0) > no) break;
      }
      back.remove();
      toast("Baseline " + (no + 1) + " alındı", "ok");
      load(true);
    } catch (e) {
      if (!(e instanceof SessionGone)) { ok.disabled = false; ok.textContent = "Tekrar dene"; toast(e.message, "err"); }
    }
  });
}

/* ── Excel (CSV) ──────────────────────────────────────────────────── */
function exportCSV() {
  const rows = [["WBS", "Görev", "Tür", "Departman", "Sorumlu", "Başlangıç", "Bitiş", "Süre (gün)", "Öncüller", "Durum", "% Tamamlanma",
    "Baseline Başlangıç", "Baseline Bitiş", "Sapma (gün)", "Kritik yol", "Gecikmede", "Onay Gerekli"]];
  const walk = (t, depth) => {
    rows.push([t.wbs, "  ".repeat(depth) + t.name, t.type, t.dept, userName(t.owner), dayToISO(t.start), dayToISO(t.end), t.end - t.start,
      t.deps.map(d => (BYID.get(d.id)?.wbs ?? d.label) + (d.type && d.type !== 1 ? ["", "FS", "SS", "FF", "SF"][d.type] : "")).join(", "), t.status || "", Math.round(t.pct || 0),
      t.baseStart != null ? dayToISO(t.baseStart) : "", t.baseEnd != null ? dayToISO(t.baseEnd) : "", t.summary ? "" : (t.variance || 0),
      t.critical ? "Evet" : "", t.late ? "Evet" : "", t.approvalNeeded ? "Evet" : ""]);
    t.children.forEach(c => walk(c, depth + 1));
  };
  TASKS.filter(t => !t.parent || !BYID.has(t.parent)).sort((a, b) => a.wbs - b.wbs).forEach(t => walk(t, 0));
  downloadCSV((v(PROJ, "P", "Proje Adı") || "proje").replace(/[^\p{L}\p{N}]+/gu, "_") + "_plan.csv", rows);
}

/* ── başlat ───────────────────────────────────────────────────────── */
document.querySelectorAll("#zoom button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll("#zoom button").forEach(x => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
  gantt.setZoom(b.dataset.z);
}));
document.getElementById("btn-today").addEventListener("click", () => gantt.scrollToToday());
let folded = false;
document.getElementById("btn-fold").addEventListener("click", e => {
  folded = !folded;
  gantt.collapseWhere(t => folded && t.type === "Faz");
  e.target.textContent = folded ? "Fazları aç" : "Fazları daralt";
});
document.getElementById("chk-base").addEventListener("change", e => gantt.setBaseline(e.target.checked));
document.getElementById("btn-csv").addEventListener("click", () => TASKS.length && exportCSV());
document.getElementById("btn-baseline").addEventListener("click", takeBaseline);
document.getElementById("btn-add").addEventListener("click", () => openAdd(null));
fDept.addEventListener("change", () => gantt.rerender());
fMine.addEventListener("change", () => gantt.rerender());
window.addEventListener("beforeunload", e => { if (PENDING.size) { e.preventDefault(); e.returnValue = ""; } });

initShell("plan").then(me => {
  ME = me;
  if (!PID) { stateEmpty(host, "Proje seçilmedi", "Portföy sayfasından bir proje açın.", el("a", { class: "btn primary", href: "index.html", text: "Portföye git" })); return; }
  load();
}).catch(e => { if (!(e instanceof SessionGone)) stateError(host, e, () => location.reload()); });
