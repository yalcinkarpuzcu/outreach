/* Ar-Ge Proje Merkezi — MS Project tarzı Gantt bileşeni (bağımlılık okları, kritik yol, baseline) */
"use strict";

const ZOOM = { hafta: 24, ay: 5.5, ceyrek: 2, yil: 0.7 };
const ROW_H = 34, HEAD_H = 48;
const SVGNS = "http://www.w3.org/2000/svg";

function createGantt(host, opts) {
  const o = Object.assign({ zoom: "ay", showBaseline: true, mode: "plan", onSelect: null }, opts || {});
  const collapsed = new Set();
  let tasks = [], roots = [], selected = null;
  const tip = el("div", { class: "tooltip", role: "tooltip", hidden: true });
  document.body.append(tip);

  function flatten() {
    const out = [];
    const walk = (t, depth) => {
      t.depth = depth;
      out.push(t);
      if (!collapsed.has(t.id)) t.children.forEach(c => walk(c, depth + 1));
    };
    roots.forEach(r => walk(r, 0));
    return out;
  }

  function range() {
    const days = [];
    for (const t of tasks) {
      if (t.start != null) days.push(t.start);
      if (t.end != null) days.push(t.end);
      if (o.showBaseline && t.baseStart != null) days.push(t.baseStart, t.baseEnd ?? t.baseStart);
    }
    if (!days.length) { const t = todayDay(); return [t - 7, t + 60]; }
    return [Math.min(...days) - 10, Math.max(...days) + 20];
  }

  function wbsText(t) {
    if (t.type === "Proje") return "P" + t.wbs;
    if (t.type === "Faz") return "F" + Math.round(t.wbs / 100);
    return String(t.wbs || "");
  }

  function scale(minD, maxD, ppd) {
    const sc = el("div", { class: "g-scale", style: "width:" + Math.ceil((maxD - minD) * ppd) + "px" });
    const a = el("div", { class: "row-a" }), b = el("div", { class: "row-b" });
    sc.append(a, b);
    const gridDays = [];
    const start = dayToDate(minD);
    if (o.zoom === "hafta") {
      // üst: ay, alt: hafta başları (Pazartesi)
      for (let d = minD; d <= maxD; d++) {
        const dt = dayToDate(d);
        if (dt.getUTCDate() === 1 || d === minD) a.append(el("div", { class: "tick major", style: `left:${(d - minD) * ppd}px`, text: AYLAR[dt.getUTCMonth()] + " " + dt.getUTCFullYear() }));
        if (dt.getUTCDay() === 1) { b.append(el("div", { class: "tick", style: `left:${(d - minD) * ppd}px`, text: String(dt.getUTCDate()).padStart(2, "0") })); gridDays.push(d); }
      }
    } else {
      // üst: yıl (veya çeyrek), alt: ay
      let y = start.getUTCFullYear(), m = start.getUTCMonth();
      for (;;) {
        const d = Math.round(Date.UTC(y, m, 1) / 864e5);
        if (d > maxD) break;
        const x = Math.max(0, (d - minD) * ppd);
        if (m === 0 || d <= minD) a.append(el("div", { class: "tick major", style: `left:${x}px`, text: String(y) }));
        if (o.zoom === "yil") { if (m % 3 === 0) { b.append(el("div", { class: "tick", style: `left:${x}px`, text: "Ç" + (m / 3 + 1) })); gridDays.push(d); } }
        else if (o.zoom === "ceyrek") { b.append(el("div", { class: "tick", style: `left:${x}px`, text: AYLAR[m].slice(0, 1) })); gridDays.push(d); }
        else { b.append(el("div", { class: "tick", style: `left:${x}px`, text: AYLAR[m] })); gridDays.push(d); }
        m++; if (m === 12) { m = 0; y++; }
      }
    }
    return { sc, gridDays };
  }

  function barClass(t) {
    if (o.mode === "kutuphane") return "s-hazir";
    return "s-" + (DURUM_SINIF[t.status] || "bekle");
  }

  function showTip(ev, t) {
    clear(tip);
    tip.append(el("b", { text: t.name }));
    const line = s => tip.append(el("div", { text: s }));
    if (o.mode === "kutuphane") {
      line("Gün " + (t.start - o.refDay) + " → " + (t.end - o.refDay) + " · " + (t.end - t.start) + " gün");
    } else {
      line(fmtDay(t.start) + " → " + fmtDay(t.end) + " · " + (t.end - t.start) + " gün");
      if (t.status) line("Durum: " + t.status + (t.summary ? "" : " · %" + Math.round(t.pct || 0)));
      if (t.owner) line("Sorumlu: " + userName(t.owner));
      if (t.baseEnd != null && !t.summary) line("Baseline bitiş: " + fmtDay(t.baseEnd) + (t.variance ? " · sapma " + (t.variance > 0 ? "+" : "") + t.variance + " gün" : ""));
    }
    if (t.critical) line("⚠ Kritik yolda");
    if (t.deps.length) line("Öncüller: " + t.deps.map(d => d.label).join(", "));
    tip.hidden = false;
    moveTip(ev);
  }
  function moveTip(ev) {
    const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(ev.clientX + pad, innerWidth - w - 8) + "px";
    tip.style.top = Math.min(ev.clientY + pad, innerHeight - h - 8) + "px";
  }
  function hideTip() { tip.hidden = true; }

  function render() {
    hideTip();
    const rows = flatten();
    const [minD, maxD] = range();
    const ppd = ZOOM[o.zoom];
    const W = Math.ceil((maxD - minD) * ppd);
    const X = d => (d - minD) * ppd;
    const g = el("div", { class: "gantt", role: "grid", "aria-label": "Gantt şeması" });

    // başlık
    const { sc, gridDays } = scale(minD, maxD, ppd);
    const lastCol = o.mode === "kutuphane" ? "Departman" : "Durum";
    const headLeft = el("div", { class: "g-left" },
      el("div", { text: "WBS" }), el("div", { text: "Görev" }), el("div", { text: "Gün" }),
      el("div", { text: o.mode === "kutuphane" ? "Başl." : "Başlangıç" }), el("div", { text: o.mode === "kutuphane" ? "Bitiş" : "Bitiş" }), el("div", { text: lastCol }));
    g.append(el("div", { class: "g-head" }, headLeft, el("div", { class: "g-right", style: `width:${W}px` }, sc)));

    // gövde katmanı (ızgara, bugün, oklar)
    const body = el("div", { style: "position:relative" });
    g.append(body);
    const pos = new Map();
    rows.forEach((t, i) => pos.set(t.id, i));

    rows.forEach((t, i) => {
      const left = el("div", { class: "g-left" });
      const name = el("div", { class: "g-name", style: `padding-inline-start:${8 + t.depth * 16}px` });
      if (t.children.length) {
        const exp = !collapsed.has(t.id);
        name.append(el("button", {
          class: "caret", "aria-expanded": exp ? "true" : "false", "aria-label": exp ? "Daralt" : "Genişlet", text: "▾",
          onclick: ev => { ev.stopPropagation(); exp ? collapsed.add(t.id) : collapsed.delete(t.id); render(); }
        }));
      } else name.append(el("span", { style: "width:16px;flex:none" }));
      if (t.milestone) name.append(el("span", { class: "ico", text: "◆", style: "color:var(--summary);font-size:11px" }));
      name.append(el("span", { class: "t", text: t.name, title: t.name }));
      if (t.late && !t.summary) name.append(el("span", { class: "tag late", text: "Gecikti" }));
      const last = el("div");
      if (o.mode === "kutuphane") last.textContent = t.dept || "";
      else if (!t.summary) last.append(chip(t.status));
      else last.append(el("span", { class: "num", text: "%" + Math.round(t.pct || 0) }));
      left.append(
        el("div", { class: "num", text: wbsText(t) }), name,
        el("div", { class: "num", text: t.start != null ? String(t.end - t.start) : "" }),
        el("div", { class: "num", text: o.mode === "kutuphane" ? (t.start != null ? "G" + (t.start - o.refDay) : "") : fmtShort(t.start) }),
        el("div", { class: "num", text: o.mode === "kutuphane" ? (t.end != null ? "G" + (t.end - o.refDay) : "") : fmtShort(t.end) }),
        last);

      const right = el("div", { class: "g-right", style: `width:${W}px` });
      if (t.start != null) {
        const hov = { onmouseenter: ev => showTip(ev, t), onmousemove: moveTip, onmouseleave: hideTip };
        if (o.showBaseline && t.baseStart != null && !t.summary) {
          right.append(el("div", { class: "base", style: `left:${X(t.baseStart)}px;width:${Math.max(3, ((t.baseEnd ?? t.baseStart) - t.baseStart) * ppd)}px`, title: "Baseline" }));
        }
        if (t.milestone && !t.summary && t.end - t.start <= 0) {
          right.append(el("div", { class: "ms " + barClass(t) + (t.critical ? " crit" : ""), style: `left:${X(t.start)}px`, ...hov }));
          right.append(el("div", { class: "bar-label", style: `left:${X(t.start) + 12}px`, text: t.name }));
        } else {
          const w = Math.max(3, (t.end - t.start) * ppd);
          const bar = el("div", { class: "bar " + (t.summary ? "summary" : barClass(t)) + (t.critical ? " crit" : ""), style: `left:${X(t.start)}px;width:${w}px`, ...hov });
          if (!t.summary && t.pct > 0 && t.pct < 100) bar.append(el("span", { class: "pct", style: `width:${t.pct}%` }));
          right.append(bar);
          if (o.zoom !== "yil") right.append(el("div", { class: "bar-label", style: `left:${X(t.start) + w + 6}px`, text: t.summary ? "" : (o.mode === "kutuphane" ? t.dept : userName(t.owner)) }));
        }
      }
      const row = el("div", { class: "g-row" + (t.summary ? " summary" : "") + (selected === t.id ? " sel" : ""), role: "row", tabindex: "0",
        onclick: () => { selected = t.id; render(); o.onSelect && o.onSelect(t); },
        onkeydown: ev => { if (ev.key === "Enter") { selected = t.id; render(); o.onSelect && o.onSelect(t); } } }, left, right);
      body.append(row);
    });

    // ızgara + bugün + oklar katmanı
    const H = rows.length * ROW_H;
    const leftW = 680;                            // .g-left genişliği (styles.css)
    const layer = el("div", { style: `position:absolute;top:0;height:${H}px;width:${W}px;pointer-events:none;z-index:1` });
    body.append(layer);
    requestAnimationFrame(() => {                 // gerçek sol sütun genişliği
      const lw = body.querySelector(".g-left")?.offsetWidth || leftW;
      layer.style.left = lw + "px";
    });
    for (const d of gridDays) layer.append(el("div", { class: "g-grid", style: `left:${X(d)}px` }));
    const td = todayDay();
    if (td >= minD && td <= maxD) layer.append(el("div", { class: "g-today", style: `left:${X(td)}px` }));

    const svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("class", "links");
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    const defs = document.createElementNS(SVGNS, "defs");
    for (const [idm, color] of [["arr", "var(--text-muted)"], ["arrc", "var(--critical)"]]) {
      const mk = document.createElementNS(SVGNS, "marker");
      mk.setAttribute("id", idm); mk.setAttribute("viewBox", "0 0 8 8"); mk.setAttribute("refX", "7"); mk.setAttribute("refY", "4");
      mk.setAttribute("markerWidth", "7"); mk.setAttribute("markerHeight", "7"); mk.setAttribute("orient", "auto-start-reverse");
      const p = document.createElementNS(SVGNS, "path");
      p.setAttribute("d", "M0,0 L8,4 L0,8 z"); p.setAttribute("style", "fill:" + color + ";stroke:none");
      mk.append(p); defs.append(mk);
    }
    svg.append(defs);
    for (const t of rows) {
      if (t.start == null) continue;
      for (const dep of t.deps) {
        const p = tasks.find(x => x.id === dep.id);
        if (!p || !pos.has(p.id) || p.start == null) continue;
        const y1 = pos.get(p.id) * ROW_H + ROW_H / 2, y2 = pos.get(t.id) * ROW_H + ROW_H / 2;
        const ss = dep.type === 2 || dep.type === 4;      // SS / SF: öncülün başından
        const ff = dep.type === 3 || dep.type === 4;      // FF / SF: ardılın sonuna
        const x1 = X(ss ? p.start : p.end) + (p.milestone && p.end === p.start ? 7 : 0);
        const x2 = X(ff ? t.end : t.start) - (t.milestone && t.end === t.start ? 8 : 0);
        let d;
        if (x2 - 10 >= x1 + 6) d = `M${x1},${y1} H${x2 - 10} V${y2} H${x2}`;
        else { const ym = y2 > y1 ? pos.get(t.id) * ROW_H : pos.get(t.id) * ROW_H + ROW_H; d = `M${x1},${y1} h6 V${ym} H${x2 - 10} V${y2} H${x2}`; }
        const path = document.createElementNS(SVGNS, "path");
        path.setAttribute("d", d);
        const crit = p.critical && t.critical;
        if (crit) path.setAttribute("class", "crit");
        path.setAttribute("marker-end", crit ? "url(#arrc)" : "url(#arr)");
        svg.append(path);
      }
    }
    layer.append(svg);

    clear(host).append(g);
    if (!rows.length) stateEmpty(host, "Görüntülenecek görev yok", "Bu görünümde görev bulunmuyor.");
  }

  return {
    setTasks(list) {
      tasks = list;
      roots = buildTree(tasks).roots;
      markCritical(tasks);
      render();
    },
    setZoom(z) { o.zoom = z; render(); },
    setBaseline(b) { o.showBaseline = b; render(); },
    collapseWhere(fn) { collapsed.clear(); tasks.filter(t => t.children.length && fn(t)).forEach(t => collapsed.add(t.id)); render(); },
    collapseAll(on) { collapsed.clear(); if (on) tasks.filter(t => t.children.length).forEach(t => collapsed.add(t.id)); render(); },
    select(id) { selected = id; render(); },
    scrollToToday() {
      const [minD] = range();
      const x = (todayDay() - minD) * ZOOM[o.zoom];
      host.scrollLeft = Math.max(0, x - host.clientWidth / 2);
    },
    rerender: render
  };
}
