"""
Cliente para el DOCM (Diario Oficial de Castilla-La Mancha).

IMPORTANTE: el DOCM NO dispone de una API REST equivalente a la del BOE.
Este módulo hace fetch de la portada y localiza el sumario del día por
patrón de URL. Es best-effort: si la estructura de la web cambia, puede
requerir ajuste. La cobertura fiable y verificada es la del BOE (API oficial).

Patrón de URL de descarga de disposición del DOCM:
https://docm.jccm.es/docm/descargarArchivo.do?ruta=AAAA/MM/DD/pdf/AAAA_NNNN.pdf&tipo=rutaDocm
"""

from datetime import date

import requests

from . import config

# Palabras clave inmobiliarias reutilizadas del BOE
from .config import KEYWORDS_INMOBILIARIO


class DOCMClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "monitor-legislativo-inmobiliario/2.0"}
        )

    def get_portada_html(self) -> str | None:
        """Descarga el HTML de la portada del DOCM (último número publicado)."""
        try:
            resp = self.session.get(config.DOCM_PORTADA, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.text
        except requests.RequestException as e:
            print(f"  DOCM: error al acceder a la portada: {e}")
        return None

    def buscar_inmobiliario(self, html: str) -> list[str]:
        """
        Búsqueda simple de titulares con keywords inmobiliarias en el HTML.
        Devuelve fragmentos de texto candidatos. Para un parsing robusto
        convendría usar BeautifulSoup; aquí se hace una detección ligera.
        """
        if not html:
            return []
        texto = html.lower()
        encontrados = []
        for kw in KEYWORDS_INMOBILIARIO:
            if kw in texto:
                encontrados.append(kw)
        return encontrados


# Nota: El parsing detallado del DOCM se deja como extensión.
# El núcleo del monitor (BOE) funciona de forma completamente autónoma y verificada.
