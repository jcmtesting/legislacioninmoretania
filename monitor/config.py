"""
Configuración del monitor legislativo inmobiliario.
Define fuentes, departamentos y criterios de filtrado por materia inmobiliaria.
"""

# ─────────────────────────────────────────────────────────────
# API DEL BOE
# ─────────────────────────────────────────────────────────────
BOE_API_BASE = "https://boe.es/datosabiertos/api/boe/sumario"
# Formato de llamada: {BOE_API_BASE}/{AAAAMMDD}

# ─────────────────────────────────────────────────────────────
# DEPARTAMENTOS DE INTERÉS (filtrado por nombre, coincidencia flexible)
# ─────────────────────────────────────────────────────────────
# El Ministerio de Vivienda se incluye SIEMPRE, sin filtro de materia.
DEPTO_VIVIENDA_KEYWORDS = [
    "vivienda y agenda urbana",
    "ministerio de vivienda",
]

# El departamento de Justicia publica las resoluciones de la DGSJFP.
DEPTO_JUSTICIA_KEYWORDS = [
    "justicia",
    "presidencia, justicia",
]

# ─────────────────────────────────────────────────────────────
# PALABRAS CLAVE DE MATERIA INMOBILIARIA
# Para filtrar disposiciones del resto de departamentos.
# ─────────────────────────────────────────────────────────────
KEYWORDS_INMOBILIARIO = [
    # Registral / notarial
    "registro de la propiedad", "registrador", "calificación registral",
    "dgsjfp", "seguridad jurídica y fe pública", "hipotecari", "ley hipotecaria",
    "inmatriculación", "georreferenciación", "tracto sucesivo", "finca",
    "notario", "notarial", "escritura",
    # Propiedad / urbanismo
    "propiedad horizontal", "urbanismo", "urbanístic", "suelo", "edificación",
    "obra nueva", "segregación", "agrupación", "servidumbre", "usufructo",
    "declaración de obra", "licencia de obra", "cambio de uso",
    # Arrendamientos / vivienda
    "arrendamiento", "alquiler", "vivienda", "inquilino", "arrendador",
    "arrendaticia", "lau", "vivienda protegida", "vpo", "zona tensionada",
    "mercado residencial tensionado", "serpavi", "nrua", "alquiler turístico",
    "alquiler de corta duración", "vut", "vivienda de uso turístico",
    # Fiscalidad inmobiliaria
    "itp", "transmisiones patrimoniales", "actos jurídicos documentados", "ajd",
    "impuesto sobre bienes inmuebles", "ibi", "plusvalía municipal", "iivtnu",
    "impuesto sobre el incremento de valor de los terrenos",
    "rendimientos de capital inmobiliario", "ganancia patrimonial",
    "sucesiones y donaciones", "iva inmobiliario",
    # Otros
    "expropiación", "catastro", "rehabilitación", "plan estatal de vivienda",
    "registro de empresas acreditadas", "sector de la construcción",
    "arrendamientos urbanos", "arrendamientos rústicos",
]

# ─────────────────────────────────────────────────────────────
# EXCLUSIONES: territorios y materias fuera de alcance
# ─────────────────────────────────────────────────────────────
# Comunidades autónomas cuyas normas se DESCARTAN (foral + resto salvo CLM/Madrid).
CCAA_EXCLUIDAS = [
    "país vasco", "vasca", "navarra", "foral de navarra",
    "cataluña", "catalunya", "generalitat de catalu",
    "andalucía", "junta de andalucía",
    "comunitat valenciana", "valenciana", "generalitat valenciana",
    "galicia", "xunta", "aragón", "aragon", "principado de asturias",
    "cantabria", "la rioja", "región de murcia", "murcia",
    "extremadura", "islas baleares", "illes balears", "canarias",
    "castilla y león", "castilla y leon",
]

# Comunidades autónomas de interés (se incluyen).
CCAA_INCLUIDAS = [
    "castilla-la mancha", "castilla la mancha",
    "comunidad de madrid", "madrid",
]

# Materias que NUNCA se incluyen (aunque contengan alguna keyword suelta).
MATERIAS_EXCLUIDAS = [
    "plaza", "oposición", "oposiciones", "concurso de méritos",
    "provisión de puesto", "convocatoria de personal", "funcionario",
    "farmacéutic", "sanitari", "educación", "educativo", "militar",
    "defensa", "seguridad social", "pesca", "agricultura",
    "moneda", "colección", "condecoración", "medalla",
    "beca ", "deportiv", "jubilación",  # jubilaciones sin doctrina
]

# ─────────────────────────────────────────────────────────────
# DOCM (Diario Oficial de Castilla-La Mancha)
# ─────────────────────────────────────────────────────────────
# El DOCM no tiene API REST equivalente. Se accede por URL de portada/fecha.
DOCM_PORTADA = "https://docm.jccm.es/docm/"

# ─────────────────────────────────────────────────────────────
# FUENTES DE ENRIQUECIMIENTO DOCTRINAL (capa 2, best-effort)
# ─────────────────────────────────────────────────────────────
FUENTES_ENRIQUECIMIENTO = {
    "notariosyregistradores": "https://www.notariosyregistradores.com/web/",
    "regispro": "https://www.regispro.es/",
}
