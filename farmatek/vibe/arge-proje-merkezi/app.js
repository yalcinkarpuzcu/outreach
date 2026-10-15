/* Ar-Ge Proje Merkezi — ortak altyapı: oturum, API, şema, tarih, UI yardımcıları */
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
  toast("Oturumunuz sona erdi — giriş sayfasına yönlendiriliyorsunuz… Kaydedilmemiş değişiklikler kaybolabilir.", "err", 4000);
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
const L = { P: SCHEMA.P, G: SCHEMA.G, K: SCHEMA.K, S: SCHEMA.S };
function fid(list, name) {
  const f = L[list].f[name];
  if (!f) throw new Error("Şemada alan yok: " + list + "." + name);
  return String(f.id);
}
function v(rec, list, name) { return rec ? rec[fid(list, name)] : undefined; }
function lbl(x) { return x && typeof x === "object" ? (x.label ?? "") : (x ?? ""); }
function linkIds(x) { return Array.isArray(x) ? x.map(o => o._id) : (x && x._id ? [x._id] : []); }
function userName(u) { return u ? (u.fullname || [u.name, u.surname].filter(Boolean).join(" ") || u.emailAddress || "") : ""; }

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
function dayToDate(n) { return new Date(n * 864e5); }   // UTC gece yarısı
function dayToISO(n) { return dayToDate(n).toISOString().slice(0, 10); }
function todayDay() { const d = new Date(); return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5); }
const AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
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

/* ── Durumlar ───────────────────────────────────────────────────────── */
const DURUM_SINIF = {
  "Başlamadı": "bekle", "Başlayabilir": "hazir", "Devam Ediyor": "devam", "Onay Bekliyor": "onay",
  "Revizyon Gerekli": "rev", "Beklemede": "devam", "Tamamlandı": "tamam", "İptal": "iptal",
  "Taslak": "bekle", "Planlanıyor": "hazir", "Plan Onaylandı (Baseline)": "onay"
};
const KAPALI = new Set(["Tamamlandı", "İptal"]);
function chip(label) {
  const s = document.createElement("span");
  s.className = "chip st-" + (DURUM_SINIF[label] || "bekle");
  s.textContent = label || "—";
  return s;
}

/* ── Görev modeli (Görevler + Kütüphane ortak) ─────────────────────── */
function taskModel(rec, list) {
  const g = n => v(rec, list, n);
  const tur = lbl(g("Tür"));
  const status = list === "G" ? lbl(g("Durum")) : "";
  const start = toDay(g("Başlangıç")), end = toDay(g("Bitiş"));
  const m = {
    id: rec._id, rec, list,
    name: g("Görev Adı") || "(adsız)",
    wbs: Number(g("WBS No")) || 0,
    type: tur,
    start, end: end ?? start,
    milestone: !!g("Kilometre Taşı") || tur === "Kilometre Taşı",
    deps: (g("Öncüller") || []).map(o => ({ id: o._id, type: o.dependencyType || 1, label: o.label })),
    parent: list === "G" ? linkIds(g("Üst Görev"))[0] : linkIds(g("Üst Öğe"))[0],
    status,
    closed: KAPALI.has(status),
    pct: list === "G" ? (Number(g("% Tamamlanma")) || (KAPALI.has(status) ? 100 : 0)) : 0,
    dept: lbl((g("Sorumlu Departman") || [])[0]),
    approvalNeeded: !!g("Onay Gerekli")
  };
  if (list === "G") {
    m.owner = g("Sorumlu");
    m.approver = g("Onaylayıcı");
    m.project = linkIds(g("Proje"))[0];
    m.projectName = lbl((g("Proje") || [])[0]);
    m.baseStart = toDay(g("Baseline Başlangıç"));
    m.baseEnd = toDay(g("Baseline Bitiş"));
    m.variance = Number(g("Sapma (gün)")) || 0;
    m.openPreds = Number(g("Açık Öncül Sayısı")) || 0;
    m.late = !m.closed && m.end != null && m.end < todayDay();
    m.approvalState = lbl(g("Onay Durumu"));
    m.notes = g("Notlar") || "";
    m.files = g("Dokümanlar") || [];
    m.actualStart = toDay(g("Gerçekleşen Başlangıç"));
    m.actualEnd = toDay(g("Gerçekleşen Bitiş"));
  }
  return m;
}

/* Hiyerarşi: üst öğe → çocuklar, WBS sırası; özet çubuklarının aralığı çocuklardan */
function buildTree(tasks) {
  const byId = new Map(tasks.map(t => [t.id, t]));
  tasks.forEach(t => { t.children = []; t.summary = false; });
  const roots = [];
  for (const t of tasks) {
    const p = t.parent && byId.get(t.parent);
    if (p) p.children.push(t); else roots.push(t);
  }
  const sortRec = arr => { arr.sort((a, b) => a.wbs - b.wbs); arr.forEach(x => sortRec(x.children)); };
  sortRec(roots);
  const roll = t => {
    if (!t.children.length) return;
    t.summary = true;
    t.children.forEach(roll);
    const ss = t.children.map(c => c.start).filter(x => x != null);
    const ee = t.children.map(c => c.end).filter(x => x != null);
    if (ss.length) t.start = Math.min(...ss);
    if (ee.length) t.end = Math.max(...ee);
    const leaves = [];
    const walk = x => x.children.length ? x.children.forEach(walk) : leaves.push(x);
    walk(t);
    const tot = leaves.reduce((a, l) => a + Math.max(1, (l.end ?? 0) - (l.start ?? 0)), 0);
    t.pct = tot ? Math.round(leaves.reduce((a, l) => a + Math.max(1, (l.end ?? 0) - (l.start ?? 0)) * (l.pct || 0), 0) / tot) : 0;
    t.closed = leaves.every(l => l.closed);
  };
  roots.forEach(roll);
  return { roots, byId };
}

/* Kritik yol: gerçek tarihlerle geri geçiş (FS). Bolluk ≤ 0 → kritik */
function markCritical(tasks) {
  const leaves = tasks.filter(t => !t.summary && t.start != null);
  const byId = new Map(leaves.map(t => [t.id, t]));
  const succ = new Map(leaves.map(t => [t.id, []]));
  for (const t of leaves) for (const d of t.deps) if (succ.has(d.id)) succ.get(d.id).push(t);
  const projEnd = Math.max(...leaves.map(t => t.end));
  const lf = new Map();
  const order = [...leaves].sort((a, b) => b.end - a.end || b.start - a.start);
  const calc = t => {
    if (lf.has(t.id)) return lf.get(t.id);
    const ss = succ.get(t.id);
    const val = ss.length ? Math.min(...ss.map(s => calc(s) - (s.end - s.start))) : projEnd;
    lf.set(t.id, val);
    return val;
  };
  order.forEach(calc);
  for (const t of leaves) t.critical = (lf.get(t.id) - t.end) <= 0;
  for (const t of tasks) if (t.summary) t.critical = false;
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

function toast(msg, kind, ms) {
  let box = document.getElementById("toasts");
  if (!box) { box = el("div", { id: "toasts", role: "status", "aria-live": "polite" }); document.body.append(box); }
  const t = el("div", { class: "toast " + (kind || "") , text: msg });
  box.append(t);
  setTimeout(() => t.remove(), ms || 3800);
}

function stateLoading(node, text) {
  clear(node).append(el("div", { class: "state" }, el("div", { class: "spinner" }), el("p", { text: text || "Yükleniyor…" })));
}
function stateError(node, err, retry) {
  if (err instanceof SessionGone) return;
  clear(node).append(el("div", { class: "state" },
    el("h2", { text: "Veriler yüklenemedi" }),
    el("p", { text: err?.message || String(err) }),
    retry ? el("button", { class: "btn primary", onclick: retry, text: "Tekrar dene" }) : null));
}
function stateEmpty(node, title, text, action) {
  clear(node).append(el("div", { class: "state" },
    el("div", { style: "font-size:34px", text: "🧪" }), el("h2", { text: title }), el("p", { text }), action || null));
}

const ICON_FLASK = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M12 3h8M13.5 3v8.2L6.2 24.6A3 3 0 0 0 8.8 29h14.4a3 3 0 0 0 2.6-4.4L18.5 11.2V3" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M9.3 21h13.4l2.2 4a1.4 1.4 0 0 1-1.2 2H8.3a1.4 1.4 0 0 1-1.2-2z" fill="#7fe0e6"/><circle cx="14" cy="24" r="1.3" fill="#0c5a6b"/><circle cx="18.5" cy="22.6" r=".9" fill="#0c5a6b"/></svg>';

/* Üst bar — her sayfa kendi oturum kontrolünü yapar */
async function initShell(active) {
  const header = document.querySelector(".topbar");
  const brand = el("div", { class: "brand" });
  const svgIcon = new DOMParser().parseFromString(ICON_FLASK.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" '), "image/svg+xml").documentElement;
  brand.append(document.importNode(svgIcon, true), el("div", null, "Ar-Ge Proje Merkezi", el("small", { text: "İlaç Ar-Ge planlama & takip" })));
  const links = [["index.html", "Portföy", "portfoy"], ["gorevlerim.html", "Görevlerim", "gorev"], ["kutuphane.html", "Görev Kütüphanesi", "kutuphane"]];
  const nav = el("nav", { class: "nav", "aria-label": "Ana menü" });
  for (const [href, text, key] of links) {
    const a = el("a", { href, text, "aria-current": key === active ? "page" : null });
    if (key === "gorev") a.id = "nav-gorev";
    nav.append(a);
  }
  const who = el("div", { class: "whoami" });
  header.append(brand, nav, who);
  if (!workiomHeaders()) { redirectToLogin(); throw new SessionGone("oturum yok"); }
  try {
    const me = await currentUser();
    who.textContent = "👤 " + userName({ name: me.name, surname: me.surname, emailAddress: me.emailAddress });
    return me;
  } catch (e) {
    if (!(e instanceof SessionGone)) who.textContent = "";
    throw e;
  }
}

/* CSV (Excel uyumlu, UTF-8 BOM, noktalı virgül) */
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

/* Sınırlı eşzamanlılıkla toplu güncelleme */
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
