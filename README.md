# Proxymite

REST API + Streamlit dashboard + Neo4j graph over French public education staff data (source: data.education.gouv.fr, rentrée 2024) for the FSU-SNUipp union, targeting the December 2026 professional elections.

## Graph model: Connu / Inconnu

The graph separates two populations:

- **`:Contact`** (connu) — real people from the SNUPers CRM (465k total across all proximity circles)
- **`:Inconnu`** — synthetic nodes representing unknown teachers (1 per rounded ETP from open data effectifs EN)

Both are linked to their school via `TRAVAILLE_DANS`. The Inconnu pool shrinks as real contacts are identified: `effectif = Contact(reconciliable) + Inconnu`.

### Design decisions

**1. Only cercle 1-3 enseignants are loaded.**

SNUPers is a historical CRM that accumulates all contacts ever registered. The `cercle` field indicates proximity: 1=section (closest), 2=adherent, 3=sympathisant, 4=contact (most distant).

Cercle 4 contacts (272k, 58% of the base) are NOT loaded — too unreliable as an indicator of current assignment (ratio 1.19x vs national effectifs, 23k schools in excess). Cercle 4 may be added in a future iteration.

**2. Non-teaching staff (ASH, AESH) are excluded.**

The open data effectifs EN only counts `etp_enseignants` — there are no national statistics on non-teaching personnel (ASH = aide à la scolarisation handicap, AESH = accompagnants). These contacts are not loaded. This may evolve when a data source for non-teaching staff becomes available.

**3. Contacts without a valid UAI are kept.**

44k C1-C2-C3 contacts have UAI codes that don't match any établissement (internal SNUipp codes). They are loaded as `:Contact` without `TRAVAILLE_DANS` — the union knows them but doesn't know their current school.

### Matching par embeddings LLM

Les Contact et Inconnu de la même école sont appariés par similarité sémantique. Les propriétés de chaque nœud sont sérialisées en texte et encodées via `text-embedding-3-small` (OpenRouter). La similarité cosinus détermine l'appariement greedy. Les deux nœuds sont conservés, reliés par `(:Contact)-[:PROBABLEMENT_IDENTIQUE {score}]->(:Inconnu)` pour inspection et validation humaine.

## Setup

```bash
pip install -r requirements.txt
# Configure .env with NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE
```

## Usage

```bash
python load_model.py              # constraints + controlled vocabulary
python load_neo4j.py              # effectifs EN → :Inconnu nodes + geography
python reconcile_snupers.py       # SNUPers contacts → :Contact (C1-C2-C3 enseignants)
python match_embeddings.py        # matching Contact ↔ Inconnu par embeddings → PROBABLEMENT_IDENTIQUE

uvicorn api:app --reload          # REST API
streamlit run dashboard.py        # dashboard (password-protected)
```
