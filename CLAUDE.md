# Proxymite — CLAUDE.md

## Project overview

REST API + Streamlit dashboard over French public education staff data
(source: data.education.gouv.fr, rentrée 2024).

## Files

| File | Role |
|------|------|
| `api.py` | FastAPI REST API — downloads, joins, and serves the CSV. Run: `uvicorn api:app --reload` |
| `data/effectifs_personnels_EN.csv` | ~68,936 rows, 48 columns. Built by `python api.py` |
| `dashboard.py` | Streamlit EDA dashboard. Run: `streamlit run dashboard.py` |

## Data schema

- **Identity**: UAI code, name, type, secteur (Public/Privé), address, lat/lon
- **Geography**: département, académie, région (19 regions, 107 dept, 34 académies)
- **ETP fields** (`etp_*`): Full-time equivalents — teachers, by gender, age, seniority, corps
- **Pct fields** (`pct_*`): Percentages — only populated for secondary schools (degré 2d, ~10,743 rows)

Two data completeness tiers:
- ~57,712 rows have `etp_enseignants` (basic teacher count)
- ~10,743 rows have `pct_*` columns (full profile, secondary only)

## Design system

Dashboard uses **Datack** (datack.fr) brand:
- Background: `#0D0D0D`
- Accent: `#C8FF00` (neon yellow)
- Text: `#FFFFFF`
- Cards: `#1A1A1A` with `1px solid #2A2A2A` border, `border-radius: 16-20px`
- Typography: bold, uppercase tags, large display headings

CSS injected via `st.markdown(..., unsafe_allow_html=True)` targeting Streamlit internal class names.

## Dashboard tabs

1. **Géographie** — scatter map (pydeck/mapbox), regional bar, dept ETP heatbar
2. **Types & Secteurs** — donut by type, grouped bar Public/Privé, nature top-10
3. **Genre & Corps** — % women histogram, corps composition pie, regional gender bar
4. **Âge & Ancienneté** — age pyramid, seniority funnel, % pies
5. **Vue régionale** — summary table with progress columns, scatter ETP vs gender, non-titulaires bar

## Key findings (EDA)

- 62.2% of teachers are women on average
- 11.5% non-tenured teachers nationally; Île-de-France highest at 15.7%
- Average school has 13.2 ETP teachers (median ~6.6 — heavily right-skewed by lycées)
- 47.9% of teachers have 8+ years seniority in their establishment
- Île-de-France: largest region (10,164 établissements), highest ETP average (17.4)
