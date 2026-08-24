"""
Cliente de la API de sumarios del BOE.
Documentación: https://www.boe.es/datosabiertos/documentos/APIsumarioBOE.pdf

La API es REST, pública, sin autenticación. Método GET sobre HTTPS.
Endpoint: /datosabiertos/api/boe/sumario/{AAAAMMDD}
Devuelve el sumario del día en JSON (o XML si se pide).
"""

import time
from datetime import date, datetime, timedelta

import requests

from . import config


class BOEClient:
    """Cliente para consumir la API de sumarios del BOE."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_sumario(self, fecha: date) -> dict | None:
        """
        Obtiene el sumario del BOE para una fecha.
        Devuelve el dict del sumario, o None si no hay BOE ese día (404)
        o si falla la petición tras los reintentos.
        """
        fecha_str = fecha.strftime("%Y%m%d")
        url = f"{config.BOE_API_BASE}/{fecha_str}"

        for intento in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("data", {}).get("sumario")
                if resp.status_code == 404:
                    # No hay BOE ese día (festivo, domingo)
                    return None
                # Otros códigos: reintentar
                print(f"  BOE {fecha_str}: HTTP {resp.status_code} (intento {intento})")
            except (requests.RequestException, ValueError) as e:
                print(f"  BOE {fecha_str}: error {e} (intento {intento})")
            time.sleep(2 * intento)

        # Tras agotar reintentos, señalamos fallo (distinto de "no hay BOE")
        raise RuntimeError(f"No se pudo obtener el sumario del BOE del {fecha_str}")

    @staticmethod
    def iter_items(sumario: dict):
        """
        Recorre el sumario y produce tuplas:
        (seccion_nombre, departamento_nombre, epigrafe_nombre, item_dict)
        Aplana la estructura anidada de la API para facilitar el filtrado.
        """
        if not sumario:
            return

        diarios = sumario.get("diario", [])
        if isinstance(diarios, dict):
            diarios = [diarios]

        for diario in diarios:
            secciones = diario.get("seccion", [])
            if isinstance(secciones, dict):
                secciones = [secciones]

            for seccion in secciones:
                sec_nombre = seccion.get("nombre", "")
                departamentos = seccion.get("departamento", [])
                if isinstance(departamentos, dict):
                    departamentos = [departamentos]

                for depto in departamentos:
                    depto_nombre = depto.get("nombre", "")

                    # Los items pueden colgar directamente del departamento
                    # o dentro de epígrafes.
                    epigrafes = depto.get("epigrafe", [])
                    if isinstance(epigrafes, dict):
                        epigrafes = [epigrafes]

                    if epigrafes:
                        for epi in epigrafes:
                            epi_nombre = epi.get("nombre", "")
                            items = epi.get("item", [])
                            if isinstance(items, dict):
                                items = [items]
                            for item in items:
                                yield sec_nombre, depto_nombre, epi_nombre, item

                    # Items directos del departamento (secciones sin epígrafe)
                    items_directos = depto.get("item", [])
                    if isinstance(items_directos, dict):
                        items_directos = [items_directos]
                    for item in items_directos:
                        yield sec_nombre, depto_nombre, "", item

    def get_sumario_pdf_url(self, sumario: dict) -> str | None:
        """Extrae la URL del PDF del sumario completo del día."""
        if not sumario:
            return None
        diarios = sumario.get("diario", [])
        if isinstance(diarios, dict):
            diarios = [diarios]
        if diarios:
            sd = diarios[0].get("sumario_diario", {})
            url_pdf = sd.get("url_pdf", {})
            if isinstance(url_pdf, dict):
                return url_pdf.get("texto")
        return None


def rango_fechas(desde: date, hasta: date):
    """Genera todas las fechas entre desde y hasta (inclusive)."""
    actual = desde
    while actual <= hasta:
        yield actual
        actual += timedelta(days=1)
