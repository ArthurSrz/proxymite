"""
API REST — Effectifs personnels de l'Éducation Nationale.

Démarrage :  uvicorn api:app --reload
Rebuild CSV : python api.py [--out effectifs.csv] [--quiet]

Endpoints :
    GET /etablissements       — liste paginée avec filtres
    GET /etablissements/{uai} — fiche par code UAI
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets"
CSV_PATH = Path("data/effectifs_personnels_EN.csv")

PERSONNEL_DATASETS: list[tuple[str, str]] = [
    ("2d", "fr-en-indicateurs_personnels_etablissements2d"),
    ("1d", "fr-en-indicateurs_personnels_etablissements1d"),
]

FIELDNAMES: list[str] = [
    "identifiant_de_l_etablissement", "nom_etablissement", "type_etablissement",
    "statut_public_prive", "adresse_1", "code_postal", "nom_commune",
    "code_departement", "libelle_departement", "code_academie", "libelle_academie",
    "code_region", "libelle_region", "latitude", "longitude",
    "date_ouverture", "etat", "libelle_nature", "appartenance_education_prioritaire",
    "degre", "annee_de_la_rentree_scolaire",
    "etp_enseignants", "etp_femmes_enseignantes",
    "etp_moins_35_ans", "etp_35_50_ans", "etp_50_ans_plus",
    "etp_anciennete_moins_2_ans", "etp_anciennete_2_5_ans",
    "etp_anciennete_5_8_ans", "etp_anciennete_8_ans_plus",
    "etp_total", "etp_vie_scolaire", "etp_agreges", "etp_certifies",
    "etp_plp", "etp_autres_titulaires", "etp_non_titulaires",
    "pct_femmes", "pct_agreges", "pct_certifies", "pct_non_titulaires",
    "pct_moins_35_ans", "pct_35_50_ans", "pct_plus_50_ans",
    "pct_anciennete_moins_2_ans", "pct_anciennete_2_5_ans",
    "pct_anciennete_5_8_ans", "pct_anciennete_8_ans_plus",
]

_ANNUAIRE_KEYS = {
    "identifiant_de_l_etablissement", "nom_etablissement", "type_etablissement",
    "statut_public_prive", "adresse_1", "code_postal", "nom_commune",
    "code_departement", "libelle_departement", "code_academie", "libelle_academie",
    "code_region", "libelle_region", "latitude", "longitude",
    "date_ouverture", "etat", "libelle_nature", "appartenance_education_prioritaire",
}
_EMPTY_PERSONNEL: dict[str, str] = {k: "" for k in FIELDNAMES if k not in _ANNUAIRE_KEYS}
_FLOAT_FIELDS = {f for f in FIELDNAMES if f.startswith(("etp_", "pct_", "lat", "lon"))}

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class Etablissement(BaseModel):
    identifiant_de_l_etablissement: str
    nom_etablissement: str
    type_etablissement: str
    statut_public_prive: str
    adresse_1: str
    code_postal: str
    nom_commune: str
    code_departement: str
    libelle_departement: str
    code_academie: str
    libelle_academie: str
    code_region: str
    libelle_region: str
    latitude: float | None = None
    longitude: float | None = None
    date_ouverture: str
    etat: str
    libelle_nature: str
    appartenance_education_prioritaire: str
    degre: str
    annee_de_la_rentree_scolaire: str
    etp_enseignants: float | None = None
    etp_femmes_enseignantes: float | None = None
    etp_moins_35_ans: float | None = None
    etp_35_50_ans: float | None = None
    etp_50_ans_plus: float | None = None
    etp_anciennete_moins_2_ans: float | None = None
    etp_anciennete_2_5_ans: float | None = None
    etp_anciennete_5_8_ans: float | None = None
    etp_anciennete_8_ans_plus: float | None = None
    etp_total: float | None = None
    etp_vie_scolaire: float | None = None
    etp_agreges: float | None = None
    etp_certifies: float | None = None
    etp_plp: float | None = None
    etp_autres_titulaires: float | None = None
    etp_non_titulaires: float | None = None
    pct_femmes: float | None = None
    pct_agreges: float | None = None
    pct_certifies: float | None = None
    pct_non_titulaires: float | None = None
    pct_moins_35_ans: float | None = None
    pct_35_50_ans: float | None = None
    pct_plus_50_ans: float | None = None
    pct_anciennete_moins_2_ans: float | None = None
    pct_anciennete_2_5_ans: float | None = None
    pct_anciennete_5_8_ans: float | None = None
    pct_anciennete_8_ans_plus: float | None = None


class PaginatedResponse(BaseModel):
    total: int
    limit: int = Field(ge=1, le=1000)
    offset: int = Field(ge=0)
    items: list[Etablissement]

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def _fetch_csv(dataset_id: str) -> str:
    url = f"{BASE_URL}/{dataset_id}/exports/csv?delimiter=%3B&lang=fr&timezone=Europe%2FParis"
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
        if resp.info().get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
    return data.decode("utf-8-sig")


def _extract_etp_enseignants(row: dict[str, str]) -> str:
    return (
        row.get("etp_enseignants_hommes_et_femmes")
        or row.get("etp_d_enseignants_hommes_et_femmes", "")
    )


def build_csv(out_path: Path = CSV_PATH, verbose: bool = True) -> None:
    """Télécharge annuaire + personnels et écrit le CSV joint (68 936 lignes)."""
    # 1. Index personnels {uai: données} — 2d prioritaire sur 1d
    personnel_index: dict[str, dict[str, str]] = {}
    for degre, dataset_id in PERSONNEL_DATASETS:
        if verbose:
            print(f"  Chargement personnels {degre}...")
        reader = csv.DictReader(io.StringIO(_fetch_csv(dataset_id)), delimiter=";")
        for row in reader:
            uai = row.get("identifiant_de_l_etablissement", "").strip()
            if uai and uai not in personnel_index:
                etp_ens = _extract_etp_enseignants(row)
                personnel_index[uai] = {
                    "degre": degre,
                    "annee_de_la_rentree_scolaire": row.get("annee_de_la_rentree_scolaire", ""),
                    "etp_enseignants": etp_ens,
                    "etp_femmes_enseignantes": row.get("etp_de_femmes_enseignantes", ""),
                    "etp_moins_35_ans": row.get("etp_d_enseignants_de_moins_de_35_ans", ""),
                    "etp_35_50_ans": row.get("etp_d_enseignants_de_35_a_moins_de_50_ans", ""),
                    "etp_50_ans_plus": row.get("etp_d_enseignants_de_50_ans_ou_plus", ""),
                    "etp_anciennete_moins_2_ans": row.get("etp_d_enseignants_ayant_une_anciennete_dans_l_etablissement_de_moins_de_2_ans", ""),
                    "etp_anciennete_2_5_ans": row.get("etp_d_enseignants_ayant_une_anciennete_dans_l_etablissement_de_2_ans_a_moins_de_5_ans", ""),
                    "etp_anciennete_5_8_ans": row.get("etp_d_enseignants_ayant_une_anciennete_dans_l_etablissement_de_5_ans_a_moins_de_8_ans", ""),
                    "etp_anciennete_8_ans_plus": row.get("etp_d_enseignants_ayant_une_anciennete_dans_l_etablissement_de_8_ans_ou_plus", ""),
                    "etp_total": row.get("etp_total", ""),
                    "etp_vie_scolaire": row.get("etp_de_personnels_de_vie_scolaire", ""),
                    "etp_agreges": row.get("etp_d_enseignants_agreges", ""),
                    "etp_certifies": row.get("etp_d_enseignants_certifies_peps", ""),
                    "etp_plp": row.get("etp_d_enseignants_plp", ""),
                    "etp_autres_titulaires": row.get("etp_d_enseignants_titulaires_d_un_autre_corps", ""),
                    "etp_non_titulaires": row.get("etp_d_enseignants_non_titulaires", ""),
                    "pct_femmes": row.get("proportion_femmes_enseignantes", ""),
                    "pct_agreges": row.get("proportion_agreges", ""),
                    "pct_certifies": row.get("proportion_certifies", ""),
                    "pct_non_titulaires": row.get("proportion_non_titulaires", ""),
                    "pct_moins_35_ans": row.get("proportion_moins_de_35_ans", ""),
                    "pct_35_50_ans": row.get("proportion_35_50_ans", ""),
                    "pct_plus_50_ans": row.get("proportion_plus_de_50_ans", ""),
                    "pct_anciennete_moins_2_ans": row.get("anciennete_moins_de_2_ans", ""),
                    "pct_anciennete_2_5_ans": row.get("anciennete_2_a_5_ans", ""),
                    "pct_anciennete_5_8_ans": row.get("anciennete_5_a_8_ans", ""),
                    "pct_anciennete_8_ans_plus": row.get("anciennete_8_ans", ""),
                }

    # 2. Annuaire → left join → CSV
    if verbose:
        print("  Chargement annuaire complet...")
    annuaire_reader = csv.DictReader(io.StringIO(_fetch_csv("fr-en-annuaire-education")), delimiter=";")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for ann in annuaire_reader:
            uai = ann.get("identifiant_de_l_etablissement", "").strip()
            personnel = personnel_index.get(uai, _EMPTY_PERSONNEL)
            writer.writerow({
                "identifiant_de_l_etablissement": uai,
                "nom_etablissement": ann.get("nom_etablissement", ""),
                "type_etablissement": ann.get("type_etablissement", ""),
                "statut_public_prive": ann.get("statut_public_prive", ""),
                "adresse_1": ann.get("adresse_1", ""),
                "code_postal": ann.get("code_postal", ""),
                "nom_commune": ann.get("nom_commune", ""),
                "code_departement": ann.get("code_departement", ""),
                "libelle_departement": ann.get("libelle_departement", ""),
                "code_academie": ann.get("code_academie", ""),
                "libelle_academie": ann.get("libelle_academie", ""),
                "code_region": ann.get("code_region", ""),
                "libelle_region": ann.get("libelle_region", ""),
                "latitude": ann.get("latitude", ""),
                "longitude": ann.get("longitude", ""),
                "date_ouverture": ann.get("date_ouverture", ""),
                "etat": ann.get("etat", ""),
                "libelle_nature": ann.get("libelle_nature", ""),
                "appartenance_education_prioritaire": ann.get("appartenance_education_prioritaire", ""),
                **personnel,
            })

    if verbose:
        print(f"  → {out_path} écrit ({out_path.stat().st_size // 1024} Ko)")

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

def _load_store(path: Path) -> tuple[list[Etablissement], dict[str, Etablissement]]:
    records: list[Etablissement] = []
    index: dict[str, Etablissement] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parsed = {k: (float(v) if k in _FLOAT_FIELDS and v else (None if k in _FLOAT_FIELDS else v)) for k, v in row.items()}
            etab = Etablissement.model_validate(parsed)
            records.append(etab)
            index[etab.identifiant_de_l_etablissement] = etab
    return records, index

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not CSV_PATH.exists():
        print(f"{CSV_PATH} absent — téléchargement...")
        build_csv()
    print("Chargement en mémoire...")
    app.state.records, app.state.index = _load_store(CSV_PATH)
    print(f"  → {len(app.state.records):,} établissements prêts")
    yield


app = FastAPI(
    title="Effectifs Éducation Nationale",
    description="Personnels des établissements scolaires (source : data.education.gouv.fr)",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/etablissements", response_model=PaginatedResponse)
def list_etablissements(
    departement: Annotated[str | None, Query(description="Code département ex: 75")] = None,
    academie: Annotated[str | None, Query(description="Code académie")] = None,
    type_etablissement: Annotated[str | None, Query(description="Collège, Lycée, Ecole…")] = None,
    degre: Annotated[str | None, Query(description="1d ou 2d")] = None,
    secteur: Annotated[str | None, Query(description="Public ou Privé")] = None,
    avec_etp: Annotated[bool | None, Query(description="Filtrer sur présence de données ETP")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse:
    results: list[Etablissement] = app.state.records
    if departement:
        results = [r for r in results if r.code_departement == departement]
    if academie:
        results = [r for r in results if r.code_academie == academie]
    if type_etablissement:
        q = type_etablissement.lower()
        results = [r for r in results if q in r.type_etablissement.lower()]
    if degre:
        results = [r for r in results if r.degre == degre]
    if secteur:
        results = [r for r in results if secteur.lower() in r.statut_public_prive.lower()]
    if avec_etp is True:
        results = [r for r in results if r.etp_enseignants is not None]
    elif avec_etp is False:
        results = [r for r in results if r.etp_enseignants is None]
    return PaginatedResponse(total=len(results), limit=limit, offset=offset, items=results[offset:offset + limit])


@app.get("/etablissements/{uai}", response_model=Etablissement)
def get_etablissement(uai: str) -> Etablissement:
    etab = app.state.index.get(uai.upper())
    if etab is None:
        raise HTTPException(status_code=404, detail=f"Établissement '{uai}' introuvable")
    return etab

# ---------------------------------------------------------------------------
# CLI (rebuild CSV)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construit le CSV des effectifs EN")
    parser.add_argument("--out", default=str(CSV_PATH))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    build_csv(out_path=Path(args.out), verbose=not args.quiet)
