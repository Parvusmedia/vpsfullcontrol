# Consultant Radar

Radar de ofertas de trabajo en consultoras (Accenture Song, Deloitte, KPMG, PwC y otras).

No sustituye a `prospeccion-consultoras` (contacto a personas). Este repo vigila **vacantes publicadas** en los portales de empleo de cada firma. Por defecto se quedan las que pegan con digital / martech / CX (`config/filters.json`). `./run.sh scan --all` guarda el resto (sigue aplicando exclusiones: tax, audit, intern, junior).

Python 3.11+, solo librería estándar.

## Comandos

```bash
cd consultant-radar
./run.sh companies
./run.sh scan                  # dry-ish: lee ATS públicos, guarda SQLite, imprime novedades
./run.sh scan --company deloitte-es --json
./run.sh list --new --limit 40
./run.sh digest --out data/digest.md
```

El primer `scan` marca todo como nuevo. El siguiente solo lista lo que no estaba en `data/radar.sqlite`.

## Fuentes (MVP)

| Empresa | Fuente | Portal |
| --- | --- | --- |
| Accenture (Song / Adobe / CX) | Workday JSON | `accenture.wd103.myworkdayjobs.com` |
| Deloitte US | Avature RSS | `apply.deloitte.com` |
| Deloitte España | Phenom HTML | `empleo.es.deloitte.com` |
| KPMG España | Phenom HTML | `carreras.kpmg.es` |
| PwC | Workday JSON | `pwc.wd3.myworkdayjobs.com` |
| Thoughtworks | Greenhouse API | `boards-api.greenhouse.io` |
| Capgemini | RSS Taleo | `jobs.capgemini.com` |

Config: `config/companies.json`. Keywords: `config/filters.json`.

Filtro por defecto: exige al menos una keyword include (`martech`, `adobe`, `song`, `digital`, …) y descarta tax / audit / intern / junior. `scan --all` relaja el include.

Workday pagina de 20 en 20 (tope del API). `max_pages` por empresa evita barrer decenas de miles de roles de Accenture India.

## Tests

```bash
cd consultant-radar
python3 -m unittest discover -s tests -v
```

Scan live (red, opcional):

```bash
CONSULTANT_RADAR_LIVE=1 python3 -m unittest tests.test_live_scan -v
```

## Extraer a repo propio

Este árbol es autónomo. Para publicarlo como `Parvusmedia/consultant-radar`:

```bash
# en una máquina con permiso de crear repos
gh repo create Parvusmedia/consultant-radar --private --source consultant-radar --remote origin --push
```

En este entorno el `gh` de GitHub es de solo lectura, así que el código vive primero en `vpsfullcontrol`.

## Siguientes pasos

- Making Science (SuccessFactors `career55.sapsf.eu`, company `makingscie`) y NTT DATA (Phenom).
- Cron VPS o GitHub Actions programado + digest a Slack.
- Faceta Workday “Song” por oficina cuando el título no lo dice.
