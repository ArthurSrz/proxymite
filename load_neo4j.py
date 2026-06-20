"""
load_neo4j.py — Matérialise les effectifs (open data EN) dans le graphe FSU-SNUipp.

Chaque ETP enseignant (etp_enseignants, 1er + 2nd degré) devient un Contact DÉRIVÉ
rattaché à son Etablissement par TRAVAILLE_DANS. C'est la matérialisation, nœud par
nœud, du « potentiel théorique » (Etablissement.effectif). Voir model/Note_de_modelisation.md.

Modèle (réutilise le schéma existant) :
    (:Contact {derive:true, corps, genre, tranche_age, tranche_anciennete, ...})
        -[:TRAVAILLE_DANS {source, quotite, annee}]->
    (:Etablissement {code_uai, effectif, ...})            # + label :Ecole si degré 1d

Usage :
    pip install -r requirements.txt
    # renseigner .env (NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD / NEO4J_DATABASE)
    python load_neo4j.py            # charge tout
    python load_neo4j.py 500        # smoke test : 500 premiers établissements
"""

import math
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "effectifs_personnels_EN.csv")
ANNEE = 2024
BATCH = 5000

# Décomposition de etp_enseignants en corps (2nd degré uniquement ; somme == etp_enseignants).
CORPS_2D = [
    ("Agrégés", "etp_agreges"),
    ("Certifiés", "etp_certifies"),
    ("PLP", "etp_plp"),
    ("Autres titulaires", "etp_autres_titulaires"),
    ("Non-titulaires", "etp_non_titulaires"),
]
AGE_BANDS = [("moins_35", "etp_moins_35_ans"), ("35_50", "etp_35_50_ans"), ("50_plus", "etp_50_ans_plus")]
ANC_BANDS = [
    ("moins_2", "etp_anciennete_moins_2_ans"),
    ("2_5", "etp_anciennete_2_5_ans"),
    ("5_8", "etp_anciennete_5_8_ans"),
    ("8_plus", "etp_anciennete_8_ans_plus"),
]


# --------------------------------------------------------------------------- #
# RÉPARTITION (cœur algorithmique)
# --------------------------------------------------------------------------- #
def apportion(weights, n):
    """Répartit `n` unités ENTIÈRES sur les catégories, proportionnellement à `weights`.

    Contrat (le reste du script en dépend) :
      - entrée : `weights` = liste de floats >= 0 (au moins un > 0), `n` = int >= 1
      - sortie : liste d'ENTIERS >= 0, MÊME longueur que `weights`, dont la SOMME == n

    Exemple : apportion([4.0, 1.0], 5)  ->  [4, 1]
              apportion([1.0, 1.0, 1.0], 5)  ->  une répartition entière de somme 5 (ex. [2, 2, 1])

    Méthode des plus forts restes (Hamilton) : on attribue d'abord la part entière de
    chaque catégorie, puis on distribue les unités restantes aux plus grandes fractions.
    Départage déterministe (fraction décroissante, puis poids, puis index) -> rejeu stable.
    """
    total = sum(weights)
    exact = [w / total * n for w in weights]          # part réelle visée
    counts = [math.floor(x) for x in exact]           # part entière garantie
    leftover = n - sum(counts)                         # unités restant à placer (< nb catégories)
    order = sorted(range(len(weights)),
                   key=lambda i: (exact[i] - counts[i], weights[i], -i), reverse=True)
    for i in range(leftover):
        counts[order[i]] += 1
    return counts


def distribute(categories, weights, n, offset, fallback="inconnu"):
    """Construit une liste de `n` labels via apportion(), décalée de `offset` pour
    décorréler les dimensions assignées indépendamment au même nœud."""
    w = [float(x) if (x is not None and not (isinstance(x, float) and math.isnan(x))) else 0.0 for x in weights]
    w = [x if x > 0 else 0.0 for x in w]
    if sum(w) <= 0:
        return [fallback] * n
    counts = apportion(w, n)
    seq = []
    for cat, c in zip(categories, counts):
        seq.extend([cat] * c)
    if n:
        offset %= n
        seq = seq[offset:] + seq[:offset]
    return seq


# --------------------------------------------------------------------------- #
# LECTURE CSV
# --------------------------------------------------------------------------- #
def _str(v):
    if v is None or v == "" or (isinstance(v, float) and math.isnan(v)):
        return None
    return str(v)


def _num(v):
    v = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(v) else float(v)


# --- Répartition des dimensions sur les n contacts d'un établissement ---------
# Chaque dimension est répartie indépendamment, puis assignée nœud par nœud. Les
# décalages de rotation (n//2, n//3, n//5, n//7) décorrèlent les dimensions entre
# elles : on n'affirme que les marginales (ce que la donnée mesure), pas les croisements.

def _corps_sequence(row, n, degre):
    if degre == "1d":
        return ["Professeur des écoles"] * n            # premier degré : corps unique
    return distribute([c[0] for c in CORPS_2D],
                      [_num(row.get(c[1])) for c in CORPS_2D], n, offset=0, fallback="Autre")


def _genre_sequence(row, n, ens):
    fem = _num(row.get("etp_femmes_enseignantes"))
    if fem is None:
        return ["inconnu"] * n
    part_femmes = min(max(fem / ens, 0.0), 1.0)
    return distribute(["F", "H"], [part_femmes, 1 - part_femmes], n, offset=n // 2)


def _band_sequence(row, n, bands, offset):
    """Répartit une dimension à tranches (âge, ancienneté) depuis ses marginales."""
    return distribute([b[0] for b in bands], [_num(row.get(b[1])) for b in bands], n, offset=offset)


def _affectation_sequence(row, n, degre, ens):
    if degre != "2d":
        return ["titulaire"] * n                        # part non-titulaires connue seulement en 2d
    nt = _num(row.get("etp_non_titulaires")) or 0.0
    part_nt = min(max(nt / ens, 0.0), 1.0)
    return distribute(["non_titulaire", "titulaire"], [part_nt, 1 - part_nt], n,
                      offset=n // 7, fallback="titulaire")


def _etablissement_record(row, uai, degre, effectif):
    nb_eleves = _num(row.get("nb_eleves"))
    return {
        "code_uai": uai,
        "nom": _str(row.get("nom_etablissement")),
        "type_etablissement": _str(row.get("type_etablissement")),
        "secteur": _str(row.get("statut_public_prive")),
        "commune": _str(row.get("nom_commune")),
        "code_postal": _str(row.get("code_postal")),
        "code_departement": _str(row.get("code_departement")),
        "libelle_departement": _str(row.get("libelle_departement")),
        "libelle_academie": _str(row.get("libelle_academie")),
        "libelle_region": _str(row.get("libelle_region")),
        "latitude": _num(row.get("latitude")),
        "longitude": _num(row.get("longitude")),
        "degre": degre,
        "nb_eleves": int(nb_eleves) if nb_eleves is not None else None,
        "effectif": effectif,                           # == nombre de contacts rattachés (invariant)
        "source": "open_data_EN",
        "is_1d": degre == "1d",                         # déclenche le label :Ecole côté Cypher
    }


def _contact_records(row, uai, degre, n, ens):
    """n contacts dérivés pour un établissement + leurs relations TRAVAILLE_DANS."""
    seqs = {
        "corps": _corps_sequence(row, n, degre),
        "genre": _genre_sequence(row, n, ens),
        "tranche_age": _band_sequence(row, n, AGE_BANDS, n // 3),
        "tranche_anciennete": _band_sequence(row, n, ANC_BANDS, n // 5),
        "type_affectation": _affectation_sequence(row, n, degre, ens),
    }
    contacts, edges = [], []
    for k in range(n):
        cid = f"{uai}#{k:04d}"
        contacts.append({
            "id_contact": cid,
            "corps": seqs["corps"][k],
            "genre": seqs["genre"][k],
            "tranche_age": seqs["tranche_age"][k],
            "tranche_anciennete": seqs["tranche_anciennete"][k],
            "type_affectation": seqs["type_affectation"][k],
            "degre": degre,
            "statut_adhesion": "inconnu",               # contact dérivé : non qualifié
            "qualite_donnee": 0.2,                      # faible : donnée synthétique
            "source": "effectifs_EN_2024",
            "annee_rentree": ANNEE,
            "derive": True,                             # sépare des ~150k contacts réels
        })
        edges.append({"sourceId": cid, "targetId": uai,
                      "source": "effectifs_EN_2024", "quotite": 1.0, "annee": ANNEE})
    return contacts, edges


def build_records(limit=None):
    """Lit le CSV et construit les records (établissements, contacts dérivés, relations).

    Ne garde que les degrés 1d/2d ayant round(etp_enseignants) >= 1 (sinon nœud orphelin).
    """
    df = pd.read_csv(CSV_PATH, low_memory=False)
    df = df[df["degre"].isin(["1d", "2d"])]

    etabs, contacts, edges = [], [], []
    for row in df.to_dict("records"):
        ens = _num(row.get("etp_enseignants"))
        if ens is None:
            continue
        effectif = int(round(ens))
        if effectif < 1:
            continue

        uai = _str(row.get("identifiant_de_l_etablissement"))
        degre = _str(row.get("degre"))

        etabs.append(_etablissement_record(row, uai, degre, effectif))
        row_contacts, row_edges = _contact_records(row, uai, degre, effectif, ens)
        contacts.extend(row_contacts)
        edges.extend(row_edges)

        if limit is not None and len(etabs) >= limit:
            break

    return etabs, contacts, edges


# --------------------------------------------------------------------------- #
# CYPHER
# --------------------------------------------------------------------------- #
# NB : le modèle canonique (Aura/Enterprise) utilise IS NODE KEY ; on retombe sur
# IS UNIQUE pour rester compatible avec Neo4j Community (instance locale).
CONSTRAINTS = [
    "CREATE CONSTRAINT Etablissement_uai IF NOT EXISTS FOR (n:Etablissement) REQUIRE n.code_uai IS UNIQUE",
    "CREATE CONSTRAINT Contact_id IF NOT EXISTS FOR (n:Contact) REQUIRE n.id_contact IS UNIQUE",
]

ETAB_CYPHER = """
UNWIND $records AS rec
MERGE (e:Etablissement {code_uai: rec.code_uai})
SET e += {nom: rec.nom, type_etablissement: rec.type_etablissement, secteur: rec.secteur,
          commune: rec.commune, code_postal: rec.code_postal, code_departement: rec.code_departement,
          libelle_departement: rec.libelle_departement, libelle_academie: rec.libelle_academie,
          libelle_region: rec.libelle_region, latitude: rec.latitude, longitude: rec.longitude,
          degre: rec.degre, nb_eleves: rec.nb_eleves, effectif: rec.effectif, source: rec.source}
FOREACH (_ IN CASE WHEN rec.is_1d THEN [1] ELSE [] END | SET e:Ecole)
"""

CONTACT_CYPHER = """
UNWIND $records AS rec
MERGE (c:Contact {id_contact: rec.id_contact})
SET c += {corps: rec.corps, genre: rec.genre, tranche_age: rec.tranche_age,
          tranche_anciennete: rec.tranche_anciennete, type_affectation: rec.type_affectation,
          degre: rec.degre, statut_adhesion: rec.statut_adhesion, qualite_donnee: rec.qualite_donnee,
          source: rec.source, annee_rentree: rec.annee_rentree, derive: rec.derive}
"""

EDGE_CYPHER = """
UNWIND $records AS rec
MATCH (c:Contact {id_contact: rec.sourceId})
MATCH (e:Etablissement {code_uai: rec.targetId})
MERGE (c)-[r:TRAVAILLE_DANS]->(e)
SET r += {source: rec.source, quotite: rec.quotite, annee: rec.annee}
"""


def _run_batches(driver, db, cypher, records, label):
    for i in range(0, len(records), BATCH):
        chunk = records[i:i + BATCH]
        driver.execute_query(cypher, records=chunk, database_=db)
        print(f"  {label}: {min(i + BATCH, len(records))}/{len(records)}", end="\r")
    print(f"  {label}: {len(records)}/{len(records)} ✓")


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    load_dotenv()
    uri = os.environ["NEO4J_URI"]
    auth = (os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    db = os.environ.get("NEO4J_DATABASE", "neo4j")

    print(f"Construction des records depuis {CSV_PATH}" + (f" (limit={limit})" if limit else ""))
    etabs, contacts, edges = build_records(limit)
    print(f"  -> {len(etabs)} établissements, {len(contacts)} contacts dérivés, {len(edges)} relations")

    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.verify_connectivity()
        print(f"Connecté à {uri} (db={db})")
        for c in CONSTRAINTS:
            driver.execute_query(c, database_=db)
        print("Contraintes OK")
        _run_batches(driver, db, ETAB_CYPHER, etabs, "Etablissement")
        _run_batches(driver, db, CONTACT_CYPHER, contacts, "Contact")
        _run_batches(driver, db, EDGE_CYPHER, edges, "TRAVAILLE_DANS")
    print("Terminé.")


if __name__ == "__main__":
    main()
