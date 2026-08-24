"""
Test del filtro con un sumario simulado basado en la estructura real de la API
y en disposiciones reales que aparecieron durante la conversación.
"""

from monitor.boe_client import BOEClient
from monitor.filtro import filtrar_sumario

# Sumario simulado que imita la estructura de la API del BOE
# con casos reales vistos en la conversación (30/04/2026 y otros)
sumario_simulado = {
    "metadatos": {"publicacion": "BOE", "fecha_publicacion": "20260430"},
    "diario": [
        {
            "numero": "105",
            "sumario_diario": {
                "identificador": "BOE-S-2026-105",
                "url_pdf": {"texto": "https://www.boe.es/boe/dias/2026/04/30/pdfs/BOE-S-2026-105.pdf"},
            },
            "seccion": [
                {
                    "codigo": "1",
                    "nombre": "I. Disposiciones generales",
                    "departamento": [
                        {
                            "codigo": "9994",
                            "nombre": "MINISTERIO DE VIVIENDA Y AGENDA URBANA",
                            "epigrafe": [
                                {
                                    "nombre": "Ayudas",
                                    "item": {
                                        "identificador": "BOE-A-2026-9349",
                                        "titulo": "Orden VAU/403/2026, de 27 de abril, por la que se aprueban las bases reguladoras de la concesión de ayudas para actuaciones de conservación, restauración y rehabilitación de bienes inmuebles del Patrimonio Histórico Español.",
                                        "url_html": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-9349",
                                    },
                                }
                            ],
                        },
                        {
                            "codigo": "1111",
                            "nombre": "JEFATURA DEL ESTADO",
                            "epigrafe": [
                                {
                                    "nombre": "Medidas urgentes",
                                    "item": {
                                        "identificador": "BOE-A-2026-9286",
                                        "titulo": "Real Decreto-ley 10/2026, de 28 de abril, por el que se aprueban medidas tributarias urgentes en respuesta a los daños causados por la DANA, incluyendo beneficios en el IBI de municipios afectados.",
                                        "url_html": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-9286",
                                    },
                                }
                            ],
                        },
                    ],
                },
                {
                    "codigo": "3",
                    "nombre": "III. Otras disposiciones",
                    "departamento": [
                        {
                            "codigo": "2222",
                            "nombre": "MINISTERIO DE LA PRESIDENCIA, JUSTICIA Y RELACIONES CON LAS CORTES",
                            "item": [
                                {
                                    "identificador": "BOE-A-2026-11137",
                                    "titulo": "Resolución de 26 de enero de 2026, de la Dirección General de Seguridad Jurídica y Fe Pública, en el recurso interpuesto contra la nota de calificación de la registradora de la propiedad de Corralejo, por la que se suspende una escritura por falta de autoliquidación del IIVTNU.",
                                    "url_html": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-11137",
                                },
                                {
                                    "identificador": "BOE-A-2026-11143",
                                    "titulo": "Resolución de 12 de febrero de 2026, de la Dirección General de Seguridad Jurídica y Fe Pública, en el recurso interpuesto contra la calificación de la registradora mercantil de Valladolid, por la que se rechaza la cancelación de un asiento societario.",
                                    "url_html": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-11143",
                                },
                            ],
                        },
                        {
                            "codigo": "3333",
                            "nombre": "COMUNIDAD AUTÓNOMA DE LA RIOJA",
                            "item": {
                                "identificador": "BOE-A-2026-10117",
                                "titulo": "Ley 2/2026, de 28 de abril, de simplificación administrativa, mercado abierto y calidad normativa de La Rioja.",
                                "url_html": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-10117",
                            },
                        },
                        {
                            "codigo": "4444",
                            "nombre": "MINISTERIO DE TRABAJO Y ECONOMÍA SOCIAL",
                            "item": {
                                "identificador": "BOE-A-2026-10206",
                                "titulo": "Resolución de 29 de abril de 2026, por la que se publica la Adenda de prórroga del Convenio con la Comunidad de Madrid para el Registro de Empresas Acreditadas en el sector de la construcción.",
                                "url_html": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-10206",
                            },
                        },
                    ],
                },
                {
                    "codigo": "2B",
                    "nombre": "II.B. Oposiciones y concursos",
                    "departamento": [
                        {
                            "codigo": "5555",
                            "nombre": "ADMINISTRACIÓN LOCAL",
                            "item": {
                                "identificador": "BOE-A-2026-10364",
                                "titulo": "Resolución del Ayuntamiento de Manzanares (Ciudad Real) referente a la convocatoria para proveer una plaza de administrativo.",
                                "url_html": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-10364",
                            },
                        },
                    ],
                },
            ],
        }
    ],
}

client = BOEClient()
items = list(client.iter_items(sumario_simulado))
print(f"Total items en el sumario simulado: {len(items)}\n")

relevantes = filtrar_sumario(items)
print(f"Disposiciones relevantes tras filtro: {len(relevantes)}\n")

for r in relevantes:
    print(f"[{r['categoria'].upper()}] {r['identificador']}")
    print(f"    {r['titulo'][:90]}...")
    print()

print("\n─── VERIFICACIÓN DE CASOS ───")
ids = {r["identificador"]: r["categoria"] for r in relevantes}

casos = [
    ("BOE-A-2026-9349", "mivau", "Orden MIVAU ayudas rehabilitación"),
    ("BOE-A-2026-9286", "estatal", "RDL DANA con IBI"),
    ("BOE-A-2026-11137", "dgsjfp", "Resolución DGSJFP plusvalía"),
    ("BOE-A-2026-11143", None, "Resolución DGSJFP MERCANTIL (debe excluirse)"),
    ("BOE-A-2026-10117", None, "Ley de La Rioja (debe excluirse por territorio)"),
    ("BOE-A-2026-10206", "madrid", "Convenio REA construcción Madrid"),
    ("BOE-A-2026-10364", None, "Plaza ayuntamiento (debe excluirse)"),
]

todo_ok = True
for id_, esperado, desc in casos:
    real = ids.get(id_)
    ok = real == esperado
    todo_ok = todo_ok and ok
    estado = "✅" if ok else "❌"
    print(f"{estado} {desc}: esperado={esperado}, real={real}")

print("\n" + ("✅ TODOS LOS CASOS OK" if todo_ok else "❌ HAY FALLOS"))
