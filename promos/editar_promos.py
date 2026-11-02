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
.pd-caja h3 { margin: 6px 0 0; font-size: 13px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); font-weight: 700; }
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
# Ficha: debajo del ahorro, la mejor promo de hoy en la tienda más barata.
rep("""        ${ahorroTxt}
      </div>""", """        ${ahorroTxt}
        ${chipPromos(mejor.tienda)}
      </div>""")
# Cada tienda en la comparación.
rep("""        <span class="tt">${tt}</span></li>`;""", """        <span class="tt">${tt}</span>${chipPromos(o.tienda)}</li>`;""")
# Destacada.
rep("""          <div class="chico">en ${esc(tienda(v.mejor.tienda))}${antes}</div></div>""",
    """          <div class="chico">en ${esc(tienda(v.mejor.tienda))}${antes}</div>${chipPromos(v.mejor.tienda)}</div>""")
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
  // La mejor promo de hoy (mayor %, si no la de más cuotas) y cuántas más hay. Socios solo en el detalle.
  function chipPromos(t) {
    const ps = promosDe(t);
    if (!ps.length && !proximasDe(t).length) return "";
    const hoy = ps.filter(p => p.hoy && p.tipo !== "socios");
    const top = hoy.slice().sort((a, b) => (b.pct || 0) - (a.pct || 0) || (b.cuotas || 0) - (a.cuotas || 0))[0];
    let txt;
    const socios = ps.filter(p => p.tipo === "socios");
    if (!top && socios.length) txt = `${Math.max(...socios.map(p => p.pct || 0))}% para socios`;
    else if (!top) txt = "Ver promos";
    else if (top.tipo === "transferencia") txt = `${top.pct}% por transferencia`;
    else if (top.pct) txt = `Hoy ${top.pct}% con ${nombreBanco(top.banco)}`;
    else txt = `Hasta ${Math.max(...hoy.map(p => p.cuotas || 0))} cuotas sin interés`;
    const resto = ps.length + proximasDe(t).length - 1;
    const mas = resto > 0 ? ` <span class="mas">+${resto} más</span>` : "";
    return `<button type="button" class="promo-chip" data-promos="${esc(t)}" aria-label="Promos en ${esc(tienda(t))}: ${esc(txt)}">${TARJETA}<span>${esc(txt)}</span>${mas}</button>`;
  }
  function abrirPromos(t) {
    const ps = promosDe(t);
    const h = hoyAR();
    const li = (p) => `<li class="${p.hoy ? "hoy" : ""}"><b>${esc(promoTitulo(p))}</b>${promoDetalle(p) ? `<span>${esc(promoDetalle(p))}</span>` : ""}</li>`;
    const orden = (a, b) => (b.pct || 0) - (a.pct || 0) || (b.cuotas || 0) - (a.cuotas || 0);
    const hoy = ps.filter(p => p.hoy && p.tipo !== "socios").sort(orden);
    const otros = ps.filter(p => !p.hoy && p.tipo !== "socios").sort(orden);
    const socios = ps.filter(p => p.tipo === "socios");
    const proximas = proximasDe(t).sort((a, b) => a.desde.localeCompare(b.desde) || orden(a, b));
    const bloque = (tit, xs) => xs.length ? `<h3>${tit}</h3><ul class="pd-lista">${xs.map(li).join("")}</ul>` : "";
    $("promos-tit").textContent = tienda(t);
    $("promos-cuerpo").innerHTML = bloque(`Hoy, ${DIA_HOY[h.dia]}`, hoy) + bloque("Otros días", otros) + bloque("Próximamente", proximas) + bloque("Socios del club", socios);
    $("promos-dlg").showModal();
    ph("abrir_promos", { tienda: tienda(t), tienda_id: t, promos: ps.length, promos_hoy: hoy.length });
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
