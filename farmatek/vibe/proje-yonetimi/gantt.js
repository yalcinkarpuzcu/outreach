/* Proje Yönetimi — MS Project tarzı plan bileşeni: düzenlenebilir tablo + Gantt (bölücü, sürükle-bırak,
   bağ çizme, kritik yol, baseline, klavye gezinme). Satırlar: F faz (özet), G görev, K kilometre taşı. */
"use strict";

const ZOOM = { gun: 30, hafta: 12, ay: 4, ceyrek: 1.6, yil: 0.6 };
const ROW_H = 30;

function createPlan(host, opts) {
  const o = Object.assign({
    zoom: "ay", showBaseline: true, showCritical: true, refDay: null,
    columns: [], leftWidth: 760,
    canDrag: null, onDragEnd: null, onLink: null, onSelect: null, onOpen: null, onCellEdit: null, onKey: null,
    rowFilter: null, pending: null, labelFor: null, emptyText: "Görüntülenecek satır yok"
  }, opts || {});
  let roots = [], all = [], byId = new Map(), selected = null, suppressClick = false;
  const collapsed = new Set();
  const tip = el("div", { class: "tooltip", role: "tooltip", hidden: true });
  document.body.append(tip);
  host.classList.add("plan-host");
  host.style.setProperty("--lw", o.leftWidth + "px");
  host.tabIndex = -1;

  /* ── yardımcılar ────────────────────────────────────────────────── */
  const visible = t => !o.rowFilter || (t.children && t.children.length ? t.children.some(visible) || o.rowFilter(t, true) : o.rowFilter(t, false));
  function flatten() {
    const out = [];
    const walk = (t, depth) => {
      if (!visible(t)) return;
      t.depth = depth;
      out.push(t);
      if (t.children && !collapsed.has(t.id)) t.children.forEach(c => walk(c, depth + 1));
    };
    roots.forEach(r => walk(r, 0));
    return out;
  }
  function range() {
    const days = [];
    for (const t of all) {
      if (t.start != null) days.push(t.start);
      if (t.end != null) days.push(t.end);
      if (o.showBaseline && t.baseStart != null) days.push(t.baseStart, t.baseEnd ?? t.baseStart);
    }
    if (!days.length) { const t = o.refDay ?? todayDay(); return [t - 7, t + 90]; }
    const pad = Math.max(7, Math.round(30 / Math.max(ZOOM[o.zoom], .3)));
    return [Math.min(...days) - pad, Math.max(...days) + pad * 2];
  }
  const gridTemplate = () => o.columns.map(c => c.flex ? `minmax(${c.w}px,1fr)` : c.w + "px").join(" ");

  function scale(minD, maxD, ppd) {
    const sc = el("div", { class: "g-scale", style: "width:" + Math.ceil((maxD - minD) * ppd) + "px" });
    const a = el("div", { class: "row-a" }), b = el("div", { class: "row-b" });
    sc.append(a, b);
    const gridDays = [];
    const rel = o.refDay != null;
    if (o.zoom === "gun" || o.zoom === "hafta") {
      for (let d = minD; d <= maxD; d++) {
        const dt = dayToDate(d), x = (d - minD) * ppd;
        if (o.zoom === "gun") {
          if (dt.getUTCDay() === 1 || d === minD) a.append(el("div", { class: "tick major", style: `left:${x}px`, text: rel ? "Hafta " + Math.floor((d - o.refDay) / 7 + 1) : fmtDay(d) }));
          b.append(el("div", { class: "tick c" + ([0, 6].includes(dt.getUTCDay()) ? " we" : ""), style: `left:${x}px;width:${ppd}px`, text: GUNLER[dt.getUTCDay()].slice(0, 2) }));
          gridDays.push(d);
        } else {
          if (dt.getUTCDate() === 1 || d === minD) a.append(el("div", { class: "tick major", style: `left:${x}px`, text: rel ? "Ay " + (Math.floor((d - o.refDay) / 30) + 1) : AYLAR[dt.getUTCMonth()] + " " + dt.getUTCFullYear() }));
          if (dt.getUTCDay() === 1) { b.append(el("div", { class: "tick", style: `left:${x}px`, text: rel ? "G" + (d - o.refDay) : String(dt.getUTCDate()).padStart(2, "0") })); gridDays.push(d); }
        }
      }
      return { sc, gridDays };
    }
    let y = dayToDate(minD).getUTCFullYear(), m = dayToDate(minD).getUTCMonth();
    for (;;) {
      const d = Math.round(Date.UTC(y, m, 1) / 864e5);
      if (d > maxD) break;
      const x = Math.max(0, (d - minD) * ppd);
      const yi = rel ? y - dayToDate(o.refDay).getUTCFullYear() + 1 : 0;
      const yl = rel ? (yi >= 1 ? "Yıl " + yi : "") : String(y);
      if (o.zoom === "ay") {
        if (m === 0 || d <= minD) a.append(el("div", { class: "tick major", style: `left:${x}px`, text: yl }));
        if (m % 3 === 0 && m !== 0 && d > minD) a.append(el("div", { class: "tick", style: `left:${x}px`, text: "Ç" + (m / 3 + 1) }));
        const mi = rel ? (y - dayToDate(o.refDay).getUTCFullYear()) * 12 + m - dayToDate(o.refDay).getUTCMonth() + 1 : 0;
        b.append(el("div", { class: "tick", style: `left:${x}px`, text: rel ? (mi >= 1 ? "Ay " + mi : "") : AYLAR[m] }));
        gridDays.push(d);
      } else if (o.zoom === "ceyrek") {
        if (m === 0 || d <= minD) a.append(el("div", { class: "tick major", style: `left:${x}px`, text: yl }));
        if (m % 3 === 0) { b.append(el("div", { class: "tick", style: `left:${x}px`, text: "Ç" + (m / 3 + 1) })); gridDays.push(d); }
      } else {
        if (m === 0 || d <= minD) { a.append(el("div", { class: "tick major", style: `left:${x}px`, text: yl })); }
        if (m % 6 === 0) { b.append(el("div", { class: "tick", style: `left:${x}px`, text: m === 0 ? "Y1" : "Y2" })); gridDays.push(d); }
      }
      m++; if (m === 12) { m = 0; y++; }
    }
    return { sc, gridDays };
  }

  function barClass(t) { return "s-" + (DURUM_SINIF[t.status] || "bekle"); }
  function dateText(n) { return n == null ? "" : (o.refDay != null ? "Gün " + (n - o.refDay) : fmtDay(n)); }

  /* ── ipucu ──────────────────────────────────────────────────────── */
  function showTip(ev, t) {
    clear(tip);
    tip.append(el("b", { text: t.name }));
    const line = s => tip.append(el("div", { text: s }));
    line(t.kind === "K" ? "Hedef: " + dateText(t.start) : dateText(t.start) + " → " + dateText(t.end) + " · " + (t.end - t.start) + " gün");
    if (t.status) line("Durum: " + t.status + (t.kind === "G" ? " · %" + Math.round(t.pct || 0) : ""));
    if (t.summary) line("İlerleme: %" + Math.round(t.pct || 0));
    if (t.owner) line("Sorumlu: " + userName(t.owner));
    if (t.baseStart != null && o.showBaseline) line("Baseline: " + dateText(t.baseStart) + (t.kind !== "K" ? " → " + dateText(t.baseEnd) : "") + (t.variance ? " · sapma " + (t.variance > 0 ? "+" : "") + t.variance + " gün" : ""));
    if (t.critical && o.showCritical) line("⚠ Kritik yolda");
    if (t.deps && t.deps.length) line((t.kind === "K" ? "Bağlı görevler: " : "Öncüller: ") + t.deps.map(d => (byId.get(d.id)?.num ?? "?") + (d.type > 1 ? ["", "", "SS", "FF", "SF"][d.type] : "")).join("; "));
    tip.hidden = false;
    moveTip(ev);
  }
  function moveTip(ev) {
    const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(ev.clientX + pad, innerWidth - w - 8) + "px";
    tip.style.top = Math.min(ev.clientY + pad, innerHeight - h - 8) + "px";
  }
  function hideTip() { tip.hidden = true; }

  /* ── satır içi düzenleme ────────────────────────────────────────── */
  let editing = null, editTimer = null;
  function startEdit(t, col, cell) {
    if (!col.edit || !o.onCellEdit || (col.editable && !col.editable(t))) return false;
    const spec = typeof col.edit === "function" ? col.edit(t) : col.edit;
    if (!spec) return false;
    hideTip();
    let inp;
    const val = spec.get ? spec.get(t) : "";
    if (spec.type === "select") {
      inp = el("select", { class: "cell-in" }, ...(spec.options(t)).map(([vv, tx]) => el("option", { value: vv, text: tx, selected: String(vv) === String(val) || null })));
    } else if (spec.type === "user") {
      inp = userSelect(t.owner, "— atanmadı —");
      inp.className = "cell-in";
    } else {
      inp = el("input", { class: "cell-in", type: spec.type === "number" ? "number" : spec.type === "date" ? "date" : "text", value: val == null ? "" : String(val) });
      if (spec.type === "number") { inp.min = spec.min ?? "0"; if (spec.max != null) inp.max = spec.max; inp.step = "1"; }
    }
    inp.setAttribute("aria-label", col.title);
    clear(cell).append(inp);
    cell.classList.add("editing");
    editing = { t, col };
    let done = false;
    const finish = commit => {
      if (done) return; done = true; editing = null;
      const nv = inp.value;
      if (commit && String(nv) !== String(val ?? "")) o.onCellEdit(t, col.key, nv);
      else render();
      host.focus({ preventScroll: true });
    };
    inp.addEventListener("keydown", e => {
      e.stopPropagation();
      if (e.key === "Enter") { e.preventDefault(); finish(true); }
      else if (e.key === "Escape") { e.preventDefault(); finish(false); }
      else if (e.key === "Tab") { e.preventDefault(); finish(true); }
    });
    inp.addEventListener("blur", () => finish(true));
    if (spec.type === "select" || spec.type === "user") inp.addEventListener("change", () => finish(true));
    inp.addEventListener("click", e => e.stopPropagation());
    inp.addEventListener("mousedown", e => e.stopPropagation());
    requestAnimationFrame(() => { inp.focus(); if (inp.select && inp.type === "text") inp.select(); });
    return true;
  }

  /* ── çizim ──────────────────────────────────────────────────────── */
  let linkLayer = null;
  function render() {
    hideTip();
    if (editing) return;
    const keepX = host.scrollLeft, keepY = host.scrollTop;
    const rows = flatten();
    const [minD, maxD] = range();
    const ppd = ZOOM[o.zoom];
    const W = Math.ceil((maxD - minD) * ppd);
    const X = d => (d - minD) * ppd;
    const tpl = gridTemplate();
    const g = el("div", { class: "gantt", role: "grid", "aria-label": "Plan tablosu ve Gantt şeması", "aria-rowcount": String(rows.length) });

    const { sc, gridDays } = scale(minD, maxD, ppd);
    const headLeft = el("div", { class: "g-left", style: `grid-template-columns:${tpl}` }, ...o.columns.map(c => el("div", { class: "hc" + (c.cls ? " " + c.cls : ""), role: "columnheader", text: c.title, title: c.tip || c.title })));
    const split = el("div", { class: "g-split", title: "Tablo genişliğini değiştirmek için sürükleyin", role: "separator", "aria-orientation": "vertical" });
    headLeft.append(split);
    bindSplit(split);
    g.append(el("div", { class: "g-head" }, headLeft, el("div", { class: "g-right", style: `width:${W}px` }, sc)));

    const body = el("div", { class: "g-body" });
    g.append(body);
    const pos = new Map();
    rows.forEach((t, i) => pos.set(t.id, i));

    rows.forEach((t, i) => {
      const left = el("div", { class: "g-left", style: `grid-template-columns:${tpl}` });
      for (const col of o.columns) {
        const cell = el("div", { class: "c" + (col.cls ? " " + col.cls : "") + (col.edit && o.onCellEdit && (!col.editable || col.editable(t)) ? " ed" : ""), role: "gridcell" });
        if (col.key === "name") {
          cell.style.paddingInlineStart = (6 + t.depth * 16) + "px";
          if (t.children && t.children.length) {
            const exp = !collapsed.has(t.id);
            cell.append(el("button", { class: "caret", type: "button", "aria-expanded": exp ? "true" : "false", "aria-label": exp ? "Daralt" : "Genişlet", text: exp ? "▾" : "▸",
              onclick: ev => { ev.stopPropagation(); exp ? collapsed.add(t.id) : collapsed.delete(t.id); render(); } }));
          } else cell.append(el("span", { class: "caret-sp" }));
          if (t.kind === "K") cell.append(el("span", { class: "ms-ic", text: "◆" }));
          cell.append(el("span", { class: "nm", text: t.name, title: t.name }));
        } else {
          const r = col.render(t);
          if (r != null && r !== "") cell.append(r.nodeType ? r : document.createTextNode(String(r)));
        }
        cell.dataset.col = col.key;
        if (col.edit) {
          cell.addEventListener("click", ev => {
            if (selected !== t.id || suppressClick || ev.detail > 1) return;
            ev.stopPropagation();
            clearTimeout(editTimer);
            editTimer = setTimeout(() => startEdit(t, col, cell), 280);     // çift tık gelirse iptal edilir (ayrıntı açılır)
          });
        }
        left.append(cell);
      }

      const right = el("div", { class: "g-right", style: `width:${W}px` });
      if (t.start != null) {
        const hov = { onmouseenter: ev => showTip(ev, t), onmousemove: moveTip, onmouseleave: hideTip };
        const crit = o.showCritical && t.critical ? " crit" : "";
        if (o.showBaseline && t.baseStart != null && !t.summary) {
          if (t.kind === "K") right.append(el("div", { class: "base-ms", style: `left:${X(t.baseStart)}px`, title: "Baseline" }));
          else right.append(el("div", { class: "base", style: `left:${X(t.baseStart)}px;width:${Math.max(2, ((t.baseEnd ?? t.baseStart) - t.baseStart) * ppd)}px`, title: "Baseline" }));
        }
        const canDrag = !t.summary && o.canDrag && o.canDrag(t);
        const pend = o.pending && o.pending.has(t.id) ? " pend" : "";
        const lab = o.labelFor ? o.labelFor(t) : "";
        if (t.kind === "K") {
          const ms = el("div", { class: "ms " + barClass(t) + crit + (canDrag ? " drag" : "") + pend, style: `left:${X(t.start)}px`, ...hov });
          right.append(ms);
          if (canDrag) bindDrag(ms, t, ppd, X, true);
          right.append(el("div", { class: "bar-label ms-l", style: `left:${X(t.start) + 12}px`, text: (o.zoom === "yil" ? "" : (o.refDay != null ? "G" + (t.start - o.refDay) : fmtShort(t.start)) + "  ") + (lab || "") }));
        } else if (t.summary) {
          const w = Math.max(3, (t.end - t.start) * ppd);
          const bar = el("div", { class: "bar summary" + (t.kind === "P" ? " proj" : ""), style: `left:${X(t.start)}px;width:${w}px`, ...hov },
            el("span", { class: "sum-pct", style: `width:${Math.round(t.pct || 0)}%` }));
          right.append(bar);
          if (o.zoom !== "yil" && lab) right.append(el("div", { class: "bar-label", style: `left:${X(t.start) + w + 8}px`, text: lab }));
        } else {
          const w = Math.max(3, (t.end - t.start) * ppd);
          const bar = el("div", { class: "bar " + barClass(t) + crit + (canDrag ? " drag" : "") + pend, style: `left:${X(t.start)}px;width:${w}px`, ...hov });
          if (t.pct > 0) bar.append(el("span", { class: "pct", style: `width:${Math.min(100, t.pct)}%` }));
          if (canDrag) { bar.append(el("span", { class: "h-end", title: "Süreyi değiştirmek için sürükleyin" })); bindDrag(bar, t, ppd, X, false); }
          right.append(bar);
          if (canDrag && o.onLink) right.append(linkHandle(t, X(t.start) + w + 2));
          if (o.zoom !== "yil" && lab) right.append(el("div", { class: "bar-label", style: `left:${X(t.start) + w + (canDrag ? 16 : 6)}px`, text: lab }));
        }
      }
      const row = el("div", {
        class: "g-row k-" + t.kind + (t.summary ? " summary" : "") + (selected === t.id ? " sel" : "") + (o.pending && o.pending.has(t.id) ? " pend-row" : ""),
        role: "row", "aria-selected": selected === t.id ? "true" : "false", "data-id": t.id,
        onclick: () => { if (suppressClick) { suppressClick = false; return; } select(t.id, true); },
        ondblclick: () => { clearTimeout(editTimer); o.onOpen && o.onOpen(t); }
      }, left, right);
      body.append(row);
    });

    // ızgara + bugün + oklar katmanı
    const H = rows.length * ROW_H;
    const layer = el("div", { class: "g-layer", style: `height:${H}px;width:${W}px` });
    body.append(layer);
    for (const d of gridDays) layer.append(el("div", { class: "g-grid", style: `left:${X(d)}px` }));
    if (o.refDay == null) {
      const td = todayDay();
      if (td >= minD && td <= maxD) layer.append(el("div", { class: "g-today", style: `left:${X(td)}px`, title: "Bugün" }));
    }
    const s = svg("svg", { class: "links", width: W, height: H });
    const defs = svg("defs");
    for (const [idm, cls] of [["arr", "a-n"], ["arrc", "a-c"]]) {
      defs.append(svg("marker", { id: idm, viewBox: "0 0 8 8", refX: "7", refY: "4", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" },
        svg("path", { d: "M0,0 L8,4 L0,8 z", class: cls })));
    }
    s.append(defs);
    for (const t of rows) {
      if (t.start == null || !t.deps) continue;
      for (const dep of t.deps) {
        const p = byId.get(dep.id);
        if (!p || !pos.has(p.id) || p.start == null) continue;
        const y1 = pos.get(p.id) * ROW_H + ROW_H / 2, y2 = pos.get(t.id) * ROW_H + ROW_H / 2;
        const ss = dep.type === 2 || dep.type === 4, ff = dep.type === 3 || dep.type === 4;
        const x1 = X(ss ? p.start : p.end) + (p.kind === "K" ? 7 : 0);
        const x2 = X(ff ? t.end : t.start) - (t.kind === "K" ? 8 : 0);
        let d;
        if (x2 - 10 >= x1 + 6) d = `M${x1},${y1} H${x2 - 10} V${y2} H${x2}`;
        else { const ym = y2 > y1 ? pos.get(t.id) * ROW_H : pos.get(t.id) * ROW_H + ROW_H; d = `M${x1},${y1} h6 V${ym} H${x2 - 10} V${y2} H${x2}`; }
        const crit = o.showCritical && p.critical && t.critical;
        s.append(svg("path", { d, class: crit ? "crit" : null, "marker-end": crit ? "url(#arrc)" : "url(#arr)" }));
      }
    }
    layer.append(s);
    linkLayer = { layer, svg: s };
    clear(host).append(g);
    if (!rows.length) host.append(el("div", { class: "state slim" }, el("p", { text: o.emptyText })));
    host.scrollLeft = keepX; host.scrollTop = keepY;
  }

  /* ── bölücü ─────────────────────────────────────────────────────── */
  function bindSplit(h) {
    h.addEventListener("pointerdown", ev => {
      ev.preventDefault(); ev.stopPropagation();
      h.setPointerCapture(ev.pointerId);
      const x0 = ev.clientX, w0 = o.leftWidth;
      const min = o.columns.reduce((a, c) => a + (c.flex ? 120 : c.w), 0);
      const move = e => { o.leftWidth = Math.max(Math.min(min, 360), Math.min(innerWidth - 160, w0 + e.clientX - x0)); host.style.setProperty("--lw", o.leftWidth + "px"); };
      const up = () => { h.removeEventListener("pointermove", move); h.removeEventListener("pointerup", up); };
      h.addEventListener("pointermove", move);
      h.addEventListener("pointerup", up);
    });
  }

  /* ── sürükle-bırak: taşı / süre / bağ ─────────────────────────────── */
  function dragTip(ev, text) { clear(tip); tip.append(el("b", { text })); tip.hidden = false; moveTip(ev); }
  function bindDrag(node, t, ppd, X, isMs) {
    node.addEventListener("pointerdown", ev => {
      if (ev.button !== 0) return;
      ev.preventDefault(); ev.stopPropagation();
      const mode = !isMs && ev.target.classList.contains("h-end") ? "resize" : "move";
      const x0 = ev.clientX, left0 = X(t.start), w0 = (t.end - t.start) * ppd;
      let dd = 0;
      node.setPointerCapture(ev.pointerId);
      node.classList.add("dragging");
      const move = e => {
        dd = Math.round((e.clientX - x0) / ppd);
        if (mode === "move") {
          node.style.left = (left0 + dd * ppd) + "px";
          dragTip(e, isMs ? dateText(t.start + dd) + (dd ? "  (" + (dd > 0 ? "+" : "") + dd + " gün)" : "")
            : dateText(t.start + dd) + " → " + dateText(t.end + dd) + (dd ? "  (" + (dd > 0 ? "+" : "") + dd + " gün)" : ""));
        } else {
          dd = Math.max(dd, -(t.end - t.start));
          node.style.width = Math.max(3, w0 + dd * ppd) + "px";
          dragTip(e, "Süre: " + (t.end - t.start + dd) + " gün · bitiş " + dateText(t.end + dd));
        }
      };
      const up = () => {
        node.removeEventListener("pointermove", move);
        node.removeEventListener("pointerup", up);
        node.removeEventListener("pointercancel", up);
        node.classList.remove("dragging");
        hideTip();
        if (dd !== 0) {
          suppressClick = true;
          setTimeout(() => { suppressClick = false; }, 0);
          if (mode === "move") o.onDragEnd && o.onDragEnd(t, t.start + dd, t.end + dd);
          else o.onDragEnd && o.onDragEnd(t, t.start, t.end + dd);
        }
      };
      node.addEventListener("pointermove", move);
      node.addEventListener("pointerup", up);
      node.addEventListener("pointercancel", up);
    });
  }
  function linkHandle(t, x) {
    const h = el("span", { class: "h-link", style: `left:${x}px`, title: "Bağımlılık için başka bir görevin ya da kilometre taşının satırına sürükleyin" });
    h.addEventListener("pointerdown", ev => {
      if (ev.button !== 0 || !linkLayer) return;
      ev.preventDefault(); ev.stopPropagation();
      h.setPointerCapture(ev.pointerId);
      const lr0 = linkLayer.layer.getBoundingClientRect();
      const hr = h.getBoundingClientRect();
      const sx = hr.left + hr.width / 2 - lr0.left, sy = hr.top + hr.height / 2 - lr0.top;
      const line = svg("path", { class: "linking" });
      linkLayer.svg.append(line);
      let target = null, lastE = null;
      const auto = setInterval(() => {
        if (!lastE) return;
        const hr2 = host.getBoundingClientRect();
        let dy = 0, dx = 0;
        const bottom = Math.min(hr2.bottom, innerHeight), right = Math.min(hr2.right, innerWidth);
        if (lastE.clientY > bottom - 40) dy = 14; else if (lastE.clientY < Math.max(hr2.top, 0) + 70) dy = -14;
        if (lastE.clientX > right - 30) dx = 18;
        if (dy || dx) { host.scrollTop += dy; host.scrollLeft += dx; move(lastE); }
      }, 30);
      const move = e => {
        lastE = e;
        const lr = linkLayer.layer.getBoundingClientRect();
        line.setAttribute("d", `M${sx + lr0.left - lr.left},${sy + lr0.top - lr.top} L${e.clientX - lr.left},${e.clientY - lr.top}`);
        const under = document.elementFromPoint(e.clientX, e.clientY);
        const row = under && under.closest && under.closest(".g-row");
        host.querySelectorAll(".g-row.link-target").forEach(r => r.classList.remove("link-target"));
        const cand = row && byId.get(row.dataset.id);
        target = cand && cand.id !== t.id && !cand.summary ? cand.id : null;
        if (target) row.classList.add("link-target");
        dragTip(e, target ? "Bırakın: " + t.name + " → " + cand.name + (cand.kind === "K" ? " (kilometre taşına bağla)" : " (FS)") : "Ardıl görevin satırına sürükleyin");
      };
      const up = () => {
        clearInterval(auto);
        h.removeEventListener("pointermove", move);
        h.removeEventListener("pointerup", up);
        h.removeEventListener("pointercancel", up);
        line.remove(); hideTip();
        host.querySelectorAll(".g-row.link-target").forEach(r => r.classList.remove("link-target"));
        suppressClick = true;
        setTimeout(() => { suppressClick = false; }, 0);
        if (target) o.onLink && o.onLink(t.id, target);
      };
      h.addEventListener("pointermove", move);
      h.addEventListener("pointerup", up);
      h.addEventListener("pointercancel", up);
    });
    return h;
  }

  /* ── seçim ve klavye ────────────────────────────────────────────── */
  function select(id, fire) {
    selected = id;
    host.querySelectorAll(".g-row.sel").forEach(r => { r.classList.remove("sel"); r.setAttribute("aria-selected", "false"); });
    const row = host.querySelector(`.g-row[data-id="${CSS.escape(id || "")}"]`);
    if (row) { row.classList.add("sel"); row.setAttribute("aria-selected", "true"); }
    if (fire && o.onSelect) o.onSelect(byId.get(id) || null);
    host.focus({ preventScroll: true });
  }
  function ensureVisible(id) {
    const rows = flatten();
    const i = rows.findIndex(r => r.id === id);
    if (i < 0) return;
    const top = i * ROW_H, head = 52;
    if (top < host.scrollTop) host.scrollTop = top;
    else if (top + ROW_H + head > host.scrollTop + host.clientHeight) host.scrollTop = top + ROW_H + head - host.clientHeight;
  }
  host.addEventListener("keydown", e => {
    if (editing || e.target.closest("input,select,textarea")) return;
    const rows = flatten();
    const i = rows.findIndex(r => r.id === selected);
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const n = rows[Math.max(0, Math.min(rows.length - 1, (i < 0 ? 0 : i + (e.key === "ArrowDown" ? 1 : -1))))];
      if (n) { select(n.id, true); ensureVisible(n.id); }
    } else if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      const t = rows[i];
      if (t && t.children && t.children.length) { e.preventDefault(); e.key === "ArrowLeft" ? collapsed.add(t.id) : collapsed.delete(t.id); render(); select(t.id, false); }
    } else if (e.key === "F2" || e.key === "Enter") {
      const t = rows[i]; if (!t) return;
      e.preventDefault();
      if (e.key === "Enter") { o.onOpen && o.onOpen(t); return; }
      const cell = host.querySelector(`.g-row[data-id="${CSS.escape(t.id)}"] .c[data-col="name"]`);
      const col = o.columns.find(c => c.key === "name");
      if (cell && col) startEdit(t, col, cell);
    } else if (o.onKey) o.onKey(e, rows[i] || null);
  });

  return {
    setRows(rs) {
      roots = rs;
      all = [];
      const walk = t => { all.push(t); (t.children || []).forEach(walk); };
      roots.forEach(walk);
      byId = new Map(all.map(t => [t.id, t]));
      render();
    },
    render,
    setZoom(z) { o.zoom = z; render(); },
    setOption(k, val) { o[k] = val; render(); },
    collapseAll(on) { collapsed.clear(); if (on) all.filter(t => t.children && t.children.length).forEach(t => collapsed.add(t.id)); render(); },
    select(id) { if (id && byId.has(id)) { const p = all.find(x => x.children && x.children.some(c => c.id === id)); if (p) collapsed.delete(p.id); render(); select(id, false); ensureVisible(id); } },
    selected: () => byId.get(selected) || null,
    scrollToDay(d) {
      const [minD] = range();
      host.scrollLeft = Math.max(0, (d - minD) * ZOOM[o.zoom] - (host.clientWidth - o.leftWidth) / 3);
    },
    scrollToToday() { this.scrollToDay(o.refDay ?? todayDay()); },
    destroy() { tip.remove(); }
  };
}
