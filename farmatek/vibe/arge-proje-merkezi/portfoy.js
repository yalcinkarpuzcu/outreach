/* Portföy sayfası: KPI'lar, proje kartları, çoklu proje Gantt'ı, yeni proje sihirbazı */
"use strict";

let ME = null, PROJ = [], TASKS = [], SABLON = [];
const projectsBox = document.getElementById("projects");
const kpiBox = document.getElementById("kpis");
const ganttHost = document.getElementById("port-gantt");
const gantt = createGantt(ganttHost, { zoom: "ceyrek", mode: "portfoy" });

function kpi(label, value, sub, icon) {
  return el("div", { class: "card kpi" },
    el("div", { class: "label" }, el("span", { "aria-hidden": "true", text: icon }), label),
    el("div", { class: "value", text: String(value) }),
    el("div", { class: "sub", text: sub || "" }));
}

function projStats(p) {
  const ts = TASKS.filter(t => t.project === p._id);
  const leaves = ts.filter(t => t.type !== "Faz");
  const w = t => Math.max(1, (t.end ?? 0) - (t.start ?? 0));
  const tot = leaves.reduce((a, t) => a + w(t), 0);
  const pct = tot ? Math.round(leaves.reduce((a, t) => a + w(t) * (t.pct || 0), 0) / tot) : 0;
  const late = leaves.filter(t => t.late).length;
  const onay = leaves.filter(t => t.status === "Onay Bekliyor").length;
  const done = leaves.filter(t => t.closed).length;
  const nextMs = leaves.filter(t => t.milestone && !t.closed && t.start != null).sort((a, b) => a.start - b.start)[0];
  const crit = leaves.filter(t => t.late && t.critical).length;
  return { ts, leaves, pct, late, onay, done, nextMs, crit };
}

function renderKPIs() {
  const aktif = PROJ.filter(p => !KAPALI.has(lbl(v(p, "P", "Durum"))));
  const leaves = TASKS.filter(t => t.type !== "Faz");
  const acik = leaves.filter(t => !t.closed);
  const late = leaves.filter(t => t.late);
  const onay = leaves.filter(t => t.status === "Onay Bekliyor");
  const t0 = todayDay();
  const ms30 = leaves.filter(t => t.milestone && !t.closed && t.start != null && t.start >= t0 && t.start <= t0 + 30);
  clear(kpiBox).append(
    kpi("Aktif proje", aktif.length, PROJ.length + " projenin", "🧪"),
    kpi("Açık görev", acik.length, leaves.length ? Math.round(100 * (leaves.length - acik.length) / leaves.length) + "% tamamlandı" : "", "📋"),
    kpi("Geciken görev", late.length, late.length ? "son tarihi geçmiş, kapanmamış" : "gecikme yok", "⏰"),
    kpi("Onay bekleyen", onay.length, "onaycı kararı bekleniyor", "✍️"),
    kpi("Yaklaşan kilometre taşı", ms30.length, "önümüzdeki 30 gün", "◆"));
}

function renderProjects() {
  if (!PROJ.length) {
    stateEmpty(projectsBox, "Henüz proje yok", "Bir şablon seçip ilk Ar-Ge projenizi oluşturun; plan görevler, öncüller ve tarihlerle birlikte otomatik kurulur.",
      el("button", { class: "btn primary", type: "button", onclick: openNew, text: "＋ Yeni Proje" }));
    return;
  }
  const grid = el("div", { class: "projects" });
  const sorted = [...PROJ].sort((a, b) => (toDay(v(a, "P", "Başlangıç Tarihi")) || 0) - (toDay(v(b, "P", "Başlangıç Tarihi")) || 0));
  for (const p of sorted) {
    const s = projStats(p);
    const plan = lbl(v(p, "P", "Plan Durumu"));
    const durum = lbl(v(p, "P", "Durum"));
    const card = el("a", { class: "card pcard", href: "plan.html?id=" + encodeURIComponent(p._id) },
      el("div", { class: "row1" },
        el("div", null,
          el("h3", { text: v(p, "P", "Proje Adı") || "(adsız proje)" }),
          el("div", { class: "meta", text: ["P" + (v(p, "P", "Proje Kodu") ?? ""), lbl((v(p, "P", "Şablon") || [])[0]), v(p, "P", "Ürün / Molekül")].filter(Boolean).join(" · ") })),
        chip(durum)),
      el("div", { class: "meta", text: "PM: " + (userName(v(p, "P", "Proje Yöneticisi")) || "—") + " · " + fmtDay(toDay(v(p, "P", "Başlangıç Tarihi"))) + " → " + fmtDay(toDay(v(p, "P", "Hedef Bitiş"))) }),
      plan !== "Hazır" && plan
        ? el("div", { class: "next-ms" }, el("span", { class: "spinner", style: "width:14px;height:14px;border-width:2px;margin:0" }), "Plan oluşturuluyor: " + plan)
        : el("div", null,
            el("div", { class: "progress", role: "progressbar", "aria-valuenow": s.pct, "aria-valuemin": 0, "aria-valuemax": 100, "aria-label": "Tamamlanma" }, el("span", { style: `width:${s.pct}%` })),
            el("div", { class: "stats", style: "margin-top:8px" },
              el("span", null, el("b", { text: "%" + s.pct }), " tamamlandı"),
              el("span", null, el("b", { text: s.done + "/" + s.leaves.length }), " görev"),
              s.late ? el("span", { class: "tag late", text: s.late + " gecikmiş" }) : el("span", { class: "tag", text: "gecikme yok" }),
              s.onay ? el("span", { class: "tag", text: s.onay + " onay bekliyor" }) : null)),
      s.nextMs ? el("div", { class: "next-ms" }, "◆ Sıradaki kilometre taşı: ", el("b", { text: s.nextMs.name }), " · " + fmtDay(s.nextMs.start)) : null);
    grid.append(card);
  }
  clear(projectsBox).append(grid);
}

function renderGantt() {
  const items = [];
  PROJ.forEach(p => {
    const durum = lbl(v(p, "P", "Durum"));
    items.push({ id: p._id, name: v(p, "P", "Proje Adı") || "", wbs: Number(v(p, "P", "Proje Kodu")) || 0, type: "Proje",
      start: toDay(v(p, "P", "Başlangıç Tarihi")), end: toDay(v(p, "P", "Hedef Bitiş")) ?? toDay(v(p, "P", "Başlangıç Tarihi")),
      deps: [], parent: null, status: durum, closed: KAPALI.has(durum), pct: 0, milestone: false });
  });
  const projIds = new Set(PROJ.map(p => p._id));
  for (const t of TASKS) {
    if (!projIds.has(t.project)) continue;
    items.push(Object.assign(Object.create(null), t, { parent: t.parent || t.project, baseStart: null, baseEnd: null }));
  }
  if (!items.length) { stateEmpty(ganttHost, "Zaman çizelgesi boş", "Projeler oluşturulduğunda burada birlikte görünür."); return; }
  gantt.setTasks(items);
  gantt.collapseWhere(t => t.type === "Faz");
  gantt.scrollToToday();
}

async function load() {
  stateLoading(projectsBox, "Projeler yükleniyor…");
  clear(kpiBox).append(...Array.from({ length: 5 }, () => el("div", { class: "card kpi skeleton", style: "height:92px" })));
  try {
    const [p, g, s] = await Promise.all([fetchAll("P"), fetchAll("G"), fetchAll("S")]);
    PROJ = p; SABLON = s;
    TASKS = g.map(r => taskModel(r, "G"));
    renderKPIs(); renderProjects(); renderGantt();
  } catch (e) {
    stateError(projectsBox, e, load);
    clear(kpiBox);
  }
}

/* ── Yeni proje sihirbazı ──────────────────────────────────────────── */
function openNew() {
  const back = el("div", { class: "modal-back" });
  const err = el("div", { class: "error-box", role: "alert" });
  const fAd = el("input", { class: "input", id: "f-ad", name: fid("P", "Proje Adı"), required: true, "aria-required": "true", maxlength: "200", placeholder: "ör. Calcium Carbonate 500 mg Film Tablet" });
  const fUrun = el("input", { class: "input", id: "f-urun", placeholder: "ör. Kalsiyum karbonat" });
  const fSab = el("select", { class: "input", id: "f-sab" }, el("option", { value: "", text: "Şablon seçin…" }),
    ...SABLON.filter(s => v(s, "S", "Aktif") !== false).map(s => el("option", { value: s._id, text: v(s, "S", "Şablon") + (v(s, "S", "Toplam Süre (gün)") ? " · ~" + Math.round(v(s, "S", "Toplam Süre (gün)") / 30) + " ay" : "") })));
  const fBas = el("input", { class: "input", id: "f-bas", type: "date", value: dayToISO(todayDay()) });
  const fAcik = el("textarea", { class: "input", id: "f-acik", rows: "2" });
  const submit = el("button", { class: "btn primary", type: "submit", text: "Projeyi oluştur" });
  const cancel = el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => back.remove() });

  const form = el("form", { class: "card modal", novalidate: true, "aria-labelledby": "np-t" },
    el("h2", { id: "np-t", text: "Yeni Ar-Ge projesi" }),
    el("p", { class: "lead", text: "Şablon ve başlangıç tarihi seçildiğinde fazlar, görevler, öncül bağları ve tarihler kütüphaneden otomatik kurulur. Proje yöneticisi siz olursunuz." }),
    el("p", { class: "req-note" }, el("span", { class: "req", "aria-hidden": "true", text: "*" }), " Zorunlu"),
    err,
    el("div", { class: "field" }, el("label", { for: "f-ad" }, "Proje adı", el("span", { class: "req", "aria-hidden": "true", text: "*" })), fAd),
    el("div", { class: "field" }, el("label", { for: "f-urun", text: "Ürün / molekül" }), fUrun),
    el("div", { class: "grid2" },
      el("div", { class: "field" }, el("label", { for: "f-sab", text: "Proje şablonu" }), fSab, el("span", { class: "hint", text: "Planın otomatik kurulması için gerekli" })),
      el("div", { class: "field" }, el("label", { for: "f-bas", text: "Başlangıç tarihi" }), fBas, el("span", { class: "hint", text: "Görev tarihleri buna göre hesaplanır" }))),
    el("div", { class: "field" }, el("label", { for: "f-acik", text: "Açıklama" }), fAcik),
    el("div", { class: "actions" }, cancel, submit));

  form.addEventListener("submit", async ev => {
    ev.preventDefault();
    clear(err);
    [fAd, fSab, fBas].forEach(x => x.removeAttribute("aria-invalid"));
    const eksik = [];
    if (isEmptyValue(fAd.value)) eksik.push([fAd, "Proje adı"]);
    if (!fSab.value) eksik.push([fSab, "Proje şablonu (plan kurulumu için)"]);
    if (!fBas.value) eksik.push([fBas, "Başlangıç tarihi (plan kurulumu için)"]);
    if (eksik.length) {
      err.textContent = "Eksik alanlar: " + eksik.map(x => x[1]).join(", ");
      eksik.forEach(x => x[0].setAttribute("aria-invalid", "true"));
      eksik[0][0].focus();
      return;
    }
    const payload = {};
    const put = (name, val) => { if (!isEmptyValue(val)) payload[fid("P", name)] = val; };
    put("Proje Adı", fAd.value.trim());
    put("Ürün / Molekül", fUrun.value.trim());
    put("Şablon", [fSab.value]);
    put("Başlangıç Tarihi", fBas.value);
    put("Proje Açıklaması", fAcik.value.trim());
    put("Proje Yöneticisi", ME.emailAddress);
    submit.disabled = true; cancel.disabled = true;
    submit.textContent = "Oluşturuluyor…";
    try {
      const res = await createRecord("P", payload);
      const id = res?.id || res?._id;
      showProgress(form, id, fAd.value.trim());
    } catch (e) {
      if (!(e instanceof SessionGone)) err.textContent = e.message;
    } finally {
      submit.disabled = false; cancel.disabled = false; submit.textContent = "Projeyi oluştur";
    }
  });
  back.addEventListener("click", e => { if (e.target === back) back.remove(); });
  back.append(form);
  document.body.append(back);
  fAd.focus();
}

function isEmptyValue(x) {
  return x == null || (typeof x === "string" && x.trim() === "") || (Array.isArray(x) && x.length === 0);
}

function showProgress(form, id, name) {
  const steps = [
    ["Proje kaydı oluşturuldu", "done"],
    ["Şablondan görevler ve tarihler oluşturuluyor", "active"],
    ["Hiyerarşi ve öncül bağları kuruluyor", ""],
    ["Plan hazır", ""]
  ];
  const ul = el("ul", { class: "steps", "aria-live": "polite" });
  const paint = () => {
    clear(ul);
    steps.forEach(([t, s]) => ul.append(el("li", { class: s }, el("span", { class: "dot", text: s === "done" ? "✓" : "" }), t)));
  };
  paint();
  const info = el("p", { class: "lead", text: "Workiom otomasyonları planı kuruyor. 38 görevlik bir şablon için bu genellikle 1–3 dakika sürer; bu pencereyi kapatabilirsiniz." });
  const openBtn = el("a", { class: "btn primary", href: "plan.html?id=" + encodeURIComponent(id), text: "Planı aç →", style: "display:none" });
  const close = el("button", { class: "btn", type: "button", text: "Kapat", onclick: () => { form.parentElement.remove(); load(); } });
  clear(form).append(el("h2", { text: name }), info, ul, el("div", { class: "actions" }, close, openBtn));
  const t0 = Date.now();
  const tick = async () => {
    if (!form.isConnected) return;
    try {
      const rec = await getRecord("P", id);
      const plan = lbl(rec?.[fid("P", "Plan Durumu")]);
      if (plan === "Görevler Oluşturuldu") { steps[1][1] = "done"; steps[2][1] = "active"; }
      if (plan === "Hazır") { steps[1][1] = "done"; steps[2][1] = "done"; steps[3][1] = "done"; paint(); openBtn.style.display = ""; info.textContent = "Plan hazır. Gantt üzerinde inceleyip baseline alabilirsiniz."; load(); return; }
      paint();
    } catch (e) { if (e instanceof SessionGone) return; }
    if (Date.now() - t0 < 6 * 60 * 1000) setTimeout(tick, 4000);
    else { info.textContent = "Plan kurulumu beklenenden uzun sürüyor. Sayfayı daha sonra yenileyin."; openBtn.style.display = ""; }
  };
  setTimeout(tick, 3000);
}

/* ── başlat ────────────────────────────────────────────────────────── */
document.getElementById("btn-new").addEventListener("click", () => { if (ME) openNew(); });
document.getElementById("btn-refresh").addEventListener("click", load);
document.querySelectorAll("#zoom button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll("#zoom button").forEach(x => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
  gantt.setZoom(b.dataset.z);
}));

initShell("portfoy").then(me => { ME = me; load(); }).catch(e => { if (!(e instanceof SessionGone)) stateError(projectsBox, e, () => location.reload()); });
