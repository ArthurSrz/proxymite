"""
reconcile_snupers.py — Charge les contacts réels SNUPers et réconcilie avec les Inconnus.

Crée des nœuds :Contact depuis le CSV SNUPers, lie chacun à son Etablissement via
TRAVAILLE_DANS, puis supprime les :Inconnu en trop pour maintenir l'invariant :
    effectif == count(Contact TRAVAILLE_DANS) + count(Inconnu TRAVAILLE_DANS)

Usage :
    python reconcile_snupers.py            # charge tout
    python reconcile_snupers.py 100        # smoke test : 100 premiers contacts
"""

import math
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "snuppers_all_20260626.csv")
ANNEE = 2024
BATCH = 2000

CERCLE_MAP = {1: "section", 2: "adherent", 3: "sympathisant", 4: "contact"}

# Seuls les cercles 1-3 comptent pour la réconciliation (suppression d'Inconnus).
# Les cercle 4 ("contact" périphérique) sont trop peu fiables comme indicateur
# d'affectation réelle : 272k contacts, ratio 1.19x vs effectif, 23k dépassements.
# Les C4 sont chargés dans le graphe mais ne réduisent pas le pool d'Inconnus.
CERCLES_RECONCILIATION = {1, 2, 3}

# Métiers extra-scolaires exclus de la réconciliation (pas des enseignants,
# donc pas comptés dans etp_enseignants). Chargés dans le graphe mais
# ne réduisent pas le pool d'Inconnus.
METIERS_EXCLUS = {"ASH", "AESH"}


def _str(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    v = str(v).strip()
    return v if v else None


def _int(v):
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _clean_sexe(v):
    v = _str(v)
    if v in ("M", "F"):
        return v
    return None


def build_records(df, valid_uais):
    """Construit les records Contact + relations depuis le DataFrame SNUPers."""
    contacts, td_edges = [], []
    cercle_edges, vote_edges = [], []

    for row in df.to_dict("records"):
        sid = _str(row.get("id"))
        if not sid:
            continue

        excl = _int(row.get("exclusion"))
        if excl == 1:
            continue

        cercle = _int(row.get("cercle"))
        if cercle not in CERCLES_RECONCILIATION:
            continue

        metier = _str(row.get("metier"))
        if metier in METIERS_EXCLUS:
            continue

        cid = f"snupers#{sid}"
        uai = _str(row.get("etab_id"))

        tel = _str(row.get("Telephone")) or _str(row.get("Mobile"))

        contacts.append({
            "id_contact": cid,
            "id_snupers": sid,
            "nom": _str(row.get("Nom")),
            "prenom": _str(row.get("Prenom")),
            "email": _str(row.get("Email")),
            "telephone": tel,
            "date_naissance": _str(row.get("DateNaissance")),
            "genre": _clean_sexe(row.get("Sexe")),
            "corps": _str(row.get("idCorps")),
            "type_affectation": metier,
            "score_proximite": _float(row.get("score")),
            "propension_vote": _float(row.get("proba_vote")),
            "anciennete": _int(row.get("anciennete")),
            "cercle": cercle,
            "degre": "1d",
            "source": "snupers",
        })

        if uai and uai in valid_uais:
            td_edges.append({
                "sourceId": cid, "targetId": uai,
                "source": "snupers", "annee": ANNEE,
            })

        if cercle in CERCLE_MAP:
            cercle_edges.append({
                "sourceId": cid,
                "targetId": CERCLE_MAP[cercle],
            })

        for col, annee in [("vote22", 2022), ("vote18", 2018), ("vote14", 2014)]:
            v = _int(row.get(col))
            if v is not None and v == 1:
                vote_edges.append({
                    "sourceId": cid,
                    "electionId": f"elections_{annee}",
                    "annee": annee,
                })

    return contacts, td_edges, cercle_edges, vote_edges


# ---------------------------------------------------------------------------
# CYPHER
# ---------------------------------------------------------------------------

CONTACT_CONSTRAINTS = [
    "CREATE CONSTRAINT Contact_id IF NOT EXISTS "
    "FOR (n:Contact) REQUIRE n.id_contact IS UNIQUE",
]

CONTACT_CYPHER = """
UNWIND $records AS rec
MERGE (c:Contact {id_contact: rec.id_contact})
SET c += {id_snupers: rec.id_snupers, nom: rec.nom, prenom: rec.prenom,
          email: rec.email, telephone: rec.telephone,
          date_naissance: date(rec.date_naissance),
          genre: rec.genre, corps: rec.corps, type_affectation: rec.type_affectation,
          score_proximite: rec.score_proximite, propension_vote: rec.propension_vote,
          anciennete: rec.anciennete, cercle: rec.cercle,

          degre: rec.degre, source: rec.source}
"""

CONTACT_CYPHER_NO_DATE = """
UNWIND $records AS rec
MERGE (c:Contact {id_contact: rec.id_contact})
SET c += {id_snupers: rec.id_snupers, nom: rec.nom, prenom: rec.prenom,
          email: rec.email, telephone: rec.telephone,
          genre: rec.genre, corps: rec.corps, type_affectation: rec.type_affectation,
          score_proximite: rec.score_proximite, propension_vote: rec.propension_vote,
          anciennete: rec.anciennete, cercle: rec.cercle,

          degre: rec.degre, source: rec.source}
"""

TD_CYPHER = """
UNWIND $records AS rec
MATCH (c:Contact {id_contact: rec.sourceId})
MATCH (e:Etablissement {code_uai: rec.targetId})
MERGE (c)-[r:TRAVAILLE_DANS]->(e)
SET r += {source: rec.source, annee: rec.annee}
"""

CERCLE_CYPHER = """
UNWIND $records AS rec
MATCH (c:Contact {id_contact: rec.sourceId})
MATCH (cp:CercleProximite {nom: rec.targetId})
MERGE (c)-[:DANS_CERCLE]->(cp)
"""

ELECTION_CYPHER = """
UNWIND $records AS rec
MERGE (el:Election {id_election: rec.electionId})
ON CREATE SET el.annee = rec.annee
WITH el, rec
MATCH (c:Contact {id_contact: rec.sourceId})
MERGE (c)-[v:A_VOTE_A]->(el)
SET v.a_vote = true
"""

RECONCILE_CYPHER = """
MATCH (e:Etablissement)
WHERE e.effectif IS NOT NULL
OPTIONAL MATCH (c:Contact)-[:TRAVAILLE_DANS]->(e)
WITH e, count(c) AS nb_contacts
WHERE nb_contacts > 0
OPTIONAL MATCH (i:Inconnu)-[:TRAVAILLE_DANS]->(e)
WITH e, nb_contacts, collect(i) AS inconnus, count(i) AS nb_inconnus
WITH e, nb_contacts, inconnus, nb_inconnus,
     CASE WHEN nb_contacts >= e.effectif THEN nb_inconnus
          ELSE nb_contacts
     END AS to_delete
WHERE to_delete > 0
UNWIND inconnus[0..to_delete] AS victim
DETACH DELETE victim
RETURN count(victim) AS deleted
"""

UPDATE_CACHES = """
MATCH (e:Etablissement)
OPTIONAL MATCH (c:Contact)-[:TRAVAILLE_DANS]->(e)
OPTIONAL MATCH (i:Inconnu)-[:TRAVAILLE_DANS]->(e)
WITH e, count(DISTINCT c) AS nb_contacts, count(DISTINCT i) AS nb_inconnus
SET e.nb_contacts_reels = nb_contacts,
    e.nb_contacts_derives = nb_inconnus,
    e.depassement = CASE WHEN nb_contacts > e.effectif THEN nb_contacts - e.effectif ELSE null END
"""


def _run_batches(driver, db, cypher, records, label):
    for i in range(0, len(records), BATCH):
        chunk = records[i:i + BATCH]
        driver.execute_query(cypher, records=chunk, database_=db)
        print(f"  {label}: {min(i + BATCH, len(records))}/{len(records)}", end="\r")
    print(f"  {label}: {len(records)}/{len(records)} ✓")


def _split_by_date(contacts):
    """Sépare les contacts avec/sans date_naissance valide (Neo4j date() échoue sur null)."""
    with_date, without_date = [], []
    for c in contacts:
        if c["date_naissance"] and len(c["date_naissance"]) >= 10:
            with_date.append(c)
        else:
            c["date_naissance"] = None
            without_date.append(c)
    return with_date, without_date


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    load_dotenv()
    uri = os.environ["NEO4J_URI"]
    auth = (os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    db = os.environ.get("NEO4J_DATABASE", "neo4j")

    etab_uais = set(
        pd.read_csv(
            os.path.join(os.path.dirname(__file__), "data", "effectifs_personnels_EN.csv"),
            low_memory=False, usecols=["identifiant_de_l_etablissement"],
        )["identifiant_de_l_etablissement"]
    )

    print(f"Lecture de {CSV_PATH}" + (f" (limit={limit})" if limit else ""))
    df = pd.read_csv(CSV_PATH, low_memory=False)
    if limit:
        df = df.head(limit)

    contacts, td_edges, cercle_edges, vote_edges = build_records(df, etab_uais)
    print(f"  -> {len(contacts)} contacts, {len(td_edges)} liens TRAVAILLE_DANS, "
          f"{len(cercle_edges)} cercles, {len(vote_edges)} votes")

    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.verify_connectivity()
        print(f"Connecté à {uri} (db={db})")

        for c in CONTACT_CONSTRAINTS:
            try:
                driver.execute_query(c, database_=db)
            except Exception:
                pass
        print("Contraintes Contact OK")

        # --- 1. Charger les Contact SNUPers ---
        with_date, without_date = _split_by_date(contacts)
        if with_date:
            _run_batches(driver, db, CONTACT_CYPHER, with_date, "Contact (date)")
        if without_date:
            _run_batches(driver, db, CONTACT_CYPHER_NO_DATE, without_date, "Contact (no date)")

        _run_batches(driver, db, TD_CYPHER, td_edges, "TRAVAILLE_DANS")
        _run_batches(driver, db, CERCLE_CYPHER, cercle_edges, "DANS_CERCLE")
        _run_batches(driver, db, ELECTION_CYPHER, vote_edges, "A_VOTE_A")

        # --- 2. Mettre à jour les caches ---
        print("Mise à jour des caches Etablissement...")
        driver.execute_query(UPDATE_CACHES, database_=db)
        print("  Caches OK ✓")

    print("Terminé.")


if __name__ == "__main__":
    main()
