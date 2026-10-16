/* Proje Yönetimi — ortak çekirdek: oturum, API, şema, tarih, modeller, UI yardımcıları, bildirim servisi */
"use strict";

/* ── Oturum ─────────────────────────────────────────────────────────── */
function getCookie(name) {
  for (const part of document.cookie.split("; ")) {
    const i = part.indexOf("=");
    if (i > -1 && part.slice(0, i) === name)
      return decodeURIComponent(part.slice(i + 1));
  }
  return null;
}

function workiomHeaders() {
  const token = getCookie("Abp.AuthToken");
  const tenantId = getCookie("Abp.TenantId");
  if (!token || !tenantId) return null;   // caller renders the logged-out state
  return {
    "Content-Type": "application/json",
    "Accept": "text/plain",
    "X-Requested-With": "XMLHttpRequest",
    "Authorization": "Bearer " + token,
    "Abp.TenantId": tenantId,
    "X-Workiom-Tenant-ID": tenantId,
    "Client-Type": "Web"
  };
}

let redirectingToLogin = false;

function redirectToLogin() {
  if (redirectingToLogin) return;        // a page firing several requests at
  redirectingToLogin = true;             // once must not redirect several times
  const dirty = typeof hasUnsaved === "function" && hasUnsaved();
  toast("Oturumunuz sona erdi — giriş sayfasına yönlendiriliyorsunuz…" + (dirty ? " Kaydedilmemiş plan değişiklikleri kaybolacak." : ""), "err", 4000);
  const returnUrl = encodeURIComponent(location.pathname + location.search);
  setTimeout(() => location.replace("/account/login?returnUrl=" + returnUrl), 1600);
}

let apiBasePromise = null;

function apiBase() {
  if (apiBasePromise) return apiBasePromise;

  // A workspace on *.workiom.com is identified by its subdomain; one on its
  // own domain, by the origin. The backend prefers tenancyName when both are
  // sent, so send exactly one.
  const host = location.hostname.toLowerCase();
  const body = host.endsWith(".workiom.com")
    ? { tenancyName: host.split(".")[0] }
    : { customDomain: location.origin };

  apiBasePromise = fetch("https://api.workiom.com/api/services/app/Account/IsTenantAvailable", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  })
    .then(r => r.json())
    .then(j => {
      // apiUrl is set only for a workspace on its own shard; serverRootAddress
      // names the host serving everyone else. Both come from Workiom, so
      // neither is a guess.
      const base = j?.result?.apiUrl || j?.result?.serverRootAddress;
      if (!base) throw new Error("Workiom did not report an API host for this workspace.");
      return base;
    })
    .catch(err => {
      apiBasePromise = null;   // a cached rejection would make any Retry fail instantly
      throw err;
    });

  return apiBasePromise;
}

class SessionGone extends Error {}

async function api(method, path, body) {
  const headers = workiomHeaders();
  if (!headers) { redirectToLogin(); throw new SessionGone("oturum yok"); }
  const base = (await apiBase()).replace(/\/$/, "");
  const res = await fetch(base + path, {
    method, headers, body: body === undefined ? undefined : JSON.stringify(body)
  });
  const json = await res.json().catch(() => null);
  if (res.status === 401 || json?.unAuthorizedRequest) {
    redirectToLogin();
    throw new SessionGone("oturum sona erdi");
  }
  if (!res.ok || !json || json.success === false) {
    throw new Error(json?.error?.message || ("İstek başarısız (" + res.status + ")"));
  }
  return json.result;
}

/* ── Şema erişimi ───────────────────────────────────────────────────── */
const L = SCHEMA;
function fid(list, name) {
  const f = L[list].f[name];
  if (!f) throw new Error("Şemada alan yok: " + list + "." + name);
  return String(f.id);
}
function v(rec, list, name) { return rec ? rec[fid(list, name)] : undefined; }
function lbl(x) { return x && typeof x === "object" ? (x.label ?? "") : (x ?? ""); }
function linkIds(x) { return Array.isArray(x) ? x.map(o => o._id) : (x && x._id ? [x._id] : []); }
function linkLabel(x) { return Array.isArray(x) ? x.map(o => o.label).filter(Boolean).join(", ") : (x?.label || ""); }
function userName(u) { return u ? (u.fullname || [u.name, u.surname].filter(Boolean).join(" ") || u.emailAddress || "") : ""; }
function initials(u) {
  const n = userName(u).trim();
  if (!n) return "?";
  const p = n.split(/\s+/);
  return (p[0][0] + (p.length > 1 ? p[p.length - 1][0] : "")).toLocaleUpperCase("tr");
}

/* ── Veri ───────────────────────────────────────────────────────────── */
async function fetchAll(list, extra) {
  const out = [];
  let skip = 0;
  for (;;) {
    const r = await api("POST", "/api/services/app/Data/All",
      { listId: L[list].id, maxResultCount: 500, skipCount: skip, ...(extra || {}) });
    out.push(...r.items);
    if (out.length >= r.totalCount || !r.items.length) return out;
    skip += 500;
  }
}
async function getRecord(list, id) {
  return api("GET", "/api/services/app/Data/Get?listId=" + encodeURIComponent(L[list].id) + "&id=" + encodeURIComponent(id));
}
async function updateRecord(list, id, payload) {
  return api("PUT", "/api/services/app/Data/UpdatePartial?listId=" + encodeURIComponent(L[list].id) + "&id=" + encodeURIComponent(id), payload);
}
async function createRecord(list, payload) {
  return api("POST", "/api/services/app/Data/Create?listId=" + encodeURIComponent(L[list].id), payload);
}
async function deleteRecord(list, id) {
  return api("DELETE", "/api/services/app/Data/Delete?listId=" + encodeURIComponent(L[list].id) + "&id=" + encodeURIComponent(id));
}

let mePromise = null;
function currentUser() {
  if (!mePromise) {
    mePromise = api("GET", "/api/services/app/Session/GetCurrentLoginInformations")
      .then(r => r.user)
      .catch(e => { mePromise = null; throw e; });
  }
  return mePromise;
}

/* ── Tarih (gün bazlı, yerel takvim) ────────────────────────────────── */
// API "2026-11-01T21:00:00Z" döner = yerel (TR) 2 Kasım. Yerel gün bileşenleri alınır.
function toDay(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d)) return null;
  return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5);
}
function inputToDay(s) {            // <input type=date> değeri "YYYY-MM-DD"
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || "");
  return m ? Math.round(Date.UTC(+m[1], +m[2] - 1, +m[3]) / 864e5) : null;
}
function dayToDate(n) { return new Date(n * 864e5); }   // UTC gece yarısı
function dayToISO(n) { return dayToDate(n).toISOString().slice(0, 10); }
function todayDay() { const d = new Date(); return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5); }
const AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
const GUNLER = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];
function fmtDay(n) {
  if (n == null) return "—";
  const d = dayToDate(n);
  return String(d.getUTCDate()).padStart(2, "0") + " " + AYLAR[d.getUTCMonth()] + " " + d.getUTCFullYear();
}
function fmtShort(n) {
  if (n == null) return "—";
  const d = dayToDate(n);
  return String(d.getUTCDate()).padStart(2, "0") + "." + String(d.getUTCMonth() + 1).padStart(2, "0") + "." + String(d.getUTCFullYear()).slice(2);
}
function fmtGrid(n) {               // MS Project: "Pzt 02.11.26"
  if (n == null) return "";
  return GUNLER[dayToDate(n).getUTCDay()] + " " + fmtShort(n);
}
function fmtStamp(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return "";
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" }) + " " + d.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
}
function relTime(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const s = (Date.now() - d.getTime()) / 1000;
  if (s < 60) return "az önce";
  if (s < 3600) return Math.floor(s / 60) + " dk önce";
  if (s < 86400) return Math.floor(s / 3600) + " sa önce";
  if (s < 7 * 86400) return Math.floor(s / 86400) + " gün önce";
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" });
}

/* ── Durumlar ───────────────────────────────────────────────────────── */
const DURUM_SINIF = {
  "Başlamadı": "bekle", "Başlayabilir": "hazir", "Devam Ediyor": "devam", "Onay Bekliyor": "onay",
  "Revizyon Gerekli": "rev", "Beklemede": "dur", "Tamamlandı": "tamam", "İptal": "iptal",
  "Taslak": "bekle", "Planlanıyor": "hazir", "Plan Onaylandı (Baseline)": "onay",
  "Bekleniyor": "bekle", "Ulaşıldı": "tamam", "Gecikti": "rev", "Onaylandı": "tamam", "Reddedildi": "rev"
};
const KAPALI = new Set(["Tamamlandı", "İptal"]);
function chip(label) {
  const s = document.createElement("span");
  s.className = "chip st-" + (DURUM_SINIF[label] || "bekle");
  s.textContent = label || "—";
  return s;
}
function avatar(u, size) {
  const a = el("span", { class: "avatar" + (size ? " " + size : ""), title: userName(u) || "Atanmadı", text: u ? initials(u) : "–" });
  if (u) { let h = 0; for (const ch of String(u.id || userName(u))) h = (h * 31 + ch.charCodeAt(0)) % 360; a.style.setProperty("--h", String(h)); }
  return a;
}

/* ── Modeller ───────────────────────────────────────────────────────── */
/* Görev (Görevler listesi) */
function taskModel(rec) {
  const g = n => v(rec, "G", n);
  const status = lbl(g("Durum"));
  const start = toDay(g("Başlangıç")), end = toDay(g("Bitiş"));
  const closed = KAPALI.has(status);
  const m = {
    kind: "G", id: rec._id, rec,
    name: g("Görev Adı") || "(adsız)",
    wbs: Number(g("WBS No")) || 0,
    start: start ?? end, end: end ?? start,
    deps: depsOf(g("Öncüller"), g("Öncül Kayıtları")),
    phase: linkIds(g("Faz"))[0] || null,
    phaseName: linkLabel(g("Faz")),
    project: linkIds(g("Proje"))[0] || null,
    projectName: linkLabel(g("Proje")),
    status, closed,
    pct: Number(g("% Tamamlanma")) || (closed ? 100 : 0),
    dept: linkLabel(g("Sorumlu Departman")),
    deptId: linkIds(g("Sorumlu Departman"))[0] || null,
    owner: g("Sorumlu") || null,
    approver: g("Onaylayıcı") || null,
    pm: g("Proje Yöneticisi") || null,
    approvalNeeded: !!g("Onay Gerekli"),
    approvalState: lbl(g("Onay Durumu")),
    baseStart: toDay(g("Baseline Başlangıç")),
    baseEnd: toDay(g("Baseline Bitiş")),
    variance: Number(g("Sapma (gün)")) || 0,
    openPreds: Number(g("Açık Öncül Sayısı")) || 0,
    notes: g("Notlar") || "",
    desc: g("Açıklama") || "",
    files: g("Dokümanlar") || [],
    actualStart: toDay(g("Gerçekleşen Başlangıç")),
    actualEnd: toDay(g("Gerçekleşen Bitiş")),
    flaggedLate: !!g("Gecikmede"),
    approvalRequest: rec.approvalRequest || null
  };
  m.late = !closed && m.end != null && m.end < todayDay();
  m.milestone = false;
  return m;
}
/* Bağlar: Öncüller (Gantt oku) + Öncül Kayıtları (kilit). İkisinde de olan = zorunlu; yalnızca okta olan = görsel */
function depsOf(arrows, hardLinks) {
  const hard = new Set(linkIds(hardLinks));
  const out = (arrows || []).map(o => ({ id: o._id, type: o.dependencyType || 1, label: o.label, hard: hard.has(o._id) }));
  for (const h of hardLinks || []) if (!out.some(d => d.id === h._id)) out.push({ id: h._id, type: 1, label: h.label, hard: true });
  return out;
}
const AKTIF_DURUMLAR = ["Devam Ediyor", "Onay Bekliyor", "Tamamlandı"];
/* tamamlanmamış zorunlu öncüller (byId: görev id → model) */
function openPredecessors(t, byId) {
  return (t.deps || []).filter(d => d.hard !== false).map(d => byId.get(d.id) || { id: d.id, name: d.label, status: "", closed: false })
    .filter(p => !p.closed);
}
function isBlocked(t, byId) { return !t.closed && (openPredecessors(t, byId).length > 0 || (!byId.size && t.openPreds > 0)); }
/* İsteği göndermeden durdurur ve nedenini gösterir */
function blockDialog(t, open, wanted) {
  const m = openModal({ title: "İşlem engellendi" });
  m.body.append(el("div", { class: "block-box" }, el("span", { class: "block-ic", "aria-hidden": "true", text: "🔒" }),
      el("div", null, el("b", { text: t.name }), el("p", { text: "\"" + wanted + "\" yapılamaz: aşağıdaki zorunlu öncül" + (open.length > 1 ? "ler" : "") + " henüz tamamlanmadı. Öncüller kapanınca görev kendiliğinden \"Başlayabilir\" olur ve sorumlusuna bildirim gider." }))),
    el("ul", { class: "pred-list" }, ...open.map(p => el("li", null, el("span", { class: "pn", text: p.name }), p.status ? chip(p.status) : null, el("small", { class: "muted", text: p.owner ? userName(p.owner) : "" })))),
    el("p", { class: "hint", text: "Bu kural Workiom'da da tanımlı: görev başka bir ekrandan güncellense bile durum geri alınır." }));
  m.foot.append(el("button", { class: "btn primary", type: "button", text: "Tamam", onclick: () => m.close() }));
}

/* Baseline (Baseline'lar listesi) ve kalemleri (Baseline Kalemleri) */
function blModel(r) {
  return { id: r._id, no: Number(v(r, "BL", "Baseline No")) || 0, name: v(r, "BL", "Baseline") || "", date: toDay(v(r, "BL", "Baseline Tarihi")),
    by: v(r, "BL", "Alan") || null, reason: v(r, "BL", "Gerekçe") || "" };
}
function blItem(r) {
  return { tur: lbl(v(r, "B", "Tür")) || "Görev", gorev: linkIds(v(r, "B", "Görev"))[0] || null, faz: linkIds(v(r, "B", "Faz"))[0] || null,
    kt: linkIds(v(r, "B", "Kilometre Taşı"))[0] || null, s: toDay(v(r, "B", "Planlanan Başlangıç")), e: toDay(v(r, "B", "Planlanan Bitiş")) };
}
async function blItemsOf(blId) {
  return (await fetchAll("B")).filter(r => linkIds(v(r, "B", "Baseline")).includes(blId)).map(blItem);
}

/* Faz (Fazlar listesi) */
function phaseModel(rec) {
  const g = n => v(rec, "F", n);
  return {
    kind: "F", id: rec._id, rec, name: g("Faz") || "(faz)", order: Number(g("Sıra")) || 0,
    start: toDay(g("Başlangıç")), end: toDay(g("Bitiş")),
    recStart: toDay(g("Başlangıç")), recEnd: toDay(g("Bitiş")),
    baseStart: toDay(g("Baseline Başlangıç")), baseEnd: toDay(g("Baseline Bitiş")),
    project: linkIds(g("Proje"))[0] || null, deps: [], desc: g("Açıklama") || ""
  };
}
/* Kilometre taşı (Kilometre Taşları listesi) */
function msModel(rec) {
  const g = n => v(rec, "K", n);
  const d = toDay(g("Hedef Tarih"));
  const status = lbl(g("KT Durumu")) || "Bekleniyor";
  return {
    kind: "K", id: rec._id, rec, name: g("Kilometre Taşı") || "(kilometre taşı)", milestone: true,
    start: d, end: d, status, closed: status === "Ulaşıldı",
    pct: status === "Ulaşıldı" ? 100 : 0,
    deps: (g("Bağlı Görevler") || []).map(o => ({ id: o._id, type: 1, label: o.label })),
    phase: linkIds(g("Faz"))[0] || null, phaseName: linkLabel(g("Faz")),
    project: linkIds(g("Proje"))[0] || null, projectName: linkLabel(g("Proje")),
    critical0: !!g("Kritik"),
    actual: toDay(g("Gerçekleşen Tarih")),
    baseStart: toDay(g("Baseline Tarih")), baseEnd: toDay(g("Baseline Tarih")),
    variance: Number(g("Sapma (gün)")) || 0,
    openLinked: Number(g("Açık Bağlı Görev")) || 0,
    pm: g("Proje Yöneticisi") || null, desc: g("Açıklama") || ""
  };
}

/* Kritik yol: FS/SS/FF/SF, gerçek tarihlerle geri geçiş. Bolluk ≤ 0 → kritik */
function markCritical(items) {
  const leaves = items.filter(t => !t.summary && t.start != null);
  const byId = new Map(leaves.map(t => [t.id, t]));
  const succ = new Map(leaves.map(t => [t.id, []]));
  for (const t of leaves) for (const d of t.deps) if (succ.has(d.id)) succ.get(d.id).push([t, d.type || 1]);
  if (!leaves.length) return;
  const projEnd = Math.max(...leaves.map(t => t.end));
  const lf = new Map();
  const calc = (t, depth) => {
    if (lf.has(t.id)) return lf.get(t.id);
    if (depth > 4000) return projEnd;
    lf.set(t.id, projEnd);                    // döngü koruması
    let val = projEnd;
    for (const [s, typ] of succ.get(t.id)) {
      const sLF = calc(s, depth + 1), sDur = s.end - s.start, sLS = sLF - sDur;
      if (typ === 2) val = Math.min(val, sLS + (t.end - t.start));        // SS: öncül başı ≤ ardıl başı
      else if (typ === 3) val = Math.min(val, sLF);                        // FF
      else if (typ === 4) val = Math.min(val, sLF + (t.end - t.start));    // SF
      else val = Math.min(val, sLS);                                       // FS
    }
    lf.set(t.id, val);
    return val;
  };
  [...leaves].sort((a, b) => b.end - a.end).forEach(t => calc(t, 0));
  for (const t of leaves) t.critical = !t.closed && (lf.get(t.id) - t.end) <= 0;
  for (const t of items) if (t.summary) t.critical = false;
  return byId;
}

/* ── UI yardımcıları ────────────────────────────────────────────────── */
function el(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, val] of Object.entries(attrs || {})) {
    if (val == null || val === false) continue;
    if (k === "class") e.className = val;
    else if (k === "text") e.textContent = val;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), val);
    else if (k === "style") e.style.cssText = val;
    else e.setAttribute(k, val === true ? "" : val);
  }
  for (const k of kids.flat()) if (k != null && k !== false) e.append(k.nodeType ? k : document.createTextNode(String(k)));
  return e;
}
function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); return node; }
const SVGNS = "http://www.w3.org/2000/svg";
function svg(tag, attrs, ...kids) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, val] of Object.entries(attrs || {})) if (val != null) e.setAttribute(k, val);
  kids.flat().forEach(k => k && e.append(k));
  return e;
}
/* Basit çizgi ikonları (harici kaynak yok) */
const ICONS = {
  portfolio: "M3 4h7v7H3zM14 4h7v4h-7zM14 11h7v9h-7zM3 14h7v6H3z",
  plan: "M3 5h8M6 10h10M9 15h12M3 20h6",
  task: "M4 12l5 5L20 6",
  approve: "M12 3l7 4v5c0 4-3 7.5-7 9-4-1.5-7-5-7-9V7zM8.5 12l2.5 2.5 4.5-5",
  bell: "M6 17V11a6 6 0 0 1 12 0v6l2 2H4zM10 21h4",
  library: "M4 4h4v16H4zM10 4h4v16h-4zM16 5l4 1-3 15-4-1z",
  log: "M12 7v5l3 2M12 3a9 9 0 1 0 9 9",
  plus: "M12 5v14M5 12h14",
  save: "M5 4h11l3 3v13H5zM8 4v5h7V4M8 20v-6h8v6",
  undo: "M9 14L4 9l5-5M4 9h10a6 6 0 0 1 0 12h-3",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3",
  today: "M4 6h16v14H4zM4 10h16M9 3v4M15 3v4M11 14h2v2h-2z",
  baseline: "M4 18h16M4 14h10M4 10h14M4 6h8",
  critical: "M12 3l9 16H3zM12 10v4M12 17v.5",
  excel: "M5 3h10l4 4v14H5zM8 11l4 6M12 11l-4 6M14 3v5h5",
  link: "M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1",
  ms: "M12 4l8 8-8 8-8-8z",
  phase: "M3 6h18v4H3zM6 14h12M6 18h8",
  info: "M12 8v.5M12 11v6M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18z",
  collapse: "M4 6h16M4 12h10M4 18h16",
  filter: "M4 5h16l-6 7v6l-4 2v-8z",
  refresh: "M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0",
  sun: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5",
  moon: "M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z",
  edit: "M4 20h4L19 9l-4-4L4 16zM14 6l4 4",
  zoomin: "M10 4a6 6 0 1 0 0 12 6 6 0 0 0 0-12zM20 20l-5.5-5.5M10 7v6M7 10h6",
  zoomout: "M10 4a6 6 0 1 0 0 12 6 6 0 0 0 0-12zM20 20l-5.5-5.5M7 10h6",
  check: "M5 12l5 5L20 7",
  x: "M6 6l12 12M18 6L6 18",
  upload: "M12 16V4M7 9l5-5 5 5M4 20h16",
  calendar: "M4 6h16v14H4zM4 10h16M9 3v4M15 3v4",
  board: "M4 4h5v16H4zM10 4h5v10h-5zM16 4h4v13h-4z",
  list: "M8 6h12M8 12h12M8 18h12M4 6h.5M4 12h.5M4 18h.5"
};
function icon(name, size) {
  const s = svg("svg", { viewBox: "0 0 24 24", width: size || 18, height: size || 18, "aria-hidden": "true", class: "ic" },
    svg("path", { d: ICONS[name] || ICONS.info, fill: "none", stroke: "currentColor", "stroke-width": "1.7", "stroke-linecap": "round", "stroke-linejoin": "round" }));
  return s;
}

function toast(msg, kind, ms) {
  let box = document.getElementById("toasts");
  if (!box) { box = el("div", { id: "toasts", role: "status", "aria-live": "polite" }); document.body.append(box); }
  const t = el("div", { class: "toast " + (kind || ""), text: msg });
  box.append(t);
  setTimeout(() => t.classList.add("out"), (ms || 3800) - 300);
  setTimeout(() => t.remove(), ms || 3800);
}

function stateLoading(node, text) {
  clear(node).append(el("div", { class: "state" }, el("div", { class: "spinner" }), el("p", { text: text || "Yükleniyor…" })));
}
function stateError(node, err, retry) {
  if (err instanceof SessionGone) return;
  clear(node).append(el("div", { class: "state" },
    el("div", { class: "state-ic err" }, icon("critical", 28)),
    el("h2", { text: "Veriler yüklenemedi" }),
    el("p", { text: err?.message || String(err) }),
    retry ? el("button", { class: "btn primary", type: "button", onclick: retry, text: "Tekrar dene" }) : null));
}
function stateEmpty(node, title, text, action, ic) {
  clear(node).append(el("div", { class: "state" },
    el("div", { class: "state-ic" }, icon(ic || "plan", 28)), el("h2", { text: title }), el("p", { text }), action || null));
}

/* Modal: içerik + eylemler. close() döner. */
function openModal(opts) {
  const back = el("div", { class: "modal-back" });
  const box = el(opts.form ? "form" : "div", { class: "modal" + (opts.wide ? " wide" : ""), role: "dialog", "aria-modal": "true", "aria-labelledby": "m-title", novalidate: opts.form ? true : null });
  const close = () => { back.remove(); document.removeEventListener("keydown", esc); opts.onClose && opts.onClose(); };
  const esc = e => { if (e.key === "Escape") close(); };
  box.append(el("header", null, el("h2", { id: "m-title", text: opts.title }),
    el("button", { class: "icon-btn", type: "button", "aria-label": "Kapat", onclick: close }, icon("x", 16))));
  const body = el("div", { class: "m-body" });
  const foot = el("footer", { class: "m-foot" });
  box.append(body, foot);
  back.append(box);
  back.addEventListener("mousedown", e => { if (e.target === back) close(); });
  document.addEventListener("keydown", esc);
  document.body.append(back);
  return { back, box, body, foot, close };
}
function confirmDialog(title, text, okText, danger) {
  return new Promise(res => {
    const m = openModal({ title, onClose: () => res(false) });
    m.body.append(el("p", { class: "lead", text }));
    const ok = el("button", { class: "btn " + (danger ? "danger" : "primary"), type: "button", text: okText || "Tamam" });
    m.foot.append(el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => m.close() }), ok);
    ok.addEventListener("click", () => { m.back.remove(); res(true); });
    ok.focus();
  });
}
function field(label, control, opts) {
  const id = control.id || ("f" + Math.random().toString(36).slice(2, 8));
  control.id = id;
  if (opts?.required) { control.setAttribute("required", ""); control.setAttribute("aria-required", "true"); }
  return el("div", { class: "field" + (opts?.wide ? " wide" : "") },
    el("label", { for: id }, label, opts?.required ? el("span", { class: "req", "aria-hidden": "true", text: "*" }) : null),
    control, opts?.hint ? el("small", { class: "hint", text: opts.hint }) : null);
}
function reqNote() { return el("p", { class: "req-note" }, el("span", { class: "req", "aria-hidden": "true", text: "*" }), " Zorunlu"); }

function isEmptyValue(x) {
  return x == null
    || (typeof x === "string" && x.trim() === "")
    || (Array.isArray(x) && x.length === 0);
}
// requiredFields: [{ id, name, control }] — <app_schema>'dan; boş olanları işaretler, ilkine odaklanır
function checkRequired(requiredFields, values, errBox) {
  const miss = requiredFields.filter(f => isEmptyValue(values[String(f.id)]));
  requiredFields.forEach(f => f.control && f.control.removeAttribute("aria-invalid"));
  if (!miss.length) { clear(errBox); return true; }
  errBox.textContent = "Eksik zorunlu alan: " + miss.map(f => f.name).join(", ");
  miss.forEach(f => f.control && f.control.setAttribute("aria-invalid", "true"));
  miss[0].control && miss[0].control.focus();
  return false;
}

/* ── Kullanıcılar ───────────────────────────────────────────────────── */
let usersPromise = null;
function listUsers() {
  if (!usersPromise) {
    usersPromise = api("GET", "/api/services/app/User/GetAll?isActive=true")
      .catch(e => { if (e instanceof SessionGone) throw e; return api("GET", "/api/services/app/User/GetUsers?MaxResultCount=500"); })
      .then(r => (Array.isArray(r) ? r : (r.items || [])).filter(u => u.isActive !== false)
        .map(u => ({ id: String(u.id), name: [u.name, u.surname].filter(Boolean).join(" ") || u.emailAddress, email: u.emailAddress || u.userName }))
        .sort((a, b) => a.name.localeCompare(b.name, "tr")))
      .catch(e => { usersPromise = null; throw e; });
  }
  return usersPromise;
}
function userSelect(current, placeholder, id) {
  const sel = el("select", { class: "input", id: id || null }, el("option", { value: "", text: placeholder || "— seçin —" }));
  listUsers().then(us => {
    us.forEach(u => sel.append(el("option", { value: u.email, text: u.name, selected: current && String(current.id) === u.id ? true : null })));
    if (current && !us.some(u => u.id === String(current.id)) && current.emailAddress)
      sel.append(el("option", { value: current.emailAddress, text: userName(current), selected: true }));
  }).catch(e => { if (!(e instanceof SessionGone)) { sel.disabled = true; sel.title = "Kullanıcı listesi alınamadı: " + e.message; } });
  return sel;
}
function multiUserSelect(current, id) {
  const sel = el("select", { class: "input", multiple: true, size: "5", id: id || null });
  const cur = new Set((current || []).map(u => String(u.id)));
  listUsers().then(us => us.forEach(u => sel.append(el("option", { value: u.email, text: u.name, selected: cur.has(u.id) || null }))))
    .catch(e => { if (!(e instanceof SessionGone)) sel.disabled = true; });
  return sel;
}
function sameUser(a, b) { return !!a && !!b && String(a.id) === String(b.id); }

/* ── Kayıt geçmişi ve yorumlar ─────────────────────────────────────── */
const ISLEM = { 0: "oluşturdu", 1: "güncelledi", 2: "sildi", 3: "geri yükledi", 8: "onay adımı" };
function histValue(x) {
  if (x == null || x === "") return "—";
  if (Array.isArray(x)) return x.map(histValue).join(", ");
  if (typeof x === "object") return x.label || x.fullname || x.FileName || x.dependencyType && ("bağ " + (x.label || "")) || JSON.stringify(x);
  const m = /^#?(\d{4}-\d{2}-\d{2})T[\d:.]+Z?#?/.exec(String(x));
  if (m) return fmtDay(toDay(m[1] + "T12:00:00"));
  if (x === "true" || x === true) return "Evet";
  if (x === "false" || x === false) return "Hayır";
  return String(x);
}
function histEntry(h, withItem) {
  const auto = h.automationId != null;
  const li = el("li", { class: auto ? "auto" : "user" });
  li.append(el("div", { class: "when" }, el("b", { text: h.username || "Sistem" }), auto ? el("span", { class: "tag", text: "otomasyon" }) : null, " · " + fmtStamp(h.date)));
  if (withItem) li.append(el("div", { class: "what" }, el("b", { text: h.itemName || "" }), " ", el("span", { class: "tag", text: h.listName || "" })));
  if (h.approvalRequestItem) {
    const a = h.approvalRequestItem;
    const st = { 0: "onay talebi açıldı", 1: "ONAYLANDI", 2: "REDDEDİLDİ", 3: "süresi doldu" }[a.requestStatus] ?? "onay";
    li.append(el("div", { class: "chg", text: "✍ " + (a.requestTitle || "Onay") + ": " + st }));
    return li;
  }
  const rec = h.record || {}, prev = h.previousRecord || {};
  const keys = Object.keys(rec).filter(k => !/^Last |^Creation|^Creator/.test(k));
  if (!keys.length) li.append(el("div", { class: "chg", text: "Kaydı " + (ISLEM[h.action] || "değiştirdi") }));
  for (const k of keys.slice(0, 12)) {
    const c = el("div", { class: "chg" }, el("b", { text: k + ": " }));
    if (k in prev) c.append(el("s", { text: histValue(prev[k]) }), " → ");
    c.append(histValue(rec[k]));
    li.append(c);
  }
  return li;
}
async function renderHistory(box, list, recordId) {
  stateLoading(box, "Geçmiş yükleniyor…");
  try {
    const q = "listId=" + encodeURIComponent(L[list].id) + "&recordId=" + encodeURIComponent(recordId) +
      "&showHistory=true&showComments=true&showConversations=false&showApprovalRequest=true&MaxResultCount=100&SkipCount=0";
    const r = await api("GET", "/api/services/app/History/GetAll?" + q);
    const items = (Array.isArray(r) ? r : (r.items || [])).filter(h => h.isVisible !== false);
    if (!items.length) { clear(box).append(el("p", { class: "hint", text: "Kayıtlı değişiklik yok." })); return; }
    clear(box).append(el("ul", { class: "hist" }, ...items.map(h => histEntry(h, false))));
  } catch (e) { if (!(e instanceof SessionGone)) clear(box).append(el("p", { class: "hint", text: "Geçmiş alınamadı: " + e.message })); }
}
async function renderComments(box, list, recordId) {
  stateLoading(box, "Yorumlar yükleniyor…");
  const form = el("form", { class: "comment-form" });
  const ta = el("textarea", { class: "input", rows: "2", placeholder: "Yorum yazın…", "aria-label": "Yorum" });
  const send = el("button", { class: "btn primary sm", type: "submit", text: "Gönder" });
  form.append(ta, send);
  const draw = async () => {
    try {
      const r = await api("GET", "/api/services/app/AdvancedComment/GetAll?listId=" + encodeURIComponent(L[list].id) + "&recordId=" + encodeURIComponent(recordId));
      const items = Array.isArray(r) ? r : (r?.items || []);
      const ul = el("ul", { class: "comments" });
      if (!items.length) ul.append(el("li", { class: "hint", text: "Henüz yorum yok." }));
      for (const c of items) {
        const txt = c.commentAsPlainText || c.plainText || c.comment || c.text || "";
        ul.append(el("li", null, el("div", { class: "when" }, el("b", { text: c.userFullName || c.fullName || c.creatorUserName || c.user?.fullname || "Kullanıcı" }), " · " + fmtStamp(c.creationTime || c.date)),
          el("div", { class: "c-txt", text: String(txt).replace(/<[^>]*>/g, "") })));
      }
      clear(box).append(ul, form);
    } catch (e) { if (!(e instanceof SessionGone)) clear(box).append(el("p", { class: "hint", text: "Yorumlar alınamadı: " + e.message }), form); }
  };
  form.addEventListener("submit", async ev => {
    ev.preventDefault();
    if (!ta.value.trim()) { ta.setAttribute("aria-invalid", "true"); ta.focus(); return; }
    send.disabled = true;
    try {
      await api("POST", "/api/services/app/AdvancedComment/Comment?commentAsPlainText=true", { listId: L[list].id, recordId, comment: ta.value.trim() });
      ta.value = ""; toast("Yorum eklendi", "ok"); await draw();
    } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
    finally { send.disabled = false; }
  });
  await draw();
}

/* ── Dosyalar (Workiom dosya uç noktaları: /api/services/app öneki YOK) ── */
async function uploadFile(file) {
  const headers = workiomHeaders();
  if (!headers) { redirectToLogin(); return null; }
  delete headers["Content-Type"];          // let the browser set the multipart boundary
  const body = new FormData();
  body.append("files", file);
  const res = await fetch(`${await apiBase()}/File/Upload`, { method: "POST", headers, body });   // NOT /api/services/app/File/Upload
  const json = await res.json().catch(() => null);
  if (res.status === 401 || json?.unAuthorizedRequest) { redirectToLogin(); return null; }
  if (!json?.success) throw new Error(json?.error?.message || "Yükleme başarısız");
  return json.result[0];
}
function toFileFieldValue(uploaded, originalFile, userId) {
  return {
    _id: uploaded.fileToken,
    AnonymousForm: false,
    ContentType: uploaded.fileType,
    ExpiryDate: null,
    FileName: uploaded.fileName,
    FileToken: uploaded.fileToken,
    FileUrl: uploaded.fileUrl,
    HasThumbnail: !!uploaded.hasThumbnail,
    IsPermanent: true,
    Size: originalFile.size,
    ThumbnailUrl: uploaded.thumbnailUrl,
    UserId: userId
  };
}
async function downloadFile(file) {
  const id = file._id || file.FileToken;
  const headers = workiomHeaders();
  if (!headers) { redirectToLogin(); return; }
  const res = await fetch(`${await apiBase()}/api/services/app/File/GeneratePublicDownloadUrl/${encodeURIComponent(id)}?forceDownload=true`, { headers });
  if (res.status === 401) { redirectToLogin(); return; }
  const data = await res.json().catch(() => null);
  if (!res.ok || data?.success === false) throw new Error(data?.error?.message || `HTTP ${res.status}`);
  const url = data?.result?.url;
  if (!url) throw new Error("Response had no result.url");
  const a = document.createElement("a");
  a.href = url;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
/* Dosya alanı düzenleyici: mevcut dosyalar + yükle; değişince onChange(yeniDizi) */
function fileEditor(files, onChange) {
  const box = el("div", { class: "files" });
  const draw = () => {
    clear(box);
    for (const f of files) box.append(el("div", { class: "file" }, icon("excel", 16), el("span", { class: "fn", text: f.FileName || "dosya" }),
      el("button", { class: "btn sm", type: "button", text: "İndir", onclick: () => downloadFile(f).catch(e => { if (!(e instanceof SessionGone)) toast(e.message, "err"); }) })));
    const inp = el("input", { type: "file", multiple: true, class: "sr-only", id: "up" + Math.random().toString(36).slice(2, 7) });
    const lab = el("label", { class: "btn sm", for: inp.id }, icon("upload", 15), " Doküman yükle");
    inp.addEventListener("change", async () => {
      if (!inp.files.length) return;
      lab.classList.add("busy");
      try {
        const me = await currentUser();
        const next = files.map(f => ({ ...f }));
        for (const file of inp.files) { const u = await uploadFile(file); if (u) next.push(toFileFieldValue(u, file, me.id)); }
        await onChange(next);
      } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
      finally { lab.classList.remove("busy"); }
    });
    box.append(el("div", { class: "file add" }, inp, lab));
  };
  draw();
  return box;
}

/* ── Excel (CSV, UTF-8 BOM, noktalı virgül) ─────────────────────────── */
function downloadCSV(filename, rows) {
  const esc = x => {
    const s = x == null ? "" : String(x);
    return /[;"\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const text = "﻿" + rows.map(r => r.map(esc).join(";")).join("\r\n");
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  const a = el("a", { href: url, download: filename });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/* Sınırlı eşzamanlılıkla güncelleme kuyruğu */
async function runPool(items, worker, size, onProgress) {
  let i = 0, done = 0;
  const errors = [];
  const next = async () => {
    while (i < items.length) {
      const it = items[i++];
      try { await worker(it); } catch (e) { if (e instanceof SessionGone) throw e; errors.push([it, e]); }
      done++;
      onProgress && onProgress(done, items.length);
    }
  };
  await Promise.all(Array.from({ length: Math.min(size, items.length) }, next));
  return errors;
}

/* ── Bildirim servisi (Workiom bildirimleri, bu uygulamaya ait olanlar) ── */
const NOTIF = {
  items: [], unread: 0, lastIds: null, listeners: new Set(), timer: null, loaded: false,
  async refresh(silent) {
    try {
      const all = [];
      for (let skip = 0; skip < 400; skip += 100) {
        const r = await api("GET", "/api/services/app/Notification/GetUserNotifications?maxResultCount=100&skipCount=" + skip);
        const items = r?.items || [];
        all.push(...items);
        if (items.length < 100) break;
      }
      const mine = all.filter(n => n.notification?.appId === L.APP.id || n.notification?.data?.properties?.appId === L.APP.id);
      const fresh = this.lastIds ? mine.filter(n => n.state === 0 && !this.lastIds.has(n.id)) : [];
      this.lastIds = new Set(mine.map(n => n.id));
      this.items = mine;
      this.unread = mine.filter(n => n.state === 0).length;
      this.loaded = true;
      if (!silent) fresh.slice(0, 3).forEach(n => toast("🔔 " + notifText(n), "info", 6000));
      this.listeners.forEach(fn => fn());
    } catch (e) { if (!(e instanceof SessionGone) && !silent) console.warn("Bildirimler alınamadı:", e.message); }
  },
  async markRead(n) {
    if (n.state !== 0) return;
    await api("POST", "/api/services/app/Notification/SetNotificationAsRead", { id: n.id });
    n.state = 1; this.unread = this.items.filter(x => x.state === 0).length;
    this.listeners.forEach(fn => fn());
  },
  start() { if (!this.timer) { this.refresh(true); this.timer = setInterval(() => this.refresh(false), 60000); } },
  on(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
};
function notifProps(n) { return n.notification?.data?.properties || {}; }
function notifText(n) {
  const p = notifProps(n);
  return String(p.notificationMessage || p.Message || n.notification?.data?.message || "Bildirim").replace(/<[^>]*>/g, "");
}
function notifKind(n) {
  const t = notifText(n);
  if (/⛔|kilit|başlatılamaz/i.test(t)) return ["lock", "Öncül kilidi"];
  if (/reddedildi|revizyon/i.test(t)) return ["rev", "Red"];
  if (/onay/i.test(t)) return ["onay", "Onay"];
  if (/🏁|ulaşıldı/i.test(t)) return ["ms", "Kilometre taşı"];
  if (/⚠️|⏰|gecik/i.test(t)) return ["late", "Gecikme"];
  if (/📅|kaldı/i.test(t)) return ["soon", "Yaklaşan"];
  if (/▶️|başlayabilir/i.test(t)) return ["go", "Başlayabilir"];
  if (/📌|baseline/i.test(t)) return ["base", "Baseline"];
  if (/plan(ı)? hazır/i.test(t)) return ["plan", "Plan"];
  return ["info", "Bildirim"];
}
