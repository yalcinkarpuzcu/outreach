"use strict";
/* Performans ve Hedefler (SuccessFactors görünümü) — çekirdek: oturum, API, veri modeli, ortak bileşenler, persona yönlendirme.
   Persona ekranları employee.js / manager.js / hr.js içinde PV[persona] olarak kaydolur. */

// ─── Oturum (Workiom vibe app kalıbı) ──────────────────────────────────────
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
  if (!token || !tenantId) return null;
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
  if (redirectingToLogin) return;
  redirectingToLogin = true;
  toast("Oturumun sona erdi, giriş sayfasına yönlendiriliyorsun…", "bad");
  const returnUrl = encodeURIComponent(location.pathname + location.search);
  setTimeout(() => location.replace("/account/login?returnUrl=" + returnUrl), 1200);
}

let apiBasePromise = null;

function apiBase() {
  if (apiBasePromise) return apiBasePromise;
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
      if (!base) throw new Error("Workiom bu çalışma alanı için API adresi bildirmedi.");
      return base.replace(/\/$/, "");
    })
    .catch(err => {
      apiBasePromise = null;
      throw err;
    });
  return apiBasePromise;
}

async function api(method, path, body) {
  const headers = workiomHeaders();
  if (!headers) { redirectToLogin(); throw new Error("Oturum bulunamadı"); }
  const res = await fetch((await apiBase()) + path, {
    method, headers, body: body === undefined ? undefined : JSON.stringify(body)
  });
  const json = await res.json().catch(() => null);
  if (res.status === 401 || json?.unAuthorizedRequest) { redirectToLogin(); throw new Error("Oturum sona erdi"); }
  if (!res.ok || !json || json.success === false)
    throw new Error(json?.error?.message || ("İstek başarısız (" + res.status + ")"));
  return json.result;
}

// ─── Şema (canlı keşiften: Performans Yönetimi + İnsan Kaynakları) ─────────
const L = {
  donem: "59ed2b31-0121-433d-87a5-4631b6bee2b6", form: "0d285bb8-0bb1-4780-b294-4882c89a4c46",
  htur: "54645d3b-94cb-4949-8b23-4e9619daaccc", yet: "63d42d40-3c3f-4634-8ab8-0c0033767e82",
  karne: "af92bbd4-ade4-4813-8628-9aa59debeece", kpi: "c8011040-d3a1-40bc-9463-0e80f2e9f8ec",
  yd: "62a2fa2d-dfd0-43c4-a700-a4b072551c60", obj: "5754b9b7-ae03-421e-b58b-0b9c96217999",
  kr: "a6f761e6-5d4b-4a33-9bc2-b964ea935a7c", ci: "6ee04a57-c0b0-48ee-9162-780c59cd5724",
  gb: "fdd846ae-03bd-4240-a9f4-32b8b52b1530",
  ozluk: "cc279e0f-af5a-4ff8-986f-a31793432ddf", org: "a045d821-d480-433d-b32d-0bae28de0689"
};
const F = {
  donem: { ad: 6037542, tur: 6037617, bas: 6037618, bit: 6037619, son: 6037620, durum: 6037621 },
  form: { ad: 6037549, op: 6037624, pr: 6037625, ku: 6037627, ye: 6037628, top: 6037845, aciklama: 6037629 },
  htur: { ad: 6037556, kod: 6037631 },
  yet: { ad: 6037563, tanim: 6037634, aktif: 6037635, sira: 6037636, formlar: 6037822 },
  karne: { ad: 6037570, calisan: 6037648, form: 6037649, donem: 6037816, durum: 6037572, grup: 6037641,
    kalibre: 6037642, kalNot: 6037643, final: 6037644, onay: 6037646, kpiSkor: 6037901, yetSkor: 6037866,
    toplam: 6037906, opSkor: 6037860, prSkor: 6037861, kuSkor: 6037862, opAg: 6037863, prAg: 6037864,
    kuAg: 6037865, agHata: 6037896, hedefSay: 6037859, okrSay: 6037867, okrOrt: 6037868,
    opOran: 6037829, prOran: 6037830, kuOran: 6037831, yetOran: 6037832 },
  kpi: { ad: 6037579, aciklama: 6037652, yon: 6037653, birim: 6037654, agirlik: 6037655, hedeflenen: 6037656,
    gerceklesen: 6037657, kilitli: 6037658, sonGun: 6037659, tur: 6037660, karne: 6037705, turKodu: 6037833,
    gerc: 6037846, puan: 6037847, agSkor: 6037848 },
  yd: { ad: 6037586, puan: 6037662, aciklama: 6037664, yet: 6037665, karne: 6037801, puan100: 6037855 },
  obj: { ad: 6037593, aciklama: 6037668, seviye: 6037669, sahip: 6037671, tur: 6037675, esik: 6037676,
    renk: 6037677, kapanis: 6037678, retro: 6037679, dept: 6037682, sahipCalisan: 6037684, karne: 6037804,
    ust: 6037808, iyKpi: 6037812, donem: 6037818, ilerleme: 6037871, guven: 6037886, beklenen: 6038233,
    fark: 6038234, durum: 6037595, krSay: 6037869 },
  kr: { ad: 6037602, sahip: 6037687, tip: 6037688, bas: 6037689, hedef: 6037690, guncel: 6037691, birim: 6037693,
    guven: 6037694, sonCi: 6037695, takipte: 6037696, obj: 6037806, kaynak: 6037814, ilerleme: 6037857, gecikti: 6037858 },
  ci: { ad: 6037609, tarih: 6037698, deger: 6037699, guven: 6037700, yapilan: 6037701, engel: 6037702, kr: 6037810 },
  gb: { ad: 6038915, tur: 6038923, mesaj: 6038924, yanit: 6038925, durum: 6038926, gorunurluk: 6038927,
    tarih: 6038928, kimden: 6038930, kime: 6038931, obj: 6038932, yet: 6038933 },
  ozluk: { isim: 5980989, form: 6037823, durum: 5981219, birim: 5981482, hesap: 5981357 },
  org: { ad: 5981224, ust: 5981480 }
};
const KARNE_DURUM = ["Hedef Belirleme", "Yönetici Onayında", "Aktif", "Değerlendirme", "Kalibrasyon", "Tamamlandı"];
const OKR_DURUM = ["Taslak", "Onayda", "Aktif", "Kapanış", "Kapandı"];
const GRUPLAR = ["Beklentinin Çok Altında", "Beklenenin Altında", "Beklenen Performans", "Beklentinin Üstünde", "Beklentinin Çok Üstünde"];
const GRUP_KISA = ["Çok altında", "Altında", "Beklenen", "Üstünde", "Çok üstünde"];
const BIRIMLER = ["%", "Puan", "Skor", "Adet", "Yıl", "Ay", "Hafta", "Gün", "Tutar", "Ton", "Dakika", "KWH/M²", "PPM", "TL/KG", "TL/M²", "M²", "Metre"];

// ─── Okuma yardımcıları ────────────────────────────────────────────────────
const lab = v => v == null ? null : Array.isArray(v) ? (v[0]?.label ?? null) : (typeof v === "object" ? (v.label ?? v.fullname ?? null) : v);
const ids = v => Array.isArray(v) ? v.map(x => x._id).filter(Boolean) : [];
const id1 = v => ids(v)[0] || null;
const num = v => (v == null || v === "" || isNaN(Number(v))) ? null : Number(v);
const g = (r, f) => r ? r[String(f)] : undefined;
const TZ = "Europe/Istanbul";
const todayISO = () => new Date().toLocaleDateString("sv-SE", { timeZone: TZ });
const daysSince = d => d ? Math.floor((Date.now() - Date.parse(d)) / 864e5) : null;
const fmt = (v, d = 1) => v == null ? "–" : Number(v).toLocaleString("tr-TR", { maximumFractionDigits: d, minimumFractionDigits: 0 });
const pct = v => v == null ? "–" : Math.round(v * 100) + "%";
const fdate = d => d ? new Date(d).toLocaleDateString("tr-TR", { day: "numeric", month: "short", timeZone: TZ }) : "–";

// ─── Veri deposu ───────────────────────────────────────────────────────────
const DB = {};
const X = {};
let ME_EMAIL = null;

async function fetchAll(key) {
  const out = [];
  for (let skip = 0; ; skip += 500) {
    const r = await api("POST", "/api/services/app/Data/All", { listId: L[key], maxResultCount: 500, skipCount: skip });
    out.push(...(r.items || []));
    if (out.length >= (r.totalCount || 0) || !(r.items || []).length) break;
  }
  DB[key] = out;
}

async function loadAll(keys = Object.keys(L)) {
  await Promise.all(keys.map(fetchAll));
  buildIndex();
}

function buildIndex() {
  X.units = new Map(DB.org.map(r => [r._id, { id: r._id, name: g(r, F.org.ad), parentId: id1(g(r, F.org.ust)) }]));
  X.unitByName = new Map([...X.units.values()].map(u => [u.name, u]));
  X.people = new Map(DB.ozluk.map(r => {
    const unitId = id1(g(r, F.ozluk.birim));
    return [r._id, { id: r._id, name: g(r, F.ozluk.isim) || "?", unitId, unit: X.units.get(unitId)?.name || "",
      active: lab(g(r, F.ozluk.durum)) === "Aktif Çalışan", account: !!g(r, F.ozluk.hesap), form: lab(g(r, F.ozluk.form)) }];
  }));
  X.peopleList = [...X.people.values()].filter(p => p.active).sort((a, b) => a.name.localeCompare(b.name, "tr"));

  X.periods = DB.donem.map(r => ({ id: r._id, name: g(r, F.donem.ad), type: lab(g(r, F.donem.tur)), start: g(r, F.donem.bas),
    end: g(r, F.donem.bit), due: g(r, F.donem.son), status: lab(g(r, F.donem.durum)) }))
    .sort((a, b) => (a.start || "").localeCompare(b.start || ""));
  X.year = X.periods.find(p => p.type === "Yıl" && p.status === "Aktif") || X.periods.filter(p => p.type === "Yıl").at(-1);
  X.quarter = X.periods.find(p => p.type === "Çeyrek" && p.status === "Aktif") || X.periods.filter(p => p.type === "Çeyrek").at(-1);

  X.forms = DB.form.map(r => ({ id: r._id, raw: r, name: g(r, F.form.ad), op: num(g(r, F.form.op)), pr: num(g(r, F.form.pr)),
    ku: num(g(r, F.form.ku)), ye: num(g(r, F.form.ye)) }));
  X.htur = new Map(DB.htur.map(r => [r._id, { id: r._id, name: g(r, F.htur.ad), code: num(g(r, F.htur.kod)) }]));
  X.yet = DB.yet.map(r => ({ id: r._id, name: g(r, F.yet.ad), def: g(r, F.yet.tanim), active: num(g(r, F.yet.aktif)) === 1,
    order: num(g(r, F.yet.sira)) || 0, forms: (g(r, F.yet.formlar) || []).map(x => x.label) }))
    .sort((a, b) => a.order - b.order);

  X.karne = new Map(DB.karne.map(r => [r._id, {
    id: r._id, name: g(r, F.karne.ad), personId: id1(g(r, F.karne.calisan)), period: lab(g(r, F.karne.donem)),
    form: lab(g(r, F.karne.form)), status: lab(g(r, F.karne.durum)), group: lab(g(r, F.karne.grup)),
    calib: lab(g(r, F.karne.kalibre)), calibNote: g(r, F.karne.kalNot), final: lab(g(r, F.karne.final)),
    approvedAt: g(r, F.karne.onay), kpiScore: num(g(r, F.karne.kpiSkor)), yetScore: num(g(r, F.karne.yetSkor)),
    total: num(g(r, F.karne.toplam)), op: num(g(r, F.karne.opSkor)), pr: num(g(r, F.karne.prSkor)), ku: num(g(r, F.karne.kuSkor)),
    opW: num(g(r, F.karne.opAg)), prW: num(g(r, F.karne.prAg)), kuW: num(g(r, F.karne.kuAg)), wErr: num(g(r, F.karne.agHata)),
    goals: num(g(r, F.karne.hedefSay)), okrCount: num(g(r, F.karne.okrSay)), okrAvg: num(g(r, F.karne.okrOrt)),
    rates: { op: num(g(r, F.karne.opOran)), pr: num(g(r, F.karne.prOran)), ku: num(g(r, F.karne.kuOran)), ye: num(g(r, F.karne.yetOran)) },
    approval: r.approvalRequest && r.approvalRequest.status === 0 ? r.approvalRequest : null
  }]));
  X.karneOf = (personId, period = X.year?.name) =>
    [...X.karne.values()].find(k => k.personId === personId && k.period === period) || null;

  X.kpi = DB.kpi.map(r => ({
    id: r._id, name: g(r, F.kpi.ad), desc: g(r, F.kpi.aciklama), dir: lab(g(r, F.kpi.yon)), unit: lab(g(r, F.kpi.birim)),
    weight: num(g(r, F.kpi.agirlik)), target: num(g(r, F.kpi.hedeflenen)), actual: num(g(r, F.kpi.gerceklesen)),
    locked: num(g(r, F.kpi.kilitli)) === 1, updated: g(r, F.kpi.sonGun), typeId: id1(g(r, F.kpi.tur)),
    type: lab(g(r, F.kpi.tur)), karneId: id1(g(r, F.kpi.karne)), real: num(g(r, F.kpi.gerc)), score: num(g(r, F.kpi.puan)),
    wScore: num(g(r, F.kpi.agSkor))
  }));
  X.kpiOf = karneId => X.kpi.filter(k => k.karneId === karneId);

  X.yd = DB.yd.map(r => ({ id: r._id, name: g(r, F.yd.ad), score: num(g(r, F.yd.puan)), note: g(r, F.yd.aciklama),
    yet: lab(g(r, F.yd.yet)), karneId: id1(g(r, F.yd.karne)) }));

  X.ci = DB.ci.map(r => ({ id: r._id, name: g(r, F.ci.ad), date: g(r, F.ci.tarih), value: num(g(r, F.ci.deger)),
    conf: num(g(r, F.ci.guven)), done: g(r, F.ci.yapilan), blocker: g(r, F.ci.engel), krId: id1(g(r, F.ci.kr)) }))
    .sort((a, b) => (a.date || "").localeCompare(b.date || ""));

  X.obj = new Map(DB.obj.map(r => [r._id, {
    id: r._id, name: g(r, F.obj.ad), desc: g(r, F.obj.aciklama), level: lab(g(r, F.obj.seviye)), type: lab(g(r, F.obj.tur)),
    threshold: num(g(r, F.obj.esik)), color: lab(g(r, F.obj.renk)), closeScore: num(g(r, F.obj.kapanis)), retro: g(r, F.obj.retro),
    dept: lab(g(r, F.obj.dept)), deptId: id1(g(r, F.obj.dept)), ownerId: id1(g(r, F.obj.sahipCalisan)),
    parentId: id1(g(r, F.obj.ust)), period: lab(g(r, F.obj.donem)), progress: num(g(r, F.obj.ilerleme)),
    conf: num(g(r, F.obj.guven)), expected: num(g(r, F.obj.beklenen)), diff: num(g(r, F.obj.fark)),
    status: lab(g(r, F.obj.durum)), karneId: id1(g(r, F.obj.karne)),
    approval: r.approvalRequest && r.approvalRequest.status === 0 ? r.approvalRequest : null
  }]));
  X.kr = DB.kr.map(r => ({
    id: r._id, name: g(r, F.kr.ad), type: lab(g(r, F.kr.tip)), start: num(g(r, F.kr.bas)), target: num(g(r, F.kr.hedef)),
    current: num(g(r, F.kr.guncel)), unit: lab(g(r, F.kr.birim)), conf: num(g(r, F.kr.guven)), lastCi: g(r, F.kr.sonCi),
    tracked: num(g(r, F.kr.takipte)) === 1, objId: id1(g(r, F.kr.obj)), sourceKpi: lab(g(r, F.kr.kaynak)),
    progress: num(g(r, F.kr.ilerleme)), late: num(g(r, F.kr.gecikti)) === 1
  }));
  X.krOf = objId => X.kr.filter(k => k.objId === objId);
  X.ciOf = krId => X.ci.filter(c => c.krId === krId);

  X.gb = DB.gb.map(r => ({ id: r._id, title: g(r, F.gb.ad), type: lab(g(r, F.gb.tur)), msg: g(r, F.gb.mesaj),
    reply: g(r, F.gb.yanit), status: lab(g(r, F.gb.durum)), vis: lab(g(r, F.gb.gorunurluk)), date: g(r, F.gb.tarih),
    from: id1(g(r, F.gb.kimden)), to: id1(g(r, F.gb.kime)), objId: id1(g(r, F.gb.obj)), yet: lab(g(r, F.gb.yet)) }))
    .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
}

// ─── Organizasyon ilişkileri ───────────────────────────────────────────────
function teamOf(personId) {
  const p = X.people.get(personId);
  if (!p) return [];
  const kids = new Set([...X.units.values()].filter(u => u.parentId === p.unitId).map(u => u.id));
  return X.peopleList.filter(q => kids.has(q.unitId));
}
function managerOf(personId) {
  const p = X.people.get(personId);
  const parent = p && X.units.get(p.unitId)?.parentId;
  return parent ? X.peopleList.find(q => q.unitId === parent) || null : null;
}
function deptUnitOf(personId) {          // departman OKR'larının bağlı olduğu birim: kendisi yöneticiyse kendi birimi
  const p = X.people.get(personId);
  if (!p) return null;
  return teamOf(personId).length ? p.unitId : (X.units.get(p.unitId)?.parentId || p.unitId);
}
const personName = id => X.people.get(id)?.name || "—";

// ─── OKR durumu (sabit palet: iyi / risk / kötü / bitti / yok) ─────────────
function toneOfDiff(diff) {
  if (diff == null) return "none";
  return diff >= -0.05 ? "good" : diff >= -0.15 ? "warn" : "bad";
}
const TONE_LABEL = { good: "Yolunda", warn: "Risk", bad: "Geride", done: "Bitti", none: "Başlamadı" };
function objTone(o) {
  if (["Kapandı", "Kapanış"].includes(o.status)) return "done";
  if (["Taslak", "Onayda", "İptal"].includes(o.status)) return "none";
  return toneOfDiff(o.diff);
}
function krExpectedValue(kr, o) {
  if (kr.start == null || kr.target == null || o?.expected == null) return null;
  return kr.start + (kr.target - kr.start) * Math.min(1, Math.max(0, o.expected));
}
function krTone(kr, o) {
  if (o && objTone(o) === "done") return "done";
  if (!X.ciOf(kr.id).length && !kr.lastCi) return "none";
  if (kr.progress == null || o?.expected == null) return "none";
  return toneOfDiff(kr.progress - o.expected);
}
function groupTone(gr) {
  const i = GRUPLAR.indexOf(gr);
  return i < 0 ? "none" : i <= 0 ? "bad" : i === 1 ? "warn" : i === 2 ? "brand" : "good";
}
function karneTone(st) {
  return { "Hedef Belirleme": "none", "Yönetici Onayında": "warn", "Aktif": "good", "Değerlendirme": "brand",
    "Kalibrasyon": "brand", "Tamamlandı": "done", "İptal": "none" }[st] || "none";
}

// ─── İkonlar (satır içi SVG; dış kaynak yok) ───────────────────────────────
const ICONS = {
  home: ["M3 11l9-7 9 7", "M5 10v10h14V10", "M10 20v-6h4v6"],
  target: ["M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18", "M12 7a5 5 0 1 0 0 10a5 5 0 1 0 0-10", "M12 11a1 1 0 1 0 0 2a1 1 0 1 0 0-2"],
  form: ["M7 3h10l2 2v16H5V3z", "M9 9h6", "M9 13h6", "M9 17h4"],
  chat: ["M4 5h16v11H9l-5 4z", "M8 10h8", "M8 13h5"],
  star: ["M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"],
  team: ["M9 11a3 3 0 1 0 0-6a3 3 0 1 0 0 6", "M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6", "M16 5.5a3 3 0 0 1 0 5.6", "M17 14.2c2.3.7 4 2.9 4 5.8"],
  check: ["M4 12l5 5L20 6"],
  approve: ["M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18", "M8 12l3 3 5-6"],
  trend: ["M3 17l6-6 4 4 8-8", "M15 7h6v6"],
  calendar: ["M4 6h16v14H4z", "M4 10h16", "M8 3v5", "M16 3v5"],
  scale: ["M12 4v16", "M5 20h14", "M4 8h16", "M7 8l-3 7h6z", "M17 8l-3 7h6z"],
  settings: ["M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6", "M12 2v3", "M12 19v3", "M2 12h3", "M19 12h3", "M4.9 4.9l2.1 2.1", "M17 17l2.1 2.1", "M4.9 19.1L7 17", "M17 7l2.1-2.1"],
  chart: ["M4 20V10", "M10 20V4", "M16 20v-7", "M22 20H2"],
  bell: ["M6 16V11a6 6 0 0 1 12 0v5l2 2H4z", "M10 20a2 2 0 0 0 4 0"],
  plus: ["M12 5v14", "M5 12h14"],
  clock: ["M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18", "M12 7v5l3 2"],
  send: ["M3 11l18-8-8 18-2-8z"],
  flag: ["M5 21V4", "M5 4h12l-2 4 2 4H5"],
  arrow: ["M5 12h14", "M13 6l6 6-6 6"]
};
function ico(name, size = 20) {
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("width", size); svg.setAttribute("height", size);
  svg.setAttribute("fill", "none"); svg.setAttribute("stroke", "currentColor"); svg.setAttribute("stroke-width", "1.8");
  svg.setAttribute("stroke-linecap", "round"); svg.setAttribute("stroke-linejoin", "round"); svg.setAttribute("aria-hidden", "true");
  for (const d of ICONS[name] || ICONS.form) { const p = document.createElementNS(NS, "path"); p.setAttribute("d", d); svg.append(p); }
  return svg;
}

// ─── DOM yardımcıları (yalnızca textContent) ───────────────────────────────
function el(tag, props, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k === "style") Object.assign(n.style, v);
    else if (k === "value") n.value = v;
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat(Infinity)) {
    if (c == null || c === false) continue;
    n.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return n;
}
const AV_COLORS = ["#114285", "#0070f2", "#256f3a", "#c35500", "#d6006f", "#046c7c", "#8b47d7", "#aa0808", "#5d36ff"];
function avatar(name, sm) {
  const parts = (name || "?").split(/\s+/).filter(Boolean);
  const ini = ((parts[0] || "?")[0] + (parts.length > 1 ? parts.at(-1)[0] : "")).toLocaleUpperCase("tr");
  let h = 0; for (const ch of name || "") h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return el("span", { class: "avatar" + (sm ? " sm" : ""), style: { background: AV_COLORS.at(h % AV_COLORS.length) }, "aria-hidden": "true", text: ini });
}
function personTag(p, role, sm) {
  if (!p) return el("span", { class: "muted", text: "—" });
  return el("div", { class: "person" }, avatar(p.name, sm),
    el("div", { style: { minWidth: 0 } }, el("div", { class: "nm", text: p.name }), role !== false ? el("div", { class: "rl", text: role || p.unit }) : null));
}
const chip = (text, tone = "", plain) => el("span", { class: "chip " + tone + (plain ? " plain" : ""), text });
function bar(v, tone = "brand", expected = null, lg) {
  const w = Math.max(0, Math.min(1, v || 0)) * 100;
  return el("div", { class: "bar" + (lg ? " lg" : ""), role: "progressbar", "aria-valuenow": Math.round(w), "aria-valuemin": 0, "aria-valuemax": 100 },
    el("i", { class: "t-" + tone, style: { width: w + "%" } }),
    expected != null ? el("span", { class: "expected", title: "Bugün beklenen", style: { left: Math.min(100, expected * 100) + "%" } }) : null);
}
function stat(label, value, hint, accent) {
  return el("div", { class: "card stat" + (accent ? " accent" : "") }, el("div", { class: "label", text: label }),
    el("div", { class: "value", text: value }), hint ? el("div", { class: "hint", text: hint }) : null);
}
function empty(msg, icon = "✦") { return el("div", { class: "empty" }, el("div", { style: { fontSize: "28px" }, text: icon }), el("div", { text: msg })); }
function head(title, sub, ...actions) {
  const crumb = state.persona && state.tab[state.persona] !== "home"
    ? el("div", { class: "crumb" }, el("a", { onclick: () => go(state.persona, "home"), text: "Ana Sayfa" }), " / ", state.crumb || title) : null;
  return el("div", { class: "page-head" }, el("div", {}, crumb, el("h1", { text: title }), sub ? el("p", { text: sub }) : null),
    actions.length ? el("div", { class: "actions" }, actions) : null);
}
function confBars(list) {   // son 6 check-in'in güven skoru
  const box = el("div", { class: "conf", title: "Son check-in'lerde güven (1–10)" });
  for (const c of list.slice(-6)) {
    const v = c.conf || 0;
    box.append(el("i", { class: "t-" + (v >= 7 ? "good" : v >= 5 ? "warn" : "bad"), style: { height: Math.max(3, v * 2.2) + "px" } }));
  }
  if (!list.length) box.append(el("span", { class: "muted", style: { fontSize: "12px" }, text: "check-in yok" }));
  return box;
}

function toast(msg, kind = "") {
  const t = el("div", { class: "toast " + kind, text: msg });
  document.getElementById("toasts").append(t);
  setTimeout(() => t.remove(), 3600);
}

const drawer = {
  open(title, body, actions = []) {
    document.getElementById("drawer-title").textContent = title;
    document.getElementById("drawer-body").replaceChildren(body);
    document.getElementById("drawer-foot").replaceChildren(...actions);
    const d = document.getElementById("drawer");
    d.classList.add("open"); d.setAttribute("aria-hidden", "false");
    setTimeout(() => d.querySelector("input, select, textarea, button.btn")?.focus(), 60);
  },
  close() {
    const d = document.getElementById("drawer");
    d.classList.remove("open"); d.setAttribute("aria-hidden", "true");
  }
};

// Form alanı: zorunluysa kırmızı yıldız + required + aria-required
function field(label, control, opts = {}) {
  const id = control.id || ("f" + Math.random().toString(36).slice(2, 8));
  control.id = id;
  if (opts.required) { control.required = true; control.setAttribute("aria-required", "true"); control.dataset.label = label; }
  return el("div", { class: "field" },
    el("label", { for: id }, label, opts.required ? el("span", { class: "req", "aria-hidden": "true", text: "*" }) : null),
    control, opts.help ? el("div", { class: "help", text: opts.help }) : null);
}
const input = (props = {}) => el("input", props);
const textarea = (props = {}) => el("textarea", props);
function select(options, props = {}, placeholder = "Seç…") {
  const s = el("select", props);
  if (placeholder !== null) s.append(el("option", { value: "", text: placeholder }));
  for (const o of options) {
    const [v, t] = Array.isArray(o) ? o : [o, o];
    const opt = el("option", { value: v, text: t });
    if (props.value === v) opt.selected = true;
    s.append(opt);
  }
  return s;
}
function isEmptyValue(v) {
  return v == null || (typeof v === "string" && v.trim() === "") || (Array.isArray(v) && v.length === 0);
}
// Zorunlu alan kontrolü: eksikse hata kutusunu doldurur, ilk alana odaklanır
function checkRequired(form, errBox) {
  const missing = [];
  for (const c of form.querySelectorAll("[aria-required='true']")) {
    const bad = isEmptyValue(c.value);
    c.setAttribute("aria-invalid", bad ? "true" : "false");
    if (bad) missing.push(c);
  }
  if (missing.length) {
    errBox.textContent = "Eksik alanlar: " + missing.map(c => c.dataset.label).join(", ");
    errBox.classList.add("show");
    missing[0].focus();
    return false;
  }
  errBox.classList.remove("show");
  return true;
}
function formShell(...kids) {
  const err = el("div", { class: "form-error", role: "alert" });
  const f = el("form", { novalidate: true }, el("p", { class: "req-note" }, el("span", { class: "req", "aria-hidden": "true", text: "*" }), " Zorunlu"), err, kids);
  f.addEventListener("submit", e => e.preventDefault());
  return { form: f, err };
}
function compact(payload) {       // create isteğinde boş alanlar gönderilmez
  const out = {};
  for (const [k, v] of Object.entries(payload)) if (!isEmptyValue(v)) out[k] = v;
  return out;
}

// Buton çalışırken kilitli; hata görünür kutuya / bildirime yazılır
async function busy(btn, fn, errBox) {
  if (btn) btn.disabled = true;
  try { await fn(); }
  catch (e) {
    if (errBox) { errBox.textContent = e.message; errBox.classList.add("show"); }
    else toast(e.message, "bad");
  }
  finally { if (btn) btn.disabled = false; }
}

// ─── Yazma işlemleri ───────────────────────────────────────────────────────
async function createRec(key, payload) {
  const r = await api("POST", "/api/services/app/Data/Create?listId=" + L[key], compact(payload));
  return r?._id || r?.id;
}
async function updateRec(key, id, payload) {
  return api("PUT", `/api/services/app/Data/UpdatePartial?listId=${L[key]}&id=${encodeURIComponent(id)}`, payload);
}
async function addComment(key, recordId, comment) {
  return api("POST", "/api/services/app/AdvancedComment/Comment?commentAsPlainText=true", { listId: L[key], recordId, comment });
}
async function approveReq(reqId) {
  return api("POST", "/api/services/app/AutomationApprovalRequest/Approve?approvalRequestId=" + encodeURIComponent(reqId));
}
async function rejectReq(reqId, msg) {
  return api("POST", `/api/services/app/AutomationApprovalRequest/Reject?approvalRequestId=${encodeURIComponent(reqId)}&message=${encodeURIComponent(msg)}`);
}
const wait = ms => new Promise(r => setTimeout(r, ms));
// Workiom otomasyonları birkaç saniye içinde çalışır; ilgili listeler sonra yeniden okunur
async function refresh(keys, delay = 0) {
  if (delay) await wait(delay);
  await loadAll(keys);
  render();
}
async function refreshLater(keys, msg) {
  if (msg) toast(msg, "good");
  render();
  await refresh(keys, 600);
  refresh(keys, 5500).catch(() => {});
}

// ─── Persona yönlendirme ───────────────────────────────────────────────────
const PV = {};
const state = {
  persona: "employee",
  who: { employee: null, manager: null, hr: null },
  tab: { employee: "home", manager: "home", hr: "home" },
  ctx: {}
};
const DEFAULT_WHO = { employee: "Barış Doğan", manager: "Murat Koç", hr: "Gülşen Yılmaz" };

function whoOptions(persona) {
  if (persona === "manager") return X.peopleList.filter(p => teamOf(p.id).length);
  if (persona === "hr") return X.peopleList.filter(p => /İK|CEO/.test(p.unit));
  return X.peopleList;
}

function currentTabs(me) {
  return PV[state.persona].tabs.filter(t => !t.when || t.when(me));
}
function closePops() {
  for (const id of ["modpop", "searchpop"]) document.getElementById(id).hidden = true;
  document.getElementById("modbtn").setAttribute("aria-expanded", "false");
}
function openModMenu() {
  const me = X.people.get(state.who[state.persona]);
  const pop = document.getElementById("modpop");
  const tabs = currentTabs(me);
  pop.replaceChildren(el("div", { class: "grp", text: { employee: "Çalışan", manager: "Yönetici", hr: "İK Yöneticisi" }[state.persona] + " modülleri" }),
    ...tabs.map(t => {
      const n = t.badge ? t.badge(me) : 0;
      return el("button", { role: "menuitem", "aria-current": t.id === state.tab[state.persona] ? "page" : null,
        onclick: () => { closePops(); go(state.persona, t.id); } }, ico(t.icon || "form", 18), el("span", { text: t.label }), n ? el("span", { class: "badge", text: n }) : null);
    }));
  pop.hidden = false;
  document.getElementById("modbtn").setAttribute("aria-expanded", "true");
  pop.querySelector("button")?.focus();
}
function runSearch(q) {
  const pop = document.getElementById("searchpop");
  q = q.trim().toLocaleLowerCase("tr");
  if (!q) { pop.hidden = true; return; }
  const me = X.people.get(state.who[state.persona]);
  const acts = currentTabs(me).filter(t => t.label.toLocaleLowerCase("tr").includes(q))
    .map(t => el("button", { onclick: () => { closePops(); document.getElementById("search").value = ""; go(state.persona, t.id); } }, ico(t.icon || "form", 18), el("span", { text: t.label })));
  const people = X.peopleList.filter(p => p.name.toLocaleLowerCase("tr").includes(q)).slice(0, 8)
    .map(p => el("button", { onclick: () => { closePops(); document.getElementById("search").value = ""; state.who.employee = p.id; go("employee", "home"); } },
      avatar(p.name, true), el("span", {}, el("span", { text: p.name }), el("span", { class: "muted", text: " · " + p.unit }))));
  pop.replaceChildren(...(acts.length ? [el("div", { class: "grp", text: "Eylemler" }), ...acts] : []),
    ...(people.length ? [el("div", { class: "grp", text: "Kişiler (profil olarak aç)" }), ...people] : []),
    ...(!acts.length && !people.length ? [el("div", { class: "grp", text: "Sonuç yok" })] : []));
  pop.hidden = false;
}

function render() {
  const pv = PV[state.persona];
  if (!pv || !X.people) return;
  document.querySelectorAll(".persona button").forEach(b => b.setAttribute("aria-selected", b.dataset.persona === state.persona ? "true" : "false"));
  const opts = whoOptions(state.persona);
  if (!state.who[state.persona] || !opts.some(p => p.id === state.who[state.persona]))
    state.who[state.persona] = (opts.find(p => p.name === DEFAULT_WHO[state.persona]) || opts[0])?.id;
  const sel = document.getElementById("who");
  sel.replaceChildren(...opts.map(p => el("option", { value: p.id, text: `${p.name} · ${p.unit}` })));
  sel.value = state.who[state.persona];
  const me = X.people.get(state.who[state.persona]);

  const tabs = currentTabs(me);
  if (!tabs.some(t => t.id === state.tab[state.persona])) state.tab[state.persona] = tabs[0].id;
  const tab = tabs.find(t => t.id === state.tab[state.persona]);
  state.crumb = tab.label;
  document.getElementById("modlabel").textContent = tab.label;
  document.getElementById("meavatar").replaceChildren(el("span", { title: `${me.name} · ${me.unit}` }, avatar(me.name)));
  const todo = pv.todos ? pv.todos(me).length : 0;
  const bc = document.getElementById("bellcount");
  bc.textContent = todo; bc.hidden = !todo;
  const main = document.getElementById("main");
  try { main.replaceChildren(tab.render(me)); }
  catch (e) { main.replaceChildren(el("div", { class: "error" }, el("strong", { text: "Ekran çizilemedi" }), el("span", { text: e.message }))); console.error(e); }
}

// ─── SuccessFactors tarzı ana sayfa: karşılama, hızlı eylemler, "Sizin için bugün", kutucuklar ──
function waves() {
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("class", "waves"); svg.setAttribute("viewBox", "0 0 1440 120"); svg.setAttribute("preserveAspectRatio", "none"); svg.setAttribute("aria-hidden", "true");
  for (const [d, o] of [["M0 70 C 240 20 480 120 760 70 S 1200 10 1440 60 V120 H0Z", ".10"], ["M0 95 C 300 50 620 130 900 85 S 1300 60 1440 90 V120 H0Z", ".14"]]) {
    const p = document.createElementNS(NS, "path"); p.setAttribute("d", d); p.setAttribute("fill", "#fff"); p.setAttribute("fill-opacity", o); svg.append(p);
  }
  return svg;
}
const TODO_COLOR = { target: "#114285", trend: "#0070f2", chat: "#c35500", approve: "#256f3a", form: "#5d36ff", clock: "#aa0808", scale: "#046c7c", calendar: "#d6006f", star: "#256f3a" };
function sfHome(me) {
  const pv = PV[state.persona];
  const hour = Number(new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", hour12: false, timeZone: TZ }).slice(0, 2));
  const greet = hour < 12 ? "Günaydın" : hour < 18 ? "İyi günler" : "İyi akşamlar";
  const todos = pv.todos(me);
  const todayCards = todos.length ? todos.map(t => el("div", { class: "tcard" },
    el("div", { class: "th" }, el("span", { class: "ic", style: { background: TODO_COLOR[t.icon] || "#114285" } }, ico(t.icon, 15)), el("span", { text: t.cat })),
    el("div", { class: "tb" }, el("b", { text: t.title }), t.sub ? el("span", { text: t.sub }) : null),
    el("div", { class: "tf" }, el("button", { class: "btn sm", text: t.action || "Aç", onclick: t.fn }))))
    : [el("div", { class: "tcard done-all" }, ico("approve", 32), el("b", { text: "Hepsi tamam" }), el("span", { text: "Bugün sizi bekleyen bir iş yok." }))];
  return el("div", {},
    el("section", { class: "hero" }, waves(),
      el("div", { class: "date", text: new Date().toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: TZ }) }),
      el("h1", { text: `${greet}, ${me.name.split(" ")[0]}` }),
      el("p", { text: pv.heroSub ? pv.heroSub(me) : me.unit })),
    el("div", { class: "quick" }, pv.quick(me).filter(Boolean).map(q => el("button", { class: "qa", onclick: q.fn },
      el("span", { class: "ic" }, ico(q.icon, 20)), el("span", {}, el("b", { text: q.label }), q.sub ? el("small", { text: q.sub }) : null)))),
    el("div", { class: "home-h" }, el("h2", { text: "Sizin İçin Bugün" }), el("span", { class: "muted", text: todos.length ? `${todos.length} iş` : "" })),
    el("div", { class: "today" }, todayCards),
    el("div", { class: "home-h" }, el("h2", { text: pv.tilesTitle || "Performans ve Hedefler" })),
    el("div", { class: "tiles" }, pv.tiles(me).map(t => el("button", { class: "tile", onclick: t.fn },
      el("b", { text: t.title }), t.sub ? el("small", { text: t.sub }) : null,
      el("div", { class: "big" }, el("strong", { class: t.tone || "", text: t.value }), ico(t.icon, 26)),
      t.foot ? el("div", { class: "ft", text: t.foot }) : null))),
    pv.homeExtra ? pv.homeExtra(me) : null);
}
function go(persona, tab) { state.persona = persona; if (tab) state.tab[persona] = tab; render(); window.scrollTo(0, 0); }

async function start() {
  const main = document.getElementById("main");
  try {
    const [, info] = await Promise.all([loadAll(), api("GET", "/api/services/app/Session/GetCurrentLoginInformations")]);
    ME_EMAIL = info?.user?.emailAddress || null;
    render();
  } catch (e) {
    if (redirectingToLogin) return;
    main.replaceChildren(el("div", { class: "error" }, el("strong", { text: "Veriler yüklenemedi" }), el("span", { text: e.message }),
      el("button", { class: "btn", text: "Tekrar dene", onclick: () => {
        main.replaceChildren(el("div", { class: "loading" }, el("span", { class: "spinner" }), el("span", { text: "Yeniden deneniyor…" })));
        start();
      } })));
  }
}

function boot() {
  document.querySelectorAll(".persona button").forEach(b => b.addEventListener("click", () => go(b.dataset.persona)));
  document.getElementById("modbtn").addEventListener("click", e => { e.stopPropagation(); document.getElementById("modpop").hidden ? openModMenu() : closePops(); });
  document.getElementById("bell").addEventListener("click", () => go(state.persona, "home"));
  const search = document.getElementById("search");
  search.addEventListener("input", () => runSearch(search.value));
  search.addEventListener("click", e => e.stopPropagation());
  document.addEventListener("click", e => { if (!e.target.closest(".popover")) closePops(); });
  document.getElementById("who").addEventListener("change", e => { state.who[state.persona] = e.target.value; render(); });
  document.getElementById("drawer-close").addEventListener("click", drawer.close);
  document.getElementById("drawer").addEventListener("click", e => { if (e.target.id === "drawer") drawer.close(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") { drawer.close(); closePops(); } });
  if (!workiomHeaders()) { redirectToLogin(); return; }
  start();
}
document.addEventListener("DOMContentLoaded", boot);
