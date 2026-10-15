"use strict";
/* Kırpart · Tedarik Zinciri Kokpiti
 * Workiom "Kırpart Tedarikçi Portalı" uygulamasının Sipariş, Sevkiyat, Aksiyon ve Kalite Vakaları
 * listeleri üzerinde çalışır. Alan kimlikleri Workiom'dan canlı keşfedilen şemadan alınmıştır.
 */

/* ════════════════════════ Şema (canlı keşiften) ════════════════════════ */
const L = {
  SIP: "e9e010d1-4f4e-4f93-bec5-8fd0ef009383",   // Siparişler
  KAL: "39c4cf16-4793-4e5b-8298-1b0ca8bad69a",   // Sipariş Kalemleri
  SEV: "7c7786f8-3ab4-40f6-8ee7-84391c997dc8",   // Sevkiyatlar
  SVK: "3b8f3100-04f9-41ac-856e-12eaafaf107a",   // Sevkiyat Kalemleri
  AKS: "47e7149c-b50f-4b17-864e-1acfc7cd7240",   // Aksiyonlar
  VAK: "23a6c8c6-89d0-4653-b7e2-ee09f13bba2a",   // Kalite Vakaları
  TED: "06cc0663-ebce-40d8-a9f3-3b6faa3de8a4",   // Tedarikçiler
  MAL: "a3e0c345-ced5-4080-9b44-5efa7d25fb57"    // Malzemeler
};

const F = {
  SIP: { no: 6021944, yayin: 6022162, tarih: 6022163, durum: 6022164, not: 6022165, ted: 6022166,
         kalemSayisi: 6022543, teyitBekleyen: 6022544, toplamBakiye: 6022545 },
  KAL: { kod: 6021951, siparis: 6022181, ted: 6022182, malzeme: 6022183, malzemeAdi: 6022448, siparisNo: 6022446,
         satir: 6022167, istenen: 6022168, miktar: 6022169, sonIrs: 6022170, sonTeslim: 6022171,
         teyit: 6022172, teyitMiktar: 6022173, teyitTarih: 6022174, kapasite: 6022175, ihtiyac: 6022176,
         redGerekce: 6022177, redAciklama: 6022178, teslimAlinan: 6022536, yoldaki: 6022539, bakiye: 6022538 },
  SEV: { irsaliye: 6021958, asn: 6022184, durum: 6022185, plan: 6022186, gercek: 6022187, varis: 6022188,
         teslim: 6022189, tasiyici: 6022190, plaka: 6022191, etiket: 6022194, ambalaj: 6022195, kabulNotu: 6022196,
         ted: 6022197, toplamKutu: 6022549, gecikme: 6022595, zamaninda: 6022596 },
  SVK: { lot: 6021965, sevk: 6022199, kabul: 6022200, kutu: 6022201, sevkiyat: 6022202, kalem: 6022203,
         ted: 6022204, kalemKodu: 6022458 },
  AKS: { baslik: 6022056, no: 6022357, kaynak: 6022358, tanim: 6022359, tip: 6022360, taraf: 6022361,
         acilis: 6022363, termin: 6022364, durum: 6022365, tamamlanma: 6022367, kapanis: 6022368, acik: 6022370,
         vaka: 6022371, ted: 6022375, kalanGun: 6022516, gecikme: 6022517 },
  VAK: { baslik: 6021986, no: 6022223, kaynak: 6022224, lot: 6022226, tespit: 6022227, kontrol: 6022228,
         hatali: 6022229, kategori: 6022230, tanim: 6022231, iade: 6022233, d8Gerekli: 6022235, d8Durum: 6022236,
         d8Termin: 6022237, revNot: 6022248, maliyetDurum: 6022259, toplamMaliyet: 6022512, ted: 6022261,
         malzeme: 6022262, acikAks: 6022574,
         d: [6022238, 6022239, 6022240, 6022241, 6022242, 6022243, 6022244, 6022245] },
  TED: { adi: 6021916, kisa: 6022099, durum: 6022100 },
  MAL: { kod: 6021930, adi: 6022141, tip: 6022143, aktif: 6022149 }
};

const OPT = {
  sipDurum: ["Açık", "Teyit Bekliyor", "Kısmi Teyit", "Teyit Edildi", "Kapandı", "İptal"],
  teyit: ["Bekliyor", "Onaylandı", "Kısmi Onay", "Reddedildi"],
  kapasite: ["Evet", "Hayır"],
  redGerekce: ["Kapasite Yetersiz", "Hammadde Yok", "Termin Uygun Değil", "Fiyat", "Diğer"],
  sevDurum: ["Planlandı", "Yolda", "Teslim Alındı", "Kısmi Kabul", "İptal"],
  aksKaynak: ["8D", "Denetim", "Sapma", "Ziyaret-Toplantı", "Diğer"],
  aksTip: ["Düzeltici", "Önleyici", "İyileştirme"],
  aksTaraf: ["Tedarikçi", "Kırpart"],
  aksDurum: ["Açık", "Devam Ediyor", "Doğrulama Bekliyor", "Kapandı", "İptal"],
  vakaKaynak: ["Hat İadesi (ERP)", "GKK Parti Reddi (ERP)", "Müşteri Şikayeti (PLM)", "Lojistik Uygunsuzluk", "Manuel"],
  vakaKategori: ["Boyutsal", "Görsel", "Malzeme", "Fonksiyonel", "Ambalaj-Etiket", "Karışık Parça"],
  iade: ["İade Yok", "İade Edilecek", "Sevk Edildi", "Tedarikçi Teslim Aldı"],
  d8Durum: ["Taslak", "Kırpart Onayında", "Tedarikçiye Gönderildi", "Tedarikçi Sundu", "Revizyon İstendi", "Onaylandı", "Kapandı"],
  maliyet: ["Maliyet Yok", "Taslak", "Tedarikçi Onayında", "İtiraz", "Onaylandı", "Faturalandı"]
};
const D_NAMES = ["D1 Ekip", "D2 Problem Tanımı", "D3 Geçici Önlem", "D4 Kök Neden", "D5 Kalıcı Önlem",
                 "D6 Uygulama ve Doğrulama", "D7 Tekrarı Önleme", "D8 Kapanış"];

/* ════════════════════════ Oturum & API (platform kalıbı) ════════════════════════ */
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

  const msg = document.getElementById("loggedout-msg");
  if (msg) msg.textContent = isDirty()
    ? "Oturumunuzun süresi doldu — kaydedilmemiş değişiklikleriniz kaybolacak. Giriş sayfasına yönlendiriliyorsunuz…"
    : "Oturumunuzun süresi doldu — giriş sayfasına yönlendiriliyorsunuz…";
  document.getElementById("loggedout").hidden = false;

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

class SessionExpired extends Error {}

async function api(method, path, payload) {
  const headers = workiomHeaders();
  if (!headers) { redirectToLogin(); throw new SessionExpired(); }
  const base = (await apiBase()).replace(/\/$/, "");
  const res = await fetch(base + path, {
    method, headers, body: payload === undefined ? undefined : JSON.stringify(payload)
  });
  const json = await res.json().catch(() => null);

  if (res.status === 401 || json?.unAuthorizedRequest) {
    redirectToLogin();                     // session expired — see the auth rules
    throw new SessionExpired();
  }

  if (!res.ok || !json || json.success === false) {
    throw new Error(json?.error?.message || ("İstek başarısız (" + res.status + ")"));
  }
  return json.result;
}

async function readAll(listId) {
  const out = [];
  for (let skip = 0; skip < 5000; skip += 200) {
    const r = await api("POST", "/api/services/app/Data/All", { listId, maxResultCount: 200, skipCount: skip });
    const items = r?.items || [];
    out.push(...items);
    if (items.length < 200 || out.length >= (r?.totalCount ?? 0)) break;
  }
  return out;
}
const createRec = (listId, data) => api("POST", "/api/services/app/Data/Create?listId=" + encodeURIComponent(listId), data);
const updateRec = (listId, id, data) =>
  api("PUT", "/api/services/app/Data/UpdatePartial?listId=" + encodeURIComponent(listId) + "&id=" + encodeURIComponent(id), data);

/* ════════════════════════ Yardımcılar ════════════════════════ */
const $ = sel => document.querySelector(sel);

function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  if (attrs) for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k === "style") el.setAttribute("style", v);
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, String(v));
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    el.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
  }
  return el;
}

const svgNS = "http://www.w3.org/2000/svg";
function icon(d) {
  const s = document.createElementNS(svgNS, "svg");
  s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("aria-hidden", "true");
  const p = document.createElementNS(svgNS, "path");
  p.setAttribute("d", d); p.setAttribute("fill", "none"); p.setAttribute("stroke", "currentColor");
  p.setAttribute("stroke-width", "2"); p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-linejoin", "round");
  s.appendChild(p);
  return s;
}
const ICO = {
  cal: "M7 3v3M17 3v3M4 8h16M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z",
  truck: "M3 7h11v9H3zM14 10h4l3 3v3h-7",
  box: "M4 7l8-4 8 4v10l-8 4-8-4zM4 7l8 4 8-4M12 11v10",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0",
  alert: "M12 9v4M12 17h.01M10.3 3.9 2 18a2 2 0 0 0 1.7 3h16.6A2 2 0 0 0 22 18L13.7 3.9a2 2 0 0 0-3.4 0z",
  clock: "M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z",
  check: "M5 12l5 5L20 7",
  order: "M7 4h10l3 4v12H4V8l3-4zM4 8h16M9 12h6",
  tool: "M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-2.4z"
};

const v = (rec, fid) => rec ? rec[String(fid)] : undefined;
function lbl(x) {
  if (x == null) return "";
  if (Array.isArray(x)) return x.map(lbl).filter(Boolean).join(", ");
  if (typeof x === "object") return x.label ?? x.fullname ?? x.name ?? "";
  return String(x);
}
const linkId = x => (Array.isArray(x) && x.length ? (x[0]?._id ?? (typeof x[0] === "string" ? x[0] : null)) : null);
const num = x => (x == null || x === "" || isNaN(Number(x)) ? null : Number(x));
const fmtN = x => (num(x) == null ? "—" : new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2 }).format(num(x)));
const fmtMoney = x => (num(x) == null ? "—" : new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 }).format(num(x)));

function toDate(x) {
  if (!x) return null;
  const d = new Date(x);
  return isNaN(d) ? null : d;
}
function fmtD(x) {
  const d = toDate(x);
  return d ? d.toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" }) : "—";
}
function isoLocal(d) {
  const p = n => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
}
const todayIso = () => isoLocal(new Date());
function inputDate(x) { const d = toDate(x); return d ? isoLocal(d) : ""; }
function daysFromToday(x) {
  const d = toDate(x);
  if (!d) return null;
  const a = new Date(); a.setHours(0, 0, 0, 0);
  const b = new Date(d); b.setHours(0, 0, 0, 0);
  return Math.round((b - a) / 86400000);
}
function norm(s) { return String(s || "").toLocaleLowerCase("tr-TR"); }

function isEmptyValue(v) {
  return v == null
    || (typeof v === "string" && v.trim() === "")
    || (Array.isArray(v) && v.length === 0);
}

const TONE = {
  "Bekliyor": "warn", "Onaylandı": "ok", "Kısmi Onay": "info", "Reddedildi": "bad",
  "Planlandı": "navy", "Yolda": "turq", "Teslim Alındı": "ok", "Kısmi Kabul": "warn", "İptal": "",
  "Açık": "info", "Devam Ediyor": "warn", "Doğrulama Bekliyor": "turq", "Kapandı": "ok",
  "Taslak": "", "Kırpart Onayında": "navy", "Tedarikçiye Gönderildi": "turq", "Tedarikçi Sundu": "info",
  "Revizyon İstendi": "warn",
  "Teyit Bekliyor": "warn", "Kısmi Teyit": "info", "Teyit Edildi": "ok",
  "Maliyet Yok": "", "Tedarikçi Onayında": "warn", "İtiraz": "bad", "Faturalandı": "ok"
};
function badge(text, tone) {
  if (!text) return h("span", { class: "cell-sub", text: "—" });
  return h("span", { class: "badge " + (tone ?? TONE[text] ?? "") , text });
}

/* ════════════════════════ Durum ════════════════════════ */
const S = {
  data: { SIP: [], KAL: [], SEV: [], SVK: [], AKS: [], VAK: [], TED: [], MAL: [] },
  tab: "siparis",
  filter: { siparis: "acik", sevkiyat: "aktif", aksiyon: "acik", vaka: "acik" },
  search: { siparis: "", sevkiyat: "", aksiyon: "" },
  loading: true,
  dirty: false
};
function isDirty() { return S.dirty; }

/* ════════════════════════ Yükleme ════════════════════════ */
let loadSeq = 0;
async function loadAll({ quiet = false } = {}) {
  const seq = ++loadSeq;
  if (!quiet) { S.loading = true; renderAll(); }
  $("#sync-label").textContent = "Güncelleniyor…";
  try {
    const keys = Object.keys(L);
    const results = await Promise.all(keys.map(k => readAll(L[k])));
    if (seq !== loadSeq) return;
    keys.forEach((k, i) => { S.data[k] = results[i]; });
    S.loading = false;
    $("#global-error").hidden = true;
    $("#sync-label").textContent = "Son güncelleme " + new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
    renderAll();
  } catch (e) {
    if (e instanceof SessionExpired) return;
    S.loading = false;
    const box = $("#global-error");
    box.textContent = "";
    box.append("Veriler yüklenemedi: " + e.message + " ", h("button", { class: "btn btn-outline btn-sm", type: "button", onclick: () => loadAll() }, "Tekrar dene"));
    box.hidden = false;
    $("#sync-label").textContent = "";
    renderAll();
  }
}

/* Kayıttan sonra: hemen ve otomasyonlar çalıştıktan sonra tekrar yükle */
function reloadAfterWrite() {
  loadAll({ quiet: true });
  setTimeout(() => loadAll({ quiet: true }), 4500);
}

/* ════════════════════════ Türetilmiş veriler ════════════════════════ */
const byId = (arr) => Object.fromEntries(arr.map(r => [r._id, r]));

function kalemRows() {
  return S.data.KAL.map(r => {
    const teyit = lbl(v(r, F.KAL.teyit));
    const kapasite = lbl(v(r, F.KAL.kapasite));
    return {
      r, id: r._id,
      kod: lbl(v(r, F.KAL.kod)) || "—",
      siparis: lbl(v(r, F.KAL.siparis)) || lbl(v(r, F.KAL.siparisNo)),
      ted: lbl(v(r, F.KAL.ted)),
      malzeme: lbl(v(r, F.KAL.malzeme)),
      malzemeAdi: lbl(v(r, F.KAL.malzemeAdi)),
      istenen: v(r, F.KAL.istenen),
      miktar: num(v(r, F.KAL.miktar)),
      teyit, kapasite,
      teyitMiktar: num(v(r, F.KAL.teyitMiktar)),
      yoldaki: num(v(r, F.KAL.yoldaki)),
      bakiye: num(v(r, F.KAL.bakiye)),
      sonIrs: lbl(v(r, F.KAL.sonIrs))
    };
  });
}

function sevkiyatRows() {
  const kalemler = {};
  for (const k of S.data.SVK) {
    const sid = linkId(v(k, F.SVK.sevkiyat));
    if (!sid) continue;
    (kalemler[sid] = kalemler[sid] || []).push(k);
  }
  return S.data.SEV.map(r => ({
    r, id: r._id,
    irsaliye: lbl(v(r, F.SEV.irsaliye)),
    asn: v(r, F.SEV.asn),
    durum: lbl(v(r, F.SEV.durum)) || "Planlandı",
    ted: lbl(v(r, F.SEV.ted)),
    plan: v(r, F.SEV.plan), varis: v(r, F.SEV.varis), teslim: v(r, F.SEV.teslim),
    tasiyici: lbl(v(r, F.SEV.tasiyici)), plaka: lbl(v(r, F.SEV.plaka)),
    toplamKutu: num(v(r, F.SEV.toplamKutu)), gecikme: num(v(r, F.SEV.gecikme)),
    kalemler: kalemler[r._id] || []
  }));
}

function aksiyonRows() {
  return S.data.AKS.map(r => ({
    r, id: r._id,
    no: v(r, F.AKS.no),
    baslik: lbl(v(r, F.AKS.baslik)),
    durum: lbl(v(r, F.AKS.durum)) || "Açık",
    kaynak: lbl(v(r, F.AKS.kaynak)),
    ted: lbl(v(r, F.AKS.ted)),
    termin: v(r, F.AKS.termin),
    taraf: lbl(v(r, F.AKS.taraf)),
    tanim: lbl(v(r, F.AKS.tanim)),
    vaka: lbl(v(r, F.AKS.vaka))
  }));
}

function vakaRows() {
  return S.data.VAK.map(r => ({
    r, id: r._id,
    no: v(r, F.VAK.no),
    baslik: lbl(v(r, F.VAK.baslik)),
    ted: lbl(v(r, F.VAK.ted)),
    malzeme: lbl(v(r, F.VAK.malzeme)),
    kaynak: lbl(v(r, F.VAK.kaynak)),
    d8: !!v(r, F.VAK.d8Gerekli),
    d8Durum: lbl(v(r, F.VAK.d8Durum)),
    d8Termin: v(r, F.VAK.d8Termin),
    hatali: num(v(r, F.VAK.hatali)),
    maliyet: num(v(r, F.VAK.toplamMaliyet)),
    maliyetDurum: lbl(v(r, F.VAK.maliyetDurum)),
    acikAks: num(v(r, F.VAK.acikAks)),
    tespit: v(r, F.VAK.tespit)
  }));
}

const isOpenAks = a => a.durum !== "Kapandı" && a.durum !== "İptal";
const isOpen8D = x => x.d8 && x.d8Durum !== "Kapandı";
const isActiveSev = s => s.durum === "Planlandı" || s.durum === "Yolda";

/* ════════════════════════ KPI ════════════════════════ */
function renderKpis() {
  const box = $("#kpis");
  box.textContent = "";
  if (S.loading) {
    for (let i = 0; i < 6; i++) box.append(h("div", { class: "kpi skeleton" }, h("div", { class: "kpi-label", text: " " }), h("div", { class: "kpi-value", text: "00" })));
    return;
  }
  const K = kalemRows(), SV = sevkiyatRows(), A = aksiyonRows(), V = vakaRows();
  const teyitBek = K.filter(k => k.teyit === "Bekliyor").length;
  const kapasite = K.filter(k => k.kapasite === "Hayır" || k.teyit === "Reddedildi" || k.teyit === "Kısmi Onay").length;
  const yolda = SV.filter(s => s.durum === "Yolda");
  const hafta = SV.filter(s => isActiveSev(s) && (daysFromToday(s.varis || s.plan) ?? 99) <= 7);
  const gecVaris = hafta.filter(s => (daysFromToday(s.varis || s.plan) ?? 0) < 0).length;
  const acikA = A.filter(isOpenAks);
  const gecA = acikA.filter(a => (daysFromToday(a.termin) ?? 1) < 0).length;
  const acik8D = V.filter(isOpen8D);
  const bakiyeAcik = K.filter(k => (k.bakiye ?? 0) > 0 && k.teyit !== "Reddedildi").reduce((s, k) => s + (k.bakiye || 0), 0);

  const tiles = [
    { label: "Teyit Bekleyen Kalem", ico: ICO.clock, val: teyitBek, sub: fmtN(bakiyeAcik) + " adet açık bakiye", accent: "var(--warn)",
      go: () => goto("siparis", "teyit") },
    { label: "Kapasite / Red Uyarısı", ico: ICO.alert, val: kapasite, sub: "kısmi onay, red veya kapasite yetersiz", accent: "var(--bad)",
      go: () => goto("siparis", "sorun") },
    { label: "Yoldaki Sevkiyat", ico: ICO.truck, val: yolda.length, sub: fmtN(yolda.reduce((s, x) => s + x.kalemler.reduce((t, k) => t + (num(v(k, F.SVK.sevk)) || 0), 0), 0)) + " adet yolda", accent: "var(--turq)",
      go: () => goto("sevkiyat", "aktif") },
    { label: "7 Gün İçinde Beklenen", ico: ICO.cal, val: hafta.length, sub: gecVaris ? gecVaris + " sevkiyat gecikmiş" : "gecikme yok", subBad: gecVaris > 0, accent: "var(--navy)",
      go: () => goto("sevkiyat", "aktif") },
    { label: "Açık Aksiyon", ico: ICO.check, val: acikA.length, sub: gecA ? gecA + " aksiyon gecikmiş" : "geciken yok", subBad: gecA > 0, accent: "var(--info)",
      go: () => goto("aksiyon", gecA ? "geciken" : "acik") },
    { label: "Açık 8D", ico: ICO.tool, val: acik8D.length, sub: acik8D.filter(x => x.d8Durum === "Revizyon İstendi").length + " revizyonda", accent: "#7a5af8",
      go: () => { S.filter.vaka = "acik"; goto("aksiyon", S.filter.aksiyon); } }
  ];
  for (const t of tiles) {
    box.append(h("button", { class: "kpi", type: "button", style: "--accent:" + t.accent, onclick: t.go },
      h("div", { class: "kpi-label" }, icon(t.ico), t.label),
      h("div", { class: "kpi-value", text: String(t.val) }),
      h("div", { class: "kpi-sub" + (t.subBad ? " bad" : ""), text: t.sub })));
  }
}

function goto(tab, filter) {
  if (filter) S.filter[tab] = filter;
  switchTab(tab);
}

/* ════════════════════════ Sekmeler ════════════════════════ */
function switchTab(tab) {
  S.tab = tab;
  for (const b of document.querySelectorAll(".tab")) {
    const on = b.dataset.tab === tab;
    b.classList.toggle("is-active", on);
    b.setAttribute("aria-selected", on ? "true" : "false");
  }
  for (const t of ["siparis", "sevkiyat", "aksiyon"]) $("#panel-" + t).hidden = t !== tab;
  renderAll();
}

function renderChips(container, items, current, onPick) {
  const box = $(container);
  box.textContent = "";
  for (const it of items) {
    box.append(h("button", { class: "chip" + (it.key === current ? " is-active" : ""), type: "button", onclick: () => onPick(it.key) },
      it.label, h("span", { class: "n", text: String(it.n) })));
  }
}

function renderAll() {
  renderKpis();
  renderSiparis();
  renderSevkiyat();
  renderAksiyon();
  renderVaka();
  if (!S.loading) {
    $("#tc-siparis").textContent = String(kalemRows().filter(k => k.teyit === "Bekliyor").length);
    $("#tc-sevkiyat").textContent = String(sevkiyatRows().filter(isActiveSev).length);
    $("#tc-aksiyon").textContent = String(aksiyonRows().filter(isOpenAks).length);
  }
}

/* ════════════════════════ SİPARİŞLER ════════════════════════ */
const SIP_FILTERS = [
  { key: "acik", label: "Açık bakiye", test: k => (k.bakiye ?? 0) > 0 && k.teyit !== "Reddedildi" },
  { key: "teyit", label: "Teyit bekliyor", test: k => k.teyit === "Bekliyor" },
  { key: "sorun", label: "Kapasite / red", test: k => k.kapasite === "Hayır" || k.teyit === "Reddedildi" || k.teyit === "Kısmi Onay" },
  { key: "yolda", label: "Yolda", test: k => (k.yoldaki ?? 0) > 0 },
  { key: "gelecek", label: "Bugünden sonra", test: k => (daysFromToday(k.istenen) ?? -1) >= 0 },
  { key: "tum", label: "Tümü", test: () => true }
];

function renderSiparis() {
  const tbody = $("#table-siparis tbody");
  const state = $("#state-siparis");
  tbody.textContent = "";
  state.textContent = "";
  if (S.loading) { state.append(h("div", { class: "loader" })); return; }

  const all = kalemRows();
  renderChips("#chips-siparis", SIP_FILTERS.map(f => ({ key: f.key, label: f.label, n: all.filter(f.test).length })),
    S.filter.siparis, k => { S.filter.siparis = k; renderSiparis(); });

  const f = SIP_FILTERS.find(x => x.key === S.filter.siparis) || SIP_FILTERS[0];
  const q = norm(S.search.siparis);
  const rows = all.filter(f.test)
    .filter(k => !q || norm([k.kod, k.siparis, k.ted, k.malzeme, k.malzemeAdi, k.sonIrs].join(" ")).includes(q))
    .sort((a, b) => (toDate(a.istenen)?.getTime() ?? 9e15) - (toDate(b.istenen)?.getTime() ?? 9e15));

  if (!rows.length) {
    state.append(h("div", { class: "big", text: "Bu filtrede kalem yok" }), h("div", { text: "Filtreyi değiştirin ya da yeni sipariş ekleyin." }));
    return;
  }
  for (const k of rows) {
    const dd = daysFromToday(k.istenen);
    const late = dd != null && dd < 0 && (k.bakiye ?? 0) > 0;
    const soon = dd != null && dd >= 0 && dd <= 3 && (k.bakiye ?? 0) > 0;
    tbody.append(h("tr", { onclick: () => openKalem(k.id), tabindex: "0", onkeydown: e => { if (e.key === "Enter") openKalem(k.id); } },
      h("td", null, h("div", { class: "cell-main", text: k.kod }), h("div", { class: "cell-sub", text: k.siparis ? "Sipariş " + k.siparis : "Siparişe bağlı değil" })),
      h("td", { text: k.ted || "—" }),
      h("td", null, h("div", { text: k.malzeme || "—" }), h("div", { class: "cell-sub", text: k.malzemeAdi })),
      h("td", { class: late ? "date-late" : soon ? "date-soon" : "" }, fmtD(k.istenen), late ? " · " + (-dd) + " gün geçti" : soon ? " · " + dd + " gün" : ""),
      h("td", { class: "num", text: fmtN(k.miktar) }),
      h("td", null, badge(k.teyit), k.kapasite === "Hayır" ? h("div", { class: "cell-sub", style: "color:var(--bad);margin-top:3px", text: "Kapasite yetersiz" }) : null),
      h("td", { class: "num", text: fmtN(k.teyitMiktar) }),
      h("td", { class: "num", text: k.yoldaki ? fmtN(k.yoldaki) : "—" }),
      h("td", { class: "num" }, h("b", { text: fmtN(k.bakiye) })),
      h("td", { text: k.sonIrs || "—" })));
  }
}

function openKalem(id) {
  const r = S.data.KAL.find(x => x._id === id);
  if (!r) return;
  const k = kalemRows().find(x => x.id === id);
  const svk = S.data.SVK.filter(s => linkId(v(s, F.SVK.kalem)) === id);
  const body = h("div", null,
    h("div", { class: "facts" },
      fact("Sipariş", k.siparis || "—"), fact("Tedarikçi", k.ted || "—"),
      fact("Malzeme", (k.malzeme || "—") + (k.malzemeAdi ? " · " + k.malzemeAdi : "")),
      fact("Teslim Alınan / Bakiye", fmtN(num(v(r, F.KAL.teslimAlinan))) + " / " + fmtN(k.bakiye)),
      fact("Yoldaki", fmtN(k.yoldaki)), fact("Son İrsaliye", (k.sonIrs || "—") + (v(r, F.KAL.sonTeslim) ? " · " + fmtD(v(r, F.KAL.sonTeslim)) : ""))),
    h("div", { class: "group-title", text: "Sipariş bilgisi" }));
  const form = buildForm(r, [
    { id: F.KAL.satir, label: "Satır No", type: "number" },
    { id: F.KAL.miktar, label: "Sipariş Miktarı", type: "number" },
    { id: F.KAL.istenen, label: "İstenen Teslim Tarihi", type: "date" }
  ]);
  body.append(form.el, h("div", { class: "group-title", text: "Tedarikçi teyidi & kapasite" }));
  const form2 = buildForm(r, [
    { id: F.KAL.teyit, label: "Teyit Durumu", type: "select", options: OPT.teyit },
    { id: F.KAL.kapasite, label: "Mevcut Kapasite Yeterli mi?", type: "select", options: OPT.kapasite },
    { id: F.KAL.teyitMiktar, label: "Teyit Edilen Miktar", type: "number" },
    { id: F.KAL.teyitTarih, label: "Teyit Edilen Tarih", type: "date" },
    { id: F.KAL.ihtiyac, label: "Neye İhtiyacın Var?", type: "textarea", full: true },
    { id: F.KAL.redGerekce, label: "Red Gerekçesi", type: "select", options: OPT.redGerekce },
    { id: F.KAL.redAciklama, label: "Red Açıklaması", type: "textarea", full: true }
  ]);
  body.append(form2.el);
  if (svk.length) {
    body.append(h("div", { class: "group-title", text: "İrsaliye bazlı tarihçe" }),
      h("div", { class: "mini-lines" }, svk.map(s => h("div", { class: "mini-line" },
        h("span", { text: lbl(v(s, F.SVK.lot)) + " · " + (lbl(v(s, F.SVK.sevkiyat)) || "—") }),
        h("span", null, "Sevk ", h("b", { text: fmtN(v(s, F.SVK.sevk)) }), " · Kabul ", h("b", { text: fmtN(v(s, F.SVK.kabul)) }))))));
  }
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  body.append(err);
  openDrawer("Sipariş Kalemi", k.kod, body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeDrawer }, "Vazgeç"),
    saveBtn(async () => {
      const ch = { ...form.changes(), ...form2.changes() };
      const teyit = form2.value(F.KAL.teyit);
      if (teyit === "Reddedildi" && isEmptyValue(form2.value(F.KAL.redGerekce))) {
        showErr(err, ["Red Gerekçesi"], form2.control(F.KAL.redGerekce)); return false;
      }
      if (!Object.keys(ch).length) { closeDrawer(); return; }
      await updateRec(L.KAL, id, ch);
      toast("Kalem güncellendi" + (ch[F.KAL.teyit] ? " — satınalmaya teyit bildirimi gidiyor" : ""), "ok");
    }, err)
  ]);
}

/* ════════════════════════ SEVKİYATLAR ════════════════════════ */
const SEV_COLS = [
  { key: "Planlandı", c: "var(--navy)" }, { key: "Yolda", c: "var(--turq)" },
  { key: "Teslim Alındı", c: "var(--ok)" }, { key: "Kısmi Kabul", c: "var(--warn)" }, { key: "İptal", c: "var(--muted)" }
];
const SEV_FILTERS = [
  { key: "aktif", label: "Aktif (planlı + yolda)", cols: ["Planlandı", "Yolda"] },
  { key: "son", label: "Son 30 gün teslim", cols: ["Planlandı", "Yolda", "Teslim Alındı", "Kısmi Kabul"] },
  { key: "tum", label: "Tümü", cols: SEV_COLS.map(c => c.key) }
];

function renderSevkiyat() {
  const board = $("#board-sevkiyat");
  board.textContent = "";
  if (S.loading) { board.append(h("div", { class: "state" }, h("div", { class: "loader" }))); return; }
  const all = sevkiyatRows();
  renderChips("#chips-sevkiyat", SEV_FILTERS.map(f => ({ key: f.key, label: f.label, n: all.filter(s => f.cols.includes(s.durum)).length })),
    S.filter.sevkiyat, k => { S.filter.sevkiyat = k; renderSevkiyat(); });
  const f = SEV_FILTERS.find(x => x.key === S.filter.sevkiyat) || SEV_FILTERS[0];
  const q = norm(S.search.sevkiyat);
  const rows = all.filter(s => !q || norm([s.irsaliye, s.ted, s.tasiyici, s.plaka, ...s.kalemler.map(k => lbl(v(k, F.SVK.lot)) + " " + lbl(v(k, F.SVK.kalemKodu)))].join(" ")).includes(q))
    .filter(s => f.key !== "son" || isActiveSev(s) || (daysFromToday(s.teslim) ?? -999) >= -30);

  for (const col of SEV_COLS.filter(c => f.cols.includes(c.key))) {
    const items = rows.filter(s => s.durum === col.key)
      .sort((a, b) => (toDate(a.varis || a.plan)?.getTime() ?? 9e15) - (toDate(b.varis || b.plan)?.getTime() ?? 9e15));
    board.append(h("div", { class: "col", style: "--c:" + col.c },
      h("div", { class: "col-head" }, h("div", { class: "col-title", text: col.key }), h("span", { class: "col-count", text: String(items.length) })),
      items.length ? items.map(sevCard) : h("div", { class: "col-empty", text: "Kayıt yok" })));
  }
}

function sevCard(s) {
  const col = SEV_COLS.find(c => c.key === s.durum);
  const dRef = s.durum === "Planlandı" ? s.plan : s.varis;
  const dd = daysFromToday(dRef);
  const late = isActiveSev(s) && dd != null && dd < 0;
  const adet = s.kalemler.reduce((t, k) => t + (num(v(k, F.SVK.sevk)) || 0), 0);
  const actions = [];
  if (s.durum === "Planlandı") actions.push(h("button", { class: "btn btn-outline btn-sm", type: "button", onclick: e => { e.stopPropagation(); quickYola(s); } }, "Yola çıktı"));
  if (s.durum === "Yolda" || s.durum === "Planlandı") actions.push(h("button", { class: "btn btn-accent btn-sm", type: "button", onclick: e => { e.stopPropagation(); openTeslimAl(s.id); } }, "Teslim al"));
  return h("div", { class: "kcard", style: "--c:" + (col?.c || "var(--line)"), tabindex: "0", onclick: () => openSevkiyat(s.id),
                     onkeydown: e => { if (e.key === "Enter") openSevkiyat(s.id); } },
    h("div", { class: "kcard-top" },
      h("div", null, h("div", { class: "kcard-title", text: s.irsaliye || "—" }), h("div", { class: "kcard-sub", text: s.ted || "Tedarikçi yok" })),
      s.asn != null ? h("span", { class: "badge plain navy", text: "ASN " + s.asn }) : null),
    h("div", { class: "kcard-meta" },
      h("span", { class: late ? "date-late" : "" }, icon(ICO.cal),
        (s.durum === "Planlandı" ? "Sevk " : s.durum === "Yolda" ? "Varış " : "Teslim ") + fmtD(s.durum === "Teslim Alındı" || s.durum === "Kısmi Kabul" ? s.teslim : dRef) + (late ? " · gecikti" : "")),
      h("span", null, icon(ICO.box), fmtN(adet) + " adet · " + s.kalemler.length + " kalem"),
      s.tasiyici ? h("span", null, icon(ICO.truck), s.tasiyici + (s.plaka ? " · " + s.plaka : "")) : null),
    (s.gecikme ?? 0) > 0 ? h("div", { class: "kcard-meta" }, badge(fmtN(s.gecikme) + " gün gecikmeli teslim", "bad")) : null,
    actions.length ? h("div", { class: "kcard-foot" }, h("span", { class: "cell-sub", text: s.durum }), h("div", { style: "display:flex;gap:6px" }, actions)) : null);
}

async function quickYola(s) {
  try {
    const p = { [F.SEV.durum]: "Yolda" };
    if (!v(s.r, F.SEV.gercek)) p[F.SEV.gercek] = todayIso();
    await updateRec(L.SEV, s.id, p);
    toast(s.irsaliye + " yola çıktı — Kırpart lojistiğe bildirim gidiyor", "ok");
    reloadAfterWrite();
  } catch (e) { if (!(e instanceof SessionExpired)) toast("Güncellenemedi: " + e.message, "bad"); }
}

function openSevkiyat(id) {
  const r = S.data.SEV.find(x => x._id === id);
  if (!r) return;
  const s = sevkiyatRows().find(x => x.id === id);
  const body = h("div", null,
    h("div", { class: "facts" },
      fact("Tedarikçi", s.ted || "—"), fact("ASN No", s.asn ?? "—"),
      fact("Toplam kutu", fmtN(s.toplamKutu)), fact("Zamanında", num(v(r, F.SEV.zamaninda)) === 1 ? "Evet" : s.teslim ? "Hayır · " + fmtN(s.gecikme) + " gün" : "—")),
    h("div", { class: "group-title", text: "Kalemler" }),
    s.kalemler.length ? h("div", { class: "mini-lines" }, s.kalemler.map(k => h("div", { class: "mini-line" },
      h("span", { text: lbl(v(k, F.SVK.lot)) + " · " + (lbl(v(k, F.SVK.kalemKodu)) || lbl(v(k, F.SVK.kalem)) || "—") }),
      h("span", null, "Sevk ", h("b", { text: fmtN(v(k, F.SVK.sevk)) }), " · Kabul ", h("b", { text: fmtN(v(k, F.SVK.kabul)) }))))) :
      h("div", { class: "cell-sub", text: "Bu sevkiyatta kalem yok." }),
    h("div", { class: "group-title", text: "Sevkiyat bilgisi" }));
  const form = buildForm(r, [
    { id: F.SEV.irsaliye, label: "İrsaliye No", type: "text", required: true },
    { id: F.SEV.durum, label: "Durum", type: "select", options: OPT.sevDurum, required: true },
    { id: F.SEV.plan, label: "Planlanan Sevk Tarihi", type: "date" },
    { id: F.SEV.gercek, label: "Gerçek Sevk Tarihi", type: "date" },
    { id: F.SEV.varis, label: "Tahmini Varış", type: "date" },
    { id: F.SEV.teslim, label: "Teslim Alma Tarihi", type: "date" },
    { id: F.SEV.tasiyici, label: "Taşıyıcı Firma", type: "text" },
    { id: F.SEV.plaka, label: "Araç Plakası", type: "text" },
    { id: F.SEV.etiket, label: "Etiketleme Uygun", type: "bool" },
    { id: F.SEV.ambalaj, label: "Ambalaj Uygun", type: "bool" },
    { id: F.SEV.kabulNotu, label: "Kabul Notu", type: "textarea", full: true }
  ]);
  body.append(form.el);
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  body.append(err);
  const foot = [h("button", { class: "btn btn-ghost", type: "button", onclick: closeDrawer }, "Vazgeç")];
  if (isActiveSev(s)) foot.push(h("button", { class: "btn btn-accent", type: "button", onclick: () => { closeDrawer(); openTeslimAl(id); } }, "Teslim al…"));
  foot.push(saveBtn(async () => {
    const miss = form.missing();
    if (miss.length) { showErr(err, miss.map(m => m.label), form.control(miss[0].id)); return false; }
    const ch = form.changes();
    if (!Object.keys(ch).length) { closeDrawer(); return; }
    await updateRec(L.SEV, id, ch);
    toast("Sevkiyat güncellendi", "ok");
  }, err));
  openDrawer("Sevkiyat / ASN", s.irsaliye, body, foot);
}

function openTeslimAl(id) {
  const s = sevkiyatRows().find(x => x.id === id);
  if (!s) return;
  const inputs = [];
  const body = h("div", null,
    h("p", { class: "hint", text: "Kabul edilen miktarları girin. Tümü sevk edilen miktara eşitse sevkiyat \"Teslim Alındı\", değilse \"Kısmi Kabul\" olur. Sipariş kalemlerinin bakiyesi ve son irsaliye numarası otomatik güncellenir." }));
  if (!s.kalemler.length) {
    body.append(h("div", { class: "alert alert-info", text: "Bu sevkiyatta kalem yok. Önce sevkiyata kalem ekleyin (Workiom'da ya da Yeni ASN ile)." }));
  } else {
    const lines = h("div", { class: "lines lines-kabul" },
      h("div", { class: "lines-head" }, h("span", { text: "Lot" }), h("span", { text: "Sipariş kalemi" }), h("span", { text: "Sevk edilen" }), h("span", { text: "Kabul edilen" })));
    for (const k of s.kalemler) {
      const sevk = num(v(k, F.SVK.sevk)) || 0;
      const inp = h("input", { type: "number", min: "0", step: "any", value: String(num(v(k, F.SVK.kabul)) ?? sevk), "aria-label": "Kabul edilen miktar " + lbl(v(k, F.SVK.lot)) });
      inputs.push({ k, sevk, inp });
      lines.append(h("div", { class: "line" },
        h("span", { class: "cell-main", text: lbl(v(k, F.SVK.lot)) }),
        h("span", { text: lbl(v(k, F.SVK.kalemKodu)) || lbl(v(k, F.SVK.kalem)) || "—" }),
        h("span", { class: "num", text: fmtN(sevk) }), inp));
    }
    body.append(lines);
  }
  const notu = h("textarea", { id: "kabul-notu", placeholder: "Kabul notu (isteğe bağlı)" });
  const et = h("input", { type: "checkbox", checked: !!v(s.r, F.SEV.etiket) });
  const am = h("input", { type: "checkbox", checked: !!v(s.r, F.SEV.ambalaj) });
  body.append(h("div", { class: "form-grid", style: "margin-top:14px" },
    h("label", { class: "check" }, et, "Etiketleme uygun"), h("label", { class: "check" }, am, "Ambalaj uygun"),
    h("div", { class: "field full" }, h("label", { for: "kabul-notu", text: "Kabul Notu" }), notu)));
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  body.append(err);

  openModal("Teslim al · " + s.irsaliye, body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeModal }, "Vazgeç"),
    saveBtn(async () => {
      for (const x of inputs) {
        const val = num(x.inp.value);
        if (val == null || val < 0) { err.textContent = "Kabul edilen miktar boş veya negatif olamaz."; err.hidden = false; x.inp.setAttribute("aria-invalid", "true"); x.inp.focus(); return false; }
      }
      const tam = inputs.every(x => num(x.inp.value) >= x.sevk);
      const p = { [F.SEV.durum]: tam ? "Teslim Alındı" : "Kısmi Kabul", [F.SEV.teslim]: todayIso(),
                  [F.SEV.etiket]: et.checked, [F.SEV.ambalaj]: am.checked };
      if (notu.value.trim()) p[F.SEV.kabulNotu] = notu.value.trim();
      await updateRec(L.SEV, s.id, p);
      for (const x of inputs) await updateRec(L.SVK, x.k._id, { [F.SVK.kabul]: num(x.inp.value) });
      toast(s.irsaliye + (tam ? " teslim alındı" : " kısmi kabul edildi") + " — bakiyeler güncelleniyor", "ok");
    }, err, "Teslim alındı olarak kaydet", closeModal)
  ]);
}

/* ════════════════════════ AKSİYONLAR ════════════════════════ */
const AKS_COLS = [
  { key: "Açık", c: "var(--info)", next: "Devam Ediyor", nextLabel: "Başla" },
  { key: "Devam Ediyor", c: "var(--warn)", next: "Doğrulama Bekliyor", nextLabel: "Doğrulamaya gönder" },
  { key: "Doğrulama Bekliyor", c: "var(--turq)", next: "Kapandı", nextLabel: "Doğrula & kapat" },
  { key: "Kapandı", c: "var(--ok)" }
];
const AKS_FILTERS = [
  { key: "acik", label: "Açık", test: isOpenAks },
  { key: "geciken", label: "Geciken", test: a => isOpenAks(a) && (daysFromToday(a.termin) ?? 1) < 0 },
  { key: "tedarikci", label: "Tedarikçide", test: a => isOpenAks(a) && a.taraf === "Tedarikçi" },
  { key: "kirpart", label: "Kırpart'ta", test: a => isOpenAks(a) && a.taraf === "Kırpart" },
  { key: "tum", label: "Tümü", test: a => a.durum !== "İptal" }
];

function renderAksiyon() {
  const board = $("#board-aksiyon");
  board.textContent = "";
  if (S.loading) { board.append(h("div", { class: "state" }, h("div", { class: "loader" }))); return; }
  const all = aksiyonRows();
  renderChips("#chips-aksiyon", AKS_FILTERS.map(f => ({ key: f.key, label: f.label, n: all.filter(f.test).length })),
    S.filter.aksiyon, k => { S.filter.aksiyon = k; renderAksiyon(); });
  const f = AKS_FILTERS.find(x => x.key === S.filter.aksiyon) || AKS_FILTERS[0];
  const q = norm(S.search.aksiyon);
  const rows = all.filter(f.test).filter(a => !q || norm([a.baslik, a.ted, a.tanim, a.kaynak, a.vaka].join(" ")).includes(q));
  const cols = f.key === "tum" ? AKS_COLS : AKS_COLS.filter(c => c.key !== "Kapandı");
  for (const col of cols) {
    const items = rows.filter(a => a.durum === col.key)
      .sort((a, b) => (toDate(a.termin)?.getTime() ?? 9e15) - (toDate(b.termin)?.getTime() ?? 9e15));
    board.append(h("div", { class: "col", style: "--c:" + col.c },
      h("div", { class: "col-head" }, h("div", { class: "col-title", text: col.key }), h("span", { class: "col-count", text: String(items.length) })),
      items.length ? items.map(a => aksCard(a, col)) : h("div", { class: "col-empty", text: "Kayıt yok" })));
  }
}

function aksCard(a, col) {
  const dd = daysFromToday(a.termin);
  const open = isOpenAks(a);
  const late = open && dd != null && dd < 0;
  const soon = open && dd != null && dd >= 0 && dd <= 3;
  return h("div", { class: "kcard", style: "--c:" + col.c, tabindex: "0", onclick: () => openAksiyon(a.id),
                     onkeydown: e => { if (e.key === "Enter") openAksiyon(a.id); } },
    h("div", { class: "kcard-top" },
      h("div", null, h("div", { class: "kcard-title", text: a.baslik || "—" }), h("div", { class: "kcard-sub", text: a.ted || "Tedarikçi yok" })),
      a.kaynak ? h("span", { class: "badge plain navy", text: a.kaynak }) : null),
    a.tanim ? h("div", { class: "kcard-sub", style: "margin-top:6px", text: a.tanim.length > 110 ? a.tanim.slice(0, 110) + "…" : a.tanim }) : null,
    h("div", { class: "kcard-meta" },
      h("span", { class: late ? "date-late" : soon ? "date-soon" : "" }, icon(ICO.cal), "Termin " + fmtD(a.termin) +
        (late ? " · " + (-dd) + " gün gecikti" : soon ? " · " + dd + " gün kaldı" : "")),
      a.taraf ? h("span", null, icon(ICO.user), a.taraf) : null),
    col.next ? h("div", { class: "kcard-foot" },
      h("span", { class: "cell-sub", text: a.no != null ? "AKS-" + a.no : "" }),
      h("button", { class: "btn btn-outline btn-sm", type: "button", onclick: e => { e.stopPropagation(); moveAks(a, col.next); } }, col.nextLabel + " →")) : null);
}

async function moveAks(a, next) {
  try {
    await updateRec(L.AKS, a.id, { [F.AKS.durum]: next });
    toast("\"" + a.baslik + "\" → " + next, "ok");
    reloadAfterWrite();
  } catch (e) { if (!(e instanceof SessionExpired)) toast("Güncellenemedi: " + e.message, "bad"); }
}

function openAksiyon(id) {
  const r = S.data.AKS.find(x => x._id === id);
  if (!r) return;
  const a = aksiyonRows().find(x => x.id === id);
  const body = h("div", null,
    h("div", { class: "facts" },
      fact("Tedarikçi", a.ted || "—"), fact("Kaynak", (a.kaynak || "—") + (a.vaka ? " · " + a.vaka : "")),
      fact("Açılış", fmtD(v(r, F.AKS.acilis))), fact("Kapanış", fmtD(v(r, F.AKS.kapanis)))));
  const form = buildForm(r, [
    { id: F.AKS.baslik, label: "Aksiyon Başlığı", type: "text", required: true, full: true },
    { id: F.AKS.durum, label: "Durum", type: "select", options: OPT.aksDurum },
    { id: F.AKS.termin, label: "Termin", type: "date" },
    { id: F.AKS.kaynak, label: "Kaynak Tipi", type: "select", options: OPT.aksKaynak },
    { id: F.AKS.tip, label: "Aksiyon Tipi", type: "select", options: OPT.aksTip },
    { id: F.AKS.taraf, label: "Sorumlu Taraf", type: "select", options: OPT.aksTaraf },
    { id: F.AKS.ted, label: "Tedarikçi", type: "link", source: "TED" },
    { id: F.AKS.tanim, label: "Aksiyon Tanımı", type: "textarea", full: true },
    { id: F.AKS.tamamlanma, label: "Tamamlanma Notu", type: "textarea", full: true }
  ]);
  body.append(form.el);
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  body.append(err);
  openDrawer("Aksiyon" + (a.no != null ? " · AKS-" + a.no : ""), a.baslik, body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeDrawer }, "Vazgeç"),
    saveBtn(async () => {
      const miss = form.missing();
      if (miss.length) { showErr(err, miss.map(m => m.label), form.control(miss[0].id)); return false; }
      const ch = form.changes();
      if (!Object.keys(ch).length) { closeDrawer(); return; }
      await updateRec(L.AKS, id, ch);
      toast("Aksiyon güncellendi", "ok");
    }, err)
  ]);
}

/* ════════════════════════ 8D / KALİTE VAKALARI ════════════════════════ */
const VAKA_FILTERS = [
  { key: "acik", label: "Açık 8D", test: isOpen8D },
  { key: "maliyet", label: "Maliyet onayı", test: x => ["Taslak", "Tedarikçi Onayında", "İtiraz"].includes(x.maliyetDurum) },
  { key: "tum", label: "Tümü", test: () => true }
];

function renderVaka() {
  const box = $("#vaka-list");
  box.textContent = "";
  if (S.loading) { box.append(h("div", { class: "state" }, h("div", { class: "loader" }))); return; }
  const all = vakaRows();
  renderChips("#chips-vaka", VAKA_FILTERS.map(f => ({ key: f.key, label: f.label, n: all.filter(f.test).length })),
    S.filter.vaka, k => { S.filter.vaka = k; renderVaka(); });
  const f = VAKA_FILTERS.find(x => x.key === S.filter.vaka) || VAKA_FILTERS[0];
  const rows = all.filter(f.test).sort((a, b) => (b.no ?? 0) - (a.no ?? 0));
  if (!rows.length) { box.append(h("div", { class: "state" }, h("div", { class: "big", text: "Kayıt yok" }))); return; }
  for (const x of rows) {
    const step = OPT.d8Durum.indexOf(x.d8Durum);
    const dd = daysFromToday(x.d8Termin);
    const late = isOpen8D(x) && dd != null && dd < 0;
    box.append(h("div", { class: "vaka", tabindex: "0", onclick: () => openVaka(x.id), onkeydown: e => { if (e.key === "Enter") openVaka(x.id); } },
      h("div", { class: "vaka-top" },
        h("div", null, h("div", { class: "vaka-title", text: x.baslik }), h("div", { class: "cell-sub", text: (x.no != null ? "KV-" + x.no + " · " : "") + (x.ted || "—") })),
        x.d8 ? badge(x.d8Durum || "Taslak") : badge("8D yok", "")),
      h("div", { class: "kcard-meta" },
        h("span", null, icon(ICO.alert), fmtN(x.hatali) + " hatalı"),
        x.d8 ? h("span", { class: late ? "date-late" : "" }, icon(ICO.cal), "Termin " + fmtD(x.d8Termin)) : null,
        (x.acikAks ?? 0) > 0 ? h("span", null, icon(ICO.check), fmtN(x.acikAks) + " açık aksiyon") : null,
        (x.maliyet ?? 0) > 0 ? h("span", null, "₺ " + fmtMoney(x.maliyet)) : null),
      x.d8 ? h("div", { class: "steps", "aria-label": "8D ilerleme" },
        OPT.d8Durum.map((s, i) => h("i", { class: x.d8Durum === "Revizyon İstendi" && i === 4 ? "rev" : (i <= step && x.d8Durum !== "Revizyon İstendi") || (x.d8Durum === "Revizyon İstendi" && i < 4) ? "on" : "" }))) : null));
  }
}

function openVaka(id) {
  const r = S.data.VAK.find(x => x._id === id);
  if (!r) return;
  const x = vakaRows().find(y => y.id === id);
  const linked = aksiyonRows().filter(a => linkId(v(a.r, F.AKS.vaka)) === id);
  const body = h("div", null,
    h("div", { class: "facts" },
      fact("Tedarikçi", x.ted || "—"), fact("Malzeme", x.malzeme || "—"),
      fact("Kaynak", x.kaynak || "—"), fact("Tespit", fmtD(x.tespit)),
      fact("Hatalı Miktar", fmtN(x.hatali)), fact("Kalitesizlik Maliyeti", fmtMoney(x.maliyet))),
    h("div", { class: "group-title", text: "8D akışı" }));
  const f1 = buildForm(r, [
    { id: F.VAK.baslik, label: "Vaka Başlığı", type: "text", required: true, full: true },
    { id: F.VAK.d8Gerekli, label: "8D Gerekli", type: "bool" },
    { id: F.VAK.d8Durum, label: "8D Durumu", type: "select", options: OPT.d8Durum },
    { id: F.VAK.d8Termin, label: "8D Termin", type: "date" },
    { id: F.VAK.iade, label: "İade Durumu", type: "select", options: OPT.iade },
    { id: F.VAK.revNot, label: "Son Revizyon Notu", type: "textarea", full: true },
    { id: F.VAK.maliyetDurum, label: "Maliyet Onay Durumu", type: "select", options: OPT.maliyet },
    { id: F.VAK.kategori, label: "Hata Kategorisi", type: "select", options: OPT.vakaKategori },
    { id: F.VAK.tanim, label: "Hata Tanımı", type: "textarea", full: true }
  ]);
  body.append(f1.el, h("div", { class: "group-title", text: "D1 – D8" }));
  const f2 = buildForm(r, F.VAK.d.map((fid, i) => ({ id: fid, label: D_NAMES[i], type: "textarea", full: true })));
  body.append(f2.el);
  body.append(h("div", { class: "group-title", text: "Bağlı aksiyonlar" }),
    linked.length ? h("div", { class: "mini-lines" }, linked.map(a => h("div", { class: "mini-line" },
      h("span", { text: a.baslik }), h("span", null, badge(a.durum), " ", fmtD(a.termin))))) : h("div", { class: "cell-sub", text: "Bu vakaya bağlı aksiyon yok." }),
    h("div", { style: "margin-top:10px" }, h("button", { class: "btn btn-outline btn-sm", type: "button", onclick: () => { closeDrawer(); newAksiyon(id); } }, "+ Bu vakaya aksiyon ekle")));
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  body.append(err);
  openDrawer("Kalite Vakası" + (x.no != null ? " · KV-" + x.no : ""), x.baslik, body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeDrawer }, "Vazgeç"),
    saveBtn(async () => {
      const miss = f1.missing();
      if (miss.length) { showErr(err, miss.map(m => m.label), f1.control(miss[0].id)); return false; }
      if (f1.value(F.VAK.d8Durum) === "Revizyon İstendi" && isEmptyValue(f1.value(F.VAK.revNot))) {
        showErr(err, ["Son Revizyon Notu"], f1.control(F.VAK.revNot)); return false;
      }
      const ch = { ...f1.changes(), ...f2.changes() };
      if (!Object.keys(ch).length) { closeDrawer(); return; }
      await updateRec(L.VAK, id, ch);
      toast("Vaka güncellendi" + (ch[F.VAK.d8Durum] ? " — 8D bildirimi gidiyor" : ""), "ok");
    }, err)
  ]);
}

/* ════════════════════════ Yeni kayıt formları ════════════════════════ */
function tedOptions() {
  return S.data.TED
    .map(t => ({ id: t._id, label: lbl(v(t, F.TED.adi)), durum: lbl(v(t, F.TED.durum)) }))
    .filter(t => t.label)
    .sort((a, b) => (a.durum === "Aktif" ? 0 : 1) - (b.durum === "Aktif" ? 0 : 1) || a.label.localeCompare(b.label, "tr"));
}
function malOptions() {
  return S.data.MAL
    .map(m => ({ id: m._id, label: lbl(v(m, F.MAL.kod)) + " · " + lbl(v(m, F.MAL.adi)), aktif: v(m, F.MAL.aktif) !== false }))
    .filter(m => m.aktif)
    .sort((a, b) => a.label.localeCompare(b.label, "tr"));
}
function selectEl(opts, { placeholder = "Seçiniz…", id, value } = {}) {
  const s = h("select", { id });
  s.append(h("option", { value: "", text: placeholder }));
  for (const o of opts) {
    const val = typeof o === "string" ? o : o.id;
    const text = typeof o === "string" ? o : o.label;
    s.append(h("option", { value: val, text, selected: value === val }));
  }
  return s;
}
function fieldEl(label, control, { required, full, hint } = {}) {
  if (required) { control.required = true; control.setAttribute("aria-required", "true"); }
  return h("div", { class: "field" + (full ? " full" : "") },
    h("label", { for: control.id }, label, required ? h("span", { class: "req", "aria-hidden": "true", text: "*" }) : null),
    control, hint ? h("span", { class: "hint", text: hint }) : null);
}
let uid = 0;
const nid = p => p + "-" + (++uid);

function newSiparis() {
  const no = h("input", { type: "text", id: nid("sip-no"), placeholder: "örn. SAS-2026-05001" });
  const yayin = h("input", { type: "text", id: nid("sip-yayin") });
  const tarih = h("input", { type: "date", id: nid("sip-tarih"), value: todayIso() });
  const ted = selectEl(tedOptions(), { id: nid("sip-ted") });
  const durum = selectEl(OPT.sipDurum, { id: nid("sip-durum") });
  const notu = h("textarea", { id: nid("sip-not") });
  const lines = h("div", { class: "lines lines-sip" },
    h("div", { class: "lines-head" }, h("span", { text: "Satır" }), h("span", { text: "Malzeme *" }), h("span", { text: "Miktar *" }), h("span", { text: "İstenen tarih" }), h("span")));
  const rows = [];
  const addLine = () => {
    const satir = h("input", { type: "number", value: String((rows.length + 1) * 10), "aria-label": "Satır No" });
    const mal = selectEl(malOptions(), { placeholder: "Malzeme seçin…" }); mal.setAttribute("aria-label", "Malzeme");
    const mik = h("input", { type: "number", min: "0", step: "any", "aria-label": "Sipariş miktarı" });
    const ist = h("input", { type: "date", "aria-label": "İstenen teslim tarihi" });
    const row = { satir, mal, mik, ist };
    const del = h("button", { class: "icon-btn", type: "button", "aria-label": "Satırı sil", onclick: () => { rows.splice(rows.indexOf(row), 1); lineEl.remove(); } }, "✕");
    const lineEl = h("div", { class: "line" }, satir, mal, mik, ist, del);
    rows.push(row);
    lines.insertBefore(lineEl, addBox);
  };
  const addBox = h("div", { class: "lines-add" }, h("button", { class: "btn btn-outline btn-sm", type: "button", onclick: addLine }, "+ Kalem ekle"));
  lines.append(addBox);
  addLine();
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  const body = h("div", null,
    h("p", { class: "req-note" }, h("span", { class: "req", "aria-hidden": "true", text: "*" }), " Zorunlu"),
    h("div", { class: "form-grid" },
      fieldEl("Sipariş No", no, { required: true }), fieldEl("Yayın No", yayin),
      fieldEl("Tedarikçi", ted, { hint: "Kalemlere de otomatik aktarılır" }), fieldEl("Sipariş Tarihi", tarih),
      fieldEl("Durum", durum), fieldEl("Kırpart Notu", notu, { full: true })),
    h("div", { class: "group-title", text: "Sipariş kalemleri" }), lines, err);
  openModal("Yeni sipariş", body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeModal }, "Vazgeç"),
    saveBtn(async () => {
      clearInvalid(body);
      const missing = [];
      if (isEmptyValue(no.value)) missing.push(["Sipariş No", no]);
      const filled = rows.filter(r => r.mal.value || r.mik.value);
      if (!filled.length) missing.push(["En az bir kalem", rows[0]?.mal]);
      for (const r of filled) {
        if (!r.mal.value) missing.push(["Kalem malzemesi", r.mal]);
        if (num(r.mik.value) == null) missing.push(["Kalem miktarı", r.mik]);
      }
      if (missing.length) { showErr(err, missing.map(m => m[0]), missing[0][1], missing.map(m => m[1])); return false; }
      const p = { [F.SIP.no]: no.value.trim() };
      if (yayin.value.trim()) p[F.SIP.yayin] = yayin.value.trim();
      if (tarih.value) p[F.SIP.tarih] = tarih.value;
      if (ted.value) p[F.SIP.ted] = [ted.value];
      if (durum.value) p[F.SIP.durum] = durum.value;
      if (notu.value.trim()) p[F.SIP.not] = notu.value.trim();
      const sipRes = await createRec(L.SIP, p);
      const sipId = sipRes?._id ?? sipRes?.id;
      if (!sipId) throw new Error("Sipariş oluşturuldu ama kimliği alınamadı.");
      for (const r of filled) {
        const kp = { [F.KAL.siparis]: [sipId], [F.KAL.malzeme]: [r.mal.value], [F.KAL.miktar]: num(r.mik.value) };
        if (ted.value) kp[F.KAL.ted] = [ted.value];
        if (num(r.satir.value) != null) kp[F.KAL.satir] = num(r.satir.value);
        if (r.ist.value) kp[F.KAL.istenen] = r.ist.value;
        await createRec(L.KAL, kp);
      }
      toast("Sipariş " + p[F.SIP.no] + " ve " + filled.length + " kalem oluşturuldu — tedarikçiye teyit bildirimi gidiyor", "ok");
      S.filter.siparis = "teyit";
    }, err, "Siparişi oluştur", closeModal)
  ]);
}

function newSevkiyat() {
  const irs = h("input", { type: "text", id: nid("sev-irs"), placeholder: "örn. ÖZM-2026-120001" });
  const ted = selectEl(tedOptions(), { id: nid("sev-ted") });
  const durum = selectEl(OPT.sevDurum, { id: nid("sev-durum"), value: "Planlandı" });
  const plan = h("input", { type: "date", id: nid("sev-plan"), value: todayIso() });
  const varis = h("input", { type: "date", id: nid("sev-varis") });
  const tas = h("input", { type: "text", id: nid("sev-tas") });
  const plk = h("input", { type: "text", id: nid("sev-plk") });
  const lines = h("div", { class: "lines lines-asn" },
    h("div", { class: "lines-head" }, h("span", { text: "Lot No *" }), h("span", { text: "Sipariş kalemi *" }), h("span", { text: "Sevk miktarı *" }), h("span", { text: "Kutu" }), h("span")));
  const rows = [];
  const kalemOpts = () => {
    const tedLabel = ted.value ? lbl(v(S.data.TED.find(t => t._id === ted.value), F.TED.adi)) : null;
    return kalemRows()
      .filter(k => (k.bakiye ?? 0) > 0 && k.teyit !== "Reddedildi" && (!tedLabel || k.ted === tedLabel))
      .map(k => ({ id: k.id, label: k.kod + " · " + (k.malzeme || "") + " · bakiye " + fmtN(k.bakiye), bakiye: k.bakiye }));
  };
  const addLine = () => {
    const lot = h("input", { type: "text", "aria-label": "Lot No" });
    const kal = selectEl(kalemOpts(), { placeholder: "Kalem seçin…" }); kal.setAttribute("aria-label", "Sipariş kalemi");
    const mik = h("input", { type: "number", min: "0", step: "any", "aria-label": "Sevk edilen miktar" });
    const kutu = h("input", { type: "number", min: "0", step: "1", "aria-label": "Kutu adedi" });
    kal.addEventListener("change", () => {
      const o = kalemOpts().find(x => x.id === kal.value);
      if (o && !mik.value) mik.value = String(o.bakiye);
    });
    const row = { lot, kal, mik, kutu };
    const del = h("button", { class: "icon-btn", type: "button", "aria-label": "Satırı sil", onclick: () => { rows.splice(rows.indexOf(row), 1); lineEl.remove(); } }, "✕");
    const lineEl = h("div", { class: "line" }, lot, kal, mik, kutu, del);
    rows.push(row);
    lines.insertBefore(lineEl, addBox);
  };
  ted.addEventListener("change", () => {
    for (const r of rows) {
      const cur = r.kal.value;
      const fresh = selectEl(kalemOpts(), { placeholder: "Kalem seçin…", value: cur });
      r.kal.replaceChildren(...fresh.childNodes);
      r.kal.value = kalemOpts().some(o => o.id === cur) ? cur : "";
    }
  });
  const addBox = h("div", { class: "lines-add" }, h("button", { class: "btn btn-outline btn-sm", type: "button", onclick: addLine }, "+ Kalem ekle"));
  lines.append(addBox);
  addLine();
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  const body = h("div", null,
    h("p", { class: "req-note" }, h("span", { class: "req", "aria-hidden": "true", text: "*" }), " Zorunlu"),
    h("div", { class: "form-grid" },
      fieldEl("İrsaliye No", irs, { required: true }), fieldEl("Tedarikçi", ted, { hint: "Seçince yalnızca o tedarikçinin açık kalemleri listelenir" }),
      fieldEl("Durum", durum, { required: true }), fieldEl("Planlanan Sevk Tarihi", plan),
      fieldEl("Tahmini Varış", varis), fieldEl("Taşıyıcı Firma", tas), fieldEl("Araç Plakası", plk)),
    h("div", { class: "group-title", text: "Sevkiyat kalemleri" }), lines, err);
  openModal("Yeni ASN / sevkiyat", body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeModal }, "Vazgeç"),
    saveBtn(async () => {
      clearInvalid(body);
      const missing = [];
      if (isEmptyValue(irs.value)) missing.push(["İrsaliye No", irs]);
      if (isEmptyValue(durum.value)) missing.push(["Durum", durum]);
      const filled = rows.filter(r => r.lot.value || r.kal.value || r.mik.value);
      for (const r of filled) {
        if (isEmptyValue(r.lot.value)) missing.push(["Lot No", r.lot]);
        if (!r.kal.value) missing.push(["Sipariş kalemi", r.kal]);
        if (num(r.mik.value) == null) missing.push(["Sevk miktarı", r.mik]);
      }
      if (missing.length) { showErr(err, missing.map(m => m[0]), missing[0][1], missing.map(m => m[1])); return false; }
      const p = { [F.SEV.irsaliye]: irs.value.trim(), [F.SEV.durum]: durum.value };
      if (ted.value) p[F.SEV.ted] = [ted.value];
      if (plan.value) p[F.SEV.plan] = plan.value;
      if (varis.value) p[F.SEV.varis] = varis.value;
      if (tas.value.trim()) p[F.SEV.tasiyici] = tas.value.trim();
      if (plk.value.trim()) p[F.SEV.plaka] = plk.value.trim();
      const sevRes = await createRec(L.SEV, p);
      const sevId = sevRes?._id ?? sevRes?.id;
      if (!sevId) throw new Error("Sevkiyat oluşturuldu ama kimliği alınamadı.");
      for (const r of filled) {
        const kp = { [F.SVK.lot]: r.lot.value.trim(), [F.SVK.sevkiyat]: [sevId], [F.SVK.kalem]: [r.kal.value], [F.SVK.sevk]: num(r.mik.value) };
        if (ted.value) kp[F.SVK.ted] = [ted.value];
        if (num(r.kutu.value) != null) kp[F.SVK.kutu] = num(r.kutu.value);
        await createRec(L.SVK, kp);
      }
      toast("ASN " + p[F.SEV.irsaliye] + " oluşturuldu (" + filled.length + " kalem)", "ok");
      S.filter.sevkiyat = "aktif";
    }, err, "ASN oluştur", closeModal)
  ]);
}

function newAksiyon(vakaId) {
  const vakaRec = vakaId ? S.data.VAK.find(x => x._id === vakaId) : null;
  const baslik = h("input", { type: "text", id: nid("aks-bas") });
  const kaynak = selectEl(OPT.aksKaynak, { id: nid("aks-kay"), value: vakaRec ? "8D" : "" });
  const vaka = selectEl(vakaRows().map(x => ({ id: x.id, label: (x.no != null ? "KV-" + x.no + " · " : "") + x.baslik })), { id: nid("aks-vaka"), placeholder: "Bağlı vaka yok", value: vakaId || "" });
  const vakaTed = id => linkId(v(S.data.VAK.find(x => x._id === id), F.VAK.ted)) || "";
  const ted = selectEl(tedOptions(), { id: nid("aks-ted"), value: vakaId ? vakaTed(vakaId) : "" });
  vaka.addEventListener("change", () => { if (vaka.value) { ted.value = vakaTed(vaka.value) || ted.value; if (!kaynak.value) kaynak.value = "8D"; } });
  const tip = selectEl(OPT.aksTip, { id: nid("aks-tip") });
  const taraf = selectEl(OPT.aksTaraf, { id: nid("aks-taraf"), value: "Tedarikçi" });
  const d = new Date(); d.setDate(d.getDate() + 14);
  const termin = h("input", { type: "date", id: nid("aks-ter"), value: isoLocal(d) });
  const tanim = h("textarea", { id: nid("aks-tan") });
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  const body = h("div", null,
    h("p", { class: "req-note" }, h("span", { class: "req", "aria-hidden": "true", text: "*" }), " Zorunlu"),
    h("div", { class: "form-grid" },
      fieldEl("Aksiyon Başlığı", baslik, { required: true, full: true }),
      fieldEl("Kaynak Tipi", kaynak), fieldEl("Kalite Vakası", vaka),
      fieldEl("Tedarikçi", ted), fieldEl("Sorumlu Taraf", taraf),
      fieldEl("Aksiyon Tipi", tip), fieldEl("Termin", termin),
      fieldEl("Aksiyon Tanımı", tanim, { full: true })), err);
  openModal("Yeni aksiyon", body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeModal }, "Vazgeç"),
    saveBtn(async () => {
      clearInvalid(body);
      if (isEmptyValue(baslik.value)) { showErr(err, ["Aksiyon Başlığı"], baslik); return false; }
      const p = { [F.AKS.baslik]: baslik.value.trim(), [F.AKS.durum]: "Açık" };
      if (kaynak.value) p[F.AKS.kaynak] = kaynak.value;
      if (vaka.value) p[F.AKS.vaka] = [vaka.value];
      if (ted.value) p[F.AKS.ted] = [ted.value];
      if (taraf.value) p[F.AKS.taraf] = taraf.value;
      if (tip.value) p[F.AKS.tip] = tip.value;
      if (termin.value) p[F.AKS.termin] = termin.value;
      if (tanim.value.trim()) p[F.AKS.tanim] = tanim.value.trim();
      await createRec(L.AKS, p);
      toast("Aksiyon oluşturuldu — sorumlulara bildirim gidiyor", "ok");
      S.filter.aksiyon = "acik";
    }, err, "Aksiyonu oluştur", closeModal)
  ]);
}

function newVaka() {
  const baslik = h("input", { type: "text", id: nid("vk-bas") });
  const kaynak = selectEl(OPT.vakaKaynak, { id: nid("vk-kay") });
  const ted = selectEl(tedOptions(), { id: nid("vk-ted") });
  const mal = selectEl(malOptions(), { id: nid("vk-mal") });
  const tespit = h("input", { type: "date", id: nid("vk-tes"), value: todayIso() });
  const hatali = h("input", { type: "number", min: "0", step: "any", id: nid("vk-hat") });
  const kat = selectEl(OPT.vakaKategori, { id: nid("vk-kat") });
  const lot = h("input", { type: "text", id: nid("vk-lot") });
  const tanim = h("textarea", { id: nid("vk-tan") });
  const d8 = h("input", { type: "checkbox", id: nid("vk-8d") });
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  const body = h("div", null,
    h("p", { class: "req-note" }, h("span", { class: "req", "aria-hidden": "true", text: "*" }), " Zorunlu"),
    h("div", { class: "form-grid" },
      fieldEl("Vaka Başlığı", baslik, { required: true, full: true }),
      fieldEl("Vaka Kaynağı", kaynak), fieldEl("Tespit Tarihi", tespit),
      fieldEl("Tedarikçi", ted), fieldEl("Malzeme", mal),
      fieldEl("Hatalı Miktar", hatali), fieldEl("Hata Kategorisi", kat),
      fieldEl("Lot No", lot), h("label", { class: "check" }, d8, "8D gerekli (Kırpart kalite onayına düşer)"),
      fieldEl("Hata Tanımı", tanim, { full: true })), err);
  openModal("Yeni kalite vakası", body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeModal }, "Vazgeç"),
    saveBtn(async () => {
      clearInvalid(body);
      if (isEmptyValue(baslik.value)) { showErr(err, ["Vaka Başlığı"], baslik); return false; }
      const p = { [F.VAK.baslik]: baslik.value.trim() };
      if (kaynak.value) p[F.VAK.kaynak] = kaynak.value;
      if (ted.value) p[F.VAK.ted] = [ted.value];
      if (mal.value) p[F.VAK.malzeme] = [mal.value];
      if (tespit.value) p[F.VAK.tespit] = tespit.value;
      if (num(hatali.value) != null) p[F.VAK.hatali] = num(hatali.value);
      if (kat.value) p[F.VAK.kategori] = kat.value;
      if (lot.value.trim()) p[F.VAK.lot] = lot.value.trim();
      if (tanim.value.trim()) p[F.VAK.tanim] = tanim.value.trim();
      if (d8.checked) p[F.VAK.d8Gerekli] = true;
      await createRec(L.VAK, p);
      toast("Kalite vakası oluşturuldu" + (d8.checked ? " — 8D onayı Kırpart kaliteye gitti" : ""), "ok");
      S.filter.vaka = d8.checked ? "acik" : "tum";
    }, err, "Vakayı oluştur", closeModal)
  ]);
}

/* ════════════════════════ Form altyapısı ════════════════════════ */
function fact(k, val) { return h("div", { class: "fact" }, h("div", { class: "k", text: k }), h("div", { class: "v", text: String(val) })); }

/* Kayıttan düzenleme formu üretir; yalnızca değişen alanları döndürür */
function buildForm(rec, defs) {
  const grid = h("div", { class: "form-grid" });
  const controls = {};
  const initial = {};
  for (const d of defs) {
    const raw = v(rec, d.id);
    const id = nid("f" + d.id);
    let ctl, init;
    if (d.type === "select") {
      init = lbl(raw);
      ctl = selectEl(d.options, { id, value: init });
      if (init && !d.options.includes(init)) ctl.append(h("option", { value: init, text: init, selected: true }));
    } else if (d.type === "link") {
      init = linkId(raw) || "";
      ctl = selectEl(d.source === "TED" ? tedOptions() : malOptions(), { id, value: init });
    } else if (d.type === "date") {
      init = inputDate(raw);
      ctl = h("input", { type: "date", id, value: init });
    } else if (d.type === "number") {
      init = num(raw) == null ? "" : String(num(raw));
      ctl = h("input", { type: "number", step: "any", id, value: init });
    } else if (d.type === "bool") {
      init = !!raw;
      ctl = h("input", { type: "checkbox", id, checked: init });
    } else if (d.type === "textarea") {
      init = lbl(raw);
      ctl = h("textarea", { id }); ctl.value = init;
    } else {
      init = lbl(raw);
      ctl = h("input", { type: "text", id, value: init });
    }
    ctl.addEventListener("input", () => { S.dirty = true; });
    ctl.addEventListener("change", () => { S.dirty = true; });
    controls[d.id] = ctl; initial[d.id] = init;
    if (d.type === "bool") grid.append(h("label", { class: "check" + (d.full ? " full" : "") }, ctl, d.label));
    else grid.append(fieldEl(d.label, ctl, { required: d.required, full: d.full }));
  }
  const cur = d => {
    const c = controls[d.id];
    return d.type === "bool" ? c.checked : c.value;
  };
  return {
    el: grid,
    control: id => controls[id],
    value: id => { const d = defs.find(x => x.id === id); return d ? cur(d) : undefined; },
    missing: () => defs.filter(d => d.required && isEmptyValue(cur(d))),
    changes() {
      const out = {};
      for (const d of defs) {
        const now = cur(d);
        if (d.type === "bool") { if (now !== initial[d.id]) out[d.id] = now; continue; }
        if (String(now ?? "") === String(initial[d.id] ?? "")) continue;
        if (isEmptyValue(now)) { out[d.id] = null; continue; }
        if (d.type === "number") out[d.id] = num(now);
        else if (d.type === "link") out[d.id] = [now];
        else out[d.id] = typeof now === "string" ? now.trim() : now;
      }
      return out;
    }
  };
}

function clearInvalid(root) { for (const el of root.querySelectorAll("[aria-invalid=true]")) el.removeAttribute("aria-invalid"); }
function showErr(box, names, focusEl, invalidEls) {
  box.textContent = "Lütfen doldurun: " + [...new Set(names)].join(", ");
  box.hidden = false;
  for (const el of (invalidEls || [focusEl])) if (el) el.setAttribute("aria-invalid", "true");
  if (focusEl) focusEl.focus();
}

/* Kaydet butonu: uçuşta kilitli, hatayı gösterir, başarıda kapatır ve yeniler */
function saveBtn(fn, errBox, label = "Kaydet", close = closeDrawer) {
  const btn = h("button", { class: "btn btn-primary", type: "button" }, label);
  btn.addEventListener("click", async () => {
    if (btn.disabled) return;
    errBox.hidden = true;
    btn.disabled = true;
    const original = btn.textContent;
    btn.textContent = "";
    btn.append(h("span", { class: "spinner" }), "Kaydediliyor…");
    try {
      const r = await fn();
      if (r === false) return;
      S.dirty = false;
      close();
      reloadAfterWrite();
    } catch (e) {
      if (e instanceof SessionExpired) return;
      errBox.textContent = "Kaydedilemedi: " + e.message;
      errBox.hidden = false;
    } finally {
      btn.disabled = false;
      btn.textContent = original;
    }
  });
  return btn;
}

/* ════════════════════════ Drawer / modal / toast ════════════════════════ */
let lastFocus = null;
function openDrawer(kicker, title, body, footer) {
  lastFocus = document.activeElement;
  $("#drawer-kicker").textContent = kicker;
  $("#drawer-title").textContent = title || "—";
  $("#drawer-body").replaceChildren(body);
  $("#drawer-foot").replaceChildren(...footer);
  $("#scrim").hidden = false;
  const d = $("#drawer");
  d.classList.add("is-open");
  d.setAttribute("aria-hidden", "false");
  S.dirty = false;
  setTimeout(() => $("#drawer-close").focus(), 50);
}
function closeDrawer() {
  if (S.dirty && !confirm("Kaydedilmemiş değişiklikler var. Kapatılsın mı?")) return;
  S.dirty = false;
  const d = $("#drawer");
  d.classList.remove("is-open");
  d.setAttribute("aria-hidden", "true");
  $("#scrim").hidden = true;
  if (lastFocus && lastFocus.focus) lastFocus.focus();
}
function openModal(title, body, footer) {
  lastFocus = document.activeElement;
  $("#modal-title").textContent = title;
  $("#modal-body").replaceChildren(body);
  $("#modal-foot").replaceChildren(...footer);
  $("#modal").hidden = false;
  S.dirty = false;
  body.addEventListener("input", () => { S.dirty = true; });
  setTimeout(() => { const f = body.querySelector("input,select,textarea"); if (f) f.focus(); }, 50);
}
function closeModal() {
  $("#modal").hidden = true;
  S.dirty = false;
  if (lastFocus && lastFocus.focus) lastFocus.focus();
}
function toast(msg, tone) {
  const t = h("div", { class: "toast " + (tone || "") }, h("span", { text: msg }));
  $("#toasts").append(t);
  setTimeout(() => t.remove(), 5000);
}

/* ════════════════════════ Başlat ════════════════════════ */
function init() {
  $("#today-label").textContent = new Date().toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  if (!workiomHeaders()) { redirectToLogin(); return; }

  for (const b of document.querySelectorAll(".tab")) b.addEventListener("click", () => switchTab(b.dataset.tab));
  $("#btn-refresh").addEventListener("click", () => loadAll());
  $("#btn-new-siparis").addEventListener("click", () => { if (!S.loading) newSiparis(); });
  $("#btn-new-sevkiyat").addEventListener("click", () => { if (!S.loading) newSevkiyat(); });
  $("#btn-new-aksiyon").addEventListener("click", () => { if (!S.loading) newAksiyon(); });
  $("#btn-new-vaka").addEventListener("click", () => { if (!S.loading) newVaka(); });
  $("#drawer-close").addEventListener("click", closeDrawer);
  $("#scrim").addEventListener("click", closeDrawer);
  $("#modal-close").addEventListener("click", () => { if (!S.dirty || confirm("Girdiğiniz bilgiler kaybolacak. Kapatılsın mı?")) closeModal(); });
  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    if (!$("#modal").hidden) { if (!S.dirty || confirm("Girdiğiniz bilgiler kaybolacak. Kapatılsın mı?")) closeModal(); }
    else if ($("#drawer").classList.contains("is-open")) closeDrawer();
  });
  for (const t of ["siparis", "sevkiyat", "aksiyon"]) {
    let timer;
    $("#search-" + t).addEventListener("input", e => {
      clearTimeout(timer);
      timer = setTimeout(() => { S.search[t] = e.target.value; renderAll(); }, 150);
    });
  }
  loadAll();
}

document.addEventListener("DOMContentLoaded", init);
