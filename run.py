#!/usr/bin/env python3
"""
Monitor Legislativo Inmobiliario — punto de entrada.

Uso:
    python run.py                    # Informe de hoy
    python run.py --fecha 2026-04-30 # Informe de un día concreto
    python run.py --desde 2026-05-01 --hasta 2026-05-15  # Rango
    python run.py --dias 7           # Últimos 7 días

Requiere la variable de entorno ANTHROPIC_API_KEY para los resúmenes con IA
(opcional: con --sin-ia se omite y solo se listan los títulos).
"""

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from monitor.boe_client import BOEClient, rango_fechas
from monitor.filtro import filtrar_sumario
from monitor.informe import generar_informe
from monitor.html_render import render_informe_html, render_index_html


def parse_args():
    p = argparse.ArgumentParser(description="Monitor legislativo inmobiliario (API BOE)")
    p.add_argument("--fecha", help="Fecha concreta AAAA-MM-DD (por defecto: hoy)")
    p.add_argument("--desde", help="Inicio de rango AAAA-MM-DD")
    p.add_argument("--hasta", help="Fin de rango AAAA-MM-DD")
    p.add_argument("--dias", type=int, help="Últimos N días hasta hoy")
    p.add_argument("--sin-ia", action="store_true", help="No usar IA para resúmenes")
    p.add_argument("--salida", help="Ruta del archivo de salida .md")
    return p.parse_args()


def resolver_rango(args) -> tuple[date, date]:
    hoy = date.today()
    if args.desde and args.hasta:
        return (
            datetime.strptime(args.desde, "%Y-%m-%d").date(),
            datetime.strptime(args.hasta, "%Y-%m-%d").date(),
        )
    if args.dias:
        return hoy - timedelta(days=args.dias - 1), hoy
    if args.fecha:
        f = datetime.strptime(args.fecha, "%Y-%m-%d").date()
        return f, f
    return hoy, hoy


def main():
    args = parse_args()
    desde, hasta = resolver_rango(args)

    print(f"🔍 Monitor BOE: {desde} → {hasta}")

    client = BOEClient()
    todas_disposiciones = []
    dias_sin_boe = []

    for fecha in rango_fechas(desde, hasta):
        try:
            sumario = client.get_sumario(fecha)
        except RuntimeError as e:
            print(f"  ⚠️  {e}")
            continue

        if sumario is None:
            dias_sin_boe.append(fecha)
            print(f"  {fecha}: sin BOE (festivo/domingo)")
            continue

        items = client.iter_items(sumario)
        relevantes = filtrar_sumario(items)
        print(f"  {fecha}: {len(relevantes)} disposiciones inmobiliarias")
        todas_disposiciones.extend(relevantes)

    # Deduplicar por identificador
    vistos = set()
    unicas = []
    for d in todas_disposiciones:
        if d["identificador"] not in vistos:
            vistos.add(d["identificador"])
            unicas.append(d)

    print(f"\n📊 Total: {len(unicas)} disposiciones inmobiliarias únicas")

    informe_md, disposiciones_con_resumen, titulo_fecha = generar_informe(
        unicas, desde, hasta, dias_sin_boe, usar_ia=not args.sin_ia
    )

    base = Path(__file__).parent
    reports = base / "informes"
    reports.mkdir(exist_ok=True)
    docs = base / "docs"          # GitHub Pages sirve desde /docs
    docs.mkdir(exist_ok=True)

    # Nombre base del informe
    if desde == hasta:
        slug = f"monitor-{desde.strftime('%Y-%m-%d')}"
    else:
        slug = f"monitor-{desde.strftime('%Y-%m-%d')}_a_{hasta.strftime('%Y-%m-%d')}"

    # 1) Markdown (en informes/)
    salida_md = Path(args.salida) if args.salida else reports / f"{slug}.md"
    salida_md.write_text(informe_md, encoding="utf-8")

    # 2) Último informe markdown
    (base / "ULTIMO-INFORME.md").write_text(informe_md, encoding="utf-8")

    # 3) HTML del informe (en docs/ para GitHub Pages)
    html_informe = render_informe_html(
        disposiciones_con_resumen, desde, hasta, titulo_fecha
    )
    (docs / f"{slug}.html").write_text(html_informe, encoding="utf-8")

    # 4) Reconstruir el índice a partir de todos los HTML de docs/
    reconstruir_indice(docs)

    print(f"📄 Markdown: {salida_md}")
    print(f"🌐 HTML: {docs / (slug + '.html')}")
    print(f"🏠 Índice: {docs / 'index.html'}")
    print("✅ Completado")


def reconstruir_indice(docs: Path):
    """Regenera docs/index.html listando todos los informes HTML presentes."""
    informes = []
    for f in docs.glob("monitor-*.html"):
        # Extraer fecha del nombre para ordenar
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        fecha_orden = m.group(1) if m else "0000-00-00"
        # Título legible y conteo de disposiciones
        contenido = f.read_text(encoding="utf-8")
        tm = re.search(r"<title>Monitor Legislativo Inmobiliario — (.+?)</title>", contenido)
        titulo = tm.group(1) if tm else f.stem
        cm = re.search(r"· (\d+) disposiciones</p>", contenido)
        total = int(cm.group(1)) if cm else 0
        informes.append(
            {"archivo": f.name, "titulo": titulo, "total": total, "fecha_orden": fecha_orden}
        )

    informes.sort(key=lambda x: x["fecha_orden"], reverse=True)
    (docs / "index.html").write_text(render_index_html(informes), encoding="utf-8")


if __name__ == "__main__":
    main()
