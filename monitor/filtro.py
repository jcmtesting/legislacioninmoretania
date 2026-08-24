"""
Filtrado de disposiciones del BOE por materia inmobiliaria.

Reglas (por orden de prioridad):
1. Ministerio de Vivienda (MIVAU): SIEMPRE se incluye, sin filtro de materia.
2. Resoluciones DGSJFP (dpto. Justicia, sección III): se incluyen si el título
   tiene contenido inmobiliario/registral.
3. Resto de departamentos: se incluye solo si el título contiene keywords
   inmobiliarias Y no cae en materias o territorios excluidos.
4. Territorio: se descartan normas de CCAA que no sean CLM o Madrid.
"""

import re

from . import config


def _norm(texto: str) -> str:
    return (texto or "").lower()


# Precompilar regex de siglas con límites de palabra
_SIGLAS_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in config.KEYWORDS_SIGLAS) + r")\b"
)


def es_departamento_vivienda(depto_nombre: str) -> bool:
    n = _norm(depto_nombre)
    return any(kw in n for kw in config.DEPTO_VIVIENDA_KEYWORDS)


def es_departamento_justicia(depto_nombre: str) -> bool:
    n = _norm(depto_nombre)
    return any(kw in n for kw in config.DEPTO_JUSTICIA_KEYWORDS)


def tiene_keyword_inmobiliaria(titulo: str) -> bool:
    n = _norm(titulo)
    # Frases largas: coincidencia por subcadena (seguras)
    if any(kw in n for kw in config.KEYWORDS_INMOBILIARIO):
        return True
    # Siglas cortas: coincidencia solo como palabra completa
    if _SIGLAS_RE.search(n):
        return True
    return False


def es_dgsjfp(titulo: str) -> bool:
    n = _norm(titulo)
    return (
        "seguridad jurídica y fe pública" in n
        or "dgsjfp" in n
        or ("registrador" in n and "recurso" in n)
        or ("nota de calificación" in n)
    )


def es_dgsjfp_mercantil(titulo: str) -> bool:
    """Detecta resoluciones DGSJFP de materia mercantil (registro mercantil,
    sociedades), que quedan fuera del ámbito inmobiliario."""
    n = _norm(titulo)
    mercantil = (
        "registro mercantil" in n
        or "registrador mercantil" in n
        or "registradora mercantil" in n
        or "mercantil y de bienes muebles" in n
        or "acuerdos sociales" in n
        or "sociedad de responsabilidad limitada" in n
        or "sociedad anónima" in n
        or "constitución de sociedad" in n
        or "cancelación de un asiento" in n
        or "hoja registral de la sociedad" in n
    )
    # Si es mercantil pero también toca finca/hipoteca/propiedad inmueble, se conserva
    inmueble = (
        "registrador de la propiedad" in n
        or "registradora de la propiedad" in n
        or "finca" in n
        or "hipotec" in n
        or "inmueble" in n
    )
    return mercantil and not inmueble


def es_materia_excluida(titulo: str) -> bool:
    n = _norm(titulo)
    return any(kw in n for kw in config.MATERIAS_EXCLUIDAS)


def es_departamento_excluido(depto_nombre: str) -> bool:
    """Departamentos cuyas licitaciones/anuncios no son de interés inmobiliario."""
    n = _norm(depto_nombre)
    return any(kw in n for kw in config.DEPARTAMENTOS_EXCLUIDOS)


def es_seccion_anuncios(sec_nombre: str) -> bool:
    """Sección V del BOE (anuncios y licitaciones)."""
    n = _norm(sec_nombre)
    return any(kw in n for kw in config.SECCION_ANUNCIOS_KEYWORDS)


def es_territorio_excluido(titulo: str, depto_nombre: str) -> bool:
    """
    Detecta si la norma proviene de una CCAA excluida.
    Solo se aplica a normativa autonómica: si menciona una CCAA incluida
    (CLM o Madrid), NO se excluye aunque también aparezca otra.
    """
    texto = _norm(titulo) + " " + _norm(depto_nombre)
    # Si menciona explícitamente CLM o Madrid, se conserva
    if any(cc in texto for cc in config.CCAA_INCLUIDAS):
        return False
    # Si menciona una CCAA excluida, se descarta
    return any(cc in texto for cc in config.CCAA_EXCLUIDAS)


def clasificar_item(sec_nombre, depto_nombre, epi_nombre, item) -> dict | None:
    """
    Decide si un item del BOE es relevante y a qué categoría pertenece.
    Devuelve un dict enriquecido con la categoría, o None si se descarta.

    Categorías: 'mivau', 'dgsjfp', 'estatal', 'clm', 'madrid'
    """
    titulo = item.get("titulo", "")
    identificador = item.get("identificador", "")

    # URLs
    url_html = item.get("url_html", "")
    url_pdf = item.get("url_pdf", {})
    if isinstance(url_pdf, dict):
        url_pdf = url_pdf.get("texto", "")

    base = {
        "identificador": identificador,
        "titulo": titulo,
        "seccion": sec_nombre,
        "departamento": depto_nombre,
        "epigrafe": epi_nombre,
        "url_html": url_html or f"https://www.boe.es/diario_boe/txt.php?id={identificador}",
        "url_pdf": url_pdf,
    }

    # ── Regla 1: MIVAU siempre entra (en cualquier sección, incluidos anuncios) ──
    if es_departamento_vivienda(depto_nombre):
        base["categoria"] = "mivau"
        return base

    # ── Departamentos excluidos (Defensa, Transportes, ADIF, AENA, CHs...) ──
    # Sus obras/licitaciones no son de interés inmobiliario.
    if es_departamento_excluido(depto_nombre):
        return None

    # ── Sección V (anuncios y licitaciones): solo se admite MIVAU ──
    # Como MIVAU ya retornó arriba, aquí se descarta todo lo demás de anuncios.
    if es_seccion_anuncios(sec_nombre):
        return None

    # ── Regla 4: territorio (aplica antes de incluir por materia) ──
    if es_territorio_excluido(titulo, depto_nombre):
        return None

    # ── Regla de exclusión de materias ──
    if es_materia_excluida(titulo):
        return None

    # ── Regla 2: resoluciones DGSJFP ──
    if es_departamento_justicia(depto_nombre) and es_dgsjfp(titulo):
        # Descartar resoluciones puramente mercantiles/societarias
        if es_dgsjfp_mercantil(titulo):
            return None
        if tiene_keyword_inmobiliaria(titulo) or "registrador de la propiedad" in _norm(titulo):
            base["categoria"] = "dgsjfp"
            return base
        return None

    # ── Regla 3: resto, solo si hay keyword inmobiliaria ──
    if tiene_keyword_inmobiliaria(titulo):
        texto = _norm(titulo) + " " + _norm(depto_nombre)
        if any(cc in texto for cc in ["castilla-la mancha", "castilla la mancha"]):
            base["categoria"] = "clm"
        elif "comunidad de madrid" in texto or "madrid" in texto:
            base["categoria"] = "madrid"
        else:
            base["categoria"] = "estatal"
        return base

    return None


def filtrar_sumario(items) -> list[dict]:
    """Aplica el filtro a todos los items de un sumario y devuelve los relevantes."""
    relevantes = []
    for sec, depto, epi, item in items:
        clasificado = clasificar_item(sec, depto, epi, item)
        if clasificado:
            relevantes.append(clasificado)
    return relevantes
