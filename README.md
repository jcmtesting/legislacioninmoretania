# Monitor Legislativo Inmobiliario — API del BOE

Monitor automatizado de novedades legislativas inmobiliarias que consume **directamente la API oficial de datos abiertos del BOE**, en lugar de depender de búsquedas web. Cobertura estatal + Castilla-La Mancha + Comunidad de Madrid.

## Por qué esta versión es mejor

La versión anterior dependía de búsquedas web, que fallaban por problemas de indexación (los famosos "⚠️ NO VERIFICADO"). Esta versión consume la [API de sumarios del BOE](https://www.boe.es/datosabiertos/documentos/APIsumarioBOE.pdf):

- **Determinista**: si la API responde 200, tienes el sumario completo del día. Cero falsos negativos en el BOE.
- **Sin API key para el BOE**: la API es pública y gratuita.
- **Filtrado por código**: la clasificación (MIVAU, DGSJFP, estatal, CLM, Madrid) se hace con reglas, no con IA. Reproducible y auditable.
- **IA solo para redactar**: la API de Anthropic se usa únicamente para resumir las disposiciones ya filtradas. Menor coste y variabilidad.

## Arquitectura

**Capa 1 — Datos estructurados (núcleo, verificado):**
- BOE vía API oficial → legislación, MIVAU, resoluciones DGSJFP, y normativa de CLM/Madrid publicada en el BOE.

**Capa 2 — Enriquecimiento (opcional, best-effort):**
- DOCM (sin API; fetch por portada) y fuentes doctrinales (notariosyregistradores.com, regispro.es). Si fallan, el informe del BOE sigue siendo completo.

Las fuentes de pago (Iberley, vLex, Lefebvre) quedan **fuera del automatismo**: legalmente no se pueden scrapear y su función (indexar el BOE) ya la cubre la API oficial mejor.

## Estructura del repositorio

```
├── .github/workflows/monitor-diario.yml   # Ejecución automática (cron)
├── monitor/
│   ├── config.py         # Keywords, departamentos, exclusiones
│   ├── boe_client.py     # Cliente de la API del BOE
│   ├── filtro.py         # Clasificación por materia inmobiliaria
│   ├── informe.py        # Generación del informe Markdown
│   └── docm_client.py    # DOCM (best-effort, sin API)
├── informes/             # Informes generados (uno por día/rango)
├── run.py                # Punto de entrada (CLI)
├── test_filtro.py        # Test del filtrado con casos reales
├── requirements.txt
├── ULTIMO-INFORME.md     # Siempre el último informe
└── README.md
```

## Uso local

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

python run.py                          # Informe de hoy
python run.py --fecha 2026-04-30       # Un día concreto
python run.py --desde 2026-05-01 --hasta 2026-05-15   # Rango
python run.py --dias 7                 # Últimos 7 días
python run.py --sin-ia                 # Sin resúmenes IA (solo títulos, gratis)
```

## Configuración en GitHub

1. Sube el repositorio a GitHub.
2. **Settings > Secrets and variables > Actions** → crea `ANTHROPIC_API_KEY`.
3. **Settings > Actions > General** → "Workflow permissions" → **Read and write permissions**.
4. El workflow corre de martes a sábado a las 08:00 (hora España). Cada BOE se publica ese mismo día.
5. Ejecución manual: **Actions > Monitor Diario > Run workflow** (permite indicar fecha o número de días).

## Verificación del filtrado

`test_filtro.py` valida la clasificación con casos reales:

```bash
python test_filtro.py
```

Comprueba que: MIVAU siempre entra, el RDL con IBI se clasifica como estatal, las resoluciones DGSJFP inmobiliarias entran pero las mercantiles no, la normativa foral/otras CCAA se descarta, el convenio de Madrid entra, y las plazas de ayuntamiento se excluyen.

## Sobre el DOCM y las fuentes doctrinales

El DOCM **no tiene API REST**. El módulo `docm_client.py` incluye un acceso best-effort a la portada, pero para un parsing robusto habría que extenderlo (por ejemplo con BeautifulSoup). El núcleo del BOE funciona de forma autónoma y verificada sin depender de ello.

## Subir el proyecto a GitHub (paso a paso)

Desde la carpeta `boe-monitor`:

```bash
cd boe-monitor
git init
git add .
git commit -m "Monitor legislativo inmobiliario - API BOE"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/boe-monitor.git
git push -u origin main
```

Crea antes el repositorio vacío en GitHub (sin README ni .gitignore, porque ya vienen incluidos).

Después, en la web del repo:
1. **Settings → Secrets and variables → Actions** → New repository secret → `ANTHROPIC_API_KEY`.
2. **Settings → Actions → General** → "Workflow permissions" → **Read and write permissions**.

## Visualización web (GitHub Pages)

El monitor genera, además del Markdown, una web estática en la carpeta `docs/`:
- `docs/index.html` — archivo de todos los informes (se reconstruye en cada ejecución).
- `docs/monitor-AAAA-MM-DD.html` — cada informe con diseño de boletín.

Para publicarla:
1. **Settings → Pages**.
2. En "Source" elige **Deploy from a branch**.
3. Branch: `main`, carpeta: **/docs**. Guarda.
4. En 1-2 minutos tu web estará en `https://TU-USUARIO.github.io/boe-monitor/`.

### Usar tu propio dominio

Si tienes un dominio (p. ej. `legislacion.tudominio.com`):

1. En **Settings → Pages → Custom domain**, escribe tu dominio y guarda. GitHub creará un archivo `CNAME` en el repo.
2. En tu proveedor de DNS (donde compraste el dominio), añade un registro:
   - Para un **subdominio** (`legislacion.tudominio.com`): registro **CNAME** apuntando a `TU-USUARIO.github.io`.
   - Para un **dominio raíz** (`tudominio.com`): cuatro registros **A** apuntando a las IP de GitHub Pages: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`.
3. Espera a la propagación DNS (de minutos a 24 h). Marca **Enforce HTTPS** en Pages cuando esté disponible.

El dominio mostrará el mismo `index.html` con el archivo de informes.

## Coste estimado

- API del BOE: **gratis**.
- GitHub Pages: **gratis**.
- API de Anthropic: solo resúmenes de disposiciones filtradas. En días normales (pocas disposiciones inmobiliarias), **céntimos por ejecución**. Con `--sin-ia`, gratis.
