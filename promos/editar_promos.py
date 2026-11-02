# Promos bancarias, de billeteras y cuotas en la página (1/11/2026).
#
# Uso:
#   python editar_promos.py vitrina_plantilla.html     (DESPUÉS de editar_clubes_orden.py y editar_categorias.py)
#   python editar_promos.py index.html
#
# La página carga promos.json de la rama "promos" del repo (lo actualiza todos los días la tarea de GitHub)
# y muestra, por tienda, la mejor promo de hoy y un botón con todas las promos y sus condiciones.
# Los precios no cambian: siguen siendo los de lista.
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
if "promos-dlg" in s:
    print("ya tenía las promos, no cambié nada")
    sys.exit()


def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:90])
    s = s.replace(old, new)


# ---------- CSS ----------
rep(""".d-precio { display: flex;""", """/* Promos bancarias por tienda */
.promo-chip {
  display: inline-flex; align-items: center; gap: 6px; max-width: 100%; cursor: pointer; text-align: left;
  background: none; border: 1px dashed var(--line); border-radius: 999px; color: var(--ink);
  font: inherit; font-size: 13px; font-weight: 600; padding: 4px 10px; line-height: 1.25;
}
.promo-chip:hover { border-color: var(--accent); color: var(--accent); }
.promo-chip svg { flex: none; color: var(--accent); }
.promo-chip .mas { color: var(--muted); font-weight: 500; white-space: nowrap; }
.lista .promo-chip { grid-column: 1 / -1; justify-self: start; font-size: 12.5px; padding: 3px 9px; margin-top: 2px; }
.d-precio .promo-chip { margin-top: 10px; font-size: 14px; }
dialog.promos-dlg {
  background: var(--surface); color: var(--ink); border: 1px solid var(--line); border-radius: 10px; padding: 0;
  width: min(520px, calc(100vw - 32px)); max-height: min(80vh, 760px); box-shadow: 0 24px 60px rgba(0,0,0,.6);
}
dialog.promos-dlg::backdrop { background: rgba(5,7,10,.72); }
.pd-caja { padding: 22px 22px 18px; position: relative; display: grid; gap: 12px; }
.pd-caja .eyebrow { margin: 0; }
.pd-caja h2 { margin: 0; padding-right: 28px; font-family: var(--display); font-weight: 800; font-size: 32px; line-height: .95; text-transform: uppercase; }
.pd-caja h4 { margin: 6px 0 0; font-size: 13px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); font-weight: 700; }
.pd-tienda { display: grid; gap: 8px; }
.pd-tienda + .pd-tienda { margin-top: 10px; padding-top: 14px; border-top: 2px solid var(--line); }
.pd-tn { margin: 0; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-family: var(--display); font-weight: 800; font-size: 26px; line-height: 1; text-transform: uppercase; }
.pd-tn span { color: var(--accent); font-variant-numeric: tabular-nums; }
.pd-lista { list-style: none; margin: 0; padding: 0; }
.pd-lista li { padding: 9px 0; border-top: 1px solid var(--line); display: grid; gap: 2px; }
.pd-lista b { font-weight: 700; }
.pd-lista span { font-size: 13.5px; color: var(--muted); }
.pd-lista li.hoy b { color: var(--accent); }
.pd-nota { margin: 4px 0 0; font-size: 13px; color: var(--muted); }
.promos-dlg .cerrar { position: absolute; top: 10px; right: 10px; background: none; border: 0; color: var(--muted); font-size: 18px; cursor: pointer; padding: 6px 8px; }
@media (max-width: 640px) {
  dialog.promos-dlg { margin: auto 0 0; width: 100%; max-width: 100%; max-height: 85vh; border-radius: 14px 14px 0 0; border-bottom: 0; }
  .pd-caja { padding-bottom: max(18px, env(safe-area-inset-bottom, 0px)); }
}
.d-precio { display: flex;""")

# ---------- HTML ----------
rep("""<footer>""", """<dialog class="promos-dlg" id="promos-dlg" aria-labelledby="promos-tit">
  <div class="pd-caja">
    <button type="button" class="cerrar" id="promos-cerrar" aria-label="Cerrar">✕</button>
    <p class="eyebrow">Promos y cuotas</p>
    <h2 id="promos-tit"></h2>
    <div id="promos-cuerpo"></div>
    <p class="pd-nota">Los precios de la página son de lista. Las promos dependen de tu banco o billetera y la tienda puede cambiarlas: revisá las condiciones antes de pagar.</p>
  </div>
</dialog>
<footer>""")

# ---------- JS: dónde se muestran ----------
# Ficha: debajo del ahorro, la mejor promo de hoy entre todas las tiendas que tienen esa camiseta.
rep("""        ${ahorroTxt}
      </div>""", """        ${ahorroTxt}
        ${chipPromos(ofs.filter(o => o.tiene))}
      </div>""")
# Cada tienda en la comparación.
rep("""        <span class="tt">${tt}</span></li>`;""", """        <span class="tt">${tt}</span>${chipPromos(o.tienda)}</li>`;""")
# Destacada.
rep("""          <div class="chico">en ${esc(tienda(v.mejor.tienda))}${antes}</div></div>""",
    """          <div class="chico">en ${esc(tienda(v.mejor.tienda))}${antes}</div>${chipPromos(v.ofs.filter(o => o.tiene))}</div>""")
# Pie.
rep("""Precios de lista de cada tienda, sin envío ni promociones bancarias.""",
    """Precios de lista de cada tienda, sin envío. Las promos bancarias y las cuotas se muestran aparte, por tienda.""")

# ---------- JS: promos ----------
rep("""  function pintar() {""", r"""  // ---------- promos bancarias ----------
  // promos.json lo genera promos/promos.py todos los días (tarea de GitHub, rama "promos").
  const PROMOS_URL = "https://raw.githubusercontent.com/enriquefox11-ai/el-vestuario/promos/promos.json";
  let PROMOS = {};
  const DIA_TXT = ["", "lunes", "martes", "miércoles", "jueves", "viernes", "sábados", "domingos"];
  const DIA_HOY = ["", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];
  const TARJETA = `<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><rect x="2.5" y="5" width="19" height="14" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M2.5 10h19" stroke="currentColor" stroke-width="2"/></svg>`;
  const hoyAR = () => { const d = new Date(Date.now() - 3 * 3600e3); return { iso: d.toISOString().slice(0, 10), dia: d.getUTCDay() || 7 }; };
  const listaY = (xs) => xs.length < 2 ? xs.join("") : xs.slice(0, -1).join(", ") + " y " + xs[xs.length - 1];
  const fechaCorta = (iso) => { const [, m, d] = iso.split("-"); return `${+d}/${+m}`; };
  function promosDe(t) {
    const h = hoyAR();
    return (PROMOS[t] || []).filter(p => (!p.desde || p.desde <= h.iso) && (!p.hasta || p.hasta >= h.iso))
      .map(p => ({ ...p, hoy: !(p.dias && p.dias.length) || p.dias.includes(h.dia) }));
  }
  // Las que empiezan en los próximos 7 días.
  function proximasDe(t) {
    const h = hoyAR();
    const tope = new Date(Date.parse(h.iso) + 7 * 864e5).toISOString().slice(0, 10);
    return (PROMOS[t] || []).filter(p => p.desde && p.desde > h.iso && p.desde <= tope);
  }
  const nombreBanco = (b) => /^Todos /.test(b) ? b.toLowerCase() : b;
  function promoTitulo(p) {
    if (p.tipo === "transferencia") return `${p.pct}% pagando por transferencia`;
    if (p.tipo === "socios") return `${p.pct}% para ${p.banco.toLowerCase()}`;
    const partes = [];
    if (p.pct) partes.push(`${p.pct}%`);
    if (p.cuotas) partes.push(`${p.cuotas} cuotas sin interés`);
    return partes.join(" y ") + (p.banco && p.banco !== "Varios" ? ` con ${nombreBanco(p.banco)}` : "");
  }
  function promoDetalle(p) {
    return [
      p.dias && p.dias.length && p.dias.length < 7 ? "los " + listaY(p.dias.map(d => DIA_TXT[d])) : "",
      p.tope, p.minimo, p.texto, p.medio && p.medio.toLowerCase() !== (p.banco || "").toLowerCase() ? p.medio : "",
      p.desde && p.desde > hoyAR().iso ? "desde el " + fechaCorta(p.desde) : "",
      p.hasta ? "hasta el " + fechaCorta(p.hasta) : ""
    ].filter(Boolean).map(x => x.charAt(0).toUpperCase() + x.slice(1)).join(" · ");
  }
  // Recibe una tienda (fila de la comparación) o las ofertas de una camiseta (tarjeta y destacada):
  // en ese caso junta las promos de todas sus tiendas, de la más barata a la más cara.
  function tiendasDe(x) {
    if (typeof x === "string") return [{ t: x }];
    const vistas = new Map();
    x.slice().sort((a, b) => a.precio - b.precio).forEach(o => { if (!vistas.has(o.tienda)) vistas.set(o.tienda, { t: o.tienda, precio: o.precio }); });
    return [...vistas.values()];
  }
  const orden = (a, b) => (b.pct || 0) - (a.pct || 0) || (b.cuotas || 0) - (a.cuotas || 0);
  // La mejor promo de hoy (mayor %, si no la de más cuotas) y cuántas más hay. Socios solo en el detalle.
  function chipPromos(x) {
    const ts = tiendasDe(x).filter(({ t }) => promosDe(t).length || proximasDe(t).length);
    if (!ts.length) return "";
    const todas = ts.flatMap(({ t }) => promosDe(t).map(p => ({ ...p, t })));
    const total = todas.length + ts.reduce((n, { t }) => n + proximasDe(t).length, 0);
    const hoy = todas.filter(p => p.hoy && p.tipo !== "socios");
    const top = hoy.slice().sort(orden)[0];
    const socios = todas.filter(p => p.tipo === "socios");
    // "en Dexter" solo si la promo no está en todas las tiendas de la camiseta.
    const donde = (p) => {
      const en = [...new Set(hoy.filter(q => promoTitulo(q) === promoTitulo(p)).map(q => q.t))];
      return ts.length > 1 && en.length < ts.length ? " en " + listaY(en.map(tienda)) : "";
    };
    let txt;
    if (!top && socios.length) txt = `${Math.max(...socios.map(p => p.pct || 0))}% para socios`;
    else if (!top) txt = "Ver promos";
    else if (top.tipo === "transferencia") txt = `${top.pct}% por transferencia${donde(top)}`;
    else if (top.pct) txt = `Hoy ${top.pct}% con ${nombreBanco(top.banco)}${donde(top)}`;
    else {
      const max = Math.max(...hoy.map(p => p.cuotas || 0));
      txt = `Hasta ${max} cuotas sin interés${donde(hoy.find(p => p.cuotas === max))}`;
    }
    const mas = total > 1 ? ` <span class="mas">+${total - 1} más</span>` : "";
    const dato = ts.map(({ t, precio }) => precio ? `${t}|${Math.round(precio)}` : t).join(",");
    const nombres = listaY(ts.map(({ t }) => tienda(t)));
    return `<button type="button" class="promo-chip" data-promos="${esc(dato)}" aria-label="Promos en ${esc(nombres)}: ${esc(txt)}">${TARJETA}<span>${esc(txt)}</span>${mas}</button>`;
  }
  function cuerpoTienda(t) {
    const h = hoyAR();
    const ps = promosDe(t);
    const li = (p) => `<li class="${p.hoy ? "hoy" : ""}"><b>${esc(promoTitulo(p))}</b>${promoDetalle(p) ? `<span>${esc(promoDetalle(p))}</span>` : ""}</li>`;
    const bloque = (tit, xs) => xs.length ? `<h4>${tit}</h4><ul class="pd-lista">${xs.map(li).join("")}</ul>` : "";
    const hoy = ps.filter(p => p.hoy && p.tipo !== "socios").sort(orden);
    const otros = ps.filter(p => !p.hoy && p.tipo !== "socios").sort(orden);
    const socios = ps.filter(p => p.tipo === "socios");
    const proximas = proximasDe(t).sort((a, b) => a.desde.localeCompare(b.desde) || orden(a, b));
    return bloque(`Hoy, ${DIA_HOY[h.dia]}`, hoy) + bloque("Otros días", otros) + bloque("Próximamente", proximas) + bloque("Socios del club", socios);
  }
  function abrirPromos(dato) {
    const ts = dato.split(",").map(x => { const [t, precio] = x.split("|"); return { t, precio: precio ? +precio : null }; })
      .filter(({ t }) => promosDe(t).length || proximasDe(t).length);
    if (!ts.length) return;
    if (ts.length === 1) {
      $("promos-tit").textContent = tienda(ts[0].t);
      $("promos-cuerpo").innerHTML = cuerpoTienda(ts[0].t);
    } else {
      $("promos-tit").textContent = `En ${ts.length} tiendas`;
      $("promos-cuerpo").innerHTML = ts.map(({ t, precio }) =>
        `<section class="pd-tienda"><h3 class="pd-tn">${esc(tienda(t))}${precio ? `<span>${plata(precio)}</span>` : ""}</h3>${cuerpoTienda(t)}</section>`).join("");
    }
    $("promos-dlg").showModal();
    $("promos-dlg").scrollTop = 0;
    ph("abrir_promos", { tiendas: ts.map(x => tienda(x.t)).join(", "), cantidad_tiendas: ts.length,
      promos: ts.reduce((n, { t }) => n + promosDe(t).length, 0) });
  }
  document.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-promos]");
    if (b) { e.stopPropagation(); abrirPromos(b.dataset.promos); }
  }, true);
  $("promos-cerrar").addEventListener("click", () => $("promos-dlg").close());
  $("promos-dlg").addEventListener("click", (e) => { if (e.target === $("promos-dlg")) $("promos-dlg").close(); });

  function pintar() {""")

# Cargar promos.json después de pintar la página (si falla, la página queda igual que antes).
rep("""  pintarControles();
  pintar();
  escribirHash();""", """  pintarControles();
  pintar();
  escribirHash();
  fetch(PROMOS_URL + "?d=" + hoyAR().iso).then(r => r.ok ? r.json() : null).then(j => {
    if (!j || !j.tiendas) return;
    PROMOS = Object.fromEntries(Object.entries(j.tiendas).map(([t, v]) => [t, v.promos || []]));
    pintar();
  }).catch(() => {});""")

open(p, "w", encoding="utf-8").write(s)
print("ok: promos agregadas")
