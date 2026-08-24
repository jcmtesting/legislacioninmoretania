"""
Generación del informe legislativo.

Toma las disposiciones ya filtradas (datos estructurados de la API del BOE)
y produce el informe en Markdown. La IA (API de Anthropic) se usa SOLO para
redactar resúmenes de las disposiciones relevantes, no para buscar ni decidir
qué incluir: eso ya lo hizo el filtro de forma determinista.
"""

import os
from datetime import date

import anthropic

MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def fecha_larga_es(f: date) -> str:
    return f"{f.day} de {MESES_ES[f.month]} de {f.year}"

# Orden y títulos de las secciones del informe
SECCIONES = [
    ("estatal", "🏛️ NORMATIVA ESTATAL"),
    ("mivau", "🏠 MINISTERIO DE VIVIENDA Y AGENDA URBANA (MIVAU)"),
    ("dgsjfp", "⚖️ RESOLUCIONES DGSJFP"),
    ("clm", "🏘️ CASTILLA-LA MANCHA"),
    ("madrid", "🏙️ COMUNIDAD DE MADRID"),
]


def _agrupar_por_categoria(disposiciones: list[dict]) -> dict[str, list[dict]]:
    grupos: dict[str, list[dict]] = {cat: [] for cat, _ in SECCIONES}
    for d in disposiciones:
        cat = d.get("categoria", "estatal")
        grupos.setdefault(cat, []).append(d)
    return grupos


def _resumir_con_ia(client, disposicion: dict) -> str:
    """
    Pide a la IA un resumen breve y objetivo de una disposición,
    a partir de su título. Sin buscar en la web: solo reformula y contextualiza.
    """
    prompt = (
        "Eres un asistente jurídico especializado en derecho inmobiliario español. "
        "A partir del título de esta disposición del BOE, redacta un resumen de UNA "
        "frase (máximo 30 palabras) explicando su relevancia inmobiliaria concreta. "
        "No inventes contenido que no esté implícito en el título. Sé objetivo y preciso.\n\n"
        f"Título: {disposicion['titulo']}\n\n"
        "Resumen:"
    )
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception as e:
        return f"(No se pudo generar resumen automático: {e})"


def _formatear_disposicion(d: dict, resumen: str) -> str:
    lineas = [
        f"▸ **{d['titulo']}**",
        f"  • Referencia: {d['identificador']}",
    ]
    if resumen:
        lineas.append(f"  • Relevancia: {resumen}")
    lineas.append(f"  • Enlace: {d['url_html']}")
    return "\n".join(lineas)


def generar_informe(
    disposiciones: list[dict],
    fecha_desde: date,
    fecha_hasta: date,
    dias_sin_boe: list[date],
    usar_ia: bool = True,
) -> tuple[str, list[dict], str]:
    """
    Genera el informe completo en Markdown.
    Devuelve (markdown, disposiciones_con_resumen, titulo_fecha).
    Las disposiciones se enriquecen in-place con la clave 'resumen'.
    """
    grupos = _agrupar_por_categoria(disposiciones)

    client = None
    if usar_ia and os.environ.get("ANTHROPIC_API_KEY"):
        client = anthropic.Anthropic()

    # Cabecera
    if fecha_desde == fecha_hasta:
        titulo_fecha = fecha_larga_es(fecha_desde)
    else:
        titulo_fecha = (
            f"{fecha_desde.strftime('%d/%m/%Y')} a {fecha_hasta.strftime('%d/%m/%Y')}"
        )

    out = [
        f"# 📅 MONITOR LEGISLATIVO INMOBILIARIO — {titulo_fecha}",
        "",
        "> Fuente primaria: **API oficial del BOE** (datos abiertos). "
        "Cobertura verificada de forma determinista.",
        "",
    ]

    # Secciones
    for cat, titulo in SECCIONES:
        out.append(f"\n## {titulo}\n")
        items = grupos.get(cat, [])
        if not items:
            out.append("_Sin novedades en materia inmobiliaria (verificado en el sumario del BOE)._")
            continue
        for d in items:
            resumen = _resumir_con_ia(client, d) if client else ""
            d["resumen"] = resumen  # enriquecer para el HTML
            out.append(_formatear_disposicion(d, resumen))
            out.append("")

    # Nota sobre días sin BOE
    if dias_sin_boe:
        dias_str = ", ".join(f.strftime("%d/%m") for f in dias_sin_boe)
        out.append(f"\n## ℹ️ Días sin BOE en el periodo\n")
        out.append(f"No se publicó BOE (festivo o domingo): {dias_str}.")

    # Pie
    out.append("\n---")
    out.append(
        "\n**Nota metodológica:** Este informe se genera consumiendo directamente "
        "la API de sumarios del BOE. La cobertura del BOE es completa y verificada. "
        "El DOCM (Castilla-La Mancha) y las fuentes de enriquecimiento doctrinal "
        "se tratan por separado, ya que no disponen de API equivalente."
    )

    return "\n".join(out), disposiciones, titulo_fecha
