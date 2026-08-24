"""
Renderizado del informe a HTML con diseño de boletín jurídico.

Genera:
- Un HTML por cada informe (en informes/html/).
- Un index.html que lista todos los informes, apto para GitHub Pages.

Diseño: registro oficial. Tipografía con serif de referencia para titulares
(evoca el BOE), monoespaciada para las referencias BOE-A-XXXX, y una retícula
sobria con filete lateral por sección. Sin dependencias externas: todo el CSS
va embebido para que GitHub Pages lo sirva sin build.
"""

import html
import re
from datetime import date
from pathlib import Path

# Colores por categoría (filete lateral)
CAT_COLOR = {
    "estatal": "#8a1c1c",   # granate institucional
    "mivau": "#1c5a8a",     # azul vivienda
    "dgsjfp": "#5a3a8a",    # violeta registral
    "clm": "#8a6a1c",       # ocre CLM
    "madrid": "#1c7a5a",    # verde
}

CAT_ETIQUETA = {
    "estatal": "Estatal",
    "mivau": "MIVAU",
    "dgsjfp": "DGSJFP",
    "clm": "Castilla-La Mancha",
    "madrid": "Comunidad de Madrid",
}

SECCIONES_ORDEN = [
    ("estatal", "Normativa estatal"),
    ("mivau", "Ministerio de Vivienda y Agenda Urbana"),
    ("dgsjfp", "Resoluciones DGSJFP"),
    ("clm", "Castilla-La Mancha"),
    ("madrid", "Comunidad de Madrid"),
]

CSS = """
:root{
  --ink:#1a1815; --paper:#f7f5f0; --line:#d8d2c4; --muted:#6b6558;
  --estatal:#8a1c1c; --mivau:#1c5a8a; --dgsjfp:#5a3a8a; --clm:#8a6a1c; --madrid:#1c7a5a;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:Georgia,"Times New Roman",serif; line-height:1.55;
}
.wrap{max-width:820px; margin:0 auto; padding:2.5rem 1.4rem 4rem}
header.masthead{border-bottom:3px double var(--ink); padding-bottom:1.2rem; margin-bottom:2rem}
.eyebrow{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:.72rem;
  letter-spacing:.18em; text-transform:uppercase; color:var(--muted); margin:0 0 .5rem
}
h1.title{font-size:2rem; line-height:1.1; margin:.1rem 0 .3rem; font-weight:700}
.dateline{font-style:italic; color:var(--muted); font-size:1rem}
.method{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:.7rem;
  color:var(--muted); margin-top:.9rem; padding-top:.7rem; border-top:1px solid var(--line)
}
section.block{margin:2.2rem 0}
.block-head{display:flex; align-items:baseline; gap:.6rem; margin-bottom:.9rem}
.block-head .marker{
  font-family:ui-monospace,monospace; font-size:.7rem; letter-spacing:.1em;
  text-transform:uppercase; padding:.15rem .5rem; border-radius:2px;
  color:#fff; white-space:nowrap
}
.block-head h2{font-size:1.15rem; margin:0; font-weight:700}
.empty{color:var(--muted); font-style:italic; font-size:.95rem; padding:.3rem 0}
article.item{
  border-left:3px solid var(--line); padding:.4rem 0 .4rem 1rem; margin:0 0 1.2rem
}
article.item h3{font-size:1.02rem; margin:0 0 .4rem; font-weight:700; line-height:1.35}
.item .meta{font-family:ui-monospace,monospace; font-size:.72rem; color:var(--muted)}
.item .resumen{margin:.35rem 0 .45rem; font-size:.96rem}
.item a.ref{
  font-family:ui-monospace,monospace; font-size:.75rem; color:inherit;
  text-decoration:none; border-bottom:1px solid currentColor
}
.item a.ref:hover{opacity:.7}
footer.foot{
  margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--line);
  font-size:.8rem; color:var(--muted)
}
a{color:var(--estatal)}
/* Índice */
.index-list{list-style:none; padding:0; margin:1.5rem 0}
.index-list li{
  border-bottom:1px solid var(--line); padding:.9rem 0;
  display:flex; justify-content:space-between; align-items:baseline; gap:1rem
}
.index-list a{
  font-size:1.05rem; text-decoration:none; color:var(--ink); font-weight:700;
  border-bottom:1px solid transparent
}
.index-list a:hover{border-bottom-color:var(--ink)}
.index-list .count{
  font-family:ui-monospace,monospace; font-size:.72rem; color:var(--muted); white-space:nowrap
}
@media (max-width:520px){ h1.title{font-size:1.6rem} .wrap{padding:1.6rem 1rem 3rem} }
@media (prefers-reduced-motion:no-preference){
  article.item{transition:border-color .2s}
}
"""


def _esc(t: str) -> str:
    return html.escape(t or "")


def _item_html(d: dict) -> str:
    cat = d.get("categoria", "estatal")
    color = CAT_COLOR.get(cat, "#666")
    resumen = d.get("resumen", "")
    resumen_html = f'<p class="resumen">{_esc(resumen)}</p>' if resumen else ""
    return f"""
    <article class="item" style="border-left-color:{color}">
      <h3>{_esc(d['titulo'])}</h3>
      {resumen_html}
      <div class="meta">{_esc(d['identificador'])}</div>
      <a class="ref" href="{_esc(d['url_html'])}" style="color:{color}" target="_blank" rel="noopener">Ver en el BOE →</a>
    </article>"""


def render_informe_html(
    disposiciones: list[dict],
    fecha_desde: date,
    fecha_hasta: date,
    titulo_fecha: str,
) -> str:
    grupos: dict[str, list[dict]] = {cat: [] for cat, _ in SECCIONES_ORDEN}
    for d in disposiciones:
        grupos.setdefault(d.get("categoria", "estatal"), []).append(d)

    bloques = []
    for cat, nombre in SECCIONES_ORDEN:
        items = grupos.get(cat, [])
        color = CAT_COLOR.get(cat, "#666")
        etiqueta = CAT_ETIQUETA.get(cat, cat)
        cuerpo = (
            "".join(_item_html(d) for d in items)
            if items
            else '<p class="empty">Sin novedades en materia inmobiliaria '
            "(verificado en el sumario del BOE).</p>"
        )
        bloques.append(f"""
    <section class="block">
      <div class="block-head">
        <span class="marker" style="background:{color}">{_esc(etiqueta)}</span>
        <h2>{_esc(nombre)}</h2>
      </div>
      {cuerpo}
    </section>""")

    total = len(disposiciones)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitor Legislativo Inmobiliario — {_esc(titulo_fecha)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">Monitor Legislativo Inmobiliario</p>
    <h1 class="title">Novedades en materia inmobiliaria</h1>
    <p class="dateline">{_esc(titulo_fecha)} · {total} disposiciones</p>
    <p class="method">Fuente: API oficial del BOE · Normativa estatal y disposiciones de CLM/Madrid publicadas en BOE · Las disposiciones propias del DOCM se siguen por alerta oficial</p>
  </header>
  {''.join(bloques)}
  <footer class="foot">
    Generado automáticamente a partir de los datos abiertos del BOE.
    El DOCM y las fuentes doctrinales se tratan por separado.
  </footer>
</div>
</body>
</html>"""


def render_index_html(informes: list[dict]) -> str:
    """
    informes: lista de dicts con {archivo, titulo, total, fecha_orden}
    ordenada de más reciente a más antiguo.
    """
    filas = []
    for inf in informes:
        filas.append(f"""
      <li>
        <a href="{_esc(inf['archivo'])}">{_esc(inf['titulo'])}</a>
        <span class="count">{inf['total']} disp.</span>
      </li>""")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitor Legislativo Inmobiliario</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">Archivo de informes</p>
    <h1 class="title">Monitor Legislativo Inmobiliario</h1>
    <p class="dateline">Novedades legislativas en materia inmobiliaria · Estatal, Castilla-La Mancha y Comunidad de Madrid</p>
    <p class="method">Fuente primaria: API oficial de sumarios del BOE</p>
  </header>
  <ul class="index-list">{''.join(filas) if filas else '<li><span class="empty">Aún no hay informes generados.</span></li>'}</ul>
  <footer class="foot">
    Cada informe se genera consumiendo directamente la API de datos abiertos del BOE.
  </footer>
</div>
</body>
</html>"""
