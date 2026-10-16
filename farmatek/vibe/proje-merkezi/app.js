/* Proje Merkezi — kabuk: kenar menü, üst çubuk, araç çubuğu, durum çubuğu, yönlendirme */
"use strict";

let ME = null;
const VIEWS = {};                  // ad → { title, icon, mount(ctx) → { unmount?, dirty? } }
let current = null, currentName = "";
const $view = document.getElementById("view");
const $ribbon = document.getElementById("ribbon");
const $status = document.getElementById("status");
const $tabs = document.getElementById("tabs");
const $projSel = document.getElementById("proj-switch");
let PROJECTS = [];                 // başlık çubuğundaki proje seçici için
let lastPlanId = null;

function hasUnsaved() { return !!(current && current.dirty && current.dirty()); }

/* ── şerit yardımcıları ───────────────────────────────────────────── */
function rbtn(o) {
  const b = el("button", { class: "rb" + (o.big ? " big" : "") + (o.cls ? " " + o.cls : ""), type: "button", title: o.title || o.text,
    "aria-pressed": o.pressed == null ? null : (o.pressed ? "true" : "false"), disabled: o.disabled || null, onclick: o.onclick },
    icon(o.icon, o.big ? 24 : 16), el("span", { text: o.text }));
  if (o.id) b.id = o.id;
  return b;
}
function rgroup(label, ...items) {
  return el("div", { class: "rgroup" }, el("div", { class: "ritems" }, ...items), el("div", { class: "rlabel", text: label }));
}
function rseg(options, value, onchange, label) {
  const box = el("div", { class: "rseg", role: "group", "aria-label": label || "" });
  for (const [val, text] of options) {
    box.append(el("button", { type: "button", "aria-pressed": val === value ? "true" : "false", text, onclick: e => {
      box.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === e.currentTarget ? "true" : "false"));
      onchange(val);
    } }));
  }
  return box;
}
function rcheck(text, checked, onchange, id) {
  const inp = el("input", { type: "checkbox", id: id || null, checked: checked || null });
  inp.addEventListener("change", () => onchange(inp.checked));
  return el("label", { class: "rcheck" }, inp, el("span", { text }));
}
function setStatus(...parts) {
  clear($status).append(...parts.filter(Boolean).map(p => typeof p === "string" ? el("span", { text: p }) : p));
}

/* ── yönlendirme ───────────────────────────────────────────────────── */
function parseHash() {
  const h = decodeURIComponent(location.hash.replace(/^#\/?/, ""));
  const [path, query] = h.split("?");
  const parts = path.split("/").filter(Boolean);
  const q = new URLSearchParams(query || "");
  return { name: parts[0] || "portfoy", arg: parts[1] || null, q };
}
function go(name, arg, q) {
  const qs = q ? "?" + new URLSearchParams(q).toString() : "";
  location.hash = "#/" + name + (arg ? "/" + encodeURIComponent(arg) : "") + qs;
}
let lastHash = location.hash;
async function route() {
  const r = parseHash();
  if (!VIEWS[r.name]) { go("portfoy"); return; }
  if (hasUnsaved() && location.hash !== lastHash) {
    const ok = await confirmDialog("Kaydedilmemiş değişiklikler", "Plandaki kaydedilmemiş değişiklikler kaybolacak. Devam edilsin mi?", "Değişiklikleri at", true);
    if (!ok) { history.replaceState(null, "", lastHash || "#/portfoy"); return; }
  }
  lastHash = location.hash;
  if (current && current.unmount) try { current.unmount(); } catch (_) { /* yoksay */ }
  current = null; currentName = r.name;
  if (r.name === "plan") {
    if (!r.arg && lastPlanId) { go("plan", lastPlanId); return; }
    lastPlanId = r.arg || lastPlanId;
  }
  $tabs.querySelectorAll("a").forEach(a => a.setAttribute("aria-selected", a.dataset.v === r.name ? "true" : "false"));
  $projSel.value = r.name === "plan" && r.arg ? r.arg : "";
  clear($ribbon); setStatus("Hazır");
  document.title = VIEWS[r.name].title + " · Proje Merkezi";
  document.getElementById("page-title").textContent = VIEWS[r.name].title;
  document.body.classList.remove("nav-open");
  try {
    current = (await VIEWS[r.name].mount({ arg: r.arg, q: r.q, main: $view, ribbon: $ribbon })) || {};
  } catch (e) { stateError($view, e, () => route()); }
}

/* ── başlık çubuğu ─────────────────────────────────────────────────── */
async function loadProjects() {
  try {
    const recs = await fetchAll("P");
    PROJECTS = recs.map(r => ({ id: r._id, name: v(r, "P", "Proje Adı") || "(adsız)", status: lbl(v(r, "P", "Durum")) }))
      .sort((a, b) => a.name.localeCompare(b.name, "tr"));
    const cur = $projSel.value;
    clear($projSel).append(el("option", { value: "", text: "Proje seçin…" }),
      ...PROJECTS.map(p => el("option", { value: p.id, text: p.name + (KAPALI.has(p.status) ? " (" + p.status + ")" : "") })));
    $projSel.value = cur;
  } catch (e) { if (!(e instanceof SessionGone)) $projSel.title = "Projeler alınamadı: " + e.message; }
}
$projSel.addEventListener("change", () => { if ($projSel.value) go("plan", $projSel.value); });

/* tema: varsayılan sistemden; düğme ile değişir (depolama yok) */
const themeBtn = document.getElementById("theme");
function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  clear(themeBtn).append(icon(t === "dark" ? "sun" : "moon", 17), el("span", { text: t === "dark" ? "Açık tema" : "Koyu tema" }));
  themeBtn.setAttribute("aria-label", t === "dark" ? "Açık temaya geç" : "Koyu temaya geç");
  themeBtn.title = themeBtn.getAttribute("aria-label");
}
applyTheme(document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
themeBtn.addEventListener("click", () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));

/* bildirim zili + açılır panel */
const bell = document.getElementById("bell"), badge = document.getElementById("bell-n"), pop = document.getElementById("bell-pop");
function drawBell() {
  badge.textContent = NOTIF.unread > 99 ? "99+" : String(NOTIF.unread);
  badge.hidden = !NOTIF.unread;
  bell.setAttribute("aria-label", "Bildirimler" + (NOTIF.unread ? " (" + NOTIF.unread + " okunmamış)" : ""));
  const navN = document.getElementById("tab-bildirim-n");
  if (navN) { navN.textContent = String(NOTIF.unread); navN.hidden = !NOTIF.unread; }
  if (!pop.hidden) drawPop();
}
function drawPop() {
  clear(pop);
  pop.append(el("div", { class: "pop-h" }, el("b", { text: "Bildirimler" }), el("span", { class: "muted", text: NOTIF.unread + " okunmamış" })));
  const list = NOTIF.items.slice(0, 8);
  if (!NOTIF.loaded) pop.append(el("div", { class: "pop-empty" }, el("div", { class: "spinner sm" })));
  else if (!list.length) pop.append(el("div", { class: "pop-empty", text: "Bu uygulamaya ait bildirim yok." }));
  for (const n of list) pop.append(notifRow(n, true));
  pop.append(el("a", { class: "pop-all", href: "#/bildirimler", text: "Tüm bildirimler ve uyarılar →", onclick: () => { pop.hidden = true; } }));
}
function notifRow(n, compact) {
  const [k, kText] = notifKind(n);
  const p = notifProps(n);
  const row = el("button", { class: "nrow" + (n.state === 0 ? " unread" : "") + (compact ? " compact" : ""), type: "button" },
    el("span", { class: "nk k-" + k, title: kText }),
    el("span", { class: "nt" }, el("span", { class: "nmsg", text: notifText(n) }),
      el("span", { class: "nmeta", text: [p.listName, relTime(n.notification?.creationTime)].filter(Boolean).join(" · ") })));
  row.addEventListener("click", () => openNotification(n));
  return row;
}
async function openNotification(n) {
  pop.hidden = true;
  NOTIF.markRead(n).catch(e => { if (!(e instanceof SessionGone)) toast(e.message, "err"); });
  const p = notifProps(n), listId = n.notification?.listId || p.listId, rid = n.notification?.recordId || p.recordId;
  try {
    if (listId === L.P.id) return go("plan", rid);
    if (listId === L.G.id || listId === L.K.id) {
      const lst = listId === L.G.id ? "G" : "K";
      const rec = await getRecord(lst, rid);
      const pid = linkIds(v(rec, lst, "Proje"))[0];
      if (pid) return go("plan", pid, { sec: rid });
    }
    if (p.recordUrl) toast("Kayıt Workiom'da açılabilir: " + (p.recordTitle || ""), "info");
  } catch (e) { if (!(e instanceof SessionGone)) toast("Kayıt açılamadı: " + e.message, "err"); }
}
bell.addEventListener("click", e => {
  e.stopPropagation();
  pop.hidden = !pop.hidden;
  if (!pop.hidden) { drawPop(); NOTIF.refresh(true); }
});
document.addEventListener("click", e => { if (!pop.hidden && !pop.contains(e.target)) pop.hidden = true; });
NOTIF.on(drawBell);

/* kenar menü ikonları + mobil menü */
$tabs.querySelectorAll("a[data-ic]").forEach(a => a.prepend(icon(a.dataset.ic, 18)));
document.getElementById("menu").addEventListener("click", () => document.body.classList.toggle("nav-open"));

/* ── başlat ───────────────────────────────────────────────────────── */
window.addEventListener("hashchange", route);
window.addEventListener("beforeunload", e => { if (hasUnsaved()) { e.preventDefault(); e.returnValue = ""; } });

async function boot() {
  if (!workiomHeaders()) { redirectToLogin(); return; }
  try {
    ME = await currentUser();
    const who = document.getElementById("whoami");
    clear(who).append(avatar({ id: ME.id, name: ME.name, surname: ME.surname }, "sm"),
      el("span", { class: "who-n", text: [ME.name, ME.surname].filter(Boolean).join(" ") || ME.emailAddress }));
  } catch (e) { if (!(e instanceof SessionGone)) stateError($view, e, () => location.reload()); return; }
  loadProjects();
  NOTIF.start();
  route();
}
document.addEventListener("DOMContentLoaded", boot);
