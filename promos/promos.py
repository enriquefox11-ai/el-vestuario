# El Vestuario — promos bancarias, de billeteras y cuotas sin interés por tienda.
#
# Uso:  python promos/promos.py SALIDA.json [ANTERIOR.json]
#
# Lee las promos de cada tienda y escribe un JSON que la página carga aparte.
# Si una tienda no responde, se conservan sus promos de la corrida anterior (solo las que siguen vigentes).
# Las promos que no se pueden leer solas (transferencia, socios, algunas tiendas) están en promos/fijas.json.

import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

AR = dt.timezone(dt.timedelta(hours=-3))
HOY = dt.datetime.now(AR).date()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SES = requests.Session()
SES.headers.update({"User-Agent": UA, "Accept-Language": "es-AR,es;q=0.9"})

# Tiendas del grupo Dexter: misma página de métodos de pago.
SFCC = {
    "dexter": "https://www.dexter.com.ar/ayuda/metodos-de-pago.html",
    "stockcenter": "https://www.stockcenter.com.ar/ayuda/metodos-de-pago.html",
    "moov": "https://www.moov.com.ar/ayuda/metodos-de-pago.html",
}
# Seven Sport publica sus promos en un JSON (lo usa su propia página /promociones).
SEVEN_JSON = "https://script.google.com/macros/s/AKfycbzX6B8rjH0pRNCYPrnxmrPDfa9nqS7h0hUeYe2CEWszyGfJnx5EpdTwaENlZOp2ZUL-/exec"
KAPPA = "https://www.kappastore.com.ar/pages/promociones-bancarias"
# Tiendas VTEX: las cuotas sin interés vienen en el buscador de productos.
VTEX = {
    "onsports": "https://www.onsports.com.ar",
    "sporting": "https://www.sporting.com.ar",
    "sevensport": "https://www.sevensport.com.ar",
    "showsport": "https://www.showsport.com.ar",
    "atomik": "https://www.atomik.com.ar",
    "bocashop": "https://www.bocashop.com.ar",
    "tiendariver": "https://www.tiendariver.com",
}

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]  # 1..7 (ISO)
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

# Nombre del banco o billetera a partir de logos, ids y textos. El orden importa: bancos antes que billeteras
# ("bancociudadmodo" es Banco Ciudad pagando con MODO).
BANCOS = [
    ("galicia", "Galicia"), ("bbva", "BBVA"), ("santander", "Santander"), ("icbc", "ICBC"), ("macro", "Macro"),
    ("ciudad", "Banco Ciudad"), ("provincia", "Banco Provincia"), ("bapro", "Banco Provincia"), ("bco-prov", "Banco Provincia"),
    ("bancoprov", "Banco Provincia"), ("nacion", "Banco Nación"), ("patagonia", "Patagonia"), ("supervielle", "Supervielle"),
    ("comafi", "Comafi"), ("credicoop", "Credicoop"), ("hipotecario", "Hipotecario"), ("columbia", "Columbia"),
    ("corrientes", "Banco de Corrientes"), ("bonita", "Bonita"), ("naranja", "Naranja X"), ("mercado", "Mercado Pago"),
    ("-mp", "Mercado Pago"), ("modo", "MODO"), ("go-cuotas", "Go Cuotas"), ("gocuotas", "Go Cuotas"),
    ("transferencia", "Transferencia"),
]
# Marcas de tarjeta: solo se usan si no aparece ningún banco ni billetera.
MARCAS = [("visa", "Visa"), ("master", "Mastercard"), ("amex", "Amex"), ("american", "Amex"), ("cabal", "Cabal")]


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()


def banco_de(*textos):
    t = sin_tildes(" ".join(t or "" for t in textos)).replace("_", "-")
    if re.search(r"^mp\d|[^a-z]mp\d", t):
        return "Mercado Pago"
    for clave, nombre in BANCOS:
        if clave in t:
            return nombre
    if re.search(r"todos los bancos|todas las tarjetas|tarjetas bancarias", t):
        return "Todos los bancos"
    marcas = list(dict.fromkeys(n for c, n in MARCAS if c in t))
    if not marcas:
        return None
    return marcas[0] if len(marcas) == 1 else ", ".join(marcas[:-1]) + " y " + marcas[-1]


def dias_de(texto):
    """[1..7] con los días nombrados; [] = todos los días."""
    t = sin_tildes(texto)
    if re.search(r"todos los dias|todos\b(?! los (lunes|martes|miercoles|jueves|viernes|sabado|domingo))", t) and not any(
            re.search(rf"\b{d}", t) for d in DIAS):
        return []
    return [i + 1 for i, d in enumerate(DIAS) if re.search(rf"\b{d}", t)]


def _fecha(d, m, a=None):
    a = int(a) if a else HOY.year
    if a < 100:
        a += 2000
    try:
        return dt.date(a, int(m), int(d))
    except ValueError:
        return None


def vigencia(texto):
    """Devuelve (desde, hasta, entendida). hasta=None con entendida=True significa 'hasta nuevo aviso'."""
    t = sin_tildes(texto)
    fechas = [_fecha(*m) for m in re.findall(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", t)]
    if not fechas:
        fechas = [_fecha(*m) for m in re.findall(r"\b(\d{1,2})/(\d{1,2})\b(?!/)", t)]
    if not fechas:
        # "del 2 al 4 de noviembre"  /  "02 al 04 de noviembre"  /  "4 y 5 de noviembre"
        m = re.search(r"(\d{1,2})\s*(?:al|y|-)\s*(\d{1,2})\s*de\s*(" + "|".join(MESES) + r")(?:\s*(?:de)?\s*(\d{4}))?", t)
        if m:
            mes = MESES.index(m.group(3)) + 1
            fechas = [_fecha(m.group(1), mes, m.group(4)), _fecha(m.group(2), mes, m.group(4))]
    fechas = [f for f in fechas if f]
    nuevo_aviso = "nuevo aviso" in t
    if not fechas:
        return None, None, nuevo_aviso
    if len(fechas) == 1:
        if re.search(r"(hasta|al)\s*(el\s*)?\d", t):
            return None, fechas[0], True
        return fechas[0], None, True
    desde, hasta = fechas[0], fechas[-1]
    if hasta < desde:  # error de tipeo en el año ("al 05/11/2023")
        try:
            hasta = hasta.replace(year=desde.year)
        except ValueError:
            pass
        if hasta < desde:
            return None, None, False
    return desde, hasta, True


def pct_de(texto):
    ns = [int(n) for n in re.findall(r"(\d{1,2})\s*%", texto or "")]
    return max(ns) if ns else None


def cuotas_de(texto):
    """Máximo de cuotas sin interés mencionado. Si el texto no dice 'sin interés', no cuenta."""
    t = sin_tildes(texto)
    if not re.search(r"sin\s*int|s/i|\bcsi\b", t):
        return None
    t = re.sub(r"\$\s*[\d.]+", " ", t)  # montos mínimos
    t = re.sub(r"plan z\s*\d+", " ", t)
    ns = [int(n) for n in re.findall(r"\b(\d{1,2})\b(?!\s*%)", t) if 2 <= int(n) <= 24]
    return max(ns) if ns else None


def tope_de(texto):
    t = sin_tildes(texto)
    if "sin tope" in t:
        return "sin tope"
    m = re.search(r"\$\s*([\d.]+)", texto or "")
    if not m:
        return None
    mensual = " por mes" if re.search(r"mes|mensual", t) else ""
    return f"tope ${m.group(1)}{mensual}"


def promo(banco, *, pct=None, cuotas=None, dias=None, desde=None, hasta=None, tope=None, medio=None, tipo=None, texto=None, minimo=None):
    if not pct and not cuotas:
        return None
    if tipo is None:
        tipo = "transferencia" if banco == "Transferencia" else ("descuento" if pct else "cuotas")
    p = {"tipo": tipo, "banco": banco or "Varios", "pct": pct, "cuotas": cuotas, "dias": dias or [],
         "desde": desde.isoformat() if desde else None, "hasta": hasta.isoformat() if hasta else None,
         "tope": tope, "minimo": minimo, "medio": medio, "texto": texto}
    return {k: v for k, v in p.items() if v not in (None, "")}


def vigente(p):
    if p.get("hasta") and p["hasta"] < HOY.isoformat():
        return False
    return True


# ---------- lectores ----------

def leer_sfcc(html):
    sopa = BeautifulSoup(html, "html.parser")
    vistos, out = set(), []
    for a in sopa.select('[data-target^="#paymentMethodModal"]'):
        mid = a["data-target"][1:]
        if mid in vistos:
            continue
        vistos.add(mid)
        modal = sopa.find(id=mid)
        if not modal:
            continue
        caja = a.find_parent(class_="paymentMethod-component-container") or a.parent
        etiqueta = (caja.select_one(".img-text") or caja).get_text(" ", strip=True) if caja else ""
        img = modal.select_one(".modal-body img")
        logo = (img.get("src") or "").split("/")[-1].split("?")[0] if img else ""
        campos = {}
        for p in modal.select(".modal-body p"):
            m = re.match(r"\s*([^:]{3,30}):\s*(.*)", p.get_text(" ", strip=True))
            if m:
                campos[sin_tildes(m.group(1)).strip()] = m.group(2).strip()
        vig = campos.get("vigencia", "")
        desde, hasta, ok = vigencia(vig)
        if not (desde or hasta or ok):
            desde, hasta, ok = vigencia(etiqueta)
        if not (desde or hasta or ok):
            continue  # sin fecha entendible: no se muestra
        medios = campos.get("medios de pago", "")
        ben = campos.get("beneficio", "")
        cuo = campos.get("cuotas", "")
        p = promo(banco_de(logo, mid, medios, cuo), pct=pct_de(ben), cuotas=cuotas_de(cuo),
                  dias=dias_de(vig + " " + etiqueta), desde=desde, hasta=hasta,
                  tope=tope_de(campos.get("tope de reintegro") or campos.get("tope") or ""),
                  minimo=_minimo(campos.get("minimo de compra", "")), medio=_corto(medios))
        if p:
            out.append(p)
    return out


def _minimo(txt):
    m = re.search(r"\$\s*([\d.]+)", txt or "")
    return f"desde ${m.group(1)}" if m else None


def _corto(txt, n=90):
    txt = re.sub(r"\s+", " ", (txt or "").split("|")[0]).strip(" .")
    return txt if len(txt) <= n else txt[:n].rsplit(" ", 1)[0] + "…"


def leer_seven(datos):
    datos = datos if isinstance(datos, list) else [datos]
    out = []
    for a in datos:
        if not set(a.get("banners") or []) & {"TODOS", "SEVEN"}:
            continue
        if not (a.get("config") or {}).get("isVisible", True):
            continue
        f = a.get("fechas") or {}
        desde = _iso_ar(f.get("inicio"))
        hasta = _iso_ar(f.get("fin"))
        nombre = re.sub(r"\s+", " ", a.get("nombre") or "")
        bancos = a.get("bancos") or []
        banco = banco_de(" ".join(bancos)) or (bancos[0] if bancos else None)
        ben = " / ".join(a.get("beneficios") or [])
        dias = [] if not a.get("dias") or "TODOS" in a["dias"] else dias_de(" ".join(a["dias"]))
        p = promo(banco, pct=pct_de(nombre), cuotas=cuotas_de(nombre), dias=dias, desde=desde, hasta=hasta,
                  tope=tope_de(ben) if "tope" in sin_tildes(ben) else None, minimo=_minimo(ben) if "minimo" in sin_tildes(ben) else None,
                  medio=_corto(" y ".join(a.get("mediosDePago") or []).capitalize()))
        if p:
            out.append(p)
    return out


def _iso_ar(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(AR).date()
    except ValueError:
        return None


def leer_kappa(html):
    sopa = BeautifulSoup(html, "html.parser")
    out = []
    for c in sopa.select(".promociones-bancarias__card"):
        img = c.select_one("img")
        logo = " ".join([(img.get("alt") or ""), (img.get("src") or "").split("/")[-1].split("?")[0]]) if img else ""
        desc_el = c.select_one(".promociones-bancarias__card-descripcion")
        desc = desc_el.get_text(" ", strip=True) if desc_el else ""
        leg = " ".join(x.get_text(" ", strip=True) for x in c.select(".collapsible__content"))
        desde, hasta, _ = vigencia(leg)
        p = promo(banco_de(logo, desc), pct=pct_de(desc), cuotas=cuotas_de(desc), dias=dias_de(desc),
                  desde=desde, hasta=hasta, tope=tope_de(leg) if "$" in leg else None,
                  minimo=_minimo(desc) if "desde $" in desc.lower() else None, texto=_corto(desc, 120))
        if p:
            out.append(p)
    return out


TARJETAS = {"Visa": "Visa y Mastercard", "Mastercard": "Visa y Mastercard", "American Express": "American Express",
            "Naranja": "Naranja X", "Cabal": "Cabal", "Diners": "Diners"}


def leer_vtex(productos):
    """Cuotas sin interés por tarjeta (el máximo entre las camisetas con stock) y descuento por transferencia."""
    maximo, transf = {}, None
    for p in productos:
        for it in p.get("items", []):
            for s in it.get("sellers", [])[:1]:
                of = s.get("commertialOffer") or {}
                if not of.get("AvailableQuantity"):
                    continue
                for c in of.get("Installments") or []:
                    nom = c.get("PaymentSystemName") or ""
                    if "transf" in nom.lower() and pct_de(nom):
                        transf = pct_de(nom)
                    if c.get("InterestRate") == 0 and c.get("NumberOfInstallments", 0) > 1 and nom in TARJETAS:
                        g = TARJETAS[nom]
                        maximo[g] = max(maximo.get(g, 0), c["NumberOfInstallments"])
    out = [promo(g, cuotas=n, tipo="cuotas", texto="según el monto de la compra") for g, n in maximo.items()]
    if transf:
        out.append(promo("Transferencia", pct=transf))
    return [p for p in out if p]


# ---------- corrida ----------

def bajar(url, **kw):
    r = SES.get(url, timeout=30, **kw)
    r.raise_for_status()
    return r


def correr(anterior):
    res, errores = {}, {}

    def guardar(t, ps, fuente):
        res.setdefault(t, []).extend(dict(p, fuente=fuente) for p in ps if vigente(p))

    for t, url in SFCC.items():
        try:
            guardar(t, leer_sfcc(bajar(url).text), "auto")
        except Exception as e:  # noqa: BLE001
            errores[t] = str(e)[:200]
    try:
        guardar("sevensport", leer_seven(bajar(SEVEN_JSON).json()), "auto")
    except Exception as e:  # noqa: BLE001
        errores["sevensport"] = str(e)[:200]
    try:
        guardar("kappastore", leer_kappa(bajar(KAPPA).text), "auto")
    except Exception as e:  # noqa: BLE001
        errores["kappastore"] = str(e)[:200]
    for t, base in VTEX.items():
        try:
            prods = bajar(base + "/api/catalog_system/pub/products/search", params={"ft": "camiseta", "_from": 0, "_to": 29}).json()
            guardar(t, leer_vtex(prods), "auto-cuotas")
        except Exception as e:  # noqa: BLE001
            errores[t + ":cuotas"] = str(e)[:200]

    # Si una tienda falló, se usan sus promos anteriores que sigan vigentes.
    for clave in errores:
        t = clave.split(":")[0]
        previas = [p for p in (anterior.get("tiendas", {}).get(t, {}).get("promos", []))
                   if p.get("fuente", "").startswith("auto") and vigente(p)]
        if clave.endswith(":cuotas"):
            previas = [p for p in previas if p.get("fuente") == "auto-cuotas"]
        else:
            previas = [p for p in previas if p.get("fuente") == "auto"]
        res.setdefault(t, []).extend(previas)

    # Promos cargadas a mano. "reemplaza_cuotas" saca las cuotas automáticas de esa tienda (p. ej. solo con BBVA).
    fijas = json.loads((Path(__file__).parent / "fijas.json").read_text(encoding="utf-8"))
    for t, info in fijas["tiendas"].items():
        if info.get("reemplaza_cuotas"):
            res[t] = [p for p in res.get(t, []) if p.get("fuente") != "auto-cuotas"]
        for p in info.get("promos", []):
            p = {k: v for k, v in p.items() if not k.startswith("_")}
            if vigente(p):
                res.setdefault(t, []).append(dict(p, fuente="manual"))

    tiendas = {}
    for t, ps in res.items():
        if not ps:
            continue
        unicas, vistas = [], set()
        for p in ps:
            k = json.dumps({k: v for k, v in p.items() if k != "fuente"}, sort_keys=True, ensure_ascii=False)
            if k not in vistas:
                vistas.add(k)
                unicas.append(p)
        unicas.sort(key=lambda p: (-(p.get("pct") or 0), -(p.get("cuotas") or 0)))
        tiendas[t] = {"promos": unicas}
    return {"generado": dt.datetime.now(AR).isoformat(timespec="minutes"), "tiendas": tiendas, "errores": errores}


if __name__ == "__main__":
    salida = Path(sys.argv[1])
    anterior = {}
    if len(sys.argv) > 2 and Path(sys.argv[2]).exists():
        try:
            anterior = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        except ValueError:
            pass
    datos = correr(anterior)
    salida.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v["promos"]) for v in datos["tiendas"].values())
    print(f"{n} promos en {len(datos['tiendas'])} tiendas")
    for t, e in datos["errores"].items():
        print(f"  ! {t}: {e}")
