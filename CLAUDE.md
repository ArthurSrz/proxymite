# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

REST API + Streamlit dashboard + Neo4j graph over French public education staff data
(source: data.education.gouv.fr, rentrée 2024). The Neo4j layer materializes teacher
ETP data into an FSU-SNUipp union graph model.

## Commands

```bash
# Rebuild the CSV from open data API (downloads + joins 1d/2d datasets)
python api.py [--out path.csv] [--quiet]

# Run the REST API
uvicorn api:app --reload

# Run the dashboard (password-protected via .streamlit/secrets.toml)
streamlit run dashboard.py

# Load data into Neo4j (requires .env with NEO4J_URI/USERNAME/PASSWORD)
python load_model.py          # constraints + controlled vocabulary
python load_neo4j.py          # effectifs EN → :Inconnu nodes + geography
python load_neo4j.py 500      # smoke test: first 500 établissements

# Load SNUPers contacts + reconcile with Inconnus
python reconcile_snupers.py        # full load (471k contacts)
python reconcile_snupers.py 100    # smoke test: first 100 contacts
```

## Architecture

| File | Role |
|------|------|
| `api.py` | FastAPI REST API — downloads, joins, and serves the CSV. Also runnable as CLI to rebuild `data/effectifs_personnels_EN.csv` |
| `dashboard.py` | Streamlit EDA dashboard (5 tabs, Datack brand). Password-gated via `_login_wall()` |
| `load_neo4j.py` | Materializes CSV rows into Neo4j as `(:Inconnu)` nodes linked via `TRAVAILLE_DANS` to `(:Etablissement)`. Scoped to 1er degré only |
| `reconcile_snupers.py` | Loads SNUPers contacts as `(:Contact)` nodes, links to établissements, and removes excess Inconnus to maintain `effectif == Contact + Inconnu` |
| `load_model.py` | Loads FSU-SNUipp graph model constraints and controlled vocabulary from `model/` |
| `enrich_eleves.py` | Enriches establishments with student count data from a separate open data source |
| `model/` | Graph schema: Cypher ingestion scripts, `.arrows.json` visual model, Mermaid diagram, Pydantic models (`fsu_snuipp_models.py`), modeling notes |

## Data schema

- **Identity**: UAI code, name, type, secteur (Public/Privé), address, lat/lon
- **Geography**: département → académie → région (19 regions, 107 dept, 34 académies)
- **ETP fields** (`etp_*`): Full-time equivalents — teachers, by gender, age, seniority, corps
- **Pct fields** (`pct_*`): Percentages — only populated for secondary schools (degré 2d, ~10,743 rows)

Two data completeness tiers:
- ~57,712 rows have `etp_enseignants` (basic teacher count)
- ~10,743 rows have `pct_*` columns (full profile, secondary only)

## Neo4j graph model

FSU-SNUipp union schema with geographic spine: `Departement → Academie → Region` with effectif rollups.

Two populations in the graph:
- **`:Contact`** — real people from SNUPers CRM (465k total, all circles)
- **`:Inconnu`** — synthetic nodes representing unknown teachers (1 per rounded ETP)

### Key design decisions

**1. Only cercle 1-3 enseignants are loaded as Contact.**

SNUPers is a historical CRM — it accumulates all contacts ever registered. The `cercle` field (1=section, 2=adherent, 3=sympathisant, 4=contact) indicates proximity. Cercle 4 ("contact périphérique", 272k / 58% of the base) is NOT loaded — too unreliable as an indicator of current assignment (ratio 1.19x vs effectif, 23k schools in excess). Cercle 4 may be added later.

**2. Non-teaching staff (ASH, AESH) are excluded.**

No national statistics exist for them in the open data effectifs EN (which only counts `etp_enseignants`). They are not loaded. This may evolve when a data source becomes available.

**3. Contacts without a valid UAI are kept.**

44k C1-C2-C3 contacts have UAI codes that don't match any établissement (internal SNUipp codes like `07500000`, `075DISPO`). They are loaded as `:Contact` without `TRAVAILLE_DANS` — the union knows them but doesn't know their school.

### Matching Contact ↔ Inconnu par embeddings LLM

Au lieu de supprimer aveuglément des Inconnus, chaque Contact est apparié à l'Inconnu le plus similaire dans la même école via des embeddings LLM (`text-embedding-3-small` via OpenRouter). Les propriétés de chaque nœud sont sérialisées en texte et encodées. La similarité cosinus détermine l'appariement. Les deux nœuds sont conservés, reliés par `PROBABLEMENT_IDENTIQUE {score}` pour inspection.

### The invariant

`effectif == count(Inconnu TRAVAILLE_DANS école)` (avant réconciliation)

Après matching : les Contact appariés à un Inconnu sont reliés par `PROBABLEMENT_IDENTIQUE`. Les Inconnus non appariés sont les vrais inconnus du syndicat.

## Design system

Dashboard uses **Datack** (datack.fr) brand:
- Background: `#0D0D0D`, Accent: `#C8FF00` (neon yellow), Text: `#FFFFFF`
- Cards: `#1A1A1A` with `1px solid #2A2A2A` border, `border-radius: 16-20px`
- Design tokens in `C` dict at top of `dashboard.py`

CSS injected via `st.markdown(..., unsafe_allow_html=True)` targeting Streamlit internal class names.

## Environment

- `.env`: Neo4j connection credentials (used by `load_neo4j.py` and `load_model.py`)
- `.streamlit/secrets.toml`: Dashboard password
- Dependencies: `pip install -r requirements.txt` (streamlit, pandas, plotly, neo4j, python-dotenv)
