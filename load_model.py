"""
load_model.py — Applique le schéma canonique FSU-SNUipp pour préparer l'ingestion.

Exécute model/fsu_snuipp_ingestion.cypher en ne gardant que ce qui ne dépend PAS de
données réelles :
  - les CONTRAINTES (section 1) — squelette du modèle (19 types de nœuds) ;
  - le VOCABULAIRE CONTRÔLÉ (section 2) — CercleProximite, ObjectifAction, TypeAction.

Les blocs paramétrés par $records (sections 3-4 : contacts, adhésions, campagnes...) sont
IGNORÉS : ce sont des gabarits réservés à l'ingestion de données réelles à venir.

Les contraintes IS NODE KEY (Enterprise/Aura) sont converties en IS UNIQUE si le serveur
tourne en édition Community.

Usage :
    python load_model.py
"""

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

CYPHER_FILE = os.path.join(os.path.dirname(__file__), "model", "fsu_snuipp_ingestion.cypher")


def iter_statements(path):
    """Découpe le fichier Cypher en instructions, en retirant les lignes de commentaire //."""
    with open(path, encoding="utf-8") as fh:
        code = "\n".join(line for line in fh if not line.lstrip().startswith("//"))
    for statement in code.split(";"):
        statement = statement.strip()
        if statement:
            yield statement


def is_enterprise(driver, db):
    records = driver.execute_query(
        "CALL dbms.components() YIELD edition RETURN edition", database_=db).records
    return bool(records) and records[0]["edition"] == "enterprise"


def main():
    load_dotenv()
    uri = os.environ["NEO4J_URI"]
    auth = (os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    db = os.environ.get("NEO4J_DATABASE", "neo4j")

    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.verify_connectivity()
        enterprise = is_enterprise(driver, db)
        print(f"Connecté à {uri} (db={db}) — édition {'enterprise' if enterprise else 'community'}")

        ran = skipped = 0
        for statement in iter_statements(CYPHER_FILE):
            if "$records" in statement:        # gabarit d'ingestion de données réelles -> ignoré
                skipped += 1
                continue
            if not enterprise:
                statement = statement.replace("IS NODE KEY", "IS UNIQUE")
            driver.execute_query(statement, database_=db)
            ran += 1

        print(f"{ran} instructions appliquées (contraintes + vocabulaire), "
              f"{skipped} gabarits $records ignorés")
    print("Schéma canonique chargé.")


if __name__ == "__main__":
    main()
