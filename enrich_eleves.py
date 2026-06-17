"""
Enrichit le CSV personnel avec le nombre d'élèves par établissement.

Sources :
  1er degré  : fr-en-ecoles-effectifs-nb_classes       (numero_ecole  → nombre_total_eleves)
  Collèges   : fr-en-college-effectifs-niveau-sexe-lv  (numero_college → nombre_eleves_total)
  Lycées     : fr-en-ips-lycees-ap2022                  (uai           → effectifs_ensemble_gt_pro)

Ajoute au CSV :
  nb_eleves          — nombre total d'élèves dans l'établissement
  eleves_par_etp     — élèves pour 1 ETP enseignant (taux d'encadrement)

Usage : python enrich_eleves.py
"""

from __future__ import annotations
import gzip, io, urllib.request
from pathlib import Path
import pandas as pd

CSV_PATH = Path("data/effectifs_personnels_EN.csv")
BASE_URL = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets"


def _fetch_csv(dataset_id: str) -> pd.DataFrame:
    """Download full CSV export — no 10k record cap."""
    url = f"{BASE_URL}/{dataset_id}/exports/csv?delimiter=%3B&lang=fr&timezone=Europe%2FParis"
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "proxymite/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
        if resp.info().get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
    df = pd.read_csv(io.StringIO(data.decode("utf-8-sig")), sep=";", low_memory=False)
    print(f"  {dataset_id}: {len(df):,} rows")
    return df


def build_eleves_index() -> pd.Series:
    """Returns Series indexed by UAI with nb_eleves values."""
    frames = []

    # 1er degré — écoles
    print("Fetching 1er degré (écoles)...")
    df1 = _fetch_csv("fr-en-ecoles-effectifs-nb_classes")
    df1 = (df1[["numero_ecole", "nombre_total_eleves", "rentree_scolaire"]]
           .sort_values("rentree_scolaire", ascending=False)
           .drop_duplicates("numero_ecole")
           .rename(columns={"numero_ecole": "uai", "nombre_total_eleves": "nb_eleves"}))
    df1["uai"] = df1["uai"].str.strip().str.upper()
    frames.append(df1[["uai", "nb_eleves"]].dropna())

    # Collèges
    print("Fetching collèges...")
    dfc = _fetch_csv("fr-en-college-effectifs-niveau-sexe-lv")
    dfc = (dfc[["numero_college", "nombre_eleves_total", "rentree_scolaire"]]
           .sort_values("rentree_scolaire", ascending=False)
           .drop_duplicates("numero_college")
           .rename(columns={"numero_college": "uai", "nombre_eleves_total": "nb_eleves"}))
    dfc["uai"] = dfc["uai"].str.strip().str.upper()
    frames.append(dfc[["uai", "nb_eleves"]].dropna())

    # Lycées GT + pro
    print("Fetching lycées...")
    dfl = _fetch_csv("fr-en-ips-lycees-ap2022")
    dfl = (dfl[["uai", "effectifs_ensemble_gt_pro", "rentree_scolaire"]]
           .sort_values("rentree_scolaire", ascending=False)
           .drop_duplicates("uai")
           .rename(columns={"effectifs_ensemble_gt_pro": "nb_eleves"}))
    dfl["uai"] = dfl["uai"].str.strip().str.upper()
    frames.append(dfl[["uai", "nb_eleves"]].dropna())

    combined = pd.concat(frames).drop_duplicates("uai").set_index("uai")["nb_eleves"]
    return combined


def enrich():
    print(f"Loading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, low_memory=False)

    # Drop old columns if re-running
    for col in ["nb_eleves", "eleves_par_etp", "ratio_eleves_par_etp"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    eleves = build_eleves_index()
    print(f"\nElèves index built: {len(eleves):,} établissements")

    df["nb_eleves"]      = df["identifiant_de_l_etablissement"].map(eleves)
    df["eleves_par_etp"] = df["nb_eleves"] / df["etp_enseignants"]

    matched = df["nb_eleves"].notna().sum()
    has_both = (df["nb_eleves"].notna() & df["etp_enseignants"].notna()).sum()
    print(f"nb_eleves matched : {matched:,}/{len(df):,} ({matched/len(df)*100:.1f}%)")
    print(f"ratio computable  : {has_both:,} établissements")
    if has_both:
        print(f"Median élèves/ETP : {df['eleves_par_etp'].median():.1f}")

    df.to_csv(CSV_PATH, index=False)
    print(f"Saved → {CSV_PATH}")


if __name__ == "__main__":
    enrich()
