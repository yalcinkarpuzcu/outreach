/* Görev kütüphanesi: şablon Gantt'ı (salt okunur — düzenleme Workiom'da PMO tarafından) */
"use strict";

let ITEMS = [], SAB = [];
const host = document.getElementById("gantt");
const sel = document.getElementById("sel-sab");
const kpiBox = document.getElementById("kpis");
let gantt = null;

function kpi(label, value, sub) {
  return el("div", { class: "card kpi" }, el("div", { class: "label", text: label }), el("div", { class: "value", text: String(value) }), el("div", { class: "sub", text: sub || "" }));
}

function show() {
  const sid = sel.value;
  const recs = ITEMS.filter(r => linkIds(v(r, "K", "Şablonlar")).includes(sid));
  const tasks = recs.map(r => taskModel(r, "K"));
  if (!tasks.length) { stateEmpty(host, "Bu şablonda kalem yok", "Kütüphaneye kalem ekleyip şablona bağlayın."); clear(kpiBox); return; }
  const ref = Math.min(...tasks.filter(t => t.start != null).map(t => t.start));
  gantt = createGantt(host, { zoom: document.querySelector("#zoom [aria-pressed=true]").dataset.z, mode: "kutuphane", refDay: ref, showBaseline: false, onSelect: detail });
  gantt.setTasks(tasks);
  const ls = tasks.filter(t => !t.summary);
  const end = Math.max(...ls.map(t => t.end));
  clear(kpiBox).append(
    kpi("Kalem", ls.length, tasks.length - ls.length + " faz"),
    kpi("Toplam süre", (end - ref) + " gün", "≈ " + Math.round((end - ref) / 30) + " ay (kritik yol)"),
    kpi("Onay gerektiren", ls.filter(t => t.approvalNeeded).length, "zorunlu onay adımı"),
    kpi("Kilometre taşı", ls.filter(t => t.milestone).length, ""),
    kpi("Varsayım", ls.filter(t => v(t.rec, "K", "Varsayım")).length, "Excel'de süre/öncül tanımsızdı — teyit edilecek"));
}

let drawerEls = null;
function closeDrawer() { if (drawerEls) { drawerEls.forEach(x => x.remove()); drawerEls = null; } }
function detail(t) {
  closeDrawer();
  const back = el("div", { class: "drawer-back", onclick: closeDrawer });
  const kv = el("dl", { class: "kv" });
  const row = (k, val) => kv.append(el("dt", { text: k }), el("dd", null, val));
  row("Tür", t.type || "—");
  row("Departman", t.dept || "—");
  row("Süre", (t.end - t.start) + " gün");
  row("Onay", t.approvalNeeded ? "Gerekli" : "Gerekmiyor");
  if (v(t.rec, "K", "Varsayım")) row("Not", "⚠ Varsayım — müşteriyle teyit edilecek");
  const pl = el("ul", { class: "pred-list" });
  if (!t.deps.length) pl.append(el("li", { text: "Öncül yok" }));
  t.deps.forEach(d => pl.append(el("li", { text: d.label + (d.type && d.type !== 1 ? " (" + ["", "FS", "SS", "FF", "SF"][d.type] + ")" : " (FS)") })));
  const kk = v(t.rec, "K", "Kabul Kriteri");
  const dr = el("aside", { class: "drawer", role: "dialog", "aria-modal": "true", "aria-labelledby": "k-t" },
    el("header", null, el("span", { class: "tag", text: "WBS " + t.wbs }), el("h2", { id: "k-t", text: t.name })),
    el("div", { class: "body" }, kv, el("div", { class: "section-t", text: "Öncüller" }), pl,
      kk ? el("div", null, el("div", { class: "section-t", text: "Kabul kriteri" }), el("p", { style: "white-space:pre-wrap", text: kk })) : null,
      el("p", { style: "color:var(--text-muted);font-size:12.5px;margin-top:16px", text: "Kütüphane, Workiom'daki 'Görev Kütüphanesi' listesinden PMO tarafından düzenlenir; değişiklikler bundan sonra açılan projelere yansır." })),
    el("footer", null, el("button", { class: "btn", type: "button", text: "Kapat", onclick: closeDrawer })));
  drawerEls = [back, dr];
  document.body.append(back, dr);
}

async function load() {
  stateLoading(host, "Kütüphane yükleniyor…");
  try {
    const [items, sab] = await Promise.all([fetchAll("K"), fetchAll("S")]);
    ITEMS = items; SAB = sab;
    clear(sel).append(...SAB.map(s => el("option", { value: s._id, text: v(s, "S", "Şablon") })));
    if (!SAB.length) { stateEmpty(host, "Şablon yok", "Workiom'da 'Proje Şablonları' listesine bir şablon ekleyin."); return; }
    show();
  } catch (e) {
    if (e instanceof SessionGone) return;
    if (/permission|yetki|access|izin/i.test(e.message)) stateEmpty(host, "Kütüphaneye erişiminiz yok", "Görev kütüphanesi proje yöneticileri ve PMO'ya açıktır.");
    else stateError(host, e, load);
  }
}

sel.addEventListener("change", show);
document.querySelectorAll("#zoom button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll("#zoom button").forEach(x => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
  gantt && gantt.setZoom(b.dataset.z);
}));
initShell("kutuphane").then(load).catch(e => { if (!(e instanceof SessionGone)) stateError(host, e, () => location.reload()); });
