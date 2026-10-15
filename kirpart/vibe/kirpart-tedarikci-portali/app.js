"use strict";
/* Kırpart · Tedarikçi Portalı
 * Tedarikçi kullanıcıları kendi siparişlerini, sipariş kalemlerini, envanter bildirimlerini ve
 * sevkiyatlarını görür. Bir kayıt, "Portal Kullanıcıları" alanında giriş yapan kullanıcı varsa
 * "benim" sayılır; asıl erişim sınırı Workiom'daki "Tedarikçi Kullanıcıları" ekip yetkileridir.
 * Alan kimlikleri Workiom'dan canlı keşfedilen şemadan alınmıştır.
 */

/* ════════════════════════ Şema (canlı keşiften) ════════════════════════ */
const L = {
  SIP: "e9e010d1-4f4e-4f93-bec5-8fd0ef009383",   // Siparişler
  KAL: "39c4cf16-4793-4e5b-8298-1b0ca8bad69a",   // Sipariş Kalemleri
  SEV: "7c7786f8-3ab4-40f6-8ee7-84391c997dc8",   // Sevkiyatlar
  SVK: "3b8f3100-04f9-41ac-856e-12eaafaf107a",   // Sevkiyat Kalemleri
  ENV: "df726636-61a9-49d2-b113-d416ce61c2e6"    // Envanter Bildirimleri
};

const F = {
  SIP: { no: 6021944, yayin: 6022162, tarih: 6022163, durum: 6022164, not: 6022165, ted: 6022166, portal: 6022445,
         teyitBekleyen: 6022544, toplamBakiye: 6022545 },
  KAL: { kod: 6021951, siparis: 6022181, ted: 6022182, malzeme: 6022183, malzemeAdi: 6022448, siparisNo: 6022446,
         satir: 6022167, istenen: 6022168, miktar: 6022169, sonIrs: 6022170, sonTeslim: 6022171,
         teyit: 6022172, teyitMiktar: 6022173, teyitTarih: 6022174, kapasite: 6022175, ihtiyac: 6022176,
         redGerekce: 6022177, redAciklama: 6022178, portal: 6022451,
         teslimAlinan: 6022536, sevkToplam: 6022537, bakiye: 6022538, yoldaki: 6022539 },
  SEV: { irsaliye: 6021958, asn: 6022184, durum: 6022185, plan: 6022186, gercek: 6022187, varis: 6022188,
         teslim: 6022189, tasiyici: 6022190, plaka: 6022191, kabulNotu: 6022196, ted: 6022197, portal: 6022453,
         toplamKutu: 6022549, gecikme: 6022595 },
  SVK: { lot: 6021965, sevk: 6022199, kabul: 6022200, kutu: 6022201, sevkiyat: 6022202, kalem: 6022203,
         ted: 6022204, kalemKodu: 6022458, portal: 6022951 },
  ENV: { ozet: 6021972, tarih: 6022207, ted: 6022209, malzeme: 6022210, no: 6022205, miktar: 6022206,
         not: 6022208, tip: 6022460, portal: 6023233 }
};

const OPT = {
  teyitSecim: ["Onaylandı", "Kısmi Onay", "Reddedildi"],
  kapasite: ["Evet", "Hayır"],
  redGerekce: ["Kapasite Yetersiz", "Hammadde Yok", "Termin Uygun Değil", "Fiyat", "Diğer"]
};

/* ════════════════════════ Dil ════════════════════════ */
const I18N = {
  tr: {
    title: "Tedarikçi Portalı", refresh: "Yenile", tabOrders: "Siparişlerim", tabInv: "Envanter Bildirimleri", tabShip: "Sevkiyatlarım",
    searchOrders: "Sipariş, kalem, malzeme ara…", searchShip: "İrsaliye, lot ara…",
    invHint: "Kırpart'a sevke hazır stok miktarlarınızı bildirin. Her bildirim tarihli olarak saklanır.",
    newInv: "+ Yeni Envanter Bildirimi", newAsn: "+ Yeni ASN", supplier: "Tedarikçi",
    kTeyit: "Teyit Bekleyen Kalem", kTeyitSub: "yanıtınızı bekliyor", kBakiye: "Açık Sipariş Bakiyesi", kBakiyeSub: "adet, {n} kalem",
    kHafta: "7 Gün İçinde Teslim", kHaftaSub: "{n} kalem gecikmiş", kHaftaOk: "gecikme yok", kYolda: "Yoldaki Sevkiyat", kYoldaSub: "{n} planlı ASN",
    fTeyit: "Teyit bekleyen", fAcik: "Açık", fTum: "Tümü", fAktif: "Aktif",
    order: "Sipariş", orderDate: "Sipariş tarihi", release: "Yayın", line: "kalem", lines: "kalem", kirpartNote: "Kırpart notu",
    noOrder: "Siparişe bağlı olmayan kalemler",
    thKalem: "Kalem", thMal: "Malzeme", thMiktar: "Miktar", thIstenen: "İstenen Teslim", thTeyit: "Teyit", thTeyitEdilen: "Teyit Edilen",
    thYolda: "Yolda", thBakiye: "Bakiye", btnConfirm: "Teyit ver", btnUpdate: "Güncelle",
    late: "{n} gün geçti", soon: "{n} gün", noRows: "Bu filtrede sipariş yok", noRowsSub: "Filtreyi değiştirin.",
    confirmTitle: "Sipariş teyidi · {k}", ordered: "Sipariş edilen", requested: "İstenen teslim",
    fTeyitDurum: "Teyit Durumu", fTeyitMiktar: "Teyit Edilen Miktar", fTeyitTarih: "Teyit Edilen Teslim Tarihi",
    fKapasite: "Mevcut kapasite yeterli mi?", fIhtiyac: "Neye ihtiyacınız var?", fRedGerekce: "Red Gerekçesi", fRedAciklama: "Red Açıklaması",
    required: "Zorunlu", cancel: "Vazgeç", save: "Kaydet", saving: "Kaydediliyor…", sendConfirm: "Teyidi gönder",
    fillIn: "Lütfen doldurun: ", saveFailed: "Kaydedilemedi: ", loadFailed: "Veriler yüklenemedi: ", retry: "Tekrar dene",
    confirmSent: "Teyit gönderildi — Kırpart satınalmaya bildirim gidiyor",
    invTitle: "Yeni envanter bildirimi", fMalzeme: "Malzeme", fMiktar: "Mevcut (sevke hazır) miktar", fTarih: "Bildirim tarihi", fNot: "Not",
    invSave: "Bildirimi gönder", invSent: "Envanter bildirimi gönderildi", invEmpty: "Henüz envanter bildirimi yok",
    invEmptySub: "\"Yeni Envanter Bildirimi\" ile sevke hazır stok miktarınızı paylaşın.", unit: "adet", invNo: "Bildirim",
    noMaterials: "Size atanmış sipariş kalemi olmadığı için malzeme listesi boş.",
    asnTitle: "Yeni ASN (sevkiyat bildirimi)", fIrsaliye: "İrsaliye No", fPlan: "Planlanan sevk tarihi", fVaris: "Tahmini varış",
    fTasiyici: "Taşıyıcı firma", fPlaka: "Araç plakası", asnLines: "Sevk edilecek kalemler", lnKalem: "Sipariş kalemi", lnLot: "Lot No",
    lnMiktar: "Miktar", lnKutu: "Kutu", addLine: "+ Kalem ekle", removeLine: "Satırı kaldır", asnSave: "ASN oluştur",
    asnSent: "ASN oluşturuldu — Kırpart lojistiğe bildirim gidiyor", noOpenLines: "Sevk edilebilecek teyitli açık kalem yok.",
    lineNeed: "En az bir kalem ekleyin.", lineFields: "Her satırda kalem, lot ve miktar dolu olmalı.", openQty: "açık {n}",
    colPlan: "Planlandı", colYolda: "Yolda", colTeslim: "Teslim Alındı", colKismi: "Kısmi Kabul", empty: "Kayıt yok",
    shipOn: "Sevk", arrive: "Varış", delivered: "Teslim", lateShort: "gecikti", qtyLines: "{a} adet · {k} kalem",
    btnOnWay: "Yola çıktı", onWayDone: "{i} yola çıktı olarak işaretlendi", shipment: "Sevkiyat / ASN",
    shipped: "Sevk", accepted: "Kabul", kabulNotu: "Kırpart kabul notu", shipInfo: "Sevkiyat bilgisi", lineItems: "Kalemler",
    noLines: "Bu sevkiyatta kalem yok.", shipUpdated: "Sevkiyat güncellendi", readonlyShip: "Teslim alınan sevkiyatlar değiştirilemez.",
    unsaved: "Kaydedilmemiş değişiklikler var. Kapatılsın mı?", lose: "Girdiğiniz bilgiler kaybolacak. Kapatılsın mı?",
    noAccessTitle: "Bu portal tedarikçiler içindir",
    noAccessMsg: "Hesabınız hiçbir tedarikçinin portal kullanıcısı olarak tanımlı değil. Erişim için Kırpart satınalma ile iletişime geçin.",
    permNote: "Bazı listelere erişiminiz yok ({l}). Bu bölümler boş görünebilir; Kırpart yöneticinizden yetki isteyin.",
    sessionGone: "Oturumunuzun süresi doldu — giriş sayfasına yönlendiriliyorsunuz…",
    sessionGoneDirty: "Oturumunuzun süresi doldu — kaydedilmemiş değişiklikleriniz kaybolacak. Giriş sayfasına yönlendiriliyorsunuz…",
    status: "Durum", updated: "Son güncelleme {t}", updating: "Güncelleniyor…", select: "Seçiniz…", capNo: "Kapasite yetersiz",
    lists: { SIP: "Siparişler", KAL: "Sipariş Kalemleri", SEV: "Sevkiyatlar", SVK: "Sevkiyat Kalemleri", ENV: "Envanter Bildirimleri" }
  },
  en: {
    title: "Supplier Portal", refresh: "Refresh", tabOrders: "My Orders", tabInv: "Inventory Reports", tabShip: "My Shipments",
    searchOrders: "Search order, line, material…", searchShip: "Search delivery note, lot…",
    invHint: "Report stock that is ready to ship to Kırpart. Every report is kept with its date.",
    newInv: "+ New Inventory Report", newAsn: "+ New ASN", supplier: "Supplier",
    kTeyit: "Lines Awaiting Confirmation", kTeyitSub: "waiting for your answer", kBakiye: "Open Order Balance", kBakiyeSub: "pcs, {n} lines",
    kHafta: "Due in 7 Days", kHaftaSub: "{n} lines overdue", kHaftaOk: "nothing overdue", kYolda: "Shipments in Transit", kYoldaSub: "{n} planned ASNs",
    fTeyit: "Awaiting confirmation", fAcik: "Open", fTum: "All", fAktif: "Active",
    order: "Order", orderDate: "Order date", release: "Release", line: "line", lines: "lines", kirpartNote: "Note from Kırpart",
    noOrder: "Lines not linked to an order",
    thKalem: "Line", thMal: "Material", thMiktar: "Qty", thIstenen: "Requested Date", thTeyit: "Confirmation", thTeyitEdilen: "Confirmed",
    thYolda: "In transit", thBakiye: "Balance", btnConfirm: "Confirm", btnUpdate: "Update",
    late: "{n} days late", soon: "{n} days", noRows: "No orders in this filter", noRowsSub: "Try another filter.",
    confirmTitle: "Order confirmation · {k}", ordered: "Ordered", requested: "Requested date",
    fTeyitDurum: "Confirmation", fTeyitMiktar: "Confirmed quantity", fTeyitTarih: "Confirmed delivery date",
    fKapasite: "Is current capacity sufficient?", fIhtiyac: "What do you need?", fRedGerekce: "Rejection reason", fRedAciklama: "Rejection details",
    required: "Required", cancel: "Cancel", save: "Save", saving: "Saving…", sendConfirm: "Send confirmation",
    fillIn: "Please fill in: ", saveFailed: "Could not save: ", loadFailed: "Could not load data: ", retry: "Try again",
    confirmSent: "Confirmation sent — Kırpart purchasing is notified",
    invTitle: "New inventory report", fMalzeme: "Material", fMiktar: "Quantity ready to ship", fTarih: "Report date", fNot: "Note",
    invSave: "Send report", invSent: "Inventory report sent", invEmpty: "No inventory reports yet",
    invEmptySub: "Use \"New Inventory Report\" to share stock that is ready to ship.", unit: "pcs", invNo: "Report",
    noMaterials: "No order lines are assigned to you, so the material list is empty.",
    asnTitle: "New ASN (advance shipping notice)", fIrsaliye: "Delivery note no.", fPlan: "Planned ship date", fVaris: "Estimated arrival",
    fTasiyici: "Carrier", fPlaka: "Vehicle plate", asnLines: "Lines to ship", lnKalem: "Order line", lnLot: "Lot no.",
    lnMiktar: "Qty", lnKutu: "Boxes", addLine: "+ Add line", removeLine: "Remove line", asnSave: "Create ASN",
    asnSent: "ASN created — Kırpart logistics is notified", noOpenLines: "No confirmed open lines to ship.",
    lineNeed: "Add at least one line.", lineFields: "Each line needs an order line, lot and quantity.", openQty: "open {n}",
    colPlan: "Planned", colYolda: "In transit", colTeslim: "Received", colKismi: "Partially accepted", empty: "Nothing here",
    shipOn: "Ships", arrive: "Arrives", delivered: "Received", lateShort: "late", qtyLines: "{a} pcs · {k} lines",
    btnOnWay: "Dispatched", onWayDone: "{i} marked as dispatched", shipment: "Shipment / ASN",
    shipped: "Shipped", accepted: "Accepted", kabulNotu: "Kırpart receiving note", shipInfo: "Shipment details", lineItems: "Lines",
    noLines: "This shipment has no lines.", shipUpdated: "Shipment updated", readonlyShip: "Received shipments cannot be changed.",
    unsaved: "You have unsaved changes. Close anyway?", lose: "What you entered will be lost. Close anyway?",
    noAccessTitle: "This portal is for suppliers",
    noAccessMsg: "Your account is not set up as a portal user of any supplier. Please contact Kırpart purchasing for access.",
    permNote: "You don't have access to some lists ({l}). Those sections may look empty; ask your Kırpart administrator for access.",
    sessionGone: "Your session has expired — taking you to the sign-in page…",
    sessionGoneDirty: "Your session has expired — unsaved changes will be lost. Taking you to the sign-in page…",
    status: "Status", updated: "Updated {t}", updating: "Updating…", select: "Select…", capNo: "Capacity insufficient",
    lists: { SIP: "Orders", KAL: "Order Lines", SEV: "Shipments", SVK: "Shipment Lines", ENV: "Inventory Reports" }
  }
};
/* Workiom seçenek etiketleri (yazarken her zaman Türkçe gönderilir) → İngilizce görünüm */
const OPT_EN = {
  "Bekliyor": "Pending", "Onaylandı": "Confirmed", "Kısmi Onay": "Partially confirmed", "Reddedildi": "Rejected",
  "Evet": "Yes", "Hayır": "No", "Kapasite Yetersiz": "Insufficient capacity", "Hammadde Yok": "No raw material",
  "Termin Uygun Değil": "Date not feasible", "Fiyat": "Price", "Diğer": "Other",
  "Açık": "Open", "Teyit Bekliyor": "Awaiting confirmation", "Kısmi Teyit": "Partially confirmed", "Teyit Edildi": "Confirmed",
  "Kapandı": "Closed", "İptal": "Cancelled", "Planlandı": "Planned", "Yolda": "In transit", "Teslim Alındı": "Received",
  "Kısmi Kabul": "Partially accepted", "Hammadde": "Raw material", "Parça": "Part", "Yarı Mamul": "Semi-finished", "Kasa-Ambalaj": "Container / packaging"
};

let LANG = (navigator.language || "tr").toLowerCase().startsWith("tr") ? "tr" : "en";
function t(key, vars) {
  let s = I18N[LANG][key] ?? I18N.tr[key] ?? key;
  if (vars) for (const [k, val] of Object.entries(vars)) s = s.replace("{" + k + "}", val);
  return s;
}
const ov = label => (LANG === "en" ? OPT_EN[label] ?? label : label);
const LOCALE = () => (LANG === "tr" ? "tr-TR" : "en-GB");

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
  if (msg) msg.textContent = S.dirty ? t("sessionGoneDirty") : t("sessionGone");
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
    throw new Error(json?.error?.message || ("HTTP " + res.status));
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
const createRec = async (listId, data) => {
  const r = await api("POST", "/api/services/app/Data/Create?listId=" + encodeURIComponent(listId), data);
  return r?._id ?? r?.id ?? null;
};
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
  clock: "M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z",
  order: "M7 4h10l3 4v12H4V8l3-4zM4 8h16M9 12h6",
  tag: "M3 12V4h8l10 10-8 8z M7.5 7.5h.01"
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
const fmtN = x => (num(x) == null ? "—" : new Intl.NumberFormat(LOCALE(), { maximumFractionDigits: 2 }).format(num(x)));

function toDate(x) { if (!x) return null; const d = new Date(x); return isNaN(d) ? null : d; }
function fmtD(x) {
  const d = toDate(x);
  return d ? d.toLocaleDateString(LOCALE(), { day: "2-digit", month: "short", year: "numeric" }) : "—";
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
const norm = s => String(s || "").toLocaleLowerCase("tr-TR");
const isEmptyValue = x => x == null || (typeof x === "string" && x.trim() === "") || (Array.isArray(x) && x.length === 0);

const TONE = {
  "Bekliyor": "warn", "Onaylandı": "ok", "Kısmi Onay": "info", "Reddedildi": "bad",
  "Planlandı": "navy", "Yolda": "turq", "Teslim Alındı": "ok", "Kısmi Kabul": "warn", "İptal": "",
  "Açık": "info", "Teyit Bekliyor": "warn", "Kısmi Teyit": "info", "Teyit Edildi": "ok", "Kapandı": "ok"
};
function badge(label, tone) {
  if (!label) return h("span", { class: "cell-sub", text: "—" });
  return h("span", { class: "badge " + (tone ?? TONE[label] ?? ""), text: ov(label) });
}

/* ════════════════════════ Durum ════════════════════════ */
const S = {
  me: null,                       // giriş yapan kullanıcının id'si (string)
  data: { SIP: [], KAL: [], SEV: [], SVK: [], ENV: [] },
  denied: [],                     // okunamayan listeler
  suppliers: [],                  // [{id, label}] — kullanıcının portal kullanıcısı olduğu tedarikçiler
  ted: null,                      // seçili tedarikçi id
  tab: "siparis",
  filter: { siparis: "teyit", sevkiyat: "aktif" },
  search: { siparis: "", sevkiyat: "" },
  loading: true,
  dirty: false
};

/* Kayıt bu kullanıcıya mı ait? "Portal Kullanıcıları" alanında giriş yapan kullanıcı olmalı */
function isMine(rec, portalFid) {
  const users = v(rec, portalFid);
  return Array.isArray(users) && users.some(u => String(u?.id ?? u) === S.me);
}
function ofSelected(rec, key) {
  return isMine(rec, F[key].portal) && linkId(v(rec, F[key].ted)) === S.ted;
}

/* ════════════════════════ Yükleme ════════════════════════ */
let loadSeq = 0;
async function loadAll({ quiet = false } = {}) {
  const seq = ++loadSeq;
  if (!quiet) { S.loading = true; renderAll(); }
  try {
    if (!S.me) {
      const info = await api("GET", "/api/services/app/Session/GetCurrentLoginInformations");
      S.me = info?.user?.id != null ? String(info.user.id) : null;
    }
    const keys = Object.keys(L);
    const denied = [];
    const results = await Promise.all(keys.map(k => readAll(L[k]).catch(e => {
      if (e instanceof SessionExpired) throw e;
      denied.push(k);
      return [];
    })));
    if (seq !== loadSeq) return;
    keys.forEach((k, i) => { S.data[k] = results[i]; });
    S.denied = denied;
    if (denied.length === keys.length) throw new Error(t("lists")[denied[0]]);
    computeSuppliers();
    S.loading = false;
    $("#global-error").hidden = true;
    renderAll();
  } catch (e) {
    if (e instanceof SessionExpired) return;
    S.loading = false;
    const box = $("#global-error");
    box.textContent = "";
    box.append(t("loadFailed") + e.message + " ", h("button", { class: "btn btn-outline btn-sm", type: "button", onclick: () => loadAll() }, t("retry")));
    box.hidden = false;
    renderAll();
  }
}

function reloadAfterWrite() {
  loadAll({ quiet: true });
  setTimeout(() => loadAll({ quiet: true }), 4500);   // otomasyonlar (bakiye, bildirim) çalıştıktan sonra
}

function computeSuppliers() {
  const map = new Map();
  for (const key of Object.keys(L)) {
    for (const r of S.data[key]) {
      if (!isMine(r, F[key].portal)) continue;
      const link = v(r, F[key].ted);
      const id = linkId(link);
      if (id && !map.has(id)) map.set(id, lbl(link));
    }
  }
  S.suppliers = [...map].map(([id, label]) => ({ id, label })).sort((a, b) => a.label.localeCompare(b.label, "tr"));
  if (!S.suppliers.some(s => s.id === S.ted)) S.ted = S.suppliers[0]?.id ?? null;
}

/* ════════════════════════ Türetilmiş veriler ════════════════════════ */
function kalemRows() {
  return S.data.KAL.filter(r => ofSelected(r, "KAL")).map(r => ({
    r, id: r._id,
    kod: lbl(v(r, F.KAL.kod)) || "—",
    sipId: linkId(v(r, F.KAL.siparis)),
    sipNo: lbl(v(r, F.KAL.siparisNo)) || lbl(v(r, F.KAL.siparis)),
    malId: linkId(v(r, F.KAL.malzeme)),
    malzeme: lbl(v(r, F.KAL.malzeme)),
    malzemeAdi: lbl(v(r, F.KAL.malzemeAdi)),
    istenen: v(r, F.KAL.istenen),
    miktar: num(v(r, F.KAL.miktar)),
    teyit: lbl(v(r, F.KAL.teyit)) || "Bekliyor",
    kapasite: lbl(v(r, F.KAL.kapasite)),
    teyitMiktar: num(v(r, F.KAL.teyitMiktar)),
    teyitTarih: v(r, F.KAL.teyitTarih),
    yoldaki: num(v(r, F.KAL.yoldaki)) || 0,
    bakiye: num(v(r, F.KAL.bakiye))
  }));
}
const openQty = k => Math.max(0, (k.bakiye ?? k.miktar ?? 0) - (k.yoldaki || 0));
const isConfirmed = k => k.teyit === "Onaylandı" || k.teyit === "Kısmi Onay";

function sevkiyatRows() {
  const lines = {};
  for (const k of S.data.SVK) {
    const sid = linkId(v(k, F.SVK.sevkiyat));
    if (sid) (lines[sid] = lines[sid] || []).push(k);
  }
  return S.data.SEV.filter(r => ofSelected(r, "SEV")).map(r => ({
    r, id: r._id,
    irsaliye: lbl(v(r, F.SEV.irsaliye)),
    asn: v(r, F.SEV.asn),
    durum: lbl(v(r, F.SEV.durum)) || "Planlandı",
    plan: v(r, F.SEV.plan), gercek: v(r, F.SEV.gercek), varis: v(r, F.SEV.varis), teslim: v(r, F.SEV.teslim),
    tasiyici: lbl(v(r, F.SEV.tasiyici)), plaka: lbl(v(r, F.SEV.plaka)),
    kabulNotu: lbl(v(r, F.SEV.kabulNotu)), gecikme: num(v(r, F.SEV.gecikme)),
    kalemler: lines[r._id] || []
  }));
}
const isActiveSev = s => s.durum === "Planlandı" || s.durum === "Yolda";

function envanterRows() {
  return S.data.ENV.filter(r => ofSelected(r, "ENV")).map(r => ({
    r, id: r._id,
    no: v(r, F.ENV.no),
    malzeme: lbl(v(r, F.ENV.malzeme)),
    tip: lbl(v(r, F.ENV.tip)),
    miktar: num(v(r, F.ENV.miktar)),
    tarih: v(r, F.ENV.tarih) || v(r, 6021975),
    not: lbl(v(r, F.ENV.not))
  })).sort((a, b) => (toDate(b.tarih)?.getTime() ?? 0) - (toDate(a.tarih)?.getTime() ?? 0));
}

/* Tedarikçinin malzemeleri: kendi sipariş kalemleri ve önceki bildirimlerinden */
function malzemeOptions() {
  const map = new Map();
  for (const k of kalemRows()) if (k.malId && !map.has(k.malId)) map.set(k.malId, k.malzeme + (k.malzemeAdi ? " · " + k.malzemeAdi : ""));
  for (const r of S.data.ENV.filter(x => ofSelected(x, "ENV"))) {
    const id = linkId(v(r, F.ENV.malzeme));
    if (id && !map.has(id)) map.set(id, lbl(v(r, F.ENV.malzeme)));
  }
  return [...map].map(([id, label]) => ({ id, label })).sort((a, b) => a.label.localeCompare(b.label, "tr"));
}

/* ════════════════════════ Genel çizim ════════════════════════ */
function renderAll() {
  applyStaticText();
  renderWho();
  renderPermNote();
  const noAccess = !S.loading && $("#global-error").hidden && !!S.me && !S.suppliers.length;
  $("#noaccess").hidden = !noAccess;
  if (noAccess) {
    $("#noaccess-title").textContent = t("noAccessTitle");
    $("#noaccess-msg").textContent = t("noAccessMsg");
  }
  renderKpis();
  renderSiparis();
  renderEnvanter();
  renderSevkiyat();
  if (!S.loading && S.ted) {
    $("#tc-siparis").textContent = String(kalemRows().filter(k => k.teyit === "Bekliyor").length);
    $("#tc-envanter").textContent = String(envanterRows().length);
    $("#tc-sevkiyat").textContent = String(sevkiyatRows().filter(isActiveSev).length);
  }
}

function applyStaticText() {
  document.documentElement.lang = LANG;
  for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t(el.dataset.i18n);
  for (const el of document.querySelectorAll("[data-i18n-ph]")) el.setAttribute("placeholder", t(el.dataset.i18nPh));
  for (const b of document.querySelectorAll(".lang button")) b.classList.toggle("is-active", b.dataset.lang === LANG);
  $("#today-label").textContent = new Date().toLocaleDateString(LOCALE(), { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}

function renderWho() {
  const box = $("#who");
  box.textContent = "";
  if (S.loading || !S.suppliers.length) return;
  if (S.suppliers.length === 1) {
    box.append(h("span", { class: "who-label", text: t("supplier") + ":" }), h("span", { class: "who-name", text: S.suppliers[0].label }));
    return;
  }
  const sel = h("select", { id: "who-select", "aria-label": t("supplier") });
  for (const s of S.suppliers) sel.append(h("option", { value: s.id, text: s.label, selected: s.id === S.ted }));
  sel.addEventListener("change", () => { S.ted = sel.value; renderAll(); });
  box.append(h("label", { class: "who-label", for: "who-select", text: t("supplier") + ":" }), sel);
}

function renderPermNote() {
  const box = $("#perm-note");
  if (S.loading || !S.denied.length) { box.hidden = true; return; }
  box.textContent = t("permNote", { l: S.denied.map(k => t("lists")[k]).join(", ") });
  box.hidden = false;
}

function renderChips(container, items, current, onPick) {
  const box = $(container);
  box.textContent = "";
  for (const it of items) {
    box.append(h("button", { class: "chip" + (it.key === current ? " is-active" : ""), type: "button", onclick: () => onPick(it.key) },
      it.label, h("span", { class: "n", text: String(it.n) })));
  }
}

function switchTab(tab) {
  S.tab = tab;
  for (const b of document.querySelectorAll(".tab")) {
    const on = b.dataset.tab === tab;
    b.classList.toggle("is-active", on);
    b.setAttribute("aria-selected", on ? "true" : "false");
  }
  for (const x of ["siparis", "envanter", "sevkiyat"]) $("#panel-" + x).hidden = x !== tab;
}

/* ════════════════════════ KPI ════════════════════════ */
function renderKpis() {
  const box = $("#kpis");
  box.textContent = "";
  if (S.loading || !S.ted) {
    for (let i = 0; i < 4; i++) box.append(h("div", { class: "kpi skeleton" }, h("div", { class: "kpi-label", text: " " }), h("div", { class: "kpi-value", text: "00" })));
    return;
  }
  const K = kalemRows(), SV = sevkiyatRows();
  const bekleyen = K.filter(k => k.teyit === "Bekliyor");
  const acik = K.filter(k => (k.bakiye ?? 0) > 0 && k.teyit !== "Reddedildi");
  const hafta = acik.filter(k => (daysFromToday(k.istenen) ?? 99) <= 7);
  const gec = hafta.filter(k => (daysFromToday(k.istenen) ?? 0) < 0).length;
  const yolda = SV.filter(s => s.durum === "Yolda").length;
  const planli = SV.filter(s => s.durum === "Planlandı").length;
  const tiles = [
    { label: t("kTeyit"), ico: ICO.clock, val: bekleyen.length, sub: t("kTeyitSub"), accent: "var(--warn)", go: () => { S.filter.siparis = "teyit"; switchTab("siparis"); renderSiparis(); } },
    { label: t("kBakiye"), ico: ICO.order, val: fmtN(acik.reduce((s, k) => s + (k.bakiye || 0), 0)), sub: t("kBakiyeSub", { n: acik.length }), accent: "var(--navy)", go: () => { S.filter.siparis = "acik"; switchTab("siparis"); renderSiparis(); } },
    { label: t("kHafta"), ico: ICO.cal, val: hafta.length, sub: gec ? t("kHaftaSub", { n: gec }) : t("kHaftaOk"), subBad: gec > 0, accent: "var(--bad)", go: () => { S.filter.siparis = "acik"; switchTab("siparis"); renderSiparis(); } },
    { label: t("kYolda"), ico: ICO.truck, val: yolda, sub: t("kYoldaSub", { n: planli }), accent: "var(--turq)", go: () => { S.filter.sevkiyat = "aktif"; switchTab("sevkiyat"); renderSevkiyat(); } }
  ];
  for (const x of tiles) {
    box.append(h("button", { class: "kpi", type: "button", style: "--accent:" + x.accent, onclick: x.go },
      h("div", { class: "kpi-label" }, icon(x.ico), x.label),
      h("div", { class: "kpi-value", text: String(x.val) }),
      h("div", { class: "kpi-sub" + (x.subBad ? " bad" : ""), text: x.sub })));
  }
}

/* ════════════════════════ SİPARİŞLER ════════════════════════ */
const SIP_FILTERS = [
  { key: "teyit", label: () => t("fTeyit"), test: k => k.teyit === "Bekliyor" },
  { key: "acik", label: () => t("fAcik"), test: k => (k.bakiye ?? 0) > 0 && k.teyit !== "Reddedildi" },
  { key: "tum", label: () => t("fTum"), test: () => true }
];

function renderSiparis() {
  const box = $("#orders");
  box.textContent = "";
  if (S.loading) { box.append(h("div", { class: "state" }, h("div", { class: "loader" }))); return; }
  if (!S.ted) return;
  const all = kalemRows();
  renderChips("#chips-siparis", SIP_FILTERS.map(f => ({ key: f.key, label: f.label(), n: all.filter(f.test).length })),
    S.filter.siparis, k => { S.filter.siparis = k; renderSiparis(); });
  const f = SIP_FILTERS.find(x => x.key === S.filter.siparis) || SIP_FILTERS[0];
  const q = norm(S.search.siparis);
  const rows = all.filter(f.test).filter(k => !q || norm([k.kod, k.sipNo, k.malzeme, k.malzemeAdi].join(" ")).includes(q));

  const sipById = Object.fromEntries(S.data.SIP.filter(r => ofSelected(r, "SIP")).map(r => [r._id, r]));
  const groups = new Map();
  for (const k of rows) {
    const key = k.sipId && sipById[k.sipId] ? k.sipId : (k.sipNo ? "no:" + k.sipNo : "none");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(k);
  }
  if (!groups.size) {
    box.append(h("div", { class: "card state" }, h("div", { class: "big", text: t("noRows") }), h("div", { text: t("noRowsSub") })));
    return;
  }
  const minDate = ks => Math.min(...ks.map(k => toDate(k.istenen)?.getTime() ?? 9e15));
  for (const [key, ks] of [...groups].sort((a, b) => minDate(a[1]) - minDate(b[1]))) {
    ks.sort((a, b) => (toDate(a.istenen)?.getTime() ?? 9e15) - (toDate(b.istenen)?.getTime() ?? 9e15));
    box.append(orderCard(sipById[key], key, ks));
  }
}

function orderCard(sip, key, ks) {
  const title = sip ? lbl(v(sip, F.SIP.no)) : key.startsWith("no:") ? key.slice(3) : t("noOrder");
  const durum = sip ? lbl(v(sip, F.SIP.durum)) : "";
  const note = sip ? lbl(v(sip, F.SIP.not)) : "";
  const yayin = sip ? lbl(v(sip, F.SIP.yayin)) : "";
  const head = h("div", { class: "order-head" },
    h("div", null,
      h("div", { class: "order-title" }, (key === "none" ? "" : t("order") + " ") + title),
      h("div", { class: "order-meta" },
        sip && v(sip, F.SIP.tarih) ? h("span", null, icon(ICO.cal), t("orderDate") + " " + fmtD(v(sip, F.SIP.tarih))) : null,
        yayin ? h("span", null, icon(ICO.tag), t("release") + " " + yayin) : null,
        h("span", null, icon(ICO.box), ks.length + " " + (ks.length === 1 ? t("line") : t("lines"))))),
    durum ? badge(durum) : null);
  const table = h("table", { class: "table" },
    h("thead", null, h("tr", null,
      h("th", { text: t("thKalem") }), h("th", { text: t("thMal") }), h("th", { class: "num", text: t("thMiktar") }),
      h("th", { text: t("thIstenen") }), h("th", { text: t("thTeyit") }), h("th", { text: t("thTeyitEdilen") }),
      h("th", { class: "num", text: t("thYolda") }), h("th", { class: "num", text: t("thBakiye") }), h("th"))),
    h("tbody", null, ks.map(kalemRow)));
  return h("div", { class: "card order" }, head,
    note ? h("div", { class: "order-note", text: t("kirpartNote") + ": " + note }) : null,
    h("div", { class: "table-wrap" }, table));
}

function kalemRow(k) {
  const dd = daysFromToday(k.istenen);
  const open = (k.bakiye ?? 0) > 0;
  const late = dd != null && dd < 0 && open;
  const soon = dd != null && dd >= 0 && dd <= 3 && open;
  const pending = k.teyit === "Bekliyor";
  return h("tr", null,
    h("td", null, h("div", { class: "cell-main", text: k.kod })),
    h("td", null, h("div", { text: k.malzeme || "—" }), h("div", { class: "cell-sub", text: k.malzemeAdi })),
    h("td", { class: "num", text: fmtN(k.miktar) }),
    h("td", { class: late ? "date-late" : soon ? "date-soon" : "" }, fmtD(k.istenen),
      late ? " · " + t("late", { n: -dd }) : soon ? " · " + t("soon", { n: dd }) : ""),
    h("td", null, badge(k.teyit), k.kapasite === "Hayır" ? h("div", { class: "cell-sub", style: "color:var(--bad);margin-top:3px", text: t("capNo") }) : null),
    h("td", null, k.teyitMiktar != null ? h("div", { class: "num", style: "text-align:left", text: fmtN(k.teyitMiktar) }) : h("span", { class: "cell-sub", text: "—" }),
      k.teyitTarih ? h("div", { class: "cell-sub", text: fmtD(k.teyitTarih) }) : null),
    h("td", { class: "num", text: k.yoldaki ? fmtN(k.yoldaki) : "—" }),
    h("td", { class: "num" }, h("b", { text: fmtN(k.bakiye) })),
    h("td", { style: "text-align:right" },
      h("button", { class: "btn btn-sm " + (pending ? "btn-accent" : "btn-outline"), type: "button", onclick: () => openTeyit(k.id) },
        pending ? t("btnConfirm") : t("btnUpdate"))));
}

function openTeyit(id) {
  const k = kalemRows().find(x => x.id === id);
  if (!k) return;
  const teyit = selectEl(OPT.teyitSecim, { id: nid("ty-durum"), value: k.teyit === "Bekliyor" ? "Onaylandı" : k.teyit });
  const miktar = h("input", { type: "number", min: "0", step: "any", id: nid("ty-mik"), value: String(k.teyitMiktar ?? k.miktar ?? "") });
  const tarih = h("input", { type: "date", id: nid("ty-tar"), value: inputDate(k.teyitTarih || k.istenen) });
  const kapasite = selectEl(OPT.kapasite, { id: nid("ty-kap"), value: k.kapasite || "Evet" });
  const ihtiyac = h("textarea", { id: nid("ty-iht") }); ihtiyac.value = lbl(v(k.r, F.KAL.ihtiyac));
  const red = selectEl(OPT.redGerekce, { id: nid("ty-red"), value: lbl(v(k.r, F.KAL.redGerekce)) });
  const redAc = h("textarea", { id: nid("ty-redac") }); redAc.value = lbl(v(k.r, F.KAL.redAciklama));

  const fMiktar = fieldEl(t("fTeyitMiktar"), miktar, { required: true });
  const fTarih = fieldEl(t("fTeyitTarih"), tarih, { required: true });
  const fIhtiyac = fieldEl(t("fIhtiyac"), ihtiyac, { full: true });
  const fRed = fieldEl(t("fRedGerekce"), red, { required: true });
  const fRedAc = fieldEl(t("fRedAciklama"), redAc, { full: true });
  const sync = () => {
    const rej = teyit.value === "Reddedildi";
    fMiktar.hidden = rej; fTarih.hidden = rej; fRed.hidden = !rej; fRedAc.hidden = !rej;
    fIhtiyac.hidden = kapasite.value !== "Hayır";
  };
  teyit.addEventListener("change", sync); kapasite.addEventListener("change", sync);
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  const body = h("div", null,
    h("div", { class: "facts" },
      fact(t("thMal"), k.malzeme + (k.malzemeAdi ? " · " + k.malzemeAdi : "")), fact(t("order"), k.sipNo || "—"),
      fact(t("ordered"), fmtN(k.miktar) + " " + t("unit")), fact(t("requested"), fmtD(k.istenen))),
    reqNote(),
    h("div", { class: "form-grid" },
      fieldEl(t("fTeyitDurum"), teyit, { required: true }), fieldEl(t("fKapasite"), kapasite),
      fMiktar, fTarih, fRed, fRedAc, fIhtiyac), err);
  sync();
  openModal(t("confirmTitle", { k: k.kod }), body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeModalAsk }, t("cancel")),
    saveBtn(async () => {
      clearInvalid(body);
      const p = { [F.KAL.teyit]: teyit.value };
      if (isEmptyValue(teyit.value)) { showErr(err, [t("fTeyitDurum")], teyit); return false; }
      if (teyit.value === "Reddedildi") {
        if (isEmptyValue(red.value)) { showErr(err, [t("fRedGerekce")], red); return false; }
        p[F.KAL.redGerekce] = red.value;
        if (redAc.value.trim()) p[F.KAL.redAciklama] = redAc.value.trim();
      } else {
        const miss = [];
        if (num(miktar.value) == null) miss.push([t("fTeyitMiktar"), miktar]);
        if (isEmptyValue(tarih.value)) miss.push([t("fTeyitTarih"), tarih]);
        if (miss.length) { showErr(err, miss.map(m => m[0]), miss[0][1], miss.map(m => m[1])); return false; }
        p[F.KAL.teyitMiktar] = num(miktar.value);
        p[F.KAL.teyitTarih] = tarih.value;
      }
      if (kapasite.value) p[F.KAL.kapasite] = kapasite.value;
      if (kapasite.value === "Hayır" && ihtiyac.value.trim()) p[F.KAL.ihtiyac] = ihtiyac.value.trim();
      await updateRec(L.KAL, id, p);
      toast(t("confirmSent"), "ok");
    }, err, t("sendConfirm"), closeModal)
  ]);
}

/* ════════════════════════ ENVANTER ════════════════════════ */
function renderEnvanter() {
  const box = $("#inv-grid");
  box.textContent = "";
  if (S.loading) { box.append(h("div", { class: "state" }, h("div", { class: "loader" }))); return; }
  if (!S.ted) return;
  const rows = envanterRows();
  if (!rows.length) {
    box.append(h("div", { class: "card state", style: "grid-column:1/-1" }, h("div", { class: "big", text: t("invEmpty") }), h("div", { text: t("invEmptySub") })));
    return;
  }
  for (const e of rows) {
    box.append(h("div", { class: "card inv" },
      h("div", { class: "inv-top" },
        h("div", null, h("div", { class: "kcard-title", text: e.malzeme || "—" }), e.tip ? h("div", { class: "kcard-sub", text: ov(e.tip) }) : null),
        h("span", { class: "badge plain navy", text: fmtD(e.tarih) })),
      h("div", { class: "inv-qty" }, fmtN(e.miktar), h("small", { text: t("unit") })),
      e.not ? h("div", { class: "inv-note", text: e.not }) : null,
      h("div", { class: "inv-foot" }, h("span", { text: e.no != null ? t("invNo") + " #" + e.no : "" }))));
  }
}

function newEnvanter() {
  const opts = malzemeOptions();
  const mal = selectEl(opts, { id: nid("env-mal") });
  const miktar = h("input", { type: "number", min: "0", step: "any", id: nid("env-mik") });
  const tarih = h("input", { type: "date", id: nid("env-tar"), value: todayIso() });
  const notu = h("textarea", { id: nid("env-not") });
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  const body = h("div", null, reqNote(),
    opts.length ? null : h("div", { class: "alert alert-info", text: t("noMaterials") }),
    h("div", { class: "form-grid" },
      fieldEl(t("fMalzeme"), mal, { required: true, full: true }),
      fieldEl(t("fMiktar"), miktar, { required: true }), fieldEl(t("fTarih"), tarih, { required: true }),
      fieldEl(t("fNot"), notu, { full: true })), err);
  openModal(t("invTitle"), body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeModalAsk }, t("cancel")),
    saveBtn(async () => {
      clearInvalid(body);
      const miss = [];
      if (isEmptyValue(mal.value)) miss.push([t("fMalzeme"), mal]);
      if (num(miktar.value) == null || num(miktar.value) < 0) miss.push([t("fMiktar"), miktar]);
      if (isEmptyValue(tarih.value)) miss.push([t("fTarih"), tarih]);
      if (miss.length) { showErr(err, miss.map(m => m[0]), miss[0][1], miss.map(m => m[1])); return false; }
      const malLabel = (opts.find(o => o.id === mal.value)?.label || "").split(" · ")[0];
      const tedLabel = S.suppliers.find(s => s.id === S.ted)?.label || "";
      const p = {
        [F.ENV.ozet]: tedLabel.split(" ")[0] + " – " + malLabel + " stok bildirimi",
        [F.ENV.ted]: [S.ted], [F.ENV.malzeme]: [mal.value],
        [F.ENV.miktar]: num(miktar.value), [F.ENV.tarih]: tarih.value
      };
      if (notu.value.trim()) p[F.ENV.not] = notu.value.trim();
      await createRec(L.ENV, p);
      toast(t("invSent"), "ok");
    }, err, t("invSave"), closeModal)
  ]);
}

/* ════════════════════════ SEVKİYATLAR ════════════════════════ */
const SEV_COLS = [
  { key: "Planlandı", c: "var(--navy)", label: () => t("colPlan") },
  { key: "Yolda", c: "var(--turq)", label: () => t("colYolda") },
  { key: "Teslim Alındı", c: "var(--ok)", label: () => t("colTeslim") },
  { key: "Kısmi Kabul", c: "var(--warn)", label: () => t("colKismi") }
];
const SEV_FILTERS = [
  { key: "aktif", label: () => t("fAktif"), cols: ["Planlandı", "Yolda"] },
  { key: "tum", label: () => t("fTum"), cols: SEV_COLS.map(c => c.key) }
];

function renderSevkiyat() {
  const board = $("#board-sevkiyat");
  board.textContent = "";
  if (S.loading) { board.append(h("div", { class: "state" }, h("div", { class: "loader" }))); return; }
  if (!S.ted) return;
  const all = sevkiyatRows();
  renderChips("#chips-sevkiyat", SEV_FILTERS.map(f => ({ key: f.key, label: f.label(), n: all.filter(s => f.cols.includes(s.durum)).length })),
    S.filter.sevkiyat, k => { S.filter.sevkiyat = k; renderSevkiyat(); });
  const f = SEV_FILTERS.find(x => x.key === S.filter.sevkiyat) || SEV_FILTERS[0];
  const q = norm(S.search.sevkiyat);
  const rows = all.filter(s => !q || norm([s.irsaliye, s.tasiyici, s.plaka, ...s.kalemler.map(k => lbl(v(k, F.SVK.lot)) + " " + lbl(v(k, F.SVK.kalemKodu)))].join(" ")).includes(q));
  for (const col of SEV_COLS.filter(c => f.cols.includes(c.key))) {
    const items = rows.filter(s => s.durum === col.key)
      .sort((a, b) => (toDate(a.varis || a.plan)?.getTime() ?? 9e15) - (toDate(b.varis || b.plan)?.getTime() ?? 9e15));
    board.append(h("div", { class: "col", style: "--c:" + col.c },
      h("div", { class: "col-head" }, h("div", { class: "col-title", text: col.label() }), h("span", { class: "col-count", text: String(items.length) })),
      items.length ? items.map(s => sevCard(s, col)) : h("div", { class: "col-empty", text: t("empty") })));
  }
}

function sevCard(s, col) {
  const dRef = s.durum === "Planlandı" ? s.plan : s.varis;
  const dd = daysFromToday(dRef);
  const late = isActiveSev(s) && dd != null && dd < 0;
  const adet = s.kalemler.reduce((a, k) => a + (num(v(k, F.SVK.sevk)) || 0), 0);
  const done = s.durum === "Teslim Alındı" || s.durum === "Kısmi Kabul";
  return h("div", { class: "kcard", style: "--c:" + col.c, tabindex: "0", onclick: () => openSevkiyat(s.id),
                     onkeydown: e => { if (e.key === "Enter") openSevkiyat(s.id); } },
    h("div", { class: "kcard-top" },
      h("div", null, h("div", { class: "kcard-title", text: s.irsaliye || "—" })),
      s.asn != null ? h("span", { class: "badge plain navy", text: "ASN " + s.asn }) : null),
    h("div", { class: "kcard-meta" },
      h("span", { class: late ? "date-late" : "" }, icon(ICO.cal),
        (s.durum === "Planlandı" ? t("shipOn") : done ? t("delivered") : t("arrive")) + " " + fmtD(done ? s.teslim : dRef) + (late ? " · " + t("lateShort") : "")),
      h("span", null, icon(ICO.box), t("qtyLines", { a: fmtN(adet), k: s.kalemler.length })),
      s.tasiyici ? h("span", null, icon(ICO.truck), s.tasiyici + (s.plaka ? " · " + s.plaka : "")) : null),
    s.durum === "Planlandı" ? h("div", { class: "kcard-foot" }, h("span"),
      h("button", { class: "btn btn-accent btn-sm", type: "button", onclick: e => { e.stopPropagation(); markOnWay(s); } }, t("btnOnWay"))) : null);
}

async function markOnWay(s) {
  try {
    const p = { [F.SEV.durum]: "Yolda" };
    if (!s.gercek) p[F.SEV.gercek] = todayIso();
    await updateRec(L.SEV, s.id, p);
    toast(t("onWayDone", { i: s.irsaliye }), "ok");
    reloadAfterWrite();
  } catch (e) { if (!(e instanceof SessionExpired)) toast(t("saveFailed") + e.message, "bad"); }
}

function openSevkiyat(id) {
  const s = sevkiyatRows().find(x => x.id === id);
  if (!s) return;
  const editable = isActiveSev(s);
  const body = h("div", null,
    h("div", { class: "facts" },
      fact("ASN", s.asn ?? "—"), fact(t("status"), ov(s.durum)),
      fact(t("fPlan"), fmtD(s.plan)), fact(t("delivered"), fmtD(s.teslim))),
    h("div", { class: "group-title", text: t("lineItems") }),
    s.kalemler.length ? h("div", { class: "mini-lines" }, s.kalemler.map(k => h("div", { class: "mini-line" },
      h("span", { text: lbl(v(k, F.SVK.lot)) + " · " + (lbl(v(k, F.SVK.kalemKodu)) || "—") }),
      h("span", null, t("shipped") + " ", h("b", { text: fmtN(v(k, F.SVK.sevk)) }),
        num(v(k, F.SVK.kabul)) != null ? [" · " + t("accepted") + " ", h("b", { text: fmtN(v(k, F.SVK.kabul)) })] : null)))) :
      h("div", { class: "cell-sub", text: t("noLines") }),
    s.kabulNotu ? h("div", { class: "order-note", style: "margin:12px 0 0", text: t("kabulNotu") + ": " + s.kabulNotu }) : null,
    h("div", { class: "group-title", text: t("shipInfo") }));
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  if (!editable) {
    body.append(h("div", { class: "facts" },
      fact(t("fTasiyici"), s.tasiyici || "—"), fact(t("fPlaka"), s.plaka || "—"),
      fact(t("fVaris"), fmtD(s.varis)), fact(t("shipOn"), fmtD(s.gercek))),
      h("p", { class: "hint", text: t("readonlyShip") }));
    openDrawer(t("shipment"), s.irsaliye, body, [h("button", { class: "btn btn-ghost", type: "button", onclick: closeDrawer }, t("cancel"))]);
    return;
  }
  const form = buildForm(s.r, [
    { id: F.SEV.irsaliye, label: t("fIrsaliye"), type: "text", required: true },
    { id: F.SEV.plan, label: t("fPlan"), type: "date" },
    { id: F.SEV.varis, label: t("fVaris"), type: "date" },
    { id: F.SEV.tasiyici, label: t("fTasiyici"), type: "text" },
    { id: F.SEV.plaka, label: t("fPlaka"), type: "text" }
  ]);
  body.append(reqNote(), form.el, err);
  const foot = [h("button", { class: "btn btn-ghost", type: "button", onclick: closeDrawer }, t("cancel"))];
  if (s.durum === "Planlandı") foot.push(h("button", { class: "btn btn-accent", type: "button", onclick: () => { S.dirty = false; closeDrawer(); markOnWay(s); } }, t("btnOnWay")));
  foot.push(saveBtn(async () => {
    clearInvalid(body);
    const miss = form.missing();
    if (miss.length) { showErr(err, miss.map(m => m.label), form.control(miss[0].id)); return false; }
    const ch = form.changes();
    if (!Object.keys(ch).length) return;
    await updateRec(L.SEV, id, ch);
    toast(t("shipUpdated"), "ok");
  }, err, t("save"), closeDrawer));
  openDrawer(t("shipment"), s.irsaliye, body, foot);
}

function newAsn() {
  const open = kalemRows().filter(k => isConfirmed(k) && openQty(k) > 0);
  const irs = h("input", { type: "text", id: nid("asn-irs") });
  const plan = h("input", { type: "date", id: nid("asn-plan"), value: todayIso() });
  const varis = h("input", { type: "date", id: nid("asn-var") });
  const tas = h("input", { type: "text", id: nid("asn-tas") });
  const plaka = h("input", { type: "text", id: nid("asn-pla") });
  const err = h("div", { class: "alert alert-danger form-error", role: "alert", hidden: true });
  const lines = h("div", { class: "lines lines-asn2" },
    h("div", { class: "lines-head" }, h("span", { text: t("lnKalem") + " *" }), h("span", { text: t("lnLot") + " *" }),
      h("span", { text: t("lnMiktar") + " *" }), h("span", { text: t("lnKutu") }), h("span")));
  const rows = [];
  const kalemOpts = open.map(k => ({ id: k.id, label: k.kod + " · " + k.malzeme + " (" + t("openQty", { n: fmtN(openQty(k)) }) + ")" }));
  const addLine = () => {
    const kal = selectEl(kalemOpts, { placeholder: t("select") }); kal.setAttribute("aria-label", t("lnKalem")); kal.setAttribute("aria-required", "true");
    const lot = h("input", { type: "text", "aria-label": t("lnLot"), "aria-required": "true" });
    const mik = h("input", { type: "number", min: "0", step: "any", "aria-label": t("lnMiktar"), "aria-required": "true" });
    const kutu = h("input", { type: "number", min: "0", step: "1", "aria-label": t("lnKutu") });
    kal.addEventListener("change", () => { const k = open.find(x => x.id === kal.value); if (k && !mik.value) mik.value = String(openQty(k)); });
    const row = { kal, lot, mik, kutu };
    const del = h("button", { class: "icon-btn", type: "button", "aria-label": t("removeLine"), text: "✕",
      onclick: () => { if (rows.length > 1) { rows.splice(rows.indexOf(row), 1); line.remove(); } } });
    const line = h("div", { class: "line" }, kal, lot, mik, kutu, del);
    rows.push(row);
    lines.insertBefore(line, addRow);
  };
  const addRow = h("div", { class: "lines-add" }, h("button", { class: "btn btn-outline btn-sm", type: "button", onclick: () => addLine() }, t("addLine")));
  lines.append(addRow);
  if (open.length) addLine();
  const body = h("div", null, reqNote(),
    h("div", { class: "form-grid" },
      fieldEl(t("fIrsaliye"), irs, { required: true }), fieldEl(t("fPlan"), plan),
      fieldEl(t("fVaris"), varis), fieldEl(t("fTasiyici"), tas), fieldEl(t("fPlaka"), plaka)),
    h("div", { class: "group-title", text: t("asnLines") }),
    open.length ? lines : h("div", { class: "alert alert-info", text: t("noOpenLines") }), err);
  openModal(t("asnTitle"), body, [
    h("button", { class: "btn btn-ghost", type: "button", onclick: closeModalAsk }, t("cancel")),
    saveBtn(async () => {
      clearInvalid(body);
      if (isEmptyValue(irs.value)) { showErr(err, [t("fIrsaliye")], irs); return false; }
      const filled = rows.filter(r => r.kal.value || r.lot.value.trim() || r.mik.value);
      if (!filled.length) { err.textContent = t("lineNeed"); err.hidden = false; return false; }
      const bad = filled.filter(r => !r.kal.value || !r.lot.value.trim() || !(num(r.mik.value) > 0));
      if (bad.length) {
        err.textContent = t("lineFields"); err.hidden = false;
        for (const r of bad) for (const el of [r.kal, r.lot, r.mik]) if (!el.value || (el === r.mik && !(num(el.value) > 0))) el.setAttribute("aria-invalid", "true");
        return false;
      }
      const p = { [F.SEV.irsaliye]: irs.value.trim(), [F.SEV.durum]: "Planlandı", [F.SEV.ted]: [S.ted] };
      if (plan.value) p[F.SEV.plan] = plan.value;
      if (varis.value) p[F.SEV.varis] = varis.value;
      if (tas.value.trim()) p[F.SEV.tasiyici] = tas.value.trim();
      if (plaka.value.trim()) p[F.SEV.plaka] = plaka.value.trim();
      const sevId = await createRec(L.SEV, p);
      if (!sevId) throw new Error("ASN ID?");
      for (const r of filled) {
        const kp = { [F.SVK.lot]: r.lot.value.trim(), [F.SVK.sevkiyat]: [sevId], [F.SVK.kalem]: [r.kal.value],
                     [F.SVK.ted]: [S.ted], [F.SVK.sevk]: num(r.mik.value) };
        if (num(r.kutu.value) != null) kp[F.SVK.kutu] = num(r.kutu.value);
        await createRec(L.SVK, kp);
      }
      toast(t("asnSent"), "ok");
      S.filter.sevkiyat = "aktif";
    }, err, t("asnSave"), closeModal)
  ]);
}

/* ════════════════════════ Form altyapısı ════════════════════════ */
let uid = 0;
const nid = p => p + "-" + (++uid);
function fact(k, val) { return h("div", { class: "fact" }, h("div", { class: "k", text: k }), h("div", { class: "v", text: String(val) })); }
function reqNote() { return h("p", { class: "req-note" }, h("span", { class: "req", "aria-hidden": "true", text: "*" }), " " + t("required")); }

function selectEl(opts, { placeholder, id, value } = {}) {
  const s = h("select", { id });
  s.append(h("option", { value: "", text: placeholder || t("select") }));
  for (const o of opts) {
    const val = typeof o === "string" ? o : o.id;
    const text = typeof o === "string" ? ov(o) : o.label;
    s.append(h("option", { value: val, text, selected: value === val }));
  }
  return s;
}
function fieldEl(label, control, { required, full } = {}) {
  if (required) { control.required = true; control.setAttribute("aria-required", "true"); }
  return h("div", { class: "field" + (full ? " full" : "") },
    h("label", { for: control.id }, label, required ? h("span", { class: "req", "aria-hidden": "true", text: "*" }) : null),
    control);
}

function buildForm(rec, defs) {
  const grid = h("div", { class: "form-grid" });
  const controls = {}, initial = {};
  for (const d of defs) {
    const raw = v(rec, d.id);
    const id = nid("f" + d.id);
    let ctl, init;
    if (d.type === "date") { init = inputDate(raw); ctl = h("input", { type: "date", id, value: init }); }
    else { init = lbl(raw); ctl = h("input", { type: "text", id, value: init }); }
    ctl.addEventListener("input", () => { S.dirty = true; });
    controls[d.id] = ctl; initial[d.id] = init;
    grid.append(fieldEl(d.label, ctl, { required: d.required, full: d.full }));
  }
  return {
    el: grid,
    control: id => controls[id],
    missing: () => defs.filter(d => d.required && isEmptyValue(controls[d.id].value)),
    changes() {
      const out = {};
      for (const d of defs) {
        const now = controls[d.id].value;
        if (now === initial[d.id]) continue;
        out[d.id] = isEmptyValue(now) ? null : now.trim();
      }
      return out;
    }
  };
}

function clearInvalid(root) { for (const el of root.querySelectorAll("[aria-invalid=true]")) el.removeAttribute("aria-invalid"); }
function showErr(box, names, focusEl, invalidEls) {
  box.textContent = t("fillIn") + [...new Set(names)].join(", ");
  box.hidden = false;
  for (const el of (invalidEls || [focusEl])) if (el) el.setAttribute("aria-invalid", "true");
  if (focusEl) focusEl.focus();
}

function saveBtn(fn, errBox, label, close) {
  const btn = h("button", { class: "btn btn-primary", type: "button" }, label);
  btn.addEventListener("click", async () => {
    if (btn.disabled) return;
    errBox.hidden = true;
    btn.disabled = true;
    btn.textContent = "";
    btn.append(h("span", { class: "spinner" }), t("saving"));
    try {
      const r = await fn();
      if (r === false) return;
      S.dirty = false;
      close();
      reloadAfterWrite();
    } catch (e) {
      if (e instanceof SessionExpired) return;
      errBox.textContent = t("saveFailed") + e.message;
      errBox.hidden = false;
    } finally {
      btn.disabled = false;
      btn.textContent = label;
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
  if (S.dirty && !confirm(t("unsaved"))) return;
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
function closeModalAsk() { if (!S.dirty || confirm(t("lose"))) closeModal(); }
function toast(msg, tone) {
  const el = h("div", { class: "toast " + (tone || "") }, h("span", { text: msg }));
  $("#toasts").append(el);
  setTimeout(() => el.remove(), 5000);
}

/* ════════════════════════ Başlat ════════════════════════ */
function init() {
  applyStaticText();
  if (!workiomHeaders()) { redirectToLogin(); return; }

  for (const b of document.querySelectorAll(".tab")) b.addEventListener("click", () => switchTab(b.dataset.tab));
  for (const b of document.querySelectorAll(".lang button")) b.addEventListener("click", () => { LANG = b.dataset.lang; renderAll(); });
  $("#btn-refresh").addEventListener("click", () => loadAll());
  $("#btn-new-env").addEventListener("click", () => { if (!S.loading && S.ted) newEnvanter(); });
  $("#btn-new-asn").addEventListener("click", () => { if (!S.loading && S.ted) newAsn(); });
  $("#drawer-close").addEventListener("click", closeDrawer);
  $("#scrim").addEventListener("click", closeDrawer);
  $("#modal-close").addEventListener("click", closeModalAsk);
  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    if (!$("#modal").hidden) closeModalAsk();
    else if ($("#drawer").classList.contains("is-open")) closeDrawer();
  });
  for (const x of ["siparis", "sevkiyat"]) {
    let timer;
    $("#search-" + x).addEventListener("input", e => {
      clearTimeout(timer);
      timer = setTimeout(() => { S.search[x] = e.target.value; if (x === "siparis") renderSiparis(); else renderSevkiyat(); }, 150);
    });
  }
  loadAll();
}

document.addEventListener("DOMContentLoaded", init);
