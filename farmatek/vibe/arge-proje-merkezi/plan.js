/* Proje planı: Gantt, görev detayı, PM için süre/tarih değişikliği + bağımlılık kaydırma, baseline, Excel */
"use strict";

const PID = new URLSearchParams(location.search).get("id");
let ME = null, PROJ = null, TASKS = [], BYID = new Map(), IS_PM = false;
const host = document.getElementById("gantt");
const kpiBox = document.getElementById("kpis");
const gantt = createGantt(host, { zoom: "ay", onSelect: openTask });

function kpi(label, value, sub) {
  return el("div", { class: "card kpi" }, el("div", { class: "label", text: label }), el("div", { class: "value", text: String(value) }), el("div", { class: "sub", text: sub || "" }));
}

function leaves() { return TASKS.filter(t => !t.summary); }

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

async function load(keepSel) {
  stateLoading(host, "Plan yükleniyor…");
  try {
    const [p, all] = await Promise.all([getRecord("P", PID), fetchAll("G")]);
    PROJ = p;
    IS_PM = (v(p, "P", "Proje Yöneticisi")?.id || "") === String(ME.id);
    TASKS = all.filter(r => linkIds(v(r, "G", "Proje")).includes(PID)).map(r => taskModel(r, "G"));
    BYID = new Map(TASKS.map(t => [t.id, t]));
    renderHead();
    if (!TASKS.length) {
      stateEmpty(host, "Bu projede görev yok", lbl(v(p, "P", "Plan Durumu")) && lbl(v(p, "P", "Plan Durumu")) !== "Hazır"
        ? "Plan otomasyonla kuruluyor (" + lbl(v(p, "P", "Plan Durumu")) + "). Birkaç dakika sonra yenileyin."
        : "Proje bir şablonla oluşturulmamış olabilir.", el("button", { class: "btn", type: "button", onclick: () => load(), text: "↻ Yenile" }));
      clear(kpiBox);
      return;
    }
    gantt.setTasks(TASKS);
    renderKPIs();
    if (!keepSel) gantt.scrollToToday();
  } catch (e) {
    stateError(host, e, () => load());
  }
}

/* ── bağımlılık kaydırma (MS Project "öncülden sonra başla", tamponu koru) ── */
function cascade(changedId, newStart, newEnd) {
  const next = new Map([[changedId, { start: newStart, end: newEnd }]]);
  const cur = t => next.get(t.id) || { start: t.start, end: t.end };
  const succ = new Map();
  for (const t of leaves()) for (const d of t.deps) {
    if (!succ.has(d.id)) succ.set(d.id, []);
    succ.get(d.id).push(t);
  }
  const queue = [changedId];
  let guard = 0;
  while (queue.length && guard++ < 5000) {
    const id = queue.shift();
    for (const s of succ.get(id) || []) {
      const sc = cur(s), dur = sc.end - sc.start;
      let need = -Infinity;
      for (const d of s.deps) {
        const p = BYID.get(d.id); if (!p) continue;
        const pc = cur(p);
        if (d.type === 2) need = Math.max(need, pc.start);              // SS
        else if (d.type === 3) need = Math.max(need, pc.end - dur);      // FF
        else if (d.type === 4) need = Math.max(need, pc.start - dur);    // SF
        else need = Math.max(need, pc.end);                              // FS
      }
      if (need > sc.start) { next.set(s.id, { start: need, end: need + dur }); queue.push(s.id); }
    }
  }
  return next;
}

/* özet (faz) aralıklarını yeni tarihlerle yeniden hesapla */
function summaryChanges(next) {
  const out = new Map();
  const span = t => {
    if (!t.children.length) return next.get(t.id) || { start: t.start, end: t.end };
    const ch = t.children.map(span);
    const s = { start: Math.min(...ch.map(c => c.start)), end: Math.max(...ch.map(c => c.end)) };
    const raw = toDay(v(t.rec, "G", "Başlangıç")), rawE = toDay(v(t.rec, "G", "Bitiş"));
    if (s.start !== raw || s.end !== rawE) out.set(t.id, s);
    return s;
  };
  TASKS.filter(t => !t.parent || !BYID.has(t.parent)).forEach(span);
  return out;
}

/* ── görev çekmecesi ──────────────────────────────────────────────── */
let drawerEls = null;
function closeDrawer() { if (drawerEls) { drawerEls.forEach(x => x.remove()); drawerEls = null; } }

function openTask(t) {
  closeDrawer();
  const back = el("div", { class: "drawer-back", onclick: closeDrawer });
  const body = el("div", { class: "body" });
  const foot = el("footer");
  const dr = el("aside", { class: "drawer", role: "dialog", "aria-modal": "true", "aria-labelledby": "dr-t" },
    el("header", null,
      el("div", { style: "display:flex;gap:6px;flex-wrap:wrap" }, t.summary ? el("span", { class: "tag", text: t.type || "Özet" }) : chip(t.status),
        t.critical ? el("span", { class: "tag crit", text: "Kritik yol" }) : null, t.late ? el("span", { class: "tag late", text: "Gecikti" }) : null,
        t.milestone ? el("span", { class: "tag", text: "◆ Kilometre taşı" }) : null, t.approvalNeeded ? el("span", { class: "tag", text: "✍ Onay gerekli" }) : null),
      el("h2", { id: "dr-t", text: t.name }),
      el("div", { class: "meta", style: "color:var(--text-secondary);font-size:12.5px", text: "WBS " + (t.wbs || "") + (t.dept ? " · " + t.dept : "") })),
    body, foot);
  drawerEls = [back, dr];
  document.body.append(back, dr);
  document.addEventListener("keydown", function esc(e) { if (e.key === "Escape") { closeDrawer(); document.removeEventListener("keydown", esc); } });

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
      pl.append(el("li", null, el("span", { text: (p ? p.name : d.label) + (d.type && d.type !== 1 ? " (" + ["", "FS", "SS", "FF", "SF"][d.type] + ")" : "") }), p ? chip(p.status) : ""));
    }
    body.append(pl);
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

  if (IS_PM && !t.summary) planEditor(t, body, foot);
  else {
    if (!t.summary && t.owner && String(t.owner.id) === String(ME.id))
      foot.append(el("a", { class: "btn primary", href: "gorevlerim.html#" + encodeURIComponent(t.id), text: "Görevlerim'de güncelle →" }));
    if (!IS_PM) body.append(el("p", { class: "hint", style: "color:var(--text-muted);font-size:12.5px", text: "Plan yapısı (tarih, süre, öncül, sorumlu) yalnızca proje yöneticisi tarafından değiştirilebilir." }));
    foot.append(el("button", { class: "btn", type: "button", text: "Kapat", onclick: closeDrawer }));
  }
}

function planEditor(t, body, foot) {
  const err = el("div", { class: "error-box", role: "alert" });
  const fStart = el("input", { class: "input", type: "date", id: "e-start", value: dayToISO(t.start) });
  const fDur = el("input", { class: "input", type: "number", id: "e-dur", min: "0", step: "1", value: String(t.end - t.start) });
  const fCasc = el("input", { type: "checkbox", id: "e-casc", checked: true });
  const impact = el("div");
  const calc = el("button", { class: "btn", type: "button", text: "Etkiyi hesapla" });
  const save = el("button", { class: "btn primary", type: "button", text: "Kaydet", disabled: true });
  let pending = null;

  body.append(el("div", { class: "section-t", text: "Planı değiştir (PM)" }), err,
    el("div", { class: "grid2" },
      el("div", { class: "field" }, el("label", { for: "e-start", text: "Başlangıç" }), fStart),
      el("div", { class: "field" }, el("label", { for: "e-dur", text: "Süre (gün)" }), fDur)),
    el("label", { style: "display:flex;gap:8px;align-items:center;font-size:13px;margin-bottom:10px" }, fCasc, "Bağımlı görevleri otomatik kaydır (tamponu koru)"),
    impact);

  const compute = () => {
    clear(err); save.disabled = true; pending = null; clear(impact);
    const s = toDay(fStart.value + "T00:00:00"), d = Number(fDur.value);
    if (s == null || !Number.isFinite(d) || d < 0) { err.textContent = "Geçerli bir başlangıç tarihi ve 0 veya daha büyük bir süre girin."; return; }
    const next = fCasc.checked ? cascade(t.id, s, s + Math.round(d)) : new Map([[t.id, { start: s, end: s + Math.round(d) }]]);
    const changed = [...next.entries()].filter(([id, n]) => { const x = BYID.get(id); return x.start !== n.start || x.end !== n.end; });
    if (!changed.length) { impact.append(el("div", { class: "impact", text: "Değişiklik yok." })); return; }
    const sums = summaryChanges(next);
    const ul = el("ul");
    changed.forEach(([id, n]) => {
      const x = BYID.get(id), dd = n.start - x.start;
      ul.append(el("li", { text: x.name + ": " + fmtShort(x.start) + " → " + fmtShort(n.start) + (dd ? " (" + (dd > 0 ? "+" : "") + dd + " g)" : " (süre " + (x.end - x.start) + "→" + (n.end - n.start) + " g)") }));
    });
    const newEnd = Math.max(...leaves().map(x => (next.get(x.id) || x).end));
    const oldEnd = Math.max(...leaves().map(x => x.end));
    impact.append(el("div", { class: "impact" },
      el("b", { text: changed.length + " görev güncellenecek" + (sums.size ? ", " + sums.size + " faz aralığı yeniden hesaplanacak" : "") }),
      el("div", { text: "Proje bitişi: " + fmtDay(oldEnd) + " → " + fmtDay(newEnd) + (newEnd !== oldEnd ? " (" + (newEnd > oldEnd ? "+" : "") + (newEnd - oldEnd) + " gün)" : "") }), ul));
    pending = { changed, sums };
    save.disabled = false;
  };
  calc.addEventListener("click", compute);
  [fStart, fDur, fCasc].forEach(x => x.addEventListener("change", compute));

  save.addEventListener("click", async () => {
    if (!pending) return;
    save.disabled = true; calc.disabled = true;
    const items = [...pending.changed, ...pending.sums.entries()];
    save.textContent = "Kaydediliyor… 0/" + items.length;
    try {
      const errors = await runPool(items, ([id, n]) => updateRecord("G", id, { [fid("G", "Başlangıç")]: dayToISO(n.start), [fid("G", "Bitiş")]: dayToISO(n.end) }), 4,
        (d, all) => { save.textContent = "Kaydediliyor… " + d + "/" + all; });
      if (errors.length) { err.textContent = errors.length + " görev kaydedilemedi: " + errors[0][1].message; }
      else { toast("Plan güncellendi: " + items.length + " kayıt", "ok"); closeDrawer(); load(true); }
    } catch (e) {
      if (!(e instanceof SessionGone)) err.textContent = e.message;
    } finally {
      save.textContent = "Kaydet"; calc.disabled = false;
    }
  });
  foot.append(el("button", { class: "btn", type: "button", text: "Kapat", onclick: closeDrawer }), calc, save);
}

/* ── baseline ─────────────────────────────────────────────────────── */
async function takeBaseline() {
  const no = Number(v(PROJ, "P", "Baseline No")) || 0;
  const back = el("div", { class: "modal-back" });
  const ok = el("button", { class: "btn primary", type: "button", text: "Baseline " + (no + 1) + " al" });
  const box = el("div", { class: "card modal", role: "dialog", "aria-modal": "true" },
    el("h2", { text: "Baseline alınsın mı?" }),
    el("p", { class: "lead", text: "Tüm görevlerin mevcut başlangıç/bitiş tarihleri Baseline " + (no + 1) + " olarak kaydedilir ve arşive yazılır. Sapma bundan sonra bu plana göre hesaplanır. Proje durumu 'Devam Ediyor' olur." }),
    el("div", { class: "actions" }, el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => back.remove() }), ok));
  back.append(box);
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
      t.deps.map(d => BYID.get(d.id)?.wbs ?? d.label).join(", "), t.status || "", Math.round(t.pct || 0),
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

initShell("plan").then(me => {
  ME = me;
  if (!PID) { stateEmpty(host, "Proje seçilmedi", "Portföy sayfasından bir proje açın.", el("a", { class: "btn primary", href: "index.html", text: "Portföye git" })); return; }
  load();
}).catch(e => { if (!(e instanceof SessionGone)) stateError(host, e, () => location.reload()); });
